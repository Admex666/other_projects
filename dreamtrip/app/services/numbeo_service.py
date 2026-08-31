import math
from typing import Dict, Any, Tuple, Optional
from app.services.exchange_service import get_eur_huf_rate

# Valós Numbeo adatbázis: költségkomponensek és hivatalos biztonsági indexek
# Költségkosár képlet: (1.5 * olcsó étkezés) + (0.5 * középkategóriás vacsora) + (2 * kávé/üdítő) + (2 * helyi vonaljegy)
NUMBEO_CITY_DATA: Dict[str, Dict[str, Any]] = {
    # Magyar és angol kulcsszavak lefedése
    "barcelona": {"meal_inexpensive": 15.0, "meal_midrange": 30.0, "coffee": 2.2, "transport_ticket": 2.55, "safety_index": 49.2},
    "rome": {"meal_inexpensive": 16.0, "meal_midrange": 32.0, "coffee": 1.6, "transport_ticket": 1.50, "safety_index": 48.5},
    "róma": {"meal_inexpensive": 16.0, "meal_midrange": 32.0, "coffee": 1.6, "transport_ticket": 1.50, "safety_index": 48.5},
    "paris": {"meal_inexpensive": 18.0, "meal_midrange": 40.0, "coffee": 3.8, "transport_ticket": 2.15, "safety_index": 43.1},
    "párizs": {"meal_inexpensive": 18.0, "meal_midrange": 40.0, "coffee": 3.8, "transport_ticket": 2.15, "safety_index": 43.1},
    "budapest": {"meal_inexpensive": 9.5, "meal_midrange": 22.0, "coffee": 2.0, "transport_ticket": 1.20, "safety_index": 66.8},
    "vienna": {"meal_inexpensive": 15.0, "meal_midrange": 35.0, "coffee": 3.9, "transport_ticket": 2.40, "safety_index": 73.4},
    "bécs": {"meal_inexpensive": 15.0, "meal_midrange": 35.0, "coffee": 3.9, "transport_ticket": 2.40, "safety_index": 73.4},
    "london": {"meal_inexpensive": 22.0, "meal_midrange": 45.0, "coffee": 4.2, "transport_ticket": 3.40, "safety_index": 45.8},
    "tokyo": {"meal_inexpensive": 7.5, "meal_midrange": 24.0, "coffee": 3.2, "transport_ticket": 1.40, "safety_index": 76.5},
    "tokió": {"meal_inexpensive": 7.5, "meal_midrange": 24.0, "coffee": 3.2, "transport_ticket": 1.40, "safety_index": 76.5},
    "funchal": {"meal_inexpensive": 11.0, "meal_midrange": 24.0, "coffee": 1.4, "transport_ticket": 1.95, "safety_index": 81.2},
    "madeira": {"meal_inexpensive": 11.0, "meal_midrange": 24.0, "coffee": 1.4, "transport_ticket": 1.95, "safety_index": 81.2},
    "bali": {"meal_inexpensive": 3.5, "meal_midrange": 12.0, "coffee": 2.2, "transport_ticket": 0.80, "safety_index": 54.0},
    "reykjavik": {"meal_inexpensive": 24.0, "meal_midrange": 58.0, "coffee": 4.8, "transport_ticket": 4.10, "safety_index": 78.9},
    "reykjavík": {"meal_inexpensive": 24.0, "meal_midrange": 58.0, "coffee": 4.8, "transport_ticket": 4.10, "safety_index": 78.9},
    "prague": {"meal_inexpensive": 10.0, "meal_midrange": 24.0, "coffee": 2.8, "transport_ticket": 1.30, "safety_index": 75.6},
    "prága": {"meal_inexpensive": 10.0, "meal_midrange": 24.0, "coffee": 2.8, "transport_ticket": 1.30, "safety_index": 75.6},
    "lisbon": {"meal_inexpensive": 12.5, "meal_midrange": 26.0, "coffee": 1.6, "transport_ticket": 1.80, "safety_index": 70.8},
    "lisszabon": {"meal_inexpensive": 12.5, "meal_midrange": 26.0, "coffee": 1.6, "transport_ticket": 1.80, "safety_index": 70.8},
    "athens": {"meal_inexpensive": 13.0, "meal_midrange": 25.0, "coffee": 3.4, "transport_ticket": 1.20, "safety_index": 44.5},
    "athén": {"meal_inexpensive": 13.0, "meal_midrange": 25.0, "coffee": 3.4, "transport_ticket": 1.20, "safety_index": 44.5},
    "santorini": {"meal_inexpensive": 16.0, "meal_midrange": 35.0, "coffee": 4.0, "transport_ticket": 2.20, "safety_index": 58.0},
    "szantorini": {"meal_inexpensive": 16.0, "meal_midrange": 35.0, "coffee": 4.0, "transport_ticket": 2.20, "safety_index": 58.0},
    "amsterdam": {"meal_inexpensive": 20.0, "meal_midrange": 42.0, "coffee": 3.9, "transport_ticket": 3.40, "safety_index": 67.2},
    "amszterdam": {"meal_inexpensive": 20.0, "meal_midrange": 42.0, "coffee": 3.9, "transport_ticket": 3.40, "safety_index": 67.2},
    "dubai": {"meal_inexpensive": 14.0, "meal_midrange": 38.0, "coffee": 4.9, "transport_ticket": 1.80, "safety_index": 83.7},
    "dubaj": {"meal_inexpensive": 14.0, "meal_midrange": 38.0, "coffee": 4.9, "transport_ticket": 1.80, "safety_index": 83.7},
    "new york": {"meal_inexpensive": 25.0, "meal_midrange": 60.0, "coffee": 5.2, "transport_ticket": 2.80, "safety_index": 50.1},
    "bangkok": {"meal_inexpensive": 3.2, "meal_midrange": 15.0, "coffee": 2.1, "transport_ticket": 1.10, "safety_index": 59.2},
    "valletta": {"meal_inexpensive": 15.0, "meal_midrange": 30.0, "coffee": 2.5, "transport_ticket": 2.00, "safety_index": 62.1},
    "málta": {"meal_inexpensive": 15.0, "meal_midrange": 30.0, "coffee": 2.5, "transport_ticket": 2.00, "safety_index": 62.1},
    "berlin": {"meal_inexpensive": 14.0, "meal_midrange": 32.0, "coffee": 3.4, "transport_ticket": 3.50, "safety_index": 55.4},
    "brussels": {"meal_inexpensive": 18.0, "meal_midrange": 38.0, "coffee": 3.6, "transport_ticket": 2.60, "safety_index": 46.2},
    "brüsszel": {"meal_inexpensive": 18.0, "meal_midrange": 38.0, "coffee": 3.6, "transport_ticket": 2.60, "safety_index": 46.2},
    "copenhagen": {"meal_inexpensive": 22.0, "meal_midrange": 52.0, "coffee": 5.5, "transport_ticket": 3.40, "safety_index": 74.8},
    "koppenhága": {"meal_inexpensive": 22.0, "meal_midrange": 52.0, "coffee": 5.5, "transport_ticket": 3.40, "safety_index": 74.8},
    "stockholm": {"meal_inexpensive": 14.5, "meal_midrange": 40.0, "coffee": 4.1, "transport_ticket": 3.60, "safety_index": 54.1},
    "oslo": {"meal_inexpensive": 20.0, "meal_midrange": 50.0, "coffee": 4.6, "transport_ticket": 3.80, "safety_index": 67.5},
    "helsinki": {"meal_inexpensive": 16.0, "meal_midrange": 42.0, "coffee": 4.2, "transport_ticket": 3.10, "safety_index": 74.2},
    "dublin": {"meal_inexpensive": 18.0, "meal_midrange": 42.0, "coffee": 3.9, "transport_ticket": 2.30, "safety_index": 47.3},
    "warsaw": {"meal_inexpensive": 9.5, "meal_midrange": 22.0, "coffee": 3.2, "transport_ticket": 1.10, "safety_index": 75.1},
    "varsó": {"meal_inexpensive": 9.5, "meal_midrange": 22.0, "coffee": 3.2, "transport_ticket": 1.10, "safety_index": 75.1},
    "tallinn": {"meal_inexpensive": 12.0, "meal_midrange": 28.0, "coffee": 3.4, "transport_ticket": 1.50, "safety_index": 77.2},
    "riga": {"meal_inexpensive": 11.0, "meal_midrange": 25.0, "coffee": 3.2, "transport_ticket": 1.50, "safety_index": 62.4},
    "vilnius": {"meal_inexpensive": 11.5, "meal_midrange": 26.0, "coffee": 3.1, "transport_ticket": 0.90, "safety_index": 72.8},
    "istanbul": {"meal_inexpensive": 7.0, "meal_midrange": 18.0, "coffee": 2.5, "transport_ticket": 0.60, "safety_index": 52.6},
    "isztambul": {"meal_inexpensive": 7.0, "meal_midrange": 18.0, "coffee": 2.5, "transport_ticket": 0.60, "safety_index": 52.6},
    "larnaca": {"meal_inexpensive": 14.0, "meal_midrange": 28.0, "coffee": 3.4, "transport_ticket": 1.50, "safety_index": 69.2},
    "luxembourg": {"meal_inexpensive": 20.0, "meal_midrange": 45.0, "coffee": 4.2, "transport_ticket": 0.00, "safety_index": 67.9},
    "split": {"meal_inexpensive": 13.0, "meal_midrange": 28.0, "coffee": 2.2, "transport_ticket": 1.70, "safety_index": 75.4},
    "sofia": {"meal_inexpensive": 8.5, "meal_midrange": 20.0, "coffee": 2.1, "transport_ticket": 0.85, "safety_index": 58.7},
    "szófia": {"meal_inexpensive": 8.5, "meal_midrange": 20.0, "coffee": 2.1, "transport_ticket": 0.85, "safety_index": 58.7},
    "bucharest": {"meal_inexpensive": 9.5, "meal_midrange": 22.0, "coffee": 2.6, "transport_ticket": 0.65, "safety_index": 68.3},
    "bukarest": {"meal_inexpensive": 9.5, "meal_midrange": 22.0, "coffee": 2.6, "transport_ticket": 0.65, "safety_index": 68.3},
    "belgrade": {"meal_inexpensive": 8.0, "meal_midrange": 20.0, "coffee": 2.2, "transport_ticket": 0.45, "safety_index": 61.5},
    "belgrád": {"meal_inexpensive": 8.0, "meal_midrange": 20.0, "coffee": 2.2, "transport_ticket": 0.45, "safety_index": 61.5},
    "tirana": {"meal_inexpensive": 7.0, "meal_midrange": 18.0, "coffee": 1.4, "transport_ticket": 0.40, "safety_index": 59.8},
    "ljubljana": {"meal_inexpensive": 12.0, "meal_midrange": 28.0, "coffee": 2.2, "transport_ticket": 1.30, "safety_index": 78.4},
    "sarajevo": {"meal_inexpensive": 6.5, "meal_midrange": 16.0, "coffee": 1.6, "transport_ticket": 0.90, "safety_index": 56.2},
    "szarajevó": {"meal_inexpensive": 6.5, "meal_midrange": 16.0, "coffee": 1.6, "transport_ticket": 0.90, "safety_index": 56.2},
    "zurich": {"meal_inexpensive": 28.0, "meal_midrange": 65.0, "coffee": 5.8, "transport_ticket": 4.50, "safety_index": 82.5},
    "zürich": {"meal_inexpensive": 28.0, "meal_midrange": 65.0, "coffee": 5.8, "transport_ticket": 4.50, "safety_index": 82.5},
    "sydney": {"meal_inexpensive": 16.0, "meal_midrange": 42.0, "coffee": 3.4, "transport_ticket": 2.80, "safety_index": 63.8}
}

# Átlagos regionális becslések ismeretlen desztinációkra
REGIONAL_FALLBACK = {
    "europe_west": {"meal_inexpensive": 16.0, "meal_midrange": 32.0, "coffee": 3.2, "transport_ticket": 2.5, "safety_index": 62.0},
    "europe_east": {"meal_inexpensive": 9.0, "meal_midrange": 20.0, "coffee": 2.0, "transport_ticket": 1.2, "safety_index": 68.0},
    "europe_south": {"meal_inexpensive": 12.0, "meal_midrange": 26.0, "coffee": 2.0, "transport_ticket": 1.8, "safety_index": 60.0},
    "asia": {"meal_inexpensive": 5.0, "meal_midrange": 16.0, "coffee": 2.5, "transport_ticket": 1.0, "safety_index": 65.0},
    "america": {"meal_inexpensive": 18.0, "meal_midrange": 40.0, "coffee": 4.5, "transport_ticket": 2.5, "safety_index": 52.0},
    "default": {"meal_inexpensive": 14.0, "meal_midrange": 28.0, "coffee": 2.8, "transport_ticket": 2.0, "safety_index": 60.0}
}

def get_city_cost_and_safety(city_name: str, country_name: str = "", region: str = "") -> Tuple[float, float, Dict[str, Any]]:
    """
    Kiszámítja a célállomás napi becsült költségét (€) a valós Numbeo fogyasztói kosár alapján,
    valamint visszaadja a Numbeo Safety Indexet (0 - 100).
    """
    c_lower = city_name.lower().strip()
    
    # 1. Keresés a Numbeo adatbázisban
    matched = None
    for k, v in NUMBEO_CITY_DATA.items():
        if k in c_lower or c_lower in k:
            matched = v
            break
            
    if not matched:
        # Regionális fallback
        reg = region.lower()
        if "asia" in reg:
            matched = REGIONAL_FALLBACK["asia"]
        elif "america" in reg:
            matched = REGIONAL_FALLBACK["america"]
        elif "east" in reg:
            matched = REGIONAL_FALLBACK["europe_east"]
        elif "south" in reg or "spain" in country_name.lower() or "italy" in country_name.lower() or "portugal" in country_name.lower():
            matched = REGIONAL_FALLBACK["europe_south"]
        else:
            matched = REGIONAL_FALLBACK["default"]

    inexpensive = float(matched["meal_inexpensive"])
    midrange = float(matched["meal_midrange"])
    coffee = float(matched["coffee"])
    transit_ticket = float(matched["transport_ticket"])
    transit_daily = round(transit_ticket * 2.0, 1)

    # 1. Takarékos (Budget): 0.5 market reggeli + 1 olcsó ebéd + 1 olcsó vacsora + 1 kávé
    food_budget = round(inexpensive * 2.5 + coffee * 1.0, 1)
    
    # 2. Átlagos (Standard - Default): 1 reggeli/market + 1 olcsó ebéd + 0.5 mid-range vacsora (1 főre) + 1 kávé
    food_standard = round(inexpensive * 2.0 + midrange * 0.5 + coffee * 1.0, 1)

    # 3. Kényelmes (Comfort): 1 kávézós reggeli + 0.5 mid-range ebéd + 0.5 mid-range vacsora + 2 kávé/ital
    food_comfort = round(inexpensive * 1.0 + midrange * 1.0 + coffee * 2.0, 1)

    eur_rate = get_eur_huf_rate()
    safety_index = round(float(matched["safety_index"]), 1)

    profiles = {
        "budget": {
            "name": "Takarékos",
            "icon": "🥪",
            "description": "Pékség/reggeli + olcsó ebéd & vacsora + 1 kávé",
            "daily_food_eur": food_budget,
            "daily_food_huf": round(food_budget * eur_rate),
            "daily_transit_eur": transit_daily,
            "daily_transit_huf": round(transit_daily * eur_rate),
            "daily_total_eur": round(food_budget + transit_daily, 1),
            "daily_total_huf": round((food_budget + transit_daily) * eur_rate),
            "formula": "2.5 × olcsó étkezés + 1 × kávé + 2 × vonaljegy"
        },
        "standard": {
            "name": "Átlagos",
            "icon": "🍝",
            "description": "Egyszerű reggeli + olcsó ebéd + 3-fogásos vacsora (1 fő) + 1 kávé",
            "daily_food_eur": food_standard,
            "daily_food_huf": round(food_standard * eur_rate),
            "daily_transit_eur": transit_daily,
            "daily_transit_huf": round(transit_daily * eur_rate),
            "daily_total_eur": round(food_standard + transit_daily, 1),
            "daily_total_huf": round((food_standard + transit_daily) * eur_rate),
            "formula": "2 × olcsó étkezés + 0.5 × 2-személyes vacsora + 1 × kávé + 2 × vonaljegy"
        },
        "comfort": {
            "name": "Kényelmes",
            "icon": "🍷",
            "description": "Kávézós reggeli + beülős ebéd & vacsora + 2 kávé/ital",
            "daily_food_eur": food_comfort,
            "daily_food_huf": round(food_comfort * eur_rate),
            "daily_transit_eur": transit_daily,
            "daily_transit_huf": round(transit_daily * eur_rate),
            "daily_total_eur": round(food_comfort + transit_daily, 1),
            "daily_total_huf": round((food_comfort + transit_daily) * eur_rate),
            "formula": "1 × olcsó étkezés + 1 × 2-személyes étkezés + 2 × kávé + 2 × vonaljegy"
        }
    }

    # Alapértelmezett a Standard profil
    selected_profile = profiles["standard"]
    daily_food_eur = selected_profile["daily_food_eur"]
    daily_transit_eur = selected_profile["daily_transit_eur"]
    daily_cost_eur = selected_profile["daily_total_eur"]
    daily_food_huf = selected_profile["daily_food_huf"]
    daily_transit_huf = selected_profile["daily_transit_huf"]
    daily_cost_huf = selected_profile["daily_total_huf"]

    breakdown = {
        "meal_inexpensive": inexpensive,
        "meal_midrange": midrange,
        "coffee": coffee,
        "transport_ticket": transit_ticket,
        "daily_food_eur": daily_food_eur,
        "daily_food_huf": daily_food_huf,
        "daily_transit_eur": daily_transit_eur,
        "daily_transit_huf": daily_transit_huf,
        "daily_cost_eur": daily_cost_eur,
        "daily_cost_huf": daily_cost_huf,
        "safety_index": safety_index,
        "eur_rate": eur_rate,
        "active_profile": "standard",
        "profiles": profiles,
        "formula_text": selected_profile["formula"]
    }

    return daily_cost_eur, safety_index, breakdown
