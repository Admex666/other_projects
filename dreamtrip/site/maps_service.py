import os
import json
import time
import requests
import random
from typing import List, Dict, Optional
from models import POI, POILocation

# Cache fájl elérési útja
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "poi_cache.json")
CACHE_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 nap

def load_poi_cache() -> Dict:
    """Betölti a POI gyorsítótárat a fájlból."""
    if not os.path.exists(CACHE_FILE):
        # Létrehozzuk a data mappát, ha nem létezik
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Hiba a POI cache betöltésekor: {e}")
        return {}

def save_poi_cache(cache_data: Dict):
    """Elmenti a POI gyorsítótárat a fájlba."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Hiba a POI cache mentésekor: {e}")

def get_google_maps_api_key() -> Optional[str]:
    """Megpróbálja beolvasni a Google Maps API kulcsot a környezeti változókból."""
    return os.environ.get("GOOGLE_MAPS_API_KEY")

def fetch_pois_from_google(city_name: str, city_id: str, lat: float, lng: float, api_key: str) -> List[POI]:
    """Valós Google Places API hívások a POI adatok lekéréséhez."""
    print(f"[INFO] Valós Google Places API lekérdezés a következőhöz: {city_name}...")
    
    # Kategóriák és típusok lekérdezése
    # Google Places API (textsearch vagy nearbysearch)
    # A Nearby Search megbízhatóbb koordináták alapján
    categories = {
        "attraction": ["tourist_attraction", "museum", "park", "amusement_park", "church"],
        "restaurant": ["restaurant"],
        "cafe": ["cafe", "bakery"],
        "viewpoint": ["point_of_interest"]  # Ezt textsearch-csel pontosítjuk
    }
    
    pois_dict = {}
    
    # 1. Nearby Search a főbb kategóriákra
    for type_name, google_types in categories.items():
        if type_name == "viewpoint":
            # Viewpoint-okat inkább textsearch-csel keresünk
            search_query = f"scenic viewpoint in {city_name}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={requests.utils.quote(search_query)}&key={api_key}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    for place in results[:10]: # Limit 10 per category
                        place_id = place["place_id"]
                        if place_id not in pois_dict:
                            pois_dict[place_id] = {
                                "place": place,
                                "type": "viewpoint"
                            }
            except Exception as e:
                print(f"[WARN] Hiba a viewpoint keresésekor: {e}")
            continue
            
        # Alap kategóriák (attraction, restaurant, cafe)
        for g_type in google_types[:2]: # Max 2 google type-ot kérdezünk le kategóriánként a kvóta miatt
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type={g_type}&key={api_key}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    for place in results[:12]: # Limit 12 per sub-type
                        place_id = place["place_id"]
                        if place_id not in pois_dict:
                            pois_dict[place_id] = {
                                "place": place,
                                "type": type_name
                            }
            except Exception as e:
                print(f"[WARN] Hiba a Nearby Search ({g_type}) során: {e}")
                
    # 2. Place Details lekérése (nyitvatartás, cím, stb.)
    final_pois = []
    
    # Korlátozzuk a részletes lekérdezéseket (pl. max 25 legértékesebb POI-ra a költségek miatt)
    # Rendezzük értékelések és szavazatok száma alapján
    sorted_places = sorted(
        pois_dict.values(),
        key=lambda x: (x["place"].get("rating", 0) * x["place"].get("user_ratings_total", 0)),
        reverse=True
    )[:25]
    
    for item in sorted_places:
        place = item["place"]
        place_id = place["place_id"]
        poi_type = item["type"]
        
        # Place Details hívás
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,user_ratings_total,price_level,geometry,opening_hours,formatted_address,photos&key={api_key}"
        
        try:
            res = requests.get(details_url, timeout=10)
            if res.status_code == 200:
                details = res.json().get("result", {})
                if not details:
                    continue
                
                # Fotó URL lekérése, ha van
                image_url = None
                photos = details.get("photos", [])
                if photos:
                    photo_reference = photos[0].get("photo_reference")
                    image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={api_key}"
                
                loc = details["geometry"]["location"]
                
                # Nyitvatartási adatok feldolgozása
                raw_hours = details.get("opening_hours", {})
                
                # Létrehozzuk a POI objektumot
                poi = POI(
                    id=place_id,
                    city_id=city_id,
                    name=details.get("name", place.get("name", "Ismeretlen hely")),
                    type=poi_type,
                    rating=details.get("rating", place.get("rating", 0.0)),
                    user_ratings_total=details.get("user_ratings_total", place.get("user_ratings_total", 0)),
                    price_level=details.get("price_level"),
                    opening_hours=raw_hours,
                    location=POILocation(lat=loc["lat"], lng=loc["lng"]),
                    image_url=image_url,
                    address=details.get("formatted_address")
                )
                final_pois.append(poi)
        except Exception as e:
            print(f"[WARN] Hiba a Place Details ({place_id}) lekérésekor: {e}")
            
    return final_pois

def generate_mock_pois(city_name: str, city_id: str, lat: float, lng: float) -> List[POI]:
    """Valósághű szimulált POI-k generálása, ha nincs API kulcs vagy hiba történt."""
    print(f"[INFO] Mock POI adatok generálása ehhez a városhoz: {city_name} ({city_id})...")
    
    # Minták kategóriánként
    poi_templates = {
        "attraction": [
            {"name_pattern": "Főtér és Történelmi Városközpont", "rating_range": (4.5, 4.8), "ratings_count": (1000, 15000), "price": 0},
            {"name_pattern": "Királyi Palota és Vármúzeum", "rating_range": (4.6, 4.9), "ratings_count": (2000, 25000), "price": 2},
            {"name_pattern": "Modern Művészeti Galéria", "rating_range": (4.2, 4.6), "ratings_count": (300, 4000), "price": 1},
            {"name_pattern": "Botanikus Kert és Pálmaház", "rating_range": (4.4, 4.7), "ratings_count": (800, 6000), "price": 1},
            {"name_pattern": "Szent Katedrális", "rating_range": (4.7, 4.9), "ratings_count": (1500, 18000), "price": 0},
            {"name_pattern": "Néprajzi Szabadtéri Múzeum", "rating_range": (4.3, 4.7), "ratings_count": (500, 3500), "price": 1},
            {"name_pattern": "Városi Népkert és Csónakázótó", "rating_range": (4.4, 4.6), "ratings_count": (1200, 8000), "price": 0},
            {"name_pattern": "Tudományos és Technológiai Központ", "rating_range": (4.5, 4.8), "ratings_count": (400, 3000), "price": 2}
        ],
        "restaurant": [
            {"name_pattern": "Bistro {city} - Helyi Ízek", "rating_range": (4.4, 4.8), "ratings_count": (200, 1500), "price": 2},
            {"name_pattern": "La Piazza Trattoria", "rating_range": (4.3, 4.7), "ratings_count": (400, 3000), "price": 2},
            {"name_pattern": "Gourmet Garden Fine Dining", "rating_range": (4.6, 4.9), "ratings_count": (100, 800), "price": 3},
            {"name_pattern": "The Rusty Anchor Fish & Chips", "rating_range": (4.1, 4.5), "ratings_count": (150, 1000), "price": 1},
            {"name_pattern": "Burger & Craft Beer House", "rating_range": (4.3, 4.6), "ratings_count": (300, 2000), "price": 2},
            {"name_pattern": "Zöld Kert Vegetáriánus Étterem", "rating_range": (4.4, 4.7), "ratings_count": (120, 900), "price": 2}
        ],
        "cafe": [
            {"name_pattern": "The Daily Grind Specialty Cafe", "rating_range": (4.6, 4.9), "ratings_count": (80, 600), "price": 1},
            {"name_pattern": "Vintage Coffee & Bookshop", "rating_range": (4.5, 4.8), "ratings_count": (150, 1200), "price": 1},
            {"name_pattern": "Central Park Espresso Bar", "rating_range": (4.2, 4.6), "ratings_count": (100, 800), "price": 1},
            {"name_pattern": "Grand Patisserie és Kávéház", "rating_range": (4.4, 4.8), "ratings_count": (250, 1800), "price": 2}
        ],
        "viewpoint": [
            {"name_pattern": "{city} Panoráma Kilátóterasz", "rating_range": (4.7, 4.9), "ratings_count": (500, 5000), "price": 0},
            {"name_pattern": "Várhegy Kilátópont", "rating_range": (4.6, 4.8), "ratings_count": (800, 7000), "price": 0},
            {"name_pattern": "TV-Torony SkyBar", "rating_range": (4.3, 4.6), "ratings_count": (200, 1500), "price": 2}
        ]
    }
    
    mock_pois = []
    
    # Nyitvatartási sablonok
    standard_hours = {
        "open_now": True,
        "periods": [
            {
                "close": {"day": d, "time": "1800"},
                "open": {"day": d, "time": "0900"}
            } for d in range(7)
        ],
        "weekday_text": [
            "Monday: 9:00 AM – 6:00 PM",
            "Tuesday: 9:00 AM – 6:00 PM",
            "Wednesday: 9:00 AM – 6:00 PM",
            "Thursday: 9:00 AM – 6:00 PM",
            "Friday: 9:00 AM – 6:00 PM",
            "Saturday: 9:00 AM – 6:00 PM",
            "Sunday: 9:00 AM – 6:00 PM"
        ]
    }
    
    restaurant_hours = {
        "open_now": True,
        "periods": [
            {
                "close": {"day": d, "time": "2200"},
                "open": {"day": d, "time": "1130"}
            } for d in range(7)
        ],
        "weekday_text": [
            "Monday: 11:30 AM – 10:00 PM",
            "Tuesday: 11:30 AM – 10:00 PM",
            "Wednesday: 11:30 AM – 10:00 PM",
            "Thursday: 11:30 AM – 10:00 PM",
            "Friday: 11:30 AM – 10:00 PM",
            "Saturday: 11:30 AM – 10:00 PM",
            "Sunday: 11:30 AM – 10:00 PM"
        ]
    }
    
    cafe_hours = {
        "open_now": True,
        "periods": [
            {
                "close": {"day": d, "time": "2000"},
                "open": {"day": d, "time": "0730"}
            } for d in range(7)
        ],
        "weekday_text": [
            "Monday: 7:30 AM – 8:00 PM",
            "Tuesday: 7:30 AM – 8:00 PM",
            "Wednesday: 7:30 AM – 8:00 PM",
            "Thursday: 7:30 AM – 8:00 PM",
            "Friday: 7:30 AM – 8:00 PM",
            "Saturday: 8:00 AM – 8:00 PM",
            "Sunday: 8:00 AM – 8:00 PM"
        ]
    }
    
    viewpoint_hours = {
        "open_now": True,
        "periods": [
            {
                "close": {"day": d, "time": "2359"},
                "open": {"day": d, "time": "0000"}
            } for d in range(7)
        ],
        "weekday_text": [
            "Monday: Open 24 hours",
            "Tuesday: Open 24 hours",
            "Wednesday: Open 24 hours",
            "Thursday: Open 24 hours",
            "Friday: Open 24 hours",
            "Saturday: Open 24 hours",
            "Sunday: Open 24 hours"
        ]
    }
    
    # Generálunk POI-kat
    for p_type, templates in poi_templates.items():
        for idx, template in enumerate(templates):
            name = template["name_pattern"].format(city=city_name)
            rating = round(random.uniform(*template["rating_range"]), 1)
            ratings_count = random.randint(*template["ratings_count"])
            price_level = template["price"]
            
            # Koordináták eltolása a városközponthoz képest (-0.02 és +0.02 fok között)
            # Ez kb 1-2 km sugarú kört ad
            offset_lat = random.uniform(-0.02, 0.02)
            offset_lng = random.uniform(-0.02, 0.02)
            
            poi_lat = lat + offset_lat
            poi_lng = lng + offset_lng
            
            # Megfelelő nyitvatartás kiválasztása
            if p_type == "restaurant":
                hours = restaurant_hours
            elif p_type == "cafe":
                hours = cafe_hours
            elif p_type == "viewpoint":
                hours = viewpoint_hours
            else:
                hours = standard_hours
                
            # Place ID formázás
            place_id = f"mock_{city_id}_{p_type}_{idx}"
            
            # Kép placeholder kategória alapján
            image_category = "architecture" if p_type == "attraction" else ("food" if p_type == "restaurant" else ("coffee" if p_type == "cafe" else "nature"))
            image_url = f"https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=400&q=80" # Default fallback
            
            poi = POI(
                id=place_id,
                city_id=city_id,
                name=name,
                type=p_type,
                rating=rating,
                user_ratings_total=ratings_count,
                price_level=price_level,
                opening_hours=hours,
                location=POILocation(lat=poi_lat, lng=poi_lng),
                image_url=image_url,
                address=f"{city_name}, Main Street {random.randint(1, 150)}."
            )
            mock_pois.append(poi)
            
    return mock_pois

def get_city_pois(city_name: str, city_id: str, lat: float, lng: float, bypass_cache: bool = False) -> List[POI]:
    """
    Lekéri a város POI-jait. Ellenőrzi a cache-t, és ha nem létezik vagy lejárt,
    akkor a Google Places API-t hívja (ha van kulcs), egyébként Mock adatokat ad vissza.
    """
    cache = load_poi_cache()
    
    # 1. Cache ellenőrzés
    if not bypass_cache and city_id in cache:
        cached_item = cache[city_id]
        timestamp = cached_item.get("timestamp", 0)
        
        # Ha a cache nem járt le
        if time.time() - timestamp < CACHE_EXPIRY_SECONDS:
            print(f"[INFO] POI adatok betöltve a gyorsítótárból ({city_name})...")
            pois_list = []
            for poi_data in cached_item.get("pois", []):
                try:
                    pois_list.append(POI(**poi_data))
                except Exception as e:
                    print(f"[WARN] Hiba a gyorsítótárazott POI objektum létrehozásakor: {e}")
            if pois_list:
                return pois_list
                
    # 2. Új adatok lekérése
    api_key = get_google_maps_api_key()
    
    try:
        if api_key:
            pois = fetch_pois_from_google(city_name, city_id, lat, lng, api_key)
            if not pois: # Ha a Google hívás nem adott eredményt, fallback mockra
                pois = generate_mock_pois(city_name, city_id, lat, lng)
        else:
            pois = generate_mock_pois(city_name, city_id, lat, lng)
    except Exception as e:
        print(f"[ERROR] Hiba a POI lekérdezés során, fallback mock adatokra: {e}")
        pois = generate_mock_pois(city_name, city_id, lat, lng)
        
    # 3. Mentés a gyorsítótárba
    pois_json_ready = [poi.dict() for poi in pois]
    cache[city_id] = {
        "timestamp": time.time(),
        "pois": pois_json_ready
    }
    save_poi_cache(cache)
    
    return pois
