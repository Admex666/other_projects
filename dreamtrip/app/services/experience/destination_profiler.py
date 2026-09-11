"""
Destination Experience Profiler for Optivoya Trip Decision Engine.
Aggregates resolved canonical entities into high-level vibe scores, category distributions,
top highlights, and a full multi-dimensional ExperienceVector for peer-group comparisons.

Pipeline:
  1. Simple legacy vibe_scores (1-10 scale, backwards-compatible)
  2. Full ExperienceVector via VibeEngine (12 dims, Bayesian-smoothed, 0-100)
  3. Persona suitability, persona tags, walkability
  4. Cache payload extended with experience_vector dict
"""
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime
import math

from .models import CanonicalExperienceEntity, DestinationExperienceProfile


class DestinationProfiler:
    def build_profile(
        self,
        destination_id: str,
        city_name: str,
        country: str,
        entities: List[CanonicalExperienceEntity],
        user_preferences: Dict[str, float] | None = None,
    ) -> DestinationExperienceProfile:
        total_count = len(entities)

        # --- Category distribution ---
        categories = Counter(e.category for e in entities)
        cat_dist = dict(categories)

        # --- Top experience ranking (quality × popularity) ---
        def score_entity(e: CanonicalExperienceEntity) -> float:
            base = (e.rating or 4.0) * 2.0
            review_bonus = math.log10(max(e.review_count, 1)) * 1.5
            conf_bonus = e.confidence_score * 2.0
            has_img_bonus = 1.0 if e.image_urls else 0.0
            return base + review_bonus + conf_bonus + has_img_bonus

        sorted_entities = sorted(entities, key=score_entity, reverse=True)
        top_highlights = []
        for e in sorted_entities[:10]:
            top_highlights.append({
                "entity_id": e.entity_id,
                "name": e.canonical_name,
                "category": e.category,
                "subcategory": e.subcategory,
                "rating": e.rating,
                "review_count": e.review_count,
                "image_url": e.image_urls[0] if e.image_urls else None,
                "lat": e.lat,
                "lon": e.lon,
                "description": e.description[:140] + "..." if e.description else None,
            })

        # --- Legacy vibe_scores (1-10, backwards-compatible) ---
        culture_count = cat_dist.get("culture_history", 0)
        nature_count = cat_dist.get("nature_viewpoint", 0)
        beach_count = cat_dist.get("beach_coastal", 0)
        food_count = cat_dist.get("food_market", 0)
        active_count = cat_dist.get("active_adventure", 0)

        # --- Persona & environment metadata ---
        persona_counts: Counter = Counter()
        rain_safe_count = 0
        walkable_places = 0
        for e in entities:
            for p in e.metadata.get("persona_tags", []):
                persona_counts[p] += 1
            if e.metadata.get("weather_sensitivity") == "rain_safe":
                rain_safe_count += 1
            if e.metadata.get("walkable_neighbors_count", 0) >= 2:
                walkable_places += 1

        persona_suitability = {
            "culture_aficionado": min(round((persona_counts["culture_aficionado"] / max(total_count * 0.4, 1)) * 100), 100),
            "solo_explorer":      min(round((persona_counts["solo_explorer"]      / max(total_count * 0.3, 1)) * 100), 100),
            "couples_romantic":   min(round((persona_counts["couples_romantic"]   / 5.0) * 100), 100),
            "family_friendly":    min(round((persona_counts["family_friendly"]    / 6.0) * 100), 100),
            "foodie_local":       min(round((persona_counts["foodie_local"]       / 5.0) * 100), 100),
            "beach_seeker":       min(round((persona_counts["beach_seeker"]       / 4.0) * 100), 100) if beach_count > 0 else 0,
        }

        walkability_score = (
            min(round((walkable_places / max(total_count * 0.15, 1)) * 10.0, 1), 10.0)
            if total_count > 0 else 5.0
        )

        vibe_scores = {
            "cultural_depth":     min(round(3.0 + (culture_count / 15.0) * 7.0, 1), 10.0),
            "nature_scenic":      min(round(3.0 + (nature_count  /  8.0) * 7.0, 1), 10.0),
            "beach_leisure":      min(round(2.0 + (beach_count   /  4.0) * 8.0, 1), 10.0) if beach_count > 0 else 1.0,
            "culinary_lifestyle": min(round(3.0 + (food_count    /  5.0) * 7.0, 1), 10.0),
            "active_exploration": min(round(3.0 + (active_count  /  4.0) * 7.0, 1), 10.0),
            "walkability":        walkability_score,
        }

        # ---------------------------------------------------------------
        # NEW: Full ExperienceVector via VibeEngine
        # ---------------------------------------------------------------
        experience_vector_dict: Dict[str, Any] = {}
        overall_confidence = 0.5
        try:
            from .vibe_engine import get_vibe_engine
            engine = get_vibe_engine()
            vector = engine.profile(
                entities=entities,
                destination_id=destination_id.upper(),
                city_name=city_name,
                country=country,
                freshness=1.0,
                user_preferences=user_preferences,
            )
            experience_vector_dict = vector.to_dict()
            overall_confidence = vector.data_confidence
        except Exception as exc:
            print(f"[PROFILER VIBE WARN] VibeEngine failed for {destination_id}: {exc}")

        # ---------------------------------------------------------------
        # Build profile dataclass (legacy fields kept for compatibility)
        # ---------------------------------------------------------------
        profile = DestinationExperienceProfile(
            destination_id=destination_id.upper(),
            city_name=city_name,
            country=country,
            total_activities_count=total_count,
            category_distribution=cat_dist,
            top_experiences_summary=top_highlights,
            vibe_scores=vibe_scores,
            confidence_level=overall_confidence,
            last_synced_at=datetime.utcnow().isoformat(),
        )

        # --- Update Ultra-Fast Cache ---
        try:
            from .cache import experience_cache
            profile_dict = profile.to_dict()
            profile_dict["persona_suitability"]  = persona_suitability
            profile_dict["rain_safe_count"]       = rain_safe_count
            profile_dict["walkability_score"]     = walkability_score
            profile_dict["experience_vector"]     = experience_vector_dict  # NEW
            experience_cache.set_destination_profile(destination_id, profile_dict)
        except Exception as exc:
            print(f"[PROFILER CACHE WARN] Failed to update cache: {exc}")

        return profile
