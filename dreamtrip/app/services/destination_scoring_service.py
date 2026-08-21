import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.services.weather_service import fetch_historical_climate, calculate_weather_score
from app.services.numbeo_service import get_city_cost_and_safety
from app.services.exchange_service import get_eur_huf_rate
from app.scrapers import scraper

def evaluate_destination_candidate(
    dest: Dict[str, Any],
    origin_city: str,
    month: int,
    duration_days: int,
    tokens: Dict[str, str],
    target_temp: float = 24.0,
    adults: int = 2,
    children: int = 0
) -> Dict[str, Any]:
    """
    Összegyűjti egyetlen célállomás valós nyers adatait:
    1. Kiwi retúr járatár (HUF) a pontos utasszámra és menetidő
    2. Open-Meteo valós klímaadatok (°C - nappali és éjszakai)
    3. Numbeo napi fogyasztói kosár (€/nap) és Safety Index (0-100)
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

    # 3. VALÓS KIWI REPÜLŐJEGY (Hónapon belüli rugalmas retúr keresés adott utasszámra)
    if month in [1, 3, 5, 7, 8, 10, 12]:
        last_day = 31
    elif month in [4, 6, 9, 11]:
        last_day = 30
    else:
        last_day = 28

    date_out_start = f"2026-{month:02d}-01"
    date_out_end = f"2026-{month:02d}-{min(24, last_day):02d}"
    
    next_m = (month % 12) + 1
    date_in_start = f"2026-{month:02d}-{min(last_day, max(1, 1 + duration_days)):02d}"
    date_in_end = f"2026-{next_m:02d}-08"

    flight_price_huf = None
    flight_duration_h = None
    flight_is_direct = False

    try:
        # Odaút keresése a hónap legolcsóbb járataira a pontos utasszámra
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
        
        # Visszaút keresése a hónap legolcsóbb járataira a pontos utasszámra
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
            # Rugalmas tartózkodás: duration_days +- 2 nap (pl. 7 napos út -> 5-9 nap közötti visszautak)
            min_stay = max(1, duration_days - 2)
            max_stay = duration_days + 2
            combos_df = scraper.create_return_combinations(out_df, in_df, min_stay_days=min_stay, max_stay_days=max_stay)
            
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

    return {
        "id": dest.get("id"),
        "name": dest.get("name"),
        "city": dest_name,
        "country": country,
        "region": region,
        "image": dest.get("image", ""),
        "raw_metrics": {
            "flight_price_huf": flight_price_huf,
            "flight_duration_h": flight_duration_h,
            "flight_is_direct": flight_is_direct,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "avg_temp": avg_temp,
            "weather_desc": weather_desc,
            "daily_cost_eur": daily_cost_eur,
            "daily_cost_huf": cost_breakdown["daily_cost_huf"],
            "safety_index": safety_index,
            "cost_breakdown": cost_breakdown
        },
        "weather_score_direct": weather_score
    }

def calculate_destination_rankings(
    candidates_raw: List[Dict[str, Any]],
    weights: Dict[str, float],
    target_temp: float = 24.0,
    adults: int = 2
) -> List[Dict[str, Any]]:
    """
    Determinisztikusan kiszámítja a célállomások rangsorát és részletes logot nyomtat a terminálba.
    
    Képlet:
    Total Score = (w_flight * s_flight + w_cost * s_cost + w_weather * s_weather + w_safety * s_safety) * 100
    """
    if not candidates_raw:
        return []

    # Súlyok meghatározása: csak a kiválasztott szempontok kapnak pozitív súlyt!
    has_any = any(k in weights for k in ["flight", "cost", "weather", "safety", "travel_time"])
    
    if has_any:
        w_flight = max(0.0, float(weights.get("flight", weights.get("travel_time", 0.0))))
        w_cost = max(0.0, float(weights.get("cost", 0.0)))
        w_weather = max(0.0, float(weights.get("weather", 0.0)))
        w_safety = max(0.0, float(weights.get("safety", 0.0)))
    else:
        w_flight = w_cost = w_weather = w_safety = 0.25

    total_w = w_flight + w_cost + w_weather + w_safety
    if total_w > 0:
        w_flight /= total_w
        w_cost /= total_w
        w_weather /= total_w
        w_safety /= total_w
    else:
        w_flight = w_cost = w_weather = w_safety = 0.25

    # 1. Min / Max értékek meghatározása a normalizáláshoz
    all_flight_prices = [c["raw_metrics"]["flight_price_huf"] for c in candidates_raw]
    all_daily_costs = [c["raw_metrics"]["daily_cost_eur"] for c in candidates_raw]
    
    min_flight, max_flight = min(all_flight_prices), max(all_flight_prices)
    min_cost, max_cost = min(all_daily_costs), max(all_daily_costs)

    print("\n" + "="*85)
    print("🎯 DESTINATION MATCHER — DETERMINISZTIKUS SZÁMÍTÁSI LEVEZETÉS")
    print("="*85)
    print(f"📊 Aktív Súlyok: Repülő={w_flight:.2f}, Napi Költség={w_cost:.2f}, Időjárás={w_weather:.2f}, Biztonság={w_safety:.2f}")
    print(f"📈 Repülőjegy tartomány: {min_flight:,.0f} Ft — {max_flight:,.0f} Ft")
    print(f"📈 Napi költségkeret tartomány: {min_cost:.1f} € — {max_cost:.1f} €")
    print(f"🌡️ Célhőmérséklet (Nappali csúcs): {target_temp}°C")
    print("-"*85)
    print(f"{'Város':<18} | {'Repülő (Ft)':<11} | {'Költség (€)':<11} | {'Nappal (°C)':<11} | {'Bizt':<4} | {'Pontszám':<8}")
    print("-"*85)

    scored_results = []

    for c in candidates_raw:
        m = c["raw_metrics"]
        
        # 1. Repülőjegy pontszám (Alacsonyabb = Jobb, 0.0 - 1.0)
        if max_flight == min_flight:
            s_flight = 1.0
        else:
            s_flight = (max_flight - m["flight_price_huf"]) / (max_flight - min_flight)
        s_flight = round(max(0.0, min(1.0, s_flight)), 3)

        # 2. Napi megélhetési költség pontszám (Alacsonyabb = Jobb, 0.0 - 1.0)
        if max_cost == min_cost:
            s_cost = 1.0
        else:
            s_cost = (max_cost - m["daily_cost_eur"]) / (max_cost - min_cost)
        s_cost = round(max(0.0, min(1.0, s_cost)), 3)

        # 3. Időjárás pontszám (Célhőmérséklethez való közelség, 0.0 - 1.0)
        s_weather = c["weather_score_direct"]

        # 4. Biztonsági pontszám (Numbeo Safety Index 0-100 skálázva 0.0 - 1.0-ra)
        s_safety = round(max(0.0, min(1.0, m["safety_index"] / 100.0)), 3)

        # Végső Súlyozott Pontszám (0 - 100)
        final_score_raw = (
            w_flight * s_flight +
            w_cost * s_cost +
            w_weather * s_weather +
            w_safety * s_safety
        ) * 100.0
        final_score = round(final_score_raw, 1)

        # Objektív „Miért ezt ajánljuk?” és Kompromisszum generálás
        reasons_pos = []
        if w_flight > 0 and s_flight >= 0.70:
            reasons_pos.append(f"✈️ Kedvező repülőjegy ár ({int(m['flight_price_huf']):,} Ft)")
        if w_weather > 0 and s_weather >= 0.80:
            reasons_pos.append(f"☀️ Ideális nappali klíma ({m['temp_max']}°C, cél: {target_temp}°C)")
        if w_safety > 0 and s_safety >= 0.70:
            reasons_pos.append(f"🛡️ Kiemelkedő közbiztonság ({int(m['safety_index'])}/100)")
        if w_cost > 0 and s_cost >= 0.70:
            reasons_pos.append(f"💰 Kedvező napi költségszint (~€{int(m['daily_cost_eur'])}/nap)")

        if not reasons_pos:
            reasons_pos.append("⚖️ Kiegyensúlyozott paraméterek a kiválasztott szempontok alapján")

        tradeoff = None
        if w_cost > 0 and s_cost <= 0.30:
            tradeoff = f"💰 Magasabb napi költési szint (~€{int(m['daily_cost_eur'])}/nap)"
        elif w_safety > 0 and s_safety <= 0.45:
            tradeoff = f"⚠️ Átlagos közbiztonsági szint ({int(m['safety_index'])}/100)"
        elif w_flight > 0 and s_flight <= 0.25:
            tradeoff = f"✈️ Magasabb utazási költség ({int(m['flight_price_huf']):,} Ft)"
        elif w_weather > 0 and s_weather <= 0.40:
            tradeoff = f"🌡️ Érezhető hőmérséklet-eltérés (Nappal: {m['temp_max']}°C)"

        print(f"{c['name']:<18} | {m['flight_price_huf']:>10,.0f} | {m['daily_cost_eur']:>10.1f} | {m['temp_max']:>10.1f} | {m['safety_index']:>4.0f} | {final_score:>6.1f}p")

        scored_results.append({
            "id": c["id"],
            "name": c["name"],
            "city": c["city"],
            "country": c["country"],
            "region": c["region"],
            "image": c["image"],
            "score": final_score,
            "subscores": {
                "flight": s_flight,
                "cost": s_cost,
                "weather": s_weather,
                "safety": s_safety
            },
            "weights": {
                "flight": round(w_flight, 2),
                "cost": round(w_cost, 2),
                "weather": round(w_weather, 2),
                "safety": round(w_safety, 2)
            },
            "metrics": {
                "flight_price_formatted": f"{int(m['flight_price_huf']):,} Ft",
                "flight_price_per_person_formatted": f"~{int(m['flight_price_huf'] / max(1, adults)):,} Ft / fő",
                "flight_price_raw": m["flight_price_huf"],
                "flight_duration": f"{m['flight_duration_h']} óra",
                "daily_cost_formatted": f"~€{int(m['daily_cost_eur'])} / nap",
                "daily_cost_huf_formatted": f"~{int(m['daily_cost_huf']):,} Ft / nap",
                "daily_cost_raw": m["daily_cost_eur"],
                "temp_formatted": f"Nappal: {int(m['temp_max'])}°C / Éjjel: {int(m['temp_min'])}°C",
                "temp_avg": m["temp_max"],
                "safety_formatted": f"{int(m['safety_index'])}/100 (Numbeo)",
                "safety_raw": m["safety_index"],
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
