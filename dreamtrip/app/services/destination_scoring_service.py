import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.services.weather_service import fetch_historical_climate, calculate_weather_score
from app.services.numbeo_service import get_city_cost_and_safety
from app.services.exchange_service import get_eur_huf_rate
from app.services.accommodation_market_service import get_destination_stay_price
from app.scrapers import scraper

def evaluate_destination_candidate(
    dest: Dict[str, Any],
    origin_city: str,
    month: int,
    duration_days: int,
    tokens: Dict[str, str],
    target_temp: float = 24.0,
    adults: int = 2,
    children: int = 0,
    year: int = 2026,
    out_from: Optional[str] = None,
    out_to: Optional[str] = None,
    in_from: Optional[str] = None,
    in_to: Optional[str] = None,
    min_stay: Optional[int] = None,
    max_stay: Optional[int] = None
) -> Dict[str, Any]:
    """
    Összegyűjti egyetlen célállomás valós nyers adatait:
    1. Kiwi retúr járatár (HUF) a pontos utasszámra és menetidő
    2. Open-Meteo valós klímaadatok (°C - nappali és éjszakai)
    3. Numbeo napi fogyasztói kosár (€/nap) és Safety Index (0-100)
    4. Cozycozy valós scrapelt szállásár (HUF) a tartózkodás napjaira
    """
    dest_name = dest.get("city") or dest.get("name")
    country = dest.get("country", "")
    lat = float(dest.get("lat", 0.0))
    lon = float(dest.get("lon", 0.0))
    region = dest.get("region", "")

    # 1. VALÓS IDŐJÁRÁS (Open-Meteo)
    temp_min, temp_max, avg_temp = fetch_historical_climate(lat, lon, month)
    weather_score, weather_desc = calculate_weather_score(temp_max, target_temp)

    # 2. VALÓS NUMBEO KÖLTSÉGKOSÁR ÉS BIZTONSÁG
    daily_cost_eur, safety_index, cost_breakdown = get_city_cost_and_safety(dest_name, country, region)
    eur_rate = get_eur_huf_rate()
    daily_cost_huf = daily_cost_eur * eur_rate

    # 3. VALÓS COZYCOZY-BÓL SCRAPELT SZÁLLÁSÁR (Honest Scraping Policy)
    stay_market = get_destination_stay_price(dest_name, country, duration_days=duration_days, adults=adults)
    total_hotel_cost_huf = stay_market["total_hotel_cost_huf"]
    nightly_hotel_cost_huf = stay_market["nightly_price_huf"]

    # 4. VALÓS KIWI REPÜLŐJEGY (Pontos vagy rugalmas dátumkeret / intervallum alapján)
    from datetime import datetime as dt_cls
    today = dt_cls.now()
    cur_year = today.year
    cur_month = today.month

    if not out_from and (year < cur_year or (year == cur_year and month < cur_month)):
        year = cur_year + 1

    if month in [1, 3, 5, 7, 8, 10, 12]:
        last_day = 31
    elif month in [4, 6, 9, 11]:
        last_day = 30
    else:
        last_day = 28

    if not out_from and year == cur_year and month == cur_month:
        if today.day >= (last_day - 4):
            month = (month % 12) + 1
            if month == 1:
                year += 1
            if month in [1, 3, 5, 7, 8, 10, 12]: last_day = 31
            elif month in [4, 6, 9, 11]: last_day = 30
            else: last_day = 28
            start_day = 1
        else:
            start_day = today.day + 1
    else:
        start_day = 1

    date_out_start = out_from if out_from else f"{year}-{month:02d}-{start_day:02d}"
    date_out_end = out_to if out_to else f"{year}-{month:02d}-{min(last_day, max(start_day, last_day - 6)):02d}"
    
    next_m = (month % 12) + 1
    next_y = year if next_m > month else year + 1
    date_in_start = in_from if in_from else f"{year}-{month:02d}-{min(last_day, max(1, start_day + duration_days)):02d}"
    date_in_end = in_to if in_to else f"{next_y}-{next_m:02d}-15"

    # Tartózkodási napok határai
    effective_min_stay = int(min_stay) if min_stay is not None else max(1, duration_days - 2)
    effective_max_stay = int(max_stay) if max_stay is not None else (duration_days + 2)

    flight_price_huf = None
    flight_duration_h = None
    flight_is_direct = False

    try:
        # Odaút keresése a legolcsóbb járatokra a pontos utasszámra
        out_df = scraper.search_flights_by_city_name_v2(
            origin_name=origin_city,
            destination_name=dest_name,
            tokens=tokens,
            date_from=date_out_start,
            date_to=date_out_end,
            adults=adults,
            children=children,
            limit=20
        )
        
        # Visszaút keresése a legolcsóbb járatokra a pontos utasszámra
        in_df = scraper.search_flights_by_city_name_v2(
            origin_name=dest_name,
            destination_name=origin_city,
            tokens=tokens,
            date_from=date_in_start,
            date_to=date_in_end,
            adults=adults,
            children=children,
            limit=20
        )

        if isinstance(out_df, pd.DataFrame) and not out_df.empty and isinstance(in_df, pd.DataFrame) and not in_df.empty:
            combos_df = scraper.create_return_combinations(out_df, in_df, min_stay_days=effective_min_stay, max_stay_days=effective_max_stay)
            
            if isinstance(combos_df, pd.DataFrame) and not combos_df.empty:
                cheapest_row = combos_df.iloc[0] # Alapból ár szerint rendezve
                flight_price_huf = float(cheapest_row["total_price_huf"])
                flight_duration_h = round(float(cheapest_row["out_duration_h"] + cheapest_row["in_duration_h"]), 1)
                flight_is_direct = bool(cheapest_row.get("total_stops", 1) == 0)
        elif isinstance(out_df, pd.DataFrame) and not out_df.empty:
            flight_price_huf = float(out_df["price_huf"].min()) * 2.0
            flight_duration_h = round(float(out_df["duration_h"].min()) * 2.0, 1)
    except Exception as e:
        print(f"  [FLIGHT SEARCH WARN] {dest_name}: {e}")

    # Ha a járatkereső API nem adott vissza járatot
    if flight_price_huf is None:
        if "america" in region.lower() or "asia" in region.lower():
            flight_price_huf = 240000.0
            flight_duration_h = 12.0
        else:
            flight_price_huf = 75000.0
            flight_duration_h = 4.0

    total_living_cost_huf = daily_cost_huf * duration_days * max(1, adults)
    total_trip_cost_huf = float(flight_price_huf + total_living_cost_huf + total_hotel_cost_huf)

    return {
        "id": dest.get("id", dest_name.lower()),
        "name": dest_name,
        "city": dest.get("city", dest_name),
        "country": country,
        "region": region,
        "image": dest.get("image", ""),
        "weather_score_direct": weather_score,
        "raw_metrics": {
            "flight_price_huf": flight_price_huf,
            "flight_duration_h": flight_duration_h,
            "flight_is_direct": flight_is_direct,
            "daily_cost_eur": daily_cost_eur,
            "daily_cost_huf": daily_cost_huf,
            "total_trip_cost_huf": total_trip_cost_huf,
            "est_hotel_cost_huf": total_hotel_cost_huf,
            "nightly_hotel_cost_huf": nightly_hotel_cost_huf,
            "stay_source": "cozycozy_market_cache",
            "temp_min": temp_min,
            "temp_max": temp_max,
            "avg_temp": avg_temp,
            "safety_index": safety_index,
            "cost_breakdown": cost_breakdown
        }
    }

def calculate_destination_rankings(
    candidates_raw: List[Dict[str, Any]],
    weights: Dict[str, float],
    target_temp: float = 24.0,
    adults: int = 2
) -> List[Dict[str, Any]]:
    """
    Kiszámítja a desztinációk rangsorát a tiszta 3-Pilléres Döntési Modell (Total Cost + Weather + Safety) szerint.
    
    Képlet:
    Total Score = (w_total_cost * s_total_cost + w_weather * s_weather + w_safety * s_safety) * 100
    """
    if not candidates_raw:
        return []

    # Súlyok meghatározása: 3-Pilléres Tiszta Modell
    if "total_cost" in weights:
        w_cost = max(0.0, float(weights.get("total_cost", 0.0)))
    elif "flight" in weights or "cost" in weights:
        w_cost = max(0.0, float(weights.get("flight", 0.0))) + max(0.0, float(weights.get("cost", 0.0)))
    else:
        w_cost = 1.0 / 3.0

    w_weather = max(0.0, float(weights.get("weather", 0.0)))
    w_safety = max(0.0, float(weights.get("safety", 0.0)))

    total_w = w_cost + w_weather + w_safety
    if total_w > 0:
        w_cost /= total_w
        w_weather /= total_w
        w_safety /= total_w
    else:
        w_cost = w_weather = w_safety = 1.0 / 3.0

    # 1. Min / Max értékek a normalizáláshoz
    all_total_costs = [c["raw_metrics"]["total_trip_cost_huf"] for c in candidates_raw]
    min_total_cost, max_total_cost = min(all_total_costs), max(all_total_costs)

    try:
        print("\n" + "="*85)
        print("[DESTINATION MATCHER] 3-PILLERES EGYSEGES DONTESI LEVEZETES")
        print("="*85)
        print(f"Aktív Súlyok: Teljes Költség={w_cost:.2f}, Időjárás={w_weather:.2f}, Biztonság={w_safety:.2f}")
        print(f"Teljes utazási költség tartomány: {min_total_cost:,.0f} Ft — {max_total_cost:,.0f} Ft")
        print(f"Célhőmérséklet (Nappali csúcs): {target_temp}°C")
        print("-"*85)
        print(f"{'Város':<18} | {'Összköltség (Ft)':<16} | {'Nappal (°C)':<11} | {'Bizt':<4} | {'Pontszám':<8}")
        print("-"*85)
    except Exception:
        pass

    scored_results = []

    for c in candidates_raw:
        m = c["raw_metrics"]
        
        # 1. Teljes Költség pontszám (Repülő + Szállás + Napi költés, Alacsonyabb = Jobb, 0.0 - 1.0)
        if max_total_cost == min_total_cost:
            s_cost = 1.0
        else:
            s_cost = (max_total_cost - m["total_trip_cost_huf"]) / (max_total_cost - min_total_cost)
        s_cost = round(max(0.0, min(1.0, s_cost)), 3)

        # 2. Időjárás pontszám (Célhőmérséklethez való közelség, 0.0 - 1.0)
        s_weather = c["weather_score_direct"]

        # 3. Biztonsági pontszám (Numbeo Safety Index 0-100 skálázva 0.0 - 1.0-ra)
        s_safety = round(max(0.0, min(1.0, m["safety_index"] / 100.0)), 3)

        # Végső Súlyozott Pontszám (0 - 100)
        final_score_raw = (
            w_cost * s_cost +
            w_weather * s_weather +
            w_safety * s_safety
        ) * 100.0
        final_score = round(final_score_raw, 1)

        # Kerekített összegek ezer forintra (pl. 267 837 -> 268 000 Ft)
        total_cost_rounded = int(round(m["total_trip_cost_huf"] / 1000.0) * 1000)
        daily_cost_rounded = int(round(m["daily_cost_huf"] / 1000.0) * 1000) if m["daily_cost_huf"] >= 10000 else int(round(m["daily_cost_huf"] / 500.0) * 500)
        
        total_cost_str = f"{total_cost_rounded:,}".replace(",", " ")
        daily_cost_str = f"{daily_cost_rounded:,}".replace(",", " ")

        # Objektív indoklások generálása
        reasons_pos = []
        if w_cost > 0 and s_cost >= 0.70:
            reasons_pos.append(f"💰 Kedvező teljes utazási költség (~{total_cost_str} Ft)")
        if w_weather > 0 and s_weather >= 0.80:
            reasons_pos.append(f"☀️ Ideális nappali klíma ({m['temp_max']}°C, cél: {target_temp}°C)")
        if w_safety > 0 and s_safety >= 0.70:
            reasons_pos.append(f"🛡️ Kiemelkedő közbiztonság ({int(m['safety_index'])}/100)")

        if not reasons_pos:
            reasons_pos.append("⚖️ Kiegyensúlyozott paraméterek a megadott prioritások alapján")

        tradeoff = None
        if w_cost > 0 and s_cost <= 0.30:
            tradeoff = f"💰 Magasabb összköltség (~{total_cost_str} Ft)"
        elif w_safety > 0 and s_safety <= 0.45:
            tradeoff = f"⚠️ Átlagos közbiztonsági szint ({int(m['safety_index'])}/100)"
        elif w_weather > 0 and s_weather <= 0.40:
            tradeoff = f"🌡️ Érezhető hőmérséklet-eltérés (Nappal: {m['temp_max']}°C)"

        try:
            print(f"{c['name']:<18} | {m['total_trip_cost_huf']:>15,.0f} | {m['temp_max']:>10.1f} | {m['safety_index']:>4.0f} | {final_score:>6.1f}p")
        except Exception:
            pass

        scored_results.append({
            "id": c["id"],
            "name": c["name"],
            "city": c["city"],
            "country": c["country"],
            "region": c["region"],
            "image": c["image"],
            "score": final_score,
            "subscores": {
                "total_cost": s_cost,
                "weather": s_weather,
                "safety": s_safety
            },
            "weights": {
                "total_cost": round(w_cost, 2),
                "weather": round(w_weather, 2),
                "safety": round(w_safety, 2)
            },
            "metrics": {
                "flight_price_formatted": f"{int(m['flight_price_huf']):,} Ft".replace(",", " "),
                "flight_price_per_person_formatted": f"~{int(m['flight_price_huf'] / max(1, adults)):,} Ft / fő".replace(",", " "),
                "flight_price_raw": m["flight_price_huf"],
                "flight_duration": f"{m['flight_duration_h']} óra",
                "daily_cost_formatted": f"~{daily_cost_str} Ft / nap",
                "daily_cost_huf_formatted": f"~{daily_cost_str} Ft / nap",
                "daily_cost_raw": m["daily_cost_eur"],
                "daily_cost_huf": m["daily_cost_huf"],
                "total_trip_cost_formatted": f"~{total_cost_str} Ft",
                "total_trip_cost_raw": m["total_trip_cost_huf"],
                "est_hotel_cost_huf": m.get("est_hotel_cost_huf", 0),
                "nightly_hotel_cost_huf": m.get("nightly_hotel_cost_huf", 0),
                "stay_source": m.get("stay_source", "cozycozy_market_cache"),
                "temp_formatted": f"Nappal: {int(m['temp_max'])}°C / Éjjel: {int(m['temp_min'])}°C",
                "temp_avg": m["temp_max"],
                "safety_formatted": f"{int(m['safety_index'])}/100 (Numbeo)",
                "safety_raw": m["safety_index"],
                "numbeo_breakdown": m.get("cost_breakdown", {}),
                "adults": adults
            },
            "highlights": reasons_pos[:2],
            "tradeoff": tradeoff,
            "explanation": " • ".join(reasons_pos[:2]) + (f" | Kompromisszum: {tradeoff}" if tradeoff else "")
        })

    print("="*85 + "\n")

    # Sorbarendezés pontszám szerint csökkenő sorrendben
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    for idx, r in enumerate(scored_results):
        r["rank"] = idx + 1

    return scored_results
