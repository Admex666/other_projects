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

def compute_ahp_weights_from_comparisons(
    criteria: List[str],
    comparisons: Dict[str, float]
) -> Dict[str, float]:
    """
    Kiszámítja az AHP normalizált sajátvektor-súlyokat páros összehasonlító mátrixból.
    """
    n = len(criteria)
    if n == 0:
        return {}
    if n == 1:
        return {criteria[0]: 1.0}

    matrix = np.ones((n, n))
    for key, val in comparisons.items():
        parts = key.split("_vs_")
        if len(parts) == 2:
            c1, c2 = parts
            if c1 in criteria and c2 in criteria:
                i = criteria.index(c1)
                j = criteria.index(c2)
                v = float(val)
                matrix[i, j] = v
                matrix[j, i] = 1.0 / v if v > 0 else 1.0

    # Geometriai átlag módszer (Geometric Mean Method)
    row_products = np.prod(matrix, axis=1)
    weights = np.power(row_products, 1.0 / n)
    total_w = np.sum(weights)
    if total_w > 0:
        norm_weights = weights / total_w
    else:
        norm_weights = np.ones(n) / n

    return {criteria[idx]: round(float(norm_weights[idx]), 4) for idx in range(n)}

def calculate_planner_destinations_sync(
    origin: str,
    adults: int = 2,
    children: int = 0,
    date_mode: str = "month", # 'exact' | 'interval' | 'month'
    month: int = 9,
    duration_days: int = 7,
    exact_out_date: Optional[str] = None,
    exact_in_date: Optional[str] = None,
    out_from: Optional[str] = None,
    out_to: Optional[str] = None,
    in_from: Optional[str] = None,
    in_to: Optional[str] = None,
    min_stay: Optional[int] = None,
    max_stay: Optional[int] = None,
    target_temp: float = 24.0,
    min_safety: int = 50,
    preferred_regions: Optional[List[str]] = None,
    exclusions: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    ahp_comparisons: Optional[Dict[str, float]] = None,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Kiszámítja és rangsorolja a célállomásokat a Master Planner intake preferenciák és AHP mátrix alapján.
    """
    exclusions = exclusions or []
    all_dests = get_filtered_destinations(exclusions)

    # Régió szűrés ha meg van adva
    if preferred_regions and len(preferred_regions) > 0 and "all" not in preferred_regions:
        all_dests = [d for d in all_dests if d.get("region") in preferred_regions]
        if not all_dests:
            all_dests = get_filtered_destinations(exclusions)

    n = len(all_dests)
    origin_clean = origin.split("(")[0].strip()
    tokens = scraper.get_kiwi_tokens(headless=True)

    # Dátum paraméterek feloldása date_mode alapján
    if date_mode == "exact" and exact_out_date and exact_in_date:
        actual_out_from = exact_out_date
        actual_out_to = exact_out_date
        actual_in_from = exact_in_date
        actual_in_to = exact_in_date
        # számítsuk ki a napokat
        try:
            d1 = pd.to_datetime(exact_out_date)
            d2 = pd.to_datetime(exact_in_date)
            duration_days = max(1, (d2 - d1).days)
            actual_min_stay = duration_days
            actual_max_stay = duration_days
            month = d1.month
        except:
            actual_min_stay = duration_days
            actual_max_stay = duration_days
    elif date_mode == "interval" and out_from and out_to:
        actual_out_from = out_from
        actual_out_to = out_to
        actual_in_from = in_from or out_to
        actual_in_to = in_to
        actual_min_stay = min_stay or max(1, duration_days - 2)
        actual_max_stay = max_stay or (duration_days + 2)
        try:
            month = pd.to_datetime(out_from).month
        except:
            pass
    else:
        # Rugalmas hónap
        actual_out_from = None
        actual_out_to = None
        actual_in_from = None
        actual_in_to = None
        actual_min_stay = min_stay or max(1, duration_days - 2)
        actual_max_stay = max_stay or (duration_days + 2)

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
            children=children,
            out_from=actual_out_from,
            out_to=actual_out_to,
            in_from=actual_in_from,
            in_to=actual_in_to,
            min_stay=actual_min_stay,
            max_stay=actual_max_stay
        )
        completed += 1
        if progress_callback:
            progress_callback(int((completed / max(1, n)) * 80), f"Adatok gyűjtése ({completed}/{n}): {d.get('name')}")
        return res

    with ThreadPoolExecutor(max_workers=8) as executor:
        candidates_raw = list(executor.map(process_dest, all_dests))

    # Súlyok összeállítása AHP-ból ha meg van adva
    w_dict = weights
    if not w_dict and ahp_comparisons:
        ahp_computed = compute_ahp_weights_from_comparisons(
            ["flight", "cost", "weather", "safety"],
            ahp_comparisons
        )
        w_dict = {k: v * 100.0 for k, v in ahp_computed.items()}

    if not w_dict:
        w_dict = {
            "flight": 30.0,
            "cost": 20.0,
            "weather": 30.0,
            "safety": 20.0
        }

    if progress_callback:
        progress_callback(90, "Végső AHP rangsorolás és indoklások összeállítása...")

    ranked = calculate_destination_rankings(
        candidates_raw=candidates_raw,
        weights=w_dict,
        target_temp=target_temp,
        adults=adults
    )

    # Biztonsági minimum szűrés
    if min_safety > 0:
        filtered_ranked = [r for r in ranked if r.get("metrics", {}).get("safety_raw", 100) >= min_safety]
        if filtered_ranked:
            ranked = filtered_ranked

    for idx, r in enumerate(ranked):
        r["rank"] = idx + 1

    return ranked

def search_and_rank_planner_flights(
    origin: str,
    destination: str,
    date_mode: str = "month",
    month: int = 9,
    duration_days: int = 7,
    exact_out_date: Optional[str] = None,
    exact_in_date: Optional[str] = None,
    out_from: Optional[str] = None,
    out_to: Optional[str] = None,
    in_from: Optional[str] = None,
    in_to: Optional[str] = None,
    min_stay: Optional[int] = None,
    max_stay: Optional[int] = None,
    adults: int = 2,
    children: int = 0,
    direct_only: bool = False,
    max_stops: int = 1,
    departure_pref: str = "any",
    max_duration_h: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Lekéri és PROMETHEE II szerint rangsorolja a járatokat az összes dátummód (exact/interval/month) támogatásával.
    """
    origin_clean = origin.split("(")[0].strip()
    dest_clean = destination.split("(")[0].strip()

    tokens = scraper.get_kiwi_tokens(headless=True)
    
    if date_mode == "exact" and exact_out_date and exact_in_date:
        date_out_start = exact_out_date
        date_out_end = exact_out_date
        date_in_start = exact_in_date
        date_in_end = exact_in_date
        try:
            d1 = pd.to_datetime(exact_out_date)
            d2 = pd.to_datetime(exact_in_date)
            duration_days = max(1, (d2 - d1).days)
        except:
            pass
        actual_min_stay = duration_days
        actual_max_stay = duration_days
    elif date_mode == "interval" and out_from and out_to:
        date_out_start = out_from
        date_out_end = out_to
        date_in_start = in_from or out_to
        date_in_end = in_to or out_to
        actual_min_stay = min_stay or max(1, duration_days - 2)
        actual_max_stay = max_stay or (duration_days + 2)
    else:
        # Month mode
        if month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
        elif month in [4, 6, 9, 11]: last_day = 30
        else: last_day = 28

        date_out_start = f"2026-{month:02d}-01"
        date_out_end = f"2026-{month:02d}-{min(24, last_day):02d}"
        
        next_m = (month % 12) + 1
        date_in_start = f"2026-{month:02d}-{min(last_day, max(1, 1 + duration_days)):02d}"
        date_in_end = f"2026-{next_m:02d}-10"
        actual_min_stay = min_stay or max(1, duration_days - 2)
        actual_max_stay = max_stay or (duration_days + 2)

    outbound = scraper.search_flights_by_city_name_v2(
        origin_name=origin_clean,
        destination_name=dest_clean,
        tokens=tokens,
        date_from=date_out_start,
        date_to=date_out_end,
        adults=adults,
        children=children,
        limit=50
    )

    inbound = scraper.search_flights_by_city_name_v2(
        origin_name=dest_clean,
        destination_name=origin_clean,
        tokens=tokens,
        date_from=date_in_start,
        date_to=date_in_end,
        adults=adults,
        children=children,
        limit=50
    )

    if outbound.empty or inbound.empty:
        return []

    combinations = scraper.create_return_combinations(
        outbound, inbound, min_stay_days=actual_min_stay, max_stay_days=actual_max_stay
    )

    if combinations is None or (isinstance(combinations, pd.DataFrame) and combinations.empty) or len(combinations) == 0:
        return []

    df = combinations.copy() if isinstance(combinations, pd.DataFrame) else pd.DataFrame(combinations)

    # Szűrések alkalmazása
    if direct_only:
        df = df[(df['out_stops'] == 0) & (df['in_stops'] == 0)]
    elif max_stops is not None and max_stops < 3:
        df = df[(df['out_stops'] <= max_stops) & (df['in_stops'] <= max_stops)]

    if max_duration_h and max_duration_h > 0:
        df = df[(df['out_duration_h'] <= max_duration_h) & (df['in_duration_h'] <= max_duration_h)]

    # Indulási napszak szűrés ha meg van adva
    if departure_pref in ["morning", "afternoon", "evening"] and 'out_dep_time' in df.columns:
        try:
            hours = pd.to_datetime(df['out_dep_time']).dt.hour
            if departure_pref == "morning":
                filtered_df = df[(hours >= 6) & (hours < 12)]
            elif departure_pref == "afternoon":
                filtered_df = df[(hours >= 12) & (hours < 18)]
            elif departure_pref == "evening":
                filtered_df = df[(hours >= 18) | (hours < 6)]
            if not filtered_df.empty:
                df = filtered_df
        except:
            pass

    if df.empty:
        df = combinations.copy() if isinstance(combinations, pd.DataFrame) else pd.DataFrame(combinations)

    # PROMETHEE II rangsorolás
    n = len(df)
    if n == 0:
        return []

    df['g1'] = df['total_price_huf']
    df['g2'] = df['out_duration_h'] + df['in_duration_h']
    df['g3'] = df['out_stops'] + df['in_stops']

    cols = ['g1', 'g2', 'g3']
    w = [0.45, 0.35, 0.20]
    if weights:
        w = [
            float(weights.get("flight", weights.get("price", 0.45))),
            float(weights.get("travel_time", 0.35)),
            float(weights.get("stops", 0.20))
        ]
        total_w = sum(w)
        if total_w > 0:
            w = [x / total_w for x in w]

    data_mat = df[cols].values
    phi_plus = np.zeros(n)
    phi_minus = np.zeros(n)

    for i in range(n):
        for j in range(n):
            if i == j: continue
            diff = data_mat[j] - data_mat[i]
            pref = np.where(diff > 0, 1.0, 0.0)
            score = np.dot(w, pref)
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
    results_list = df_sorted.head(25).to_dict(orient='records')
    
    for idx, r in enumerate(results_list):
        r["rank"] = idx + 1

    return results_list
