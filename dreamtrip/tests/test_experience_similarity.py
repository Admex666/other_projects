"""
Tests for Experience Fit Vector Similarity and Level 2 Experience Preferences.
Verifies cosine similarity, alias mapping, 4-pillar weighting, and models separation.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import ExperiencePreferences, LogisticsPreferences, UnifiedTrip
from app.services.destination_scoring_service import (
    _cosine_similarity,
    calculate_destination_rankings
)
from app.services.dummy_planner_service import generate_dummy_destinations


class TestExperienceSimilarity(unittest.TestCase):

    def test_cosine_similarity_edge_cases(self):
        # 1. Identical vectors -> 1.0
        v1 = {"culture": 0.8, "gastronomy": 0.6}
        self.assertEqual(round(_cosine_similarity(v1, v1), 4), 1.0)

        # 2. Orthogonal / Disjoint vectors -> fallback 0.5 (neutral)
        v_a = {"culture": 1.0}
        v_b = {"beach": 1.0}
        self.assertEqual(_cosine_similarity(v_a, v_b), 0.5)

        # 3. Proportional vectors -> 1.0
        v_low = {"culture": 10.0, "nature": 20.0}
        v_high = {"culture": 50.0, "nature": 100.0}
        self.assertEqual(round(_cosine_similarity(v_low, v_high), 4), 1.0)

        # 4. Empty vector -> fallback 0.5
        self.assertEqual(_cosine_similarity({}, {"culture": 0.5}), 0.5)

    def test_experience_models(self):
        # ExperiencePreferences defaults
        exp = ExperiencePreferences()
        self.assertEqual(exp.culture, 50.0)
        self.assertEqual(exp.gastronomy, 50.0)
        self.assertTrue(hasattr(exp, "to_vector"))
        vec = exp.to_vector()
        self.assertIsInstance(vec, dict)
        self.assertIn("gastronomy", vec)
        self.assertIn("culture", vec)

        # Custom weights
        custom_exp = ExperiencePreferences(gastronomy=95.0, beach=10.0)
        self.assertEqual(custom_exp.gastronomy, 95.0)
        self.assertEqual(custom_exp.beach, 10.0)

        # LogisticsPreferences defaults
        logistics = LogisticsPreferences()
        self.assertEqual(logistics.day_start_time, "09:00")
        self.assertEqual(logistics.day_end_time, "21:00")
        self.assertEqual(logistics.max_walking_minutes, 25)

        # UnifiedTrip container
        trip = UnifiedTrip(trip_id="trip_test_001", destination_name="Rome", destination_city="Rome", destination_country="Italy")
        self.assertIsNotNone(trip.experience_preferences)
        self.assertIsNotNone(trip.logistics_preferences)
        self.assertEqual(trip.trip_score, 0.0)

    def test_destination_rankings_with_experience(self):
        candidates_raw = [
            {
                "id": "IT_ROME",
                "name": "Rome",
                "city": "Rome",
                "country": "Italy",
                "region": "Europe",
                "weather_score_direct": 0.95,
                "raw_metrics": {
                    "total_trip_cost_huf": 280000.0,
                    "flight_price_huf": 45000.0,
                    "flight_duration_h": 2.0,
                    "flight_is_direct": True,
                    "safety_index": 72.0,
                    "avg_temp": 24.0
                }
            },
            {
                "id": "FR_NICE",
                "name": "Nice",
                "city": "Nice",
                "country": "France",
                "region": "Europe",
                "weather_score_direct": 0.90,
                "raw_metrics": {
                    "total_trip_cost_huf": 350000.0,
                    "flight_price_huf": 60000.0,
                    "flight_duration_h": 2.5,
                    "flight_is_direct": True,
                    "safety_index": 80.0,
                    "avg_temp": 23.5
                }
            }
        ]

        weights = {"total_cost": 25.0, "weather": 25.0, "safety": 25.0, "experience": 25.0}

        food_prefs = {"gastronomy": 95.0, "culture": 90.0, "authenticity": 85.0}
        rankings_food = calculate_destination_rankings(
            candidates_raw=candidates_raw,
            weights=weights,
            target_temp=24.0,
            adults=2,
            experience_preferences=food_prefs
        )

        self.assertEqual(len(rankings_food), 2)
        for r in rankings_food:
            self.assertIn("score", r)
            self.assertIn("subscores", r)
            self.assertIn("experience", r["subscores"])
            self.assertTrue(0.0 <= r["subscores"]["experience"] <= 1.0)

    def test_dummy_destinations_4_pillars(self):
        class MockIntake:
            target_temp = 24.0
            adults = 2
            duration = 7
            ahp_weights = {"total_cost": 25.0, "weather": 25.0, "safety": 25.0, "experience": 25.0}
            exclusions = []
            preferred_regions = ["Europe"]
            experience_preferences = {"gastronomy": 95.0, "culture": 90.0}

        dests = generate_dummy_destinations(MockIntake())
        self.assertGreaterEqual(len(dests), 5)
        self.assertEqual(dests[0]["rank"], 1)
        self.assertGreater(dests[0]["score"], 50.0)


if __name__ == "__main__":
    unittest.main()
