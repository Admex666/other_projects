"""
Optivoya Shared Intelligence — Experience Intelligence Service
POI extraction, 12D destination vibe profiling, schedule validation, and personalized activity curation.
"""

from typing import List, Dict, Any, Optional, Union
import os
import json
from app.services import maps_service
from app.services.geo_experience_layer import (
    DIMENSIONS_12,
    DIMENSION_ALIASES,
    normalize_preference_vector,
    extract_destination_vector,
    calculate_cosine_similarity,
    calculate_experience_fit_12d,
    calculate_activity_fit_score,
    is_poi_open_at_time,
    get_closed_days_of_week,
    validate_activity_time_slot,
    calculate_haversine_distance_km,
    estimate_transit_time_minutes,
    estimate_airport_to_hotel_transit,
    analyze_hotel_poi_clustering,
    calculate_normalized_location_score,
)


class ExperienceIntelligenceService:
    """
    Unified experience service managing POI graphs, 12-dimensional destination vibe profiles,
    opening hours validation, location scoring, and curated activity suggestions for both B2C and B2B workflows.
    """

    # Legacy Vibe and category profiles for destinations (kept for backwards compatibility)
    VIBE_PROFILES = {
        "barcelona": {"culture": 92, "beach": 85, "gastronomy": 95, "nightlife": 90, "nature": 70},
        "rome": {"culture": 98, "beach": 60, "gastronomy": 96, "nightlife": 80, "nature": 65},
        "róma": {"culture": 98, "beach": 60, "gastronomy": 96, "nightlife": 80, "nature": 65},
        "paris": {"culture": 98, "beach": 20, "gastronomy": 98, "nightlife": 88, "nature": 60},
        "párizs": {"culture": 98, "beach": 20, "gastronomy": 98, "nightlife": 88, "nature": 60},
        "santorini": {"culture": 75, "beach": 92, "gastronomy": 90, "nightlife": 82, "nature": 88},
        "szantorini": {"culture": 75, "beach": 92, "gastronomy": 90, "nightlife": 82, "nature": 88},
        "bali": {"culture": 90, "beach": 94, "gastronomy": 85, "nightlife": 85, "nature": 98},
        "funchal": {"culture": 78, "beach": 75, "gastronomy": 88, "nightlife": 65, "nature": 96},
        "madeira": {"culture": 78, "beach": 75, "gastronomy": 88, "nightlife": 65, "nature": 96},
        "vienna": {"culture": 96, "beach": 30, "gastronomy": 90, "nightlife": 75, "nature": 75},
        "bécs": {"culture": 96, "beach": 30, "gastronomy": 90, "nightlife": 75, "nature": 75},
        "lisbon": {"culture": 90, "beach": 82, "gastronomy": 92, "nightlife": 88, "nature": 80},
        "lisszabon": {"culture": 90, "beach": 82, "gastronomy": 92, "nightlife": 88, "nature": 80},
        "dubai": {"culture": 70, "beach": 88, "gastronomy": 94, "nightlife": 92, "nature": 65},
        "dubaj": {"culture": 70, "beach": 88, "gastronomy": 94, "nightlife": 92, "nature": 65},
        "prague": {"culture": 94, "beach": 20, "gastronomy": 88, "nightlife": 90, "nature": 70},
        "prága": {"culture": 94, "beach": 20, "gastronomy": 88, "nightlife": 90, "nature": 70},
        "amsterdam": {"culture": 92, "beach": 40, "gastronomy": 88, "nightlife": 94, "nature": 78},
        "amszterdam": {"culture": 92, "beach": 40, "gastronomy": 88, "nightlife": 94, "nature": 78},
        "tokyo": {"culture": 96, "beach": 35, "gastronomy": 99, "nightlife": 92, "nature": 82},
        "tokió": {"culture": 96, "beach": 35, "gastronomy": 99, "nightlife": 92, "nature": 82},
        "reykjavik": {"culture": 78, "beach": 40, "gastronomy": 82, "nightlife": 80, "nature": 99},
        "reykjavík": {"culture": 78, "beach": 40, "gastronomy": 82, "nightlife": 80, "nature": 99}
    }

    @classmethod
    def get_destination_vibe(cls, city_name: str) -> Dict[str, int]:
        """Returns vibe profile for a destination with sensible defaults."""
        clean = city_name.lower().strip()
        return cls.VIBE_PROFILES.get(clean, {
            "culture": 80, "beach": 60, "gastronomy": 80, "nightlife": 70, "nature": 75
        })

    @classmethod
    def get_destination_profile_12d(cls, destination_id_or_name: str) -> Dict[str, Any]:
        """
        Fetches the full 12-dimensional destination profile from ExperienceCache / VibeEngine
        or generates one from known vibe tables.
        """
        clean_id = destination_id_or_name.upper().strip()
        try:
            from app.services.experience.cache import experience_cache
            profile = experience_cache.get_destination_profile(clean_id)
            if profile:
                return profile
            # Try with IT_ / ES_ prefix or city name
            if "_" not in clean_id:
                for prefix in ["IT_", "ES_", "FR_", "GR_", "PT_", "HU_", "CZ_", "AT_"]:
                    profile = experience_cache.get_destination_profile(f"{prefix}{clean_id}")
                    if profile:
                        return profile
        except Exception:
            pass

        # Fallback profile based on VIBE_PROFILES
        legacy_vibe = cls.get_destination_vibe(destination_id_or_name)
        return {
            "destination_id": clean_id,
            "city_name": destination_id_or_name,
            "experience_vector": {
                "dimensions": {
                    "culture": {"absolute": float(legacy_vibe.get("culture", 80))},
                    "food": {"absolute": float(legacy_vibe.get("gastronomy", 80))},
                    "beach": {"absolute": float(legacy_vibe.get("beach", 50))},
                    "nature": {"absolute": float(legacy_vibe.get("nature", 70))},
                    "nightlife": {"absolute": float(legacy_vibe.get("nightlife", 70))},
                    "romance": {"absolute": 75.0},
                    "authenticity": {"absolute": 70.0},
                    "locality": {"absolute": 75.0},
                    "walkability": {"absolute": 80.0},
                    "tourist_intensity": {"absolute": 60.0},
                    "adventure": {"absolute": 50.0},
                    "family": {"absolute": 65.0},
                }
            }
        }

    @classmethod
    def calculate_experience_fit(
        cls,
        user_preferences: Union[Dict[str, float], Any, List[str]],
        destination_id_or_profile: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Computes 12-dimensional cosine similarity and fit metrics between client vibe preferences
        and a target destination.
        """
        if isinstance(destination_id_or_profile, str):
            dest_profile = cls.get_destination_profile_12d(destination_id_or_profile)
        else:
            dest_profile = destination_id_or_profile

        return calculate_experience_fit_12d(user_preferences, dest_profile)

    @classmethod
    def validate_poi_schedule(
        cls,
        poi_or_hours: Union[Dict[str, Any], Any],
        date_str: str,
        start_time: str,
        duration_minutes: int = 90
    ) -> Dict[str, Any]:
        """
        Validates whether a POI is open on the requested date and time slot.
        Detects recurring closures (e.g. closed on Mondays) and conflict warnings.
        """
        return validate_activity_time_slot(poi_or_hours, date_str, start_time, duration_minutes)

    @classmethod
    def calculate_location_score(
        cls,
        hotel_lat: float,
        hotel_lon: float,
        city_lat: float,
        city_lon: float,
        city_name: str = "",
        city_id: str = "",
        pois: Optional[List[Any]] = None,
        airport_lat: Optional[float] = None,
        airport_lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes the normalized LocationScore (0.0 - 10.0) combining:
        - Hotel-to-POI proximity & clustering density
        - City center centrality
        - Airport-to-hotel transit time
        """
        if pois is None:
            c_name = city_name or "Város"
            c_id = city_id or c_name.lower().replace(" ", "_")
            pois = maps_service.get_city_pois(c_name, c_id, city_lat, city_lon)

        return calculate_normalized_location_score(
            hotel_lat=hotel_lat,
            hotel_lon=hotel_lon,
            city_lat=city_lat,
            city_lon=city_lon,
            pois=pois,
            airport_lat=airport_lat,
            airport_lon=airport_lon
        )

    @classmethod
    def get_curated_activities(
        cls,
        city_name: str,
        country: str = "",
        duration_days: int = 7,
        travel_style: Optional[List[str]] = None,
        user_preferences: Optional[Union[Dict[str, float], Any]] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves curated POIs and experiences for the destination, scored and ranked
        by personalized preference fit.
        """
        try:
            city_clean = city_name.strip()
            city_id = city_clean.lower().replace(" ", "_")
            raw_lat = lat if lat is not None else 41.38
            raw_lng = lng if lng is not None else 2.17

            raw_pois = maps_service.get_city_pois(
                city_name=city_clean,
                city_id=city_id,
                lat=raw_lat,
                lng=raw_lng
            )
            pois = []
            for p in (raw_pois or []):
                p_name = p.name if hasattr(p, "name") else p.get("name", "Látványosság")
                p_cat = getattr(p, "type", None) or (p.get("type") if isinstance(p, dict) else "culture")
                p_rating = float(getattr(p, "rating", 4.5) if hasattr(p, "rating") else p.get("rating", 4.5))
                p_reviews = int(getattr(p, "user_ratings_total", 350) if hasattr(p, "user_ratings_total") else p.get("user_ratings_total", 350))
                p_price = getattr(p, "price_level", 1) if hasattr(p, "price_level") else p.get("price_level", 1)
                p_hours = getattr(p, "opening_hours", None) if hasattr(p, "opening_hours") else p.get("opening_hours")
                
                loc = getattr(p, "location", None) if hasattr(p, "location") else p.get("location")
                if isinstance(loc, dict):
                    p_lat, p_lon = float(loc.get("lat") or raw_lat), float(loc.get("lng") or loc.get("lon") or raw_lng)
                elif hasattr(loc, "lat") and hasattr(loc, "lng"):
                    p_lat, p_lon = float(loc.lat), float(loc.lng)
                else:
                    p_lat, p_lon = raw_lat, raw_lng

                p_img = getattr(p, "image_url", None) if hasattr(p, "image_url") else p.get("image_url")
                if not p_img:
                    p_img = "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=400&q=80"

                closed_days = get_closed_days_of_week(p_hours)
                closed_days_hu = [cd["day_hu"] for cd in closed_days]

                item = {
                    "id": getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else f"{city_id}_{abs(hash(p_name))}"),
                    "name": p_name,
                    "category": p_cat,
                    "rating": p_rating,
                    "review_count": p_reviews,
                    "price_level": p_price,
                    "duration_h": 2.5 if p_cat in ["attraction", "culture"] else (1.5 if p_cat == "cafe" else 2.0),
                    "estimated_cost_eur": 15 if p_cat in ["attraction", "culture"] else (25 if p_cat == "restaurant" else 0),
                    "lat": p_lat,
                    "lon": p_lon,
                    "image_url": p_img,
                    "opening_hours": p_hours,
                    "closed_days": closed_days_hu,
                    "schedule_note": f"Zárva: {', '.join(closed_days_hu)}" if closed_days_hu else "Minden nap nyitva",
                }

                # Calculate preference fit if user preferences provided
                if user_preferences or travel_style:
                    prefs = user_preferences or travel_style
                    fit = calculate_activity_fit_score(item, prefs)
                    item["fit_score"] = fit
                else:
                    item["fit_score"] = round(p_rating / 5.0, 2)

                pois.append(item)

            if pois:
                # Sort by fit_score descending then rating
                pois.sort(key=lambda x: (x.get("fit_score", 0.0) * 1.5 + (x["rating"] / 5.0)), reverse=True)
                return pois[:max(4, duration_days * 2)]
        except Exception:
            pass

        # Fallback curated list
        return [
            {
                "name": f"{city_name} Főtere és Történelmi Központ",
                "category": "culture",
                "rating": 4.8,
                "duration_h": 3.0,
                "estimated_cost_eur": 0,
                "closed_days": [],
                "schedule_note": "Minden nap nyitva",
                "fit_score": 0.95
            },
            {
                "name": "Helyi Gasztro Piac & Kóstoló",
                "category": "gastronomy",
                "rating": 4.7,
                "duration_h": 2.5,
                "estimated_cost_eur": 25,
                "closed_days": ["Vasárnap"],
                "schedule_note": "Zárva: Vasárnap",
                "fit_score": 0.90
            },
            {
                "name": "Panoráma Kilátó & Sétaútvonal",
                "category": "nature",
                "rating": 4.6,
                "duration_h": 2.0,
                "estimated_cost_eur": 5,
                "closed_days": [],
                "schedule_note": "Minden nap nyitva",
                "fit_score": 0.85
            },
            {
                "name": "Művészeti és Nemzeti Múzeum",
                "category": "culture",
                "rating": 4.7,
                "duration_h": 3.0,
                "estimated_cost_eur": 18,
                "closed_days": ["Hétfő"],
                "schedule_note": "Zárva: Hétfő",
                "fit_score": 0.88
            }
        ][:max(4, duration_days * 2)]
