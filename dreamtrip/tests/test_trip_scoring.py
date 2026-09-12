"""
Tests for Unified Trip Scoring and Experience Diversity Engine.
Verifies Shannon diversity calculation, holistic TripScore, and friction penalties.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.trip_scoring_service import (
    calculate_experience_diversity,
    calculate_unified_trip_score
)
from app.services.experience.trip_generator import trip_generator


class TestTripScoring(unittest.TestCase):

    def test_experience_diversity_entropy(self):
        # 1. Single category -> low diversity
        single_cat = [
            {"canonical_name": "Museum 1", "category": "culture_history"},
            {"canonical_name": "Museum 2", "category": "culture_history"},
            {"canonical_name": "Museum 3", "category": "culture_history"}
        ]
        div_single = calculate_experience_diversity(single_cat)
        self.assertLessEqual(div_single, 0.5)

        # 2. Balanced multi-category -> high diversity
        balanced_cats = [
            {"canonical_name": "Museum", "category": "culture_history"},
            {"canonical_name": "Market", "category": "food_market"},
            {"canonical_name": "Viewpoint", "category": "nature_viewpoint"},
            {"canonical_name": "Beach", "category": "beach_coastal"}
        ]
        div_balanced = calculate_experience_diversity(balanced_cats)
        self.assertGreater(div_balanced, 0.8)

    def test_unified_trip_score_calculation(self):
        dest = {"name": "Rome", "score": 88.0}
        flight = {"airline": "Wizz Air", "relevance_pct": 85.0, "effective_vacation_hours": 21.0, "out_stops": 0, "in_stops": 0}
        stay = {"name": "Central Hotel", "rating": 9.2, "is_market_benchmark": True}
        activities = [
            {"canonical_name": "Colosseum", "category": "culture_history"},
            {"canonical_name": "Testaccio Market", "category": "food_market"},
            {"canonical_name": "Villa Borghese", "category": "nature_viewpoint"}
        ]
        exp_prefs = {"culture": 85.0, "gastronomy": 90.0}

        score_res = calculate_unified_trip_score(
            destination=dest,
            flight=flight,
            accommodation=stay,
            activities=activities,
            experience_preferences=exp_prefs
        )

        self.assertIn("trip_score", score_res)
        self.assertGreater(score_res["trip_score"], 80.0)
        self.assertIn("strengths", score_res)
        self.assertGreater(len(score_res["strengths"]), 0)
        self.assertIn("subscores", score_res)
        self.assertEqual(score_res["subscores"]["friction_penalty"], 0.0)

    def test_friction_penalty_on_stops(self):
        dest = {"name": "Bari", "score": 80.0}
        flight_with_stops = {"airline": "Lufthansa", "relevance_pct": 75.0, "effective_vacation_hours": 9.0, "out_stops": 1, "in_stops": 1}
        stay = {"name": "Old Town B&B", "rating": 8.5}

        res = calculate_unified_trip_score(
            destination=dest,
            flight=flight_with_stops,
            accommodation=stay,
            activities=[]
        )

        self.assertGreater(res["subscores"]["friction_penalty"], 0.0)
        self.assertIn("tradeoffs", res)

    def test_trip_generator_recommended_experiences(self):
        recs = trip_generator.generate_recommended_experiences(
            destination_id="IT_BARI",
            experience_preferences={"gastronomy": 95.0, "culture": 80.0},
            limit=5
        )
        if recs:
            self.assertIn("fit_score", recs[0])
            self.assertIn("recommendation_reason", recs[0])
            self.assertGreater(recs[0]["fit_score"], 50.0)


if __name__ == "__main__":
    unittest.main()
