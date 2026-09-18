"""
Optivoya Shared Intelligence — Experience Intelligence Service
POI extraction, destination vibe profiling, and personalized activity curation.
"""

from typing import List, Dict, Any, Optional
import os
import json
from app.services import maps_service


class ExperienceIntelligenceService:
    """
    Unified experience service managing POI graphs, destination vibe profiles,
    and curated activity suggestions for both B2C and B2B workflows.
    """

    # Vibe and category profiles for destinations
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
    def get_curated_activities(
        cls,
        city_name: str,
        country: str = "",
        duration_days: int = 7,
        travel_style: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves curated POIs and experiences for the destination.
        """
        try:
            city_clean = city_name.strip()
            raw_pois = maps_service.get_city_pois(
                city_name=city_clean,
                city_id=city_clean.lower().replace(" ", "_"),
                lat=41.38,
                lng=2.17
            )
            pois = []
            for p in (raw_pois or []):
                if hasattr(p, "name"):
                    pois.append({
                        "name": p.name,
                        "category": getattr(p, "type", "culture"),
                        "rating": float(getattr(p, "rating", 4.5)),
                        "duration_h": 2.5,
                        "estimated_cost_eur": 15
                    })
                elif isinstance(p, dict):
                    pois.append({
                        "name": p.get("name", "Látványosság"),
                        "category": p.get("type") or p.get("category", "culture"),
                        "rating": float(p.get("rating", 4.5)),
                        "duration_h": 2.5,
                        "estimated_cost_eur": 15
                    })
            if pois:
                return pois[:max(4, duration_days * 2)]
        except Exception:
            pass

        # Fallback curated list
        return [
            {"name": f"{city_name} Főtere és Történelmi Központ", "category": "culture", "rating": 4.8, "duration_h": 3.0, "estimated_cost_eur": 0},
            {"name": "Helyi Gasztro Piac & Kóstoló", "category": "gastronomy", "rating": 4.7, "duration_h": 2.5, "estimated_cost_eur": 25},
            {"name": "Panoráma Kilátó & Sétaútvonal", "category": "nature", "rating": 4.6, "duration_h": 2.0, "estimated_cost_eur": 5},
            {"name": "Művészeti és Nemzeti Múzeum", "category": "culture", "rating": 4.7, "duration_h": 3.0, "estimated_cost_eur": 18}
        ][:max(4, duration_days * 2)]

