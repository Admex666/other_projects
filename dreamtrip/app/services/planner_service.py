import os
import json
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from app.services.destination_service import get_filtered_destinations
from app.services.destination_scoring_service import evaluate_destination_candidate, calculate_destination_rankings
from app.services.numbeo_service import get_city_cost_and_safety
from app.services.exchange_service import get_eur_huf_rate
from app.scrapers import scraper
from app.scrapers import accommodation_scraper

def calculate_planner_destinations_sync(
    origin: str,
    adults: int,
    children: int,
    month: int,
    duration_days: int,
    target_temp: float = 24.0,
    min_safety: int = 50,
    preferred_regions: Optional[List[str]] = None,
    exclusions: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Kiszámítja és rangsorolja a célállomásokat a Master Planner intake preferenciák alapján.
    """
    exclusions = exclusions or []
    all_dests = get_filtered_destinations(exclusions)

    # Régió szűrés ha meg van adva
    if preferred_regions and len(preferred_regions) > 0 and "all" not in preferred_regions:
        all_dests = [d for d in all_dests if d.get("region") in preferred_regions]
        if not all_dests: # fallback ha túl szigorú
            all_dests = get_filtered_destinations(exclusions)

    n = len(all_dests)
    origin_clean = origin.split("(")[0].strip()
    tokens = scraper.get_kiwi_tokens(headless=True)

    completed = 0
    def process_dest(d):
        nonlocal completed
        res = evaluate_destination_candidate(
            dest=d,
            origin_city=origin_clean,
            month=month,
            duration_days=duration_days,
            tokens=tokens,
            target_temp=target_temp,
            adults=adults,
            children=children
        )
        completed += 1
        if progress_callback:
            progress_callback(int((completed / max(1, n)) * 80), f"Adatok gyűjtése ({completed}/{n}): {d.get('name')}")
        return res

    with ThreadPoolExecutor(max_workers=8) as executor:
        candidates_raw = list(executor.map(process_dest, all_dests))

    # Súlyok összeállítása
    w_dict = weights or {
        "flight": 30.0,
        "cost": 20.0,
        "weather": 30.0,
        "safety": 20.0
    }

    if progress_callback:
        progress_callback(90, "Végső rangsorolás és indoklások összeállítása...")

    ranked = calculate_destination_rankings(
        candidates_raw=candidates_raw,
        weights=w_dict,
        target_temp=target_temp,
        adults=adults
    )

    # Biztonsági minimum szűrés (ha a felhasználó kéri)
    if min_safety > 0:
        ranked = [r for r in ranked if r.get("metrics", {}).get("safety_raw", 100) >= min_safety]
        if not ranked: # Fallback ha minden kiesne
            ranked = calculate_destination_rankings(candidates_raw, w_dict, target_temp, adults)

    for idx, r in enumerate(ranked):
        r["rank"] = idx + 1

    return ranked

def search_and_rank_planner_flights(
    origin: str,
    destination: str,
    month: int,
    duration_days: int,
    adults: int = 2,
    children: int = 0,
    direct_only: bool = False,
    max_stops: int = 1,
    departure_pref: str = "any" # any, morning, afternoon, evening
) -> List[Dict[str, Any]]:
    """
    Lekéri és rangsorolja a valós járatokat a célvárosra a megadott preferenciákkal.
    """
    origin_clean = origin.split("(")[0].strip()
    dest_clean = destination.split("(")[0].strip()

    tokens = scraper.get_kiwi_tokens(headless=True)
    
    # Dátumok generálása az adott hónapra
    if month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
    elif month in [4, 6, 9, 11]: last_day = 30
    else: last_day = 28

    date_out_start = f"2026-{month:02d}-01"
    date_out_end = f"2026-{month:02d}-{min(24, last_day):02d}"
    
    next_m = (month % 12) + 1
    date_in_start = f"2026-{month:02d}-{min(last_day, max(1, 1 + duration_days)):02d}"
    date_in_end = f"2026-{next_m:02d}-10"

    outbound = scraper.search_flights_by_city_name_v2(
        origin_name=origin_clean,
        destination_name=dest_clean,
        tokens=tokens,
        date_from=date_out_start,
        date_to=date_out_end,
        adults=adults,
        children=children,
        limit=40
    )

    inbound = scraper.search_flights_by_city_name_v2(
        origin_name=dest_clean,
        destination_name=origin_clean,
        tokens=tokens,
        date_from=date_in_start,
        date_to=date_in_end,
        adults=adults,
        children=children,
        limit=40
    )

    if outbound.empty or inbound.empty:
        return []

    min_stay = max(1, duration_days - 2)
    max_stay = duration_days + 2
    combinations = scraper.create_return_combinations(
        outbound, inbound, min_stay_days=min_stay, max_stay_days=max_stay
    )

    if combinations is None or (isinstance(combinations, pd.DataFrame) and combinations.empty) or len(combinations) == 0:
        return []

    df = combinations.copy() if isinstance(combinations, pd.DataFrame) else pd.DataFrame(combinations)

    # Szűrések alkalmazása
    if direct_only:
        df = df[(df['out_stops'] == 0) & (df['in_stops'] == 0)]
    elif max_stops is not None:
        df = df[(df['out_stops'] <= max_stops) & (df['in_stops'] <= max_stops)]

    if df.empty:
        df = pd.DataFrame(combinations) # Fallback ha a szűrő mindent kizárt

    # PROMETHEE II rangsorolás
    n = len(df)
    if n == 0:
        return []

    # g1: Ár (Min), g2: Utazási idő (Min), g3: Átszállások (Min)
    df['g1'] = df['total_price_huf']
    df['g2'] = df['out_duration_h'] + df['in_duration_h']
    df['g3'] = df['out_stops'] + df['in_stops']

    cols = ['g1', 'g2', 'g3']
    weights = [0.45, 0.35, 0.20] # Ár, Utazási idő, Átszállás

    data_mat = df[cols].values
    phi_plus = np.zeros(n)
    phi_minus = np.zeros(n)

    for i in range(n):
        for j in range(n):
            if i == j: continue
            diff = data_mat[j] - data_mat[i] # minimalizálás: j - i > 0 ha i jobb mint j
            pref = np.where(diff > 0, 1.0, 0.0)
            score = np.dot(weights, pref)
            phi_plus[i] += score
            phi_minus[j] += score

    if n > 1:
        phi_plus /= (n - 1)
        phi_minus /= (n - 1)
        df['phi_net'] = (phi_plus - phi_minus + 1) / 2
    else:
        df['phi_net'] = 1.0

    # Convert Timestamp columns to str for JSON serialization
    for col in ['out_dep_time', 'out_arr_time', 'in_dep_time', 'in_arr_time']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df_sorted = df.sort_values('phi_net', ascending=False)
    results_list = df_sorted.head(20).to_dict(orient='records')
    
    for idx, r in enumerate(results_list):
        r["rank"] = idx + 1

    return results_list
