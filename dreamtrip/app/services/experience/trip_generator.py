"""
Complete Trip & Daily Itinerary Generator for Optivoya.
Uses resolved canonical experience entities, their walkability graph, optimal time slots,
and duration modeling to generate cohesive, realistic multi-day travel plans without crisscrossing the city.
"""
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta

from .cache import experience_cache

class ExperienceTripGenerator:
    def generate_recommended_experiences(
        self,
        destination_id: str,
        experience_preferences: Optional[Dict[str, float]] = None,
        persona: Optional[str] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        'Ezeket ajánljuk nektek' személyre szabott élményajánló modul.
        Minden entitáshoz illeszkedési pontszámot (fit_score) és magyar nyelvű indoklást generál.
        """
        dest_upper = destination_id.upper()
        entities = experience_cache.get_destination_entities(dest_upper)
        if not entities and "bari" in destination_id.lower():
            entities = experience_cache.get_destination_entities("IT_BARI")

        if not entities:
            return []

        prefs = experience_preferences or {}
        top_cats = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
        top_pref_name = top_cats[0][0] if top_cats and top_cats[0][1] >= 60 else None

        results = []
        for e in entities:
            item = dict(e)
            cat = item.get("category", "")
            tier = item.get("metadata", {}).get("quality_tier", "supplemental")
            rating = item.get("rating") or 4.5
            
            fit = 70.0
            reasons = []

            # Preferencia illeszkedés
            if top_pref_name:
                if top_pref_name in ("gastronomy", "food") and ("food" in cat or "market" in cat):
                    fit += 20.0
                    reasons.append("Kiemelt gasztronómiai prioritásod alapján")
                elif top_pref_name in ("culture", "sightseeing") and ("culture" in cat or "history" in cat):
                    fit += 20.0
                    reasons.append("Kulturális fókuszodhoz illeszkedve")
                elif top_pref_name in ("nature",) and ("nature" in cat or "viewpoint" in cat):
                    fit += 20.0
                    reasons.append("Természet- és panoráma-preferenciád alapján")
                elif top_pref_name in ("beach",) and "beach" in cat:
                    fit += 20.0
                    reasons.append("Tengerparti és strandolási vágyaidhoz igazítva")
                elif top_pref_name in ("relaxation",) and ("wellness" in cat or "park" in cat):
                    fit += 20.0
                    reasons.append("Pihentető és feltöltő élmény jellege miatt")

            if tier == "flagship":
                fit += 10.0
                reasons.append("A város kihagyhatatlan ikonikus helyszíne")
            elif rating >= 4.7:
                fit += 6.0
                reasons.append(f"Kiemelkedő {rating}★ látogatói értékelés")

            item["fit_score"] = round(min(99.0, fit), 1)
            item["recommendation_reason"] = " • ".join(reasons) if reasons else "Népszerű helyi élmény"
            results.append(item)

        results.sort(key=lambda x: x["fit_score"], reverse=True)
        return results[:limit]

    def generate_trip_itinerary(
        self,
        destination_id: str,
        num_days: int = 3,
        start_date_str: Optional[str] = None,
        persona: Optional[str] = None,
        selected_activity_ids: Optional[List[str]] = None,
        experience_preferences: Optional[Dict[str, float]] = None,
        logistics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generates a complete multi-day itinerary powered by real experience entities and logistics budget."""
        dest_upper = destination_id.upper()
        entities = experience_cache.get_destination_entities(dest_upper)
        profile = experience_cache.get_destination_profile(dest_upper)

        if not entities and "bari" in destination_id.lower():
            entities = experience_cache.get_destination_entities("IT_BARI")
            profile = experience_cache.get_destination_profile("IT_BARI")

        if not entities:
            # Fallback if no entities loaded
            return {
                "destination_id": dest_upper,
                "days": [],
                "itinerary_days": [],
                "total_days": num_days,
                "message": "No experience entities available for this destination."
            }

        # Multi-factor prioritization: Selected by user -> Experience pref -> Persona -> Tier -> Rating
        selected_set = set(selected_activity_ids) if selected_activity_ids else set()
        tier_weights = {"flagship": 3, "recommended": 2, "supplemental": 1}

        def entity_score(e):
            is_selected = 10 if e.get("entity_id") in selected_set else 0
            exp_match = 0.0
            if experience_preferences:
                cat = e.get("category", "")
                if "food" in cat or "market" in cat:
                    exp_match = experience_preferences.get("gastronomy", 50.0) / 20.0
                elif "culture" in cat or "history" in cat:
                    exp_match = experience_preferences.get("culture", 50.0) / 20.0
                elif "beach" in cat or "coastal" in cat:
                    exp_match = experience_preferences.get("beach", 50.0) / 20.0
                elif "nature" in cat or "viewpoint" in cat:
                    exp_match = experience_preferences.get("nature", 50.0) / 20.0
                elif "nightlife" in cat:
                    exp_match = experience_preferences.get("nightlife", 50.0) / 20.0

            persona_match = 2 if (persona and persona in e.get("metadata", {}).get("persona_tags", [])) else 0
            tier_val = tier_weights.get(e.get("metadata", {}).get("quality_tier", "supplemental"), 1)
            rating = e.get("rating") or 0.0
            reviews = e.get("review_count") or 0
            return (is_selected, exp_match, persona_match, tier_val, rating, reviews)

        sorted_entities = sorted(entities, key=entity_score, reverse=True)

        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.now() + timedelta(days=14)
        logistics_cfg = logistics or {}
        day_start = logistics_cfg.get("day_start_time", "09:30")
        lunch_start = logistics_cfg.get("lunch_window_start", "12:30")
        lunch_end = logistics_cfg.get("lunch_window_end", "14:00")
        dinner_start = logistics_cfg.get("dinner_window_start", "19:00")
        day_end = logistics_cfg.get("day_end_time", "21:00")
        max_walk_mins = int(logistics_cfg.get("max_walking_minutes", 25))
        max_walk_m = max_walk_mins * 80  # ~80m/min kényelmes gyaloglási tempó

        visited_ids: Set[str] = set()
        days_itinerary = []

        for day_num in range(1, num_days + 1):
            day_date = start_dt + timedelta(days=day_num - 1)
            date_formatted = day_date.strftime("%Y-%m-%d")
            weekday_name = day_date.strftime("%A")

            slots = []

            # 1. Délelőtti idősáv: Kulturális vagy gasztró fókusz
            morning_item = self._pick_slot_item(
                sorted_entities,
                visited_ids,
                preferred_slots=["morning", "anytime"],
                preferred_categories=["culture_history", "food_market"]
            )
            if morning_item:
                visited_ids.add(morning_item["entity_id"])
                slots.append({
                    "slot": "morning",
                    "time_window": f"{day_start} - {lunch_start}",
                    "title": morning_item["canonical_name"],
                    "entity_id": morning_item["entity_id"],
                    "category": morning_item["category"],
                    "subcategory": morning_item.get("subcategory"),
                    "rating": morning_item.get("rating"),
                    "review_count": morning_item.get("review_count"),
                    "duration_hours": morning_item.get("est_duration_hours", 1.5),
                    "price_level": morning_item.get("price_level", "free"),
                    "image_url": morning_item.get("image_urls", [None])[0] if morning_item.get("image_urls") else None,
                    "description": morning_item.get("description"),
                    "lat": morning_item.get("lat"),
                    "lon": morning_item.get("lon"),
                    "weather_resilience": morning_item.get("metadata", {}).get("weather_sensitivity", "all_weather")
                })

            # 2. Ebédszünet
            slots.append({
                "slot": "lunch",
                "time_window": f"{lunch_start} - {lunch_end}",
                "title": "Helyi gasztronómiai szünet & Kávé",
                "type": "meal",
                "note": "Közeli trattoria / pékség autentikus focacciával vagy tengeri fogásokkal."
            })

            # 3. Délutáni idősáv: Gyalogosan elérhető szomszéd vagy kiemelt látványosság
            afternoon_item = None
            if morning_item:
                nearby_list = morning_item.get("metadata", {}).get("nearby_walkable_entities", [])
                for n in nearby_list:
                    n_id = n.get("entity_id")
                    if n_id and n_id not in visited_ids:
                        candidate = next((e for e in sorted_entities if e["entity_id"] == n_id), None)
                        if candidate:
                            afternoon_item = candidate
                            break

            if not afternoon_item:
                afternoon_item = self._pick_slot_item(
                    sorted_entities,
                    visited_ids,
                    preferred_slots=["afternoon", "anytime"],
                    preferred_categories=["culture_history", "active_adventure"]
                )

            if afternoon_item:
                visited_ids.add(afternoon_item["entity_id"])
                walk_distance_m = None
                transit_rec = None
                if morning_item and morning_item.get("lat") and afternoon_item.get("lat"):
                    from .enrichment import haversine_km
                    walk_distance_m = int(haversine_km(
                        morning_item["lat"], morning_item["lon"],
                        afternoon_item["lat"], afternoon_item["lon"]
                    ) * 1000)
                    if walk_distance_m > max_walk_m:
                        transit_rec = f"Tömegközlekedés vagy taxi javasolt (~{walk_distance_m}m távolság)"

                slots.append({
                    "slot": "afternoon",
                    "time_window": f"{lunch_end} - {dinner_start}",
                    "title": afternoon_item["canonical_name"],
                    "entity_id": afternoon_item["entity_id"],
                    "category": afternoon_item["category"],
                    "subcategory": afternoon_item.get("subcategory"),
                    "rating": afternoon_item.get("rating"),
                    "review_count": afternoon_item.get("review_count"),
                    "duration_hours": afternoon_item.get("est_duration_hours", 2.0),
                    "price_level": afternoon_item.get("price_level", "budget"),
                    "walk_from_previous_m": walk_distance_m,
                    "transit_recommendation": transit_rec,
                    "image_url": afternoon_item.get("image_urls", [None])[0] if afternoon_item.get("image_urls") else None,
                    "description": afternoon_item.get("description"),
                    "lat": afternoon_item.get("lat"),
                    "lon": afternoon_item.get("lon")
                })

            # 4. Naplemente & Esti idősáv
            sunset_item = self._pick_slot_item(
                sorted_entities,
                visited_ids,
                preferred_slots=["sunset", "evening"],
                preferred_categories=["nature_viewpoint", "beach_coastal", "culture_history"]
            )
            if sunset_item:
                visited_ids.add(sunset_item["entity_id"])
                slots.append({
                    "slot": "sunset_evening",
                    "time_window": f"{dinner_start} - {day_end}",
                    "title": sunset_item["canonical_name"],
                    "entity_id": sunset_item["entity_id"],
                    "category": sunset_item["category"],
                    "subcategory": sunset_item.get("subcategory"),
                    "rating": sunset_item.get("rating"),
                    "duration_hours": sunset_item.get("est_duration_hours", 1.0),
                    "price_level": "free",
                    "image_url": sunset_item.get("image_urls", [None])[0] if sunset_item.get("image_urls") else None,
                    "description": sunset_item.get("description"),
                    "lat": sunset_item.get("lat"),
                    "lon": sunset_item.get("lon")
                })

            days_itinerary.append({
                "day_number": day_num,
                "date": date_formatted,
                "weekday": weekday_name,
                "theme": f"Nap {day_num}: {morning_item['canonical_name'] if morning_item else 'Városfelfedezés'}",
                "slots": slots
            })

        return {
            "destination_id": dest_upper,
            "city_name": profile.get("city_name", dest_upper) if profile else dest_upper,
            "total_days": num_days,
            "days": days_itinerary,
            "itinerary_days": days_itinerary,
            "total_activities_scheduled": len(visited_ids)
        }

    def _pick_slot_item(
        self,
        entities: List[Dict[str, Any]],
        visited_ids: Set[str],
        preferred_slots: List[str],
        preferred_categories: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Selects the highest quality unvisited place fitting the target slot and categories."""
        # 1st try: matches preferred slot AND preferred category
        for e in entities:
            e_id = e.get("entity_id")
            if e_id not in visited_ids:
                if e.get("best_time_of_day") in preferred_slots and e.get("category") in preferred_categories:
                    return e

        # 2nd try: matches preferred category
        for e in entities:
            e_id = e.get("entity_id")
            if e_id not in visited_ids:
                if e.get("category") in preferred_categories:
                    return e

        # 3rd try: any high quality unvisited entity
        for e in entities:
            e_id = e.get("entity_id")
            if e_id not in visited_ids:
                return e

        return None

# Global generator instance
trip_generator = ExperienceTripGenerator()
