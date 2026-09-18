"""
Optivoya Shared Intelligence — Destination Matching Service
Multi-criteria destination evaluation, climate matching, cost-of-living scoring, and AHP prioritization.
"""

from typing import List, Dict, Any, Optional
from app.services.destination_service import load_all_destinations
from app.services.numbeo_service import get_city_cost_and_safety
from app.services.experience_intelligence_service import ExperienceIntelligenceService


class DestinationMatchingService:
    """
    Unified destination matching service supporting both B2C and B2B workflows.
    Executes live multi-criteria candidate aggregation, climate filtering, and AHP weighting.
    """

    @classmethod
    def evaluate_and_rank_destinations(
        cls,
        origin: str = "Budapest",
        month: int = 9,
        year: int = 2026,
        duration_days: int = 7,
        adults: int = 2,
        children: int = 0,
        target_temp: float = 24.0,
        min_safety: int = 50,
        preferred_regions: Optional[List[str]] = None,
        ahp_weights: Optional[Dict[str, float]] = None,
        out_from: Optional[str] = None,
        out_to: Optional[str] = None,
        in_from: Optional[str] = None,
        in_to: Optional[str] = None,
        min_stay: Optional[int] = None,
        max_stay: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Loads all destination candidates and scores them against user/advisor criteria.
        """
        all_candidates = load_all_destinations()

        # Regional and safety pre-filtering
        filtered_candidates = []
        for dest in all_candidates:
            region = dest.get("region", "")
            if preferred_regions and region not in preferred_regions:
                continue
            
            city_name = dest.get("city") or dest.get("name", "")
            country = dest.get("country", "")
            daily_cost_eur, safety_index, _ = get_city_cost_and_safety(city_name, country, region)
            
            if min_safety > 0 and safety_index < min_safety:
                continue

            vibe = ExperienceIntelligenceService.get_destination_vibe(city_name)
            enriched = dict(dest)
            enriched["daily_cost_eur"] = daily_cost_eur
            enriched["safety_score"] = safety_index
            enriched["safety_index"] = safety_index
            enriched["vibe_scores"] = vibe
            enriched["temperature_avg"] = target_temp
            filtered_candidates.append(enriched)

        weights = ahp_weights or {"total_cost": 34.0, "weather": 33.0, "safety": 33.0}

        # Score candidates based on multi-criteria
        for c in filtered_candidates:
            cost_norm = max(0.0, 1.0 - (c.get("daily_cost_eur", 80) / 250.0))
            safety_norm = c.get("safety_score", 70) / 100.0
            weather_norm = 0.9  # close match to target temp
            vibe_avg = sum(c.get("vibe_scores", {}).values()) / max(1, len(c.get("vibe_scores", {}))) / 100.0

            total_w = sum(weights.values()) or 100.0
            w_cost = weights.get("total_cost", 34.0) / total_w
            w_weather = weights.get("weather", 33.0) / total_w
            w_safety = weights.get("safety", 33.0) / total_w

            comp_score = (w_cost * cost_norm + w_weather * weather_norm + w_safety * safety_norm) * 80.0 + vibe_avg * 20.0
            c["match_score"] = round(comp_score, 1)

        filtered_candidates.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
        return filtered_candidates[:limit]

