"""
Optivoya Shared Intelligence — Itinerary Optimization Service
Day-by-day activity scheduling, walking logistics, and POI sequencing.
"""

from typing import List, Dict, Any, Optional
from app.services.itinerary_service import generate_optimized_itinerary, compute_itinerary_summary


class ItineraryOptimizationService:
    """
    Unified itinerary optimization service organizing activities into realistic daily plans.
    """

    @classmethod
    def generate_daily_itinerary(
        cls,
        destination_name: str,
        duration_days: int = 7,
        activities: Optional[List[Dict[str, Any]]] = None,
        hotel_location: Optional[Dict[str, float]] = None,
        pace: str = "moderate"
    ) -> List[Dict[str, Any]]:
        """
        Generates structured daily itinerary schedule for duration_days.
        """
        raw_schedule = generate_optimized_itinerary(
            city_name=destination_name,
            duration_days=duration_days,
            user_prefs={"pace": pace}
        )

        return raw_schedule
