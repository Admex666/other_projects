"""
Optivoya Shared Intelligence — TripScore Service
Composite 4-pillar trip evaluation, effective vacation time calculation, and package harmony scoring.
"""

import math
from typing import Dict, Any, List, Optional


class TripScoreService:
    """
    Standardized TripScore calculation service evaluating holistic complete trip packages.
    Integrates Destination Fit, Flight Comfort & Timing, Accommodation Quality, and Experience Diversity.
    """

    @classmethod
    def calculate_experience_diversity(cls, activities: List[Dict[str, Any]]) -> float:
        """
        Calculates Shannon-entropy normalized activity diversity ratio (0.0 to 1.0).
        Higher diversity indicates a well-balanced experience mix (gastronomy + culture + nature + viewpoints).
        """
        if not activities:
            return 0.5

        cat_counts: Dict[str, int] = {}
        for a in activities:
            cat = a.get("category", "other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        total = len(activities)
        if total <= 1:
            return 0.7

        entropy = 0.0
        for count in cat_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        max_entropy = math.log2(min(max(len(cat_counts), 2), 5))
        if max_entropy <= 0:
            return 0.5

        diversity_ratio = min(1.0, entropy / max_entropy)
        return round(diversity_ratio, 3)

    @classmethod
    def calculate_effective_vacation_time(
        cls,
        out_arr_time: str,
        in_dep_time: str,
        duration_days: int = 7
    ) -> float:
        """
        Calculates usable daylight vacation hours based on flight arrival and departure times.
        """
        try:
            arr_hour = int(out_arr_time.split("T")[1].split(":")[0]) if "T" in out_arr_time else 14
            dep_hour = int(in_dep_time.split("T")[1].split(":")[0]) if "T" in in_dep_time else 12

            # First day daylight hours after 1.5h airport buffer
            first_day_hours = max(0.0, 20.0 - max(8.0, arr_hour + 1.5))
            # Last day daylight hours before 2.5h airport buffer
            last_day_hours = max(0.0, min(18.0, dep_hour - 2.5) - 8.0)
            # Full middle days (avg 10 active daylight hours per day)
            middle_days_hours = max(0, duration_days - 2) * 10.0

            return round(first_day_hours + last_day_hours + middle_days_hours, 1)
        except Exception:
            return round(duration_days * 8.5, 1)

    @classmethod
    def calculate_trip_score(
        cls,
        destination: Optional[Dict[str, Any]] = None,
        flight: Optional[Dict[str, Any]] = None,
        accommodation: Optional[Dict[str, Any]] = None,
        activities: Optional[List[Dict[str, Any]]] = None,
        experience_preferences: Optional[Dict[str, float]] = None,
        logistics_preferences: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates holistic 4-pillar TripScore (0-100).
        """
        w_dest = 0.25
        w_flight = 0.25
        w_stay = 0.25
        w_exp = 0.25

        if weights:
            w_total = sum(weights.values()) or 1.0
            w_dest = weights.get("destination", weights.get("dest", 25.0)) / w_total
            w_flight = weights.get("flight", 25.0) / w_total
            w_stay = weights.get("accommodation", weights.get("stay", 25.0)) / w_total
            w_exp = weights.get("experience", 25.0) / w_total

        # 1. Destination Fit (0 - 100)
        dest_score = float(destination.get("score", 75.0)) if destination else 75.0

        # 2. Flight Fit & Effective Vacation Time (0 - 100)
        flight_score = 75.0
        effective_hours = 16.0
        if flight:
            flight_score = float(flight.get("relevance_pct", 78.0) or 78.0)
            effective_hours = float(flight.get("effective_vacation_hours", 16.0) or 16.0)
            if effective_hours >= 20.0:
                flight_score = min(99.0, flight_score + 4.0)
            elif effective_hours <= 10.0:
                flight_score = max(40.0, flight_score - 6.0)

        # 3. Accommodation Fit & Location (0 - 100)
        stay_score = 75.0
        if accommodation:
            rating_10 = float(accommodation.get("rating_normalized", accommodation.get("rating", 8.0)) or 8.0)
            stay_score = min(99.0, rating_10 * 10.0)
            stars = int(accommodation.get("stars", 3) or 3)
            if stars >= 4:
                stay_score = min(99.0, stay_score + 3.0)

        # 4. Experience Fit & Diversity (0 - 100)
        exp_score = 75.0
        diversity = cls.calculate_experience_diversity(activities or [])
        if activities:
            ratings = [float(a.get("rating", 4.5)) for a in activities if a.get("rating")]
            avg_rating_5 = (sum(ratings) / len(ratings)) if ratings else 4.5
            exp_score = min(99.0, (avg_rating_5 / 5.0) * 85.0 + (diversity * 15.0))

        # Friction and Strengths
        friction_penalty = 0.0
        tradeoffs = []
        strengths = []

        if flight and (flight.get("out_stops", 0) > 0 or flight.get("in_stops", 0) > 0 or flight.get("stops", 0) > 0):
            friction_penalty += 5.0
            tradeoffs.append("Átszállásos repülőút miatti időveszteség")
        else:
            strengths.append("Kényelmes, közvetlen járat")

        if dest_score >= 85:
            strengths.append("Kiemelkedő célállomás- és klímailleszkedés")
        if stay_score >= 85:
            strengths.append("Kiváló minőségű és elhelyezkedésű szállás")

        # Composite score
        base_score = (
            w_dest * dest_score +
            w_flight * flight_score +
            w_stay * stay_score +
            w_exp * exp_score
        ) - friction_penalty

        final_score = int(round(max(30.0, min(99.0, base_score))))

        return {
            "trip_score": final_score,
            "pillar_scores": {
                "destination": round(dest_score, 1),
                "flight": round(flight_score, 1),
                "accommodation": round(stay_score, 1),
                "experience": round(exp_score, 1)
            },
            "subscores": {
                "destination_fit": round(dest_score, 1),
                "flight_comfort": round(flight_score, 1),
                "stay_quality": round(stay_score, 1),
                "experience_diversity": diversity,
                "friction_penalty": friction_penalty
            },
            "strengths": strengths,
            "tradeoffs": tradeoffs,
            "weights": {
                "destination": round(w_dest, 2),
                "flight": round(w_flight, 2),
                "accommodation": round(w_stay, 2),
                "experience": round(w_exp, 2)
            },
            "effective_vacation_hours": effective_hours,
            "experience_diversity": diversity,
            "harmony_level": "Kiváló" if final_score >= 85 else ("Jó" if final_score >= 70 else "Közepes")
        }



# Backward compatibility functions
calculate_experience_diversity = TripScoreService.calculate_experience_diversity
calculate_unified_trip_score = TripScoreService.calculate_trip_score
