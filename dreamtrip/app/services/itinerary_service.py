import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from app.models.models import POI, ItineraryDay, ItineraryItem, POILocation
from app.services import maps_service

def haversine_distance(loc1: POILocation, loc2: POILocation) -> float:
    """Kiszámolja a távolságot két koordináta között kilométerben (Haversine képlet)."""
    R = 6371.0  # Föld sugara km-ben
    lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lng)
    lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lng)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def calculate_travel_time_minutes(loc1: POILocation, loc2: POILocation) -> Tuple[float, int]:
    """
    Kiszámolja az utazási időt percekben és a távolságot km-ben.
    - Sétálva (ha távolság <= 1.5 km): ~4.5 km/h -> ~13 perc/km
    - Tömegközlekedéssel/autóval (ha távolság > 1.5 km): ~20 km/h -> ~3 perc/km + 5 perc várakozási idő
    """
    dist = haversine_distance(loc1, loc2)
    if dist <= 1.5:
        # Sétálás
        time_mins = max(5, int(dist * 13))
    else:
        # Tömegközlekedés/Autó
        time_mins = max(10, int(dist * 3 + 5))
    return dist, time_mins

def is_poi_open_at(poi: POI, weekday: int, hour: int, minute: int) -> bool:
    """
    Megvizsgálja, hogy a POI nyitva van-e a megadott napon és időpontban.
    weekday: 0 (Hétfő) - 6 (Vasárnap)
    hour: 0-23
    minute: 0-59
    """
    # Ha nincs megadva nyitvatartás, feltételezzük, hogy nyitva van (Failure Scenario default)
    if not poi.opening_hours or "periods" not in poi.opening_hours:
        return True
        
    periods = poi.opening_hours.get("periods", [])
    if not periods:
        return True
        
    current_time_str = f"{hour:02d}{minute:02d}"
    
    for period in periods:
        # Google Places-ben a napok: 0 (Vasárnap) - 6 (Szombat)
        # Python weekday: 0 (Hétfő) - 6 (Vasárnap)
        # Konvertáljuk a Python weekday-t Google Place day-re:
        # Python 0 -> Google 1, Python 5 -> Google 6, Python 6 -> Google 0
        google_day = (weekday + 1) % 7
        
        # Nyitó és záró adatok lekérése
        open_info = period.get("open", {})
        close_info = period.get("close", {})
        
        if not open_info:
            continue
            
        open_day = open_info.get("day")
        open_time = open_info.get("time")
        
        # Ha 24 órás nyitvatartás van
        if open_day == google_day and open_time == "0000" and not close_info:
            return True
            
        if open_day == google_day:
            close_day = close_info.get("day", google_day)
            close_time = close_info.get("time", "2359")
            
            # Egyszerűsített ellenőrzés azonos napon belüli nyitvatartásra
            if close_day == google_day:
                if open_time <= current_time_str <= close_time:
                    return True
            else:
                # Ha a nyitvatartás átnyúlik a következő napra
                if current_time_str >= open_time:
                    return True
        
        # Ha a zárás az aktuális napra esik, de a nyitás az előző napon volt
        prev_google_day = (google_day - 1) % 7
        if open_info.get("day") == prev_google_day and close_info:
            close_day = close_info.get("day")
            close_time = close_info.get("time", "0000")
            if close_day == google_day and current_time_str <= close_time:
                return True
                
    return False

def parse_time_str(time_str: str) -> Tuple[int, int]:
    """HH:MM formátumú string felbontása órára és percre."""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

def format_time_str(hour: int, minute: int) -> str:
    """Óra és perc formázása HH:MM formátumra."""
    return f"{hour:02d}:{minute:02d}"

def add_minutes_to_time(time_str: str, minutes: int) -> str:
    """HH:MM stringhez hozzáad megadott mennyiségű percet."""
    h, m = parse_time_str(time_str)
    new_time = datetime(2020, 1, 1, h, m) + timedelta(minutes=minutes)
    return new_time.strftime("%H:%M")

def generate_default_itinerary(
    city_id: str,
    city_name: str,
    lat: float,
    lng: float,
    start_date_str: str,
    end_date_str: str
) -> List[ItineraryDay]:
    """
    Létrehoz egy alapértelmezett, constraint-alapú napitervet a megadott dátumok között.
    Automatikusan feltölti étkezésekkel és a legjobb POI-kkal.
    """
    # Dátumok kiszámítása
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    num_days = (end_date - start_date).days + 1
    
    # Lekérjük a város összes POI-ját
    all_pois = maps_service.get_city_pois(city_name, city_id, lat, lng)
    
    # Szétosztjuk kategóriák szerint
    attractions = [p for p in all_pois if p.type in ["attraction", "viewpoint"]]
    restaurants = [p for p in all_pois if p.type == "restaurant"]
    cafes = [p for p in all_pois if p.type == "cafe"]
    
    # Rendezzük minőség alapján (rating * user_ratings_total)
    attractions.sort(key=lambda p: p.rating * p.user_ratings_total, reverse=True)
    restaurants.sort(key=lambda p: p.rating * p.user_ratings_total, reverse=True)
    cafes.sort(key=lambda p: p.rating * p.user_ratings_total, reverse=True)
    
    itinerary_days = []
    visited_pois: Set[str] = set()
    
    for d_idx in range(num_days):
        current_day = start_date + timedelta(days=d_idx)
        date_str = current_day.strftime("%Y-%m-%d")
        weekday = current_day.weekday() # 0: Hétfő, 6: Vasárnap
        
        day_items: List[ItineraryItem] = []
        
        # 1. Reggeli Slot (08:30 - 09:15)
        breakfast_cafe = None
        for cafe in cafes:
            if cafe.id not in visited_pois and is_poi_open_at(cafe, weekday, 8, 30):
                breakfast_cafe = cafe
                visited_pois.add(cafe.id)
                break
        # Fallback ha mind foglalt vagy zárva
        if not breakfast_cafe and cafes:
            breakfast_cafe = cafes[0]
            
        if breakfast_cafe:
            day_items.append(ItineraryItem(
                poi_id=breakfast_cafe.id,
                poi_name=breakfast_cafe.name,
                start_time="08:30",
                end_time="09:15",
                type="meal",
                details={
                    "category": "breakfast",
                    "price_level": breakfast_cafe.price_level,
                    "address": breakfast_cafe.address,
                    "image": breakfast_cafe.image_url,
                    "rating": breakfast_cafe.rating
                }
            ))
            
        # 2. Délelőtti Aktivitás (09:45 - 12:30)
        # Utazási idő hozzáadása a reggelitől
        morning_poi = None
        for attr in attractions:
            if attr.id not in visited_pois and is_poi_open_at(attr, weekday, 9, 45):
                morning_poi = attr
                visited_pois.add(attr.id)
                break
                
        if morning_poi:
            # Utazás kiszámítása reggelitől
            if breakfast_cafe:
                dist, duration = calculate_travel_time_minutes(breakfast_cafe.location, morning_poi.location)
                day_items.append(ItineraryItem(
                    start_time="09:15",
                    end_time=add_minutes_to_time("09:15", duration),
                    type="travel",
                    details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                ))
                
            day_items.append(ItineraryItem(
                poi_id=morning_poi.id,
                poi_name=morning_poi.name,
                start_time="09:45",
                end_time="12:30",
                type="activity",
                details={
                    "category": "attraction",
                    "price_level": morning_poi.price_level,
                    "address": morning_poi.address,
                    "image": morning_poi.image_url,
                    "rating": morning_poi.rating
                }
            ))
            
        # 3. Ebéd Slot (13:00 - 14:15)
        lunch_rest = None
        # Ebédnél jó lenne a délelőtti POI-hoz közeli éttermet választani
        local_restaurants = list(restaurants)
        if morning_poi:
            local_restaurants.sort(key=lambda r: haversine_distance(r.location, morning_poi.location))
            
        for rest in local_restaurants:
            if rest.id not in visited_pois and is_poi_open_at(rest, weekday, 13, 0):
                lunch_rest = rest
                visited_pois.add(rest.id)
                break
        if not lunch_rest and restaurants:
            lunch_rest = restaurants[0]
            
        if lunch_rest:
            if morning_poi:
                dist, duration = calculate_travel_time_minutes(morning_poi.location, lunch_rest.location)
                day_items.append(ItineraryItem(
                    start_time="12:30",
                    end_time=add_minutes_to_time("12:30", duration),
                    type="travel",
                    details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                ))
                
            day_items.append(ItineraryItem(
                poi_id=lunch_rest.id,
                poi_name=lunch_rest.name,
                start_time="13:00",
                end_time="14:15",
                type="meal",
                details={
                    "category": "lunch",
                    "price_level": lunch_rest.price_level,
                    "address": lunch_rest.address,
                    "image": lunch_rest.image_url,
                    "rating": lunch_rest.rating
                }
            ))
            
        # 4. Délutáni Aktivitás (14:45 - 18:00)
        # Ebéd utáni POI keresése közelség alapján
        local_attractions = list(attractions)
        if lunch_rest:
            local_attractions.sort(key=lambda a: haversine_distance(a.location, lunch_rest.location))
            
        afternoon_poi = None
        for attr in local_attractions:
            if attr.id not in visited_pois and is_poi_open_at(attr, weekday, 14, 45):
                afternoon_poi = attr
                visited_pois.add(attr.id)
                break
                
        if afternoon_poi:
            if lunch_rest:
                dist, duration = calculate_travel_time_minutes(lunch_rest.location, afternoon_poi.location)
                day_items.append(ItineraryItem(
                    start_time="14:15",
                    end_time=add_minutes_to_time("14:15", duration),
                    type="travel",
                    details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                ))
                
            day_items.append(ItineraryItem(
                poi_id=afternoon_poi.id,
                poi_name=afternoon_poi.name,
                start_time="14:45",
                end_time="18:00",
                type="activity",
                details={
                    "category": "attraction",
                    "price_level": afternoon_poi.price_level,
                    "address": afternoon_poi.address,
                    "image": afternoon_poi.image_url,
                    "rating": afternoon_poi.rating
                }
            ))
            
        # 5. Vacsora Slot (18:30 - 20:00)
        dinner_rest = None
        local_restaurants = list(restaurants)
        if afternoon_poi:
            local_restaurants.sort(key=lambda r: haversine_distance(r.location, afternoon_poi.location))
            
        for rest in local_restaurants:
            if rest.id not in visited_pois and is_poi_open_at(rest, weekday, 18, 30):
                dinner_rest = rest
                visited_pois.add(rest.id)
                break
        if not dinner_rest and len(restaurants) > 1:
            dinner_rest = restaurants[1]
            
        if dinner_rest:
            if afternoon_poi:
                dist, duration = calculate_travel_time_minutes(afternoon_poi.location, dinner_rest.location)
                day_items.append(ItineraryItem(
                    start_time="18:00",
                    end_time=add_minutes_to_time("18:00", duration),
                    type="travel",
                    details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                ))
                
            day_items.append(ItineraryItem(
                poi_id=dinner_rest.id,
                poi_name=dinner_rest.name,
                start_time="18:30",
                end_time="20:00",
                type="meal",
                details={
                    "category": "dinner",
                    "price_level": dinner_rest.price_level,
                    "address": dinner_rest.address,
                    "image": dinner_rest.image_url,
                    "rating": dinner_rest.rating
                }
            ))
            
        # 6. Esti Kilátópont / Séta (20:30 - 22:00)
        evening_poi = None
        local_attractions = list(attractions)
        if dinner_rest:
            local_attractions.sort(key=lambda a: haversine_distance(a.location, dinner_rest.location))
            
        for attr in local_attractions:
            if attr.id not in visited_pois and is_poi_open_at(attr, weekday, 20, 30):
                evening_poi = attr
                visited_pois.add(attr.id)
                break
                
        if evening_poi:
            if dinner_rest:
                dist, duration = calculate_travel_time_minutes(dinner_rest.location, evening_poi.location)
                day_items.append(ItineraryItem(
                    start_time="20:00",
                    end_time=add_minutes_to_time("20:00", duration),
                    type="travel",
                    details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                ))
                
            day_items.append(ItineraryItem(
                poi_id=evening_poi.id,
                poi_name=evening_poi.name,
                start_time="20:30",
                end_time="22:00",
                type="activity",
                details={
                    "category": "viewpoint" if evening_poi.type == "viewpoint" else "attraction",
                    "price_level": evening_poi.price_level,
                    "address": evening_poi.address,
                    "image": evening_poi.image_url,
                    "rating": evening_poi.rating
                }
            ))
            
        itinerary_days.append(ItineraryDay(date=date_str, items=day_items))
        
    return itinerary_days

def reoptimize_itinerary_day(
    day_data: ItineraryDay,
    city_id: str,
    city_name: str,
    lat: float,
    lng: float
) -> ItineraryDay:
    """
    Újraszámolja a napirendet (időpontok és utazási idők) a fixen rögzített (locked) elemeket megtartva.
    Megkeresi az ütközéseket és megpróbálja kijavítani őket.
    """
    weekday = datetime.strptime(day_data.date, "%Y-%m-%d").weekday()
    all_pois = maps_service.get_city_pois(city_name, city_id, lat, lng)
    pois_dict = {p.id: p for p in all_pois}
    
    # 1. Kiszűrjük az utazási elemeket, mert azokat dinamikusan újrageneráljuk
    clean_items = [item for item in day_data.items if item.type != "travel"]
    if not clean_items:
        return day_data
        
    new_items: List[ItineraryItem] = []
    
    # Kezdő időpont
    current_time = "08:30"
    
    for idx, item in enumerate(clean_items):
        poi = pois_dict.get(item.poi_id) if item.poi_id else None
        
        # Ha zárolva van az időpont, azt kötelező megtartani
        if item.locked:
            start_t = item.start_time
            end_t = item.end_time
        else:
            # Egyébként a legkorábbi lehetséges időpontra tesszük
            start_t = current_time
            # Kiszámoljuk az időtartamot percekben
            h1, m1 = parse_time_str(item.start_time)
            h2, m2 = parse_time_str(item.end_time)
            duration_mins = (h2 * 60 + m2) - (h1 * 60 + m1)
            if duration_mins <= 0:
                duration_mins = 60 # Default 1 óra
            end_t = add_minutes_to_time(start_t, duration_mins)
            
        # Nyitvatartás ellenőrzés
        conflict_msg = None
        if poi:
            sh, sm = parse_time_str(start_t)
            is_open = is_poi_open_at(poi, weekday, sh, sm)
            if not is_open:
                conflict_msg = f"A hely ({poi.name}) valószínűleg zárva van ebben az időpontban!"
                
        # Frissítjük a start/end-eket és a konfliktust
        updated_item = ItineraryItem(
            poi_id=item.poi_id,
            poi_name=item.poi_name,
            start_time=start_t,
            end_time=end_t,
            type=item.type,
            locked=item.locked,
            details=item.details or {}
        )
        if conflict_msg:
            updated_item.details["conflict"] = conflict_msg
        elif "conflict" in updated_item.details:
            del updated_item.details["conflict"]
            
        # Utazási idő beszúrása a megelőző elem és eközött
        if idx > 0 and new_items:
            prev_item = new_items[-1]
            prev_poi = pois_dict.get(prev_item.poi_id) if prev_item.poi_id else None
            
            if prev_poi and poi:
                dist, duration = calculate_travel_time_minutes(prev_poi.location, poi.location)
                
                # Ha nem zárolt az elem, akkor korrigáljuk a kezdést, hogy beleférjen a travel time is
                if not updated_item.locked:
                    start_with_travel = add_minutes_to_time(prev_item.end_time, duration)
                    # Frissítjük a startot és end-et
                    updated_item.start_time = start_with_travel
                    updated_item.end_time = add_minutes_to_time(start_with_travel, duration_mins)
                    
                    # Beillesztjük az utazást
                    new_items.append(ItineraryItem(
                        start_time=prev_item.end_time,
                        end_time=start_with_travel,
                        type="travel",
                        details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                    ))
                else:
                    # Ha zárolt az elem, de az utazási idő nem fér be a kettő közé
                    # (pl. a zárolt elem kezdete korábbi, mint az előző vége + utazási idő)
                    travel_start = prev_item.end_time
                    travel_end = updated_item.start_time
                    
                    h_start, m_start = parse_time_str(travel_start)
                    h_end, m_end = parse_time_str(travel_end)
                    available_mins = (h_end * 60 + m_end) - (h_start * 60 + m_start)
                    
                    if available_mins < duration:
                        # Konfliktus jelzése az utazáson
                        new_items.append(ItineraryItem(
                            start_time=travel_start,
                            end_time=travel_end,
                            type="travel",
                            details={
                                "distance_km": round(dist, 2),
                                "duration_min": duration,
                                "mode": "walk" if dist <= 1.5 else "transit",
                                "conflict": "Nincs elég utazási idő a két program között!"
                            }
                        ))
                    else:
                        # Minden rendben, beillesztjük az utazást
                        new_items.append(ItineraryItem(
                            start_time=travel_start,
                            end_time=travel_end,
                            type="travel",
                            details={"distance_km": round(dist, 2), "duration_min": duration, "mode": "walk" if dist <= 1.5 else "transit"}
                        ))
            else:
                # Nincs POI koordinátánk, csak beillesztünk egy alapértelmezett utazást
                new_items.append(ItineraryItem(
                    start_time=prev_item.end_time,
                    end_time=updated_item.start_time,
                    type="travel",
                    details={"distance_km": 0.0, "duration_min": 15, "mode": "transit"}
                ))
                
        new_items.append(updated_item)
        current_time = updated_item.end_time
        
    return ItineraryDay(date=day_data.date, items=new_items)
