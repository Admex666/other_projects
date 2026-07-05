import os
import json
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple
from models import City, TravelPreferences
import scraper
import maps_service

# Statikus walkability pontszámok (ha nem áll rendelkezésre más adat)
WALKABILITY_SCORES = {
    "barcelona": 92.0, "roma": 88.0, "rome": 88.0, "bali": 35.0, "reykjavik": 65.0,
    "tokio": 90.0, "tokyo": 90.0, "szantorini": 55.0, "santorini": 55.0, "new york": 89.0,
    "amszterdam": 96.0, "amsterdam": 96.0, "dubaj": 40.0, "dubai": 40.0, "parizs": 94.0,
    "paris": 94.0, "lisszabon": 85.0, "lisbon": 85.0, "bangkok": 60.0, "sydney": 80.0,
    "berlin": 90.0, "london": 92.0, "becs": 93.0, "vienna": 93.0, "zurich": 91.0,
    "brusszel": 88.0, "brussels": 88.0, "praga": 92.0, "prague": 92.0, "varso": 84.0,
    "warsaw": 84.0, "koppenhaga": 95.0, "copenhagen": 95.0, "stockholm": 92.0, "oslo": 90.0,
    "helsinki": 91.0, "dublin": 87.0, "tallinn": 89.0, "riga": 85.0, "vilnius": 84.0,
    "isztambul": 78.0, "istanbul": 78.0, "valletta": 82.0, "larnaca": 70.0, "luxembourg": 85.0,
    "split": 80.0, "szofia": 78.0, "sofia": 78.0, "bukarest": 75.0, "bucharest": 75.0,
    "belgrad": 77.0, "belgrade": 77.0, "tirana": 70.0
}

def load_numbeo_data() -> Dict:
    """Betölti a Numbeo adatokat."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    numbeo_path = os.path.join(base_dir, "data", "live_numbeo_indices.json")
    if os.path.exists(numbeo_path):
        try:
            with open(numbeo_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Hiba a Numbeo adatok betöltésekor: {e}")
    return {}

def get_city_numbeo_metrics(city_name: str, static_metrics: Dict, numbeo_data: Dict) -> Tuple[float, float]:
    """Megállapítja a város cost és safety indexét a Numbeo fájl vagy a statikus adatok alapján."""
    # Alapértelmezett értékek a statikus json-ből
    city_cost = static_metrics.get("cost_index_daily_eur", 100.0)
    city_safety = static_metrics.get("safety_index", 50.0)
    
    # Keresés a Numbeo adatokban
    for key, val in numbeo_data.items():
        if city_name.lower() in key.lower():
            if val.get("cost_index"):
                # Átszámítás euróra a main.py mintájára: max(65, round(Index * 4.7 - 115))
                city_cost = max(65.0, float(round(val["cost_index"] * 4.7 - 115)))
            if val.get("safety_index"):
                city_safety = float(round(val["safety_index"]))
            break
            
    return city_cost, city_safety

def get_city_walkability(city_name: str) -> float:
    """Visszaadja a város walkability pontszámát."""
    name_clean = city_name.lower().strip()
    return WALKABILITY_SCORES.get(name_clean, 70.0)

def fetch_single_city_data(dest: Dict, origin_city: str, month: int, ideal_temp: float, tokens: Dict, numbeo_data: Dict) -> Dict:
    """Lekéri egy város repülőjegyét, időjárását és POI-jait párhuzamos futtatáshoz."""
    dest_name = dest["name"]
    dest_id = dest["id"]
    lat = dest["lat"]
    lon = dest["lon"]
    
    # 1. Időjárás lekérése (Open-Meteo)
    weather_start = f"2024-{month:02d}-10"
    weather_end = f"2024-{month:02d}-16"
    avg_temp = 20.0  # Alapértelmezett fallback
    
    try:
        w_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={weather_start}&end_date={weather_end}&daily=temperature_2m_max,temperature_2m_min&timezone=GMT"
        wr = requests.get(w_url, timeout=5)
        if wr.status_code == 200:
            w_data = wr.json()
            max_temps = w_data.get("daily", {}).get("temperature_2m_max", [])
            min_temps = w_data.get("daily", {}).get("temperature_2m_min", [])
            valid_temps = [ (mx + mn)/2 for mx, mn in zip(max_temps, min_temps) if mx is not None and mn is not None ]
            if valid_temps:
                avg_temp = sum(valid_temps) / len(valid_temps)
    except Exception as e:
        print(f"[WARN] Weather error for {dest_name}: {e}")
        
    # 2. Repülőjegy árak (Kiwi API)
    cheapest_flight = None
    try:
        # Repülőjegy keresése a hónap 10-20 között
        flight_df = scraper.search_flights_by_city_name_v2(
            origin_name=origin_city,
            destination_name=dest_name,
            tokens=tokens,
            date_from=f"2026-{month:02d}-10",
            date_to=f"2026-{month:02d}-20",
            limit=5
        )
        if not flight_df.empty:
            cheapest_flight = float(flight_df["price_huf"].min())
    except Exception as e:
        print(f"[WARN] Flight error for {dest_name}: {e}")
        
    # 3. POI lekérdezés a sűrűséghez (attraction density)
    attraction_count = 0
    try:
        pois = maps_service.get_city_pois(dest_name, dest_id, lat, lon)
        attraction_count = len([p for p in pois if p.type == "attraction"])
    except Exception as e:
        print(f"[WARN] POI density error for {dest_name}: {e}")
        
    # Numbeo adatok lekérése
    cost_index, safety_index = get_city_numbeo_metrics(dest_name, dest.get("metrics", {}), numbeo_data)
    
    return {
        "id": dest_id,
        "name": dest_name,
        "country": dest["country"],
        "region": dest.get("region"),
        "lat": lat,
        "lon": lon,
        "image": dest.get("image"),
        "avg_temp": avg_temp,
        "cheapest_flight": cheapest_flight,
        "attraction_count": attraction_count,
        "cost_index": cost_index,
        "safety_index": safety_index,
        "walkability": get_city_walkability(dest_name)
    }

def calculate_city_scores(
    dests: List[Dict],
    prefs: TravelPreferences,
    origin_city: str,
    month: int
) -> List[City]:
    """
    Kiszámolja a városok pontszámát és rangsorolja őket.
    A hiányzó repülőjegy árak esetén a súlyozás automatikusan igazodik (failure scenario).
    """
    n = len(dests)
    if n == 0:
        return []
        
    tokens = scraper.get_kiwi_tokens()
    numbeo_data = load_numbeo_data()
    
    # 1. Párhuzamos adatgyűjtés
    print(f"[INFO] Adatok lekérése {n} városra...")
    city_raw_data = []
    with ThreadPoolExecutor(max_workers=min(5, n)) as executor:
        futures = [
            executor.submit(fetch_single_city_data, dest, origin_city, month, prefs.weather_temp, tokens, numbeo_data)
            for dest in dests
        ]
        for f in futures:
            try:
                city_raw_data.append(f.result())
            except Exception as e:
                print(f"[ERROR] Hiba egy város adatainak feldolgozásakor: {e}")
                
    if not city_raw_data:
        return []
        
    # 2. Normalizálás és Pontszámítás
    # Összegyűjtjük a szélsőértékeket a skálázáshoz
    flight_prices = [c["cheapest_flight"] for c in city_raw_data if c["cheapest_flight"] is not None]
    cost_indices = [c["cost_index"] for c in city_raw_data]
    attraction_counts = [c["attraction_count"] for c in city_raw_data]
    
    max_flight = max(flight_prices) if flight_prices else 500000.0
    min_flight = min(flight_prices) if flight_prices else 10000.0
    
    max_cost = max(cost_indices) if cost_indices else 300.0
    min_cost = min(cost_indices) if cost_indices else 40.0
    
    max_attr = max(attraction_counts) if attraction_counts else 10
    min_attr = min(attraction_counts) if attraction_counts else 0

    scored_cities = []
    
    for c in city_raw_data:
        # -- Flight Score (0-100, olcsóbb = magasabb pont)
        flight_score = 0.0
        has_flight = c["cheapest_flight"] is not None
        if has_flight:
            if max_flight == min_flight:
                flight_score = 100.0
            else:
                flight_score = 100.0 * (max_flight - c["cheapest_flight"]) / (max_flight - min_flight)
                
        # -- Cost Score (0-100, olcsóbb = magasabb pont)
        if max_cost == min_cost:
            cost_score = 100.0
        else:
            cost_score = 100.0 * (max_cost - c["cost_index"]) / (max_cost - min_cost)
            
        # -- Attraction Density Score (0-100, több = magasabb pont)
        if max_attr == min_attr:
            attr_score = 100.0
        else:
            attr_score = 100.0 * (c["attraction_count"] - min_attr) / (max_attr - min_attr)
            
        # -- Weather Score (0-100, eltérés az ideálistól)
        # Ideális hőmérséklethez való közelség
        temp_diff = abs(c["avg_temp"] - prefs.weather_temp)
        weather_score = max(0.0, 100.0 - (temp_diff * 6.0)) # 16 fok eltérés felett 0
        
        # -- Safety Score (0-100, Numbeo index)
        safety_score = float(c["safety_index"])
        
        # -- Walkability Score (0-100, előre definiált)
        walk_score = float(c["walkability"])
        
        # Súlyok beállítása (specifikáció szerint)
        # flight cost (0.3), cost of living (0.2), attraction density (0.2), weather (0.1), safety (0.1), walkability (0.1)
        w_flight = 0.3
        w_cost = 0.2
        w_attraction = 0.2
        w_weather = 0.1
        w_safety = 0.1
        w_walkability = 0.1
        
        # Súlyok újraszámolása ha nincs repülőjegy adat (Failure Scenario)
        if not has_flight:
            total_active_w = w_cost + w_attraction + w_weather + w_safety + w_walkability
            # Normalizáljuk a meglévőket 1.0-ra
            w_cost /= total_active_w
            w_attraction /= total_active_w
            w_weather /= total_active_w
            w_safety /= total_active_w
            w_walkability /= total_active_w
            w_flight = 0.0
            
        computed_score = (
            w_flight * flight_score +
            w_cost * cost_score +
            w_attraction * attr_score +
            w_weather * weather_score +
            w_safety * safety_score +
            w_walkability * walk_score
        )
        
        # Magyarázat generálása
        reasons = []
        if has_flight and flight_score > 75:
            reasons.append("kedvező árú repülőjegy")
        if cost_score > 75:
            reasons.append("alacsony kinti árak")
        if attr_score > 75:
            reasons.append("rendkívül sok látnivaló")
        if weather_score > 80:
            reasons.append("kellemes, ideális időjárás")
        if safety_score > 70:
            reasons.append("kiemelkedő közbiztonság")
        if walk_score > 85:
            reasons.append("kiválóan bejárható gyalogosan")
            
        if len(reasons) >= 2:
            explanation = f"Főbb előnyök: {', '.join(reasons[:-1])} és {reasons[-1]}."
        elif reasons:
            explanation = f"Főbb előny: {reasons[0]}."
        else:
            explanation = "Kiegyensúlyozott opció, átlagos értékekkel."
            
        # City objektum létrehozása
        city_obj = City(
            id=c["id"],
            name=c["name"],
            country=c["country"],
            cost_index=c["cost_index"],
            safety_index=c["safety_index"],
            weather_score=weather_score,
            attraction_density=c["attraction_count"],
            nightlife_score=50.0, # Placeholder
            walkability_score=walk_score,
            flight_score=flight_score if has_flight else 0.0,
            computed_score=round(computed_score, 1),
            image=c["image"],
            lat=c["lat"],
            lon=c["lon"],
            region=c["region"]
        )
        
        # Mentjük az explanation-t ideiglenesen egy extra attribútumba (vagy a main.py kezeli)
        city_obj.__dict__["explanation"] = explanation
        scored_cities.append(city_obj)
        
    # Rendezés pontszám szerint csökkenő sorrendbe
    scored_cities.sort(key=lambda x: x.computed_score, reverse=True)
    
    return scored_cities
