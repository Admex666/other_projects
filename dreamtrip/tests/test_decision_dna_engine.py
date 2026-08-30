"""
Unit Tests for Optivoya Decision DNA (AHP & PROMETHEE II Engines)
"""

import unittest
import math
import numpy as np
import pandas as pd
from app.services.planner_service import compute_ahp_weights_from_comparisons

class TestDecisionDNAEngine(unittest.TestCase):

    def test_ahp_equal_weights(self):
        criteria = ["total_cost", "weather", "safety"]
        comparisons = {
            "total_cost_vs_weather": 1.0,
            "total_cost_vs_safety": 1.0,
            "weather_vs_safety": 1.0
        }
        weights = compute_ahp_weights_from_comparisons(criteria, comparisons)
        
        self.assertEqual(len(weights), 3)
        self.assertTrue(math.isclose(weights["total_cost"], 1/3, rel_tol=1e-2))
        self.assertTrue(math.isclose(weights["weather"], 1/3, rel_tol=1e-2))
        self.assertTrue(math.isclose(weights["safety"], 1/3, rel_tol=1e-2))
        self.assertTrue(math.isclose(sum(weights.values()), 1.0, rel_tol=1e-3))

    def test_ahp_dominant_cost(self):
        criteria = ["total_cost", "weather", "safety"]
        comparisons = {
            "total_cost_vs_weather": 9.0, # Cost strongly preferred over weather
            "total_cost_vs_safety": 9.0,  # Cost strongly preferred over safety
            "weather_vs_safety": 1.0
        }
        weights = compute_ahp_weights_from_comparisons(criteria, comparisons)
        
        self.assertGreater(weights["total_cost"], weights["weather"])
        self.assertGreater(weights["total_cost"], weights["safety"])
        self.assertGreater(weights["total_cost"], 0.70)
        self.assertTrue(math.isclose(sum(weights.values()), 1.0, rel_tol=1e-3))

    def test_ahp_stay_four_criteria(self):
        criteria = ["price", "rating", "location", "amenities"]
        comparisons = {
            "price_vs_rating": 3.0,
            "price_vs_location": 3.0,
            "price_vs_amenities": 5.0,
            "rating_vs_location": 1.0,
            "rating_vs_amenities": 3.0,
            "location_vs_amenities": 3.0
        }
        weights = compute_ahp_weights_from_comparisons(criteria, comparisons)
        
        self.assertEqual(len(weights), 4)
        self.assertGreater(weights["price"], weights["rating"])
        self.assertGreater(weights["rating"], weights["amenities"])
        self.assertTrue(math.isclose(sum(weights.values()), 1.0, rel_tol=1e-3))

if __name__ == "__main__":
    unittest.main()
