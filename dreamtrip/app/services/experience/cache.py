"""
Ultra-Fast Experience & Profile Cache System for Optivoya.
Provides multi-tier caching:
- Tier 1: In-Memory L1 Cache (<1ms lookup for request-time Destination Matcher)
- Tier 2: Supabase Cloud Database (public.destination_experience_profiles & public.experience_entities)
- Tier 3: Local Disk Persistent Cache (data/experience_profiles/{destination_id}.json)
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "experience_profiles"))

class ExperienceMemoryCache:
    _instance = None
    _l1_profiles: Dict[str, Dict[str, Any]] = {}
    _l1_entities: Dict[str, List[Dict[str, Any]]] = {}
    _last_fetched: Dict[str, float] = {}
    TTL_SECONDS = 3600  # 1 hour in-memory TTL

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExperienceMemoryCache, cls).__new__(cls)
            os.makedirs(CACHE_DIR, exist_ok=True)
            cls._instance._warm_up_from_disk()
        return cls._instance

    def _warm_up_from_disk(self):
        """Loads cached profiles from disk into memory on initialization for zero-latency startup."""
        if not os.path.exists(CACHE_DIR):
            return
        try:
            for fname in os.listdir(CACHE_DIR):
                if fname.endswith(".json"):
                    dest_id = fname[:-5].upper()
                    fpath = os.path.join(CACHE_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._l1_profiles[dest_id] = data
                        self._last_fetched[dest_id] = time.time()
        except Exception as e:
            print(f"[CACHE WARN] Warm-up from disk failed: {e}")

    def get_destination_profile(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """Ultra-fast lookup of a destination's experience profile (<1ms if in L1)."""
        dest_upper = destination_id.upper()

        # 1. Check L1 Memory Cache
        now = time.time()
        if dest_upper in self._l1_profiles:
            if (now - self._last_fetched.get(dest_upper, 0)) < self.TTL_SECONDS:
                return self._l1_profiles[dest_upper]

        # 2. Check Supabase
        try:
            from app.core.supabase import get_supabase, is_supabase_configured
            if is_supabase_configured():
                sb = get_supabase()
                if sb:
                    res = sb.table("destination_experience_profiles").select("*").eq("destination_id", dest_upper).limit(1).execute()
                    if res.data and len(res.data) > 0:
                        profile = res.data[0]
                        self._save_to_l1_and_disk(dest_upper, profile)
                        return profile
        except Exception as e:
            print(f"[CACHE WARN] Supabase profile fetch failed: {e}")

        # 3. Check Disk Cache
        disk_path = os.path.join(CACHE_DIR, f"{dest_upper}.json")
        if os.path.exists(disk_path):
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                    self._l1_profiles[dest_upper] = profile
                    self._last_fetched[dest_upper] = now
                    return profile
            except Exception:
                pass

        # 4. Fallback: Auto-generate from destination entities if available
        entities = self.get_destination_entities(dest_upper)
        if entities:
            try:
                from .vibe_engine import get_vibe_engine
                engine = get_vibe_engine()
                # Find city name from destinations.json
                city_name = dest_upper
                country = "Európa"
                dests_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "destinations.json"))
                if os.path.exists(dests_path):
                    with open(dests_path, "r", encoding="utf-8") as f:
                        all_dests = json.load(f)
                        matched = next((d for d in all_dests if d.get("id", "").upper() == dest_upper or d.get("name", "").upper() in dest_upper), None)
                        if matched:
                            city_name = matched.get("name", dest_upper)
                            country = matched.get("country", "Európa")
                from .models import CanonicalExperienceEntity
                entity_objs = [e if isinstance(e, CanonicalExperienceEntity) else CanonicalExperienceEntity(**e) for e in entities]
                vector = engine.profile(entity_objs, dest_upper, city_name, country)
                profile = {
                    "destination_id": dest_upper,
                    "city_name": city_name,
                    "country": country,
                    "total_experiences": len(entities),
                    "experience_vector": vector.to_dict() if hasattr(vector, "to_dict") else vector.__dict__,
                    "top_experiences_summary": [
                        {"canonical_name": e.get("canonical_name"), "category": e.get("category"), "rating": e.get("rating")}
                        for e in entities[:5]
                    ]
                }
                self._save_to_l1_and_disk(dest_upper, profile)
                return profile
            except Exception as e:
                print(f"[CACHE WARN] Auto-generating profile failed: {e}")

        return None

    def get_destination_entities(self, destination_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves canonical experience entities with memory caching & robust POI fallback."""
        dest_upper = destination_id.upper()

        # 1. Check L1 memory
        if dest_upper in self._l1_entities:
            cached = self._l1_entities[dest_upper]
            if category:
                return [e for e in cached if e.get("category") == category]
            return cached

        # 2. Fetch from Supabase
        try:
            from app.core.supabase import get_supabase, is_supabase_configured
            if is_supabase_configured():
                sb = get_supabase()
                if sb:
                    res = sb.table("experience_entities").select("*").eq("destination_id", dest_upper).order("review_count", desc=True).execute()
                    if res.data and len(res.data) > 0:
                        self._l1_entities[dest_upper] = res.data
                        if category:
                            return [e for e in res.data if e.get("category") == category]
                        return res.data
        except Exception as e:
            print(f"[CACHE WARN] Supabase entities fetch failed: {e}")

        # 3. Fallback: Load from POI cache or maps_service for complete destination catalog support
        fallback_entities = self._load_fallback_entities(dest_upper)
        if fallback_entities:
            self._l1_entities[dest_upper] = fallback_entities
            if category:
                return [e for e in fallback_entities if e.get("category") == category]
            return fallback_entities

        return []

    def _load_fallback_entities(self, dest_upper: str) -> List[Dict[str, Any]]:
        """Adapts cached destination POIs into canonical experience entities."""
        dest_lower = dest_upper.lower()
        poi_cache_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "poi_cache.json"))
        pois = []

        if os.path.exists(poi_cache_path):
            try:
                with open(poi_cache_path, "r", encoding="utf-8") as f:
                    cache_dict = json.load(f)
                    # Try direct match, stripped match, or city name match
                    key = next((k for k in cache_dict.keys() if k.lower() == dest_lower or k.lower() in dest_lower or dest_lower in k.lower()), None)
                    if key and "pois" in cache_dict[key]:
                        pois = cache_dict[key]["pois"]
            except Exception as e:
                print(f"[CACHE WARN] Reading poi_cache failed: {e}")

        # If not found in poi_cache, try maps_service
        if not pois:
            try:
                from app.services.destination_service import load_all_destinations
                from app.services.maps_service import get_city_pois
                all_dests = load_all_destinations()
                matched = next((d for d in all_dests if d.get("id", "").upper() == dest_upper or d.get("name", "").upper() in dest_upper), None)
                if matched:
                    raw_pois = get_city_pois(matched["name"], matched["id"], matched["lat"], matched["lon"])
                    pois = [p.__dict__ if hasattr(p, "__dict__") else p for p in raw_pois]
            except Exception as e:
                print(f"[CACHE WARN] maps_service POI fallback failed: {e}")

        # Convert to Canonical Experience Entities
        entities = []
        for p in pois:
            p_id = p.get("id") or f"{dest_upper}_{abs(hash(p.get('name', '')))}"
            p_name = p.get("name") or "Élmény"
            p_type = p.get("type") or "attraction"
            p_rating = float(p.get("rating") or 4.5)
            p_reviews = int(p.get("user_ratings_total") or 350)
            p_price_lvl = p.get("price_level", 1)

            loc = p.get("location") or {}
            lat = loc.get("lat") if isinstance(loc, dict) else (getattr(loc, "lat", 0.0))
            lon = loc.get("lng") if isinstance(loc, dict) else (getattr(loc, "lng", 0.0))

            cat = "culture_history"
            if p_type in ["viewpoint", "nature", "park"]:
                cat = "nature_viewpoint"
            elif p_type in ["beach"]:
                cat = "beach_coastal"
            elif p_type in ["restaurant", "cafe", "food"]:
                cat = "food_market"

            price_str = "free" if p_price_lvl == 0 else ("budget" if p_price_lvl == 1 else ("moderate" if p_price_lvl == 2 else "premium"))
            tier = "flagship" if (p_reviews > 3000 or p_rating >= 4.8) else ("recommended" if p_rating >= 4.3 else "supplemental")

            img = p.get("image_url") or p.get("photo_url")
            img_list = [img] if img else []

            entities.append({
                "entity_id": p_id,
                "canonical_name": p_name,
                "destination_id": dest_upper,
                "category": cat,
                "subcategory": p_type,
                "rating": p_rating,
                "review_count": p_reviews,
                "lat": float(lat or 0.0),
                "lon": float(lon or 0.0),
                "image_urls": img_list,
                "price_level": price_str,
                "est_duration_hours": 2.0 if cat == "culture_history" else (1.5 if cat == "food_market" else 1.0),
                "description": p.get("address") or f"{p_name} — kihagyhatatlan látnivaló és program.",
                "best_time_of_day": "morning" if cat == "culture_history" else ("evening" if cat == "food_market" else "sunset"),
                "metadata": {
                    "quality_tier": tier,
                    "persona_tags": ["culture_aficionado"] if cat == "culture_history" else (["foodie_local"] if cat == "food_market" else ["couples_romantic", "solo_explorer"]),
                    "indoor_outdoor": "outdoor" if cat in ["nature_viewpoint", "beach_coastal"] else "indoor",
                    "weather_sensitivity": "fair_weather" if cat in ["nature_viewpoint", "beach_coastal"] else "all_weather"
                }
            })

        return entities

    def set_destination_profile(self, destination_id: str, profile_data: Dict[str, Any]):
        """Caches profile in L1 memory, Supabase and disk."""
        dest_upper = destination_id.upper()
        self._save_to_l1_and_disk(dest_upper, profile_data)

    def _save_to_l1_and_disk(self, destination_id: str, profile_data: Dict[str, Any]):
        """Helper to store in memory and write to disk."""
        self._l1_profiles[destination_id] = profile_data
        self._last_fetched[destination_id] = time.time()
        
        disk_path = os.path.join(CACHE_DIR, f"{destination_id}.json")
        try:
            with open(disk_path, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CACHE WARN] Failed to write disk cache for {destination_id}: {e}")

# Global singleton instance
experience_cache = ExperienceMemoryCache()
