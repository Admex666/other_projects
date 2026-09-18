"""
Optivoya Test Suite — Shared Intelligence Layer & Architecture Extraction
Unit and integration tests for AHPEngine, PrometheeEngine, TripScoreService,
ExperienceIntelligenceService, DestinationMatchingService, and ProposalRenderer.
"""

import unittest
import numpy as np
from app.services.ahp_engine import AHPEngine
from app.services.promethee_engine import PrometheeEngine
from app.services.trip_scoring_service import TripScoreService
from app.services.experience_intelligence_service import ExperienceIntelligenceService
from app.services.proposal_renderer import ProposalRenderer


class TestSharedIntelligenceServices(unittest.TestCase):

    def test_ahp_engine_geometric_mean_and_cr(self):
        """Tests AHP weight calculation, 100% sum normalization, and consistency ratio."""
        criteria = ["total_cost", "weather", "safety"]
        comparisons = {
            "total_cost_vs_weather": 3.0,
            "total_cost_vs_safety": 5.0,
            "weather_vs_safety": 2.0
        }

        matrix = AHPEngine.build_matrix_from_pairwise_dict(criteria, comparisons)
        self.assertEqual(matrix.shape, (3, 3))
        self.assertAlmostEqual(matrix[0][1], 3.0)
        self.assertAlmostEqual(matrix[1][0], 1.0 / 3.0)

        res = AHPEngine.calculate_weights(matrix, criteria)
        weights = res["weights"]

        # Cost should have highest weight
        self.assertGreater(weights["total_cost"], weights["weather"])
        self.assertGreater(weights["weather"], weights["safety"])

        # Sum of normalized weights should equal 1.0
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        self.assertAlmostEqual(sum(res["weights_percentage"].values()), 100.0, places=1)
        self.assertTrue(res["is_consistent"])

    def test_promethee_engine_ranking(self):
        """Tests PROMETHEE II multi-criteria outranking with Type 5 and Min/Max directions."""
        alternatives = [
            {"id": "fl_1", "price": 30000, "duration": 2.0, "stops": 0},
            {"id": "fl_2", "price": 20000, "duration": 5.5, "stops": 1},
            {"id": "fl_3", "price": 60000, "duration": 1.8, "stops": 0}
        ]

        criteria_configs = {
            "price": {"type": 5, "q": 5000, "p": 25000, "direction": "min"},
            "duration": {"type": 5, "q": 0.5, "p": 3.0, "direction": "min"},
            "stops": {"type": 1, "q": 0, "p": 1, "direction": "min"}
        }

        weights = {"price": 50.0, "duration": 30.0, "stops": 20.0}

        ranked = PrometheeEngine.rank_alternatives(alternatives, criteria_configs, weights)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[1]["rank"], 2)
        self.assertEqual(ranked[2]["rank"], 3)

        # Net flows should be descending
        self.assertGreaterEqual(ranked[0]["phi_net"], ranked[1]["phi_net"])
        self.assertGreaterEqual(ranked[1]["phi_net"], ranked[2]["phi_net"])

        # Relevance percentage should be in [0, 100]
        for r in ranked:
            self.assertGreaterEqual(r["relevance_pct"], 0)
            self.assertLessEqual(r["relevance_pct"], 100)

    def test_trip_score_service_composite(self):
        """Tests 4-pillar TripScore calculation and effective daylight vacation hours."""
        dest = {"name": "Róma", "score": 88.0}
        flight = {"airline": "Wizz Air", "relevance_pct": 82.0, "effective_vacation_hours": 22.0}
        stay = {"name": "Hotel Roma", "rating_normalized": 8.8, "stars": 4}
        activities = [
            {"name": "Colosseum", "category": "culture", "rating": 4.9},
            {"name": "Trastevere Food Tour", "category": "gastronomy", "rating": 4.8},
            {"name": "Gianicolo Viewpoint", "category": "nature", "rating": 4.7}
        ]

        res = TripScoreService.calculate_trip_score(
            destination=dest,
            flight=flight,
            accommodation=stay,
            activities=activities
        )

        self.assertIn("trip_score", res)
        self.assertGreaterEqual(res["trip_score"], 70)
        self.assertLessEqual(res["trip_score"], 100)
        self.assertIn("pillar_scores", res)
        self.assertEqual(res["pillar_scores"]["destination"], 88.0)

        # Effective vacation hours
        eff_hours = TripScoreService.calculate_effective_vacation_time(
            out_arr_time="2026-09-10T11:00:00",
            in_dep_time="2026-09-17T18:00:00",
            duration_days=7
        )
        self.assertGreater(eff_hours, 50.0)

    def test_experience_intelligence_vibe(self):
        """Tests destination vibe profile retrieval."""
        vibe = ExperienceIntelligenceService.get_destination_vibe("Barcelona")
        self.assertGreaterEqual(vibe["culture"], 80)
        self.assertGreaterEqual(vibe["gastronomy"], 90)

    def test_proposal_renderer_single_and_multi(self):
        """Tests HTML proposal rendering for both SingleTrip and MultiOption proposals."""
        trip_data = {
            "destination": {"name": "Róma", "country": "Olaszország", "explanation": "Kiváló időjárás"},
            "flight": {"airline": "Wizz Air", "out_date": "2026-09-10", "in_date": "2026-09-17", "price_total_huf": 48900},
            "accommodation": {"name": "Hotel Quirinale", "nights": 7, "rating_normalized": 8.8, "price_total_huf": 140000},
            "breakdown": {"totalHuf": 280000}
        }

        single_html = ProposalRenderer.render_single_trip_html(trip_data)
        self.assertIn("Hotel Quirinale", single_html)
        self.assertIn("Wizz Air", single_html)
        self.assertIn("280,000 Ft", single_html)

        case_data = {"id": "CASE-101", "client_name": "Kovács Péter", "title": "Olaszországi Utazás"}
        options = [
            {
                "title": "Klasszikus Róma Élmény",
                "archetype": "best_overall",
                "total_price_huf": 280000,
                "price_per_person_huf": 140000,
                "destination": {"name": "Róma", "country": "Olaszország"},
                "flight": {"airline": "Wizz Air", "out_date": "2026-09-10", "in_date": "2026-09-17", "stops": 0},
                "stay": {"name": "Hotel Quirinale", "stars": 4, "rating": 8.8},
                "why_this_option": "Tökéletes elhelyezkedés és közvetlen repülőút."
            }
        ]

        multi_html = ProposalRenderer.render_multi_option_html(case_data, options)
        self.assertIn("Kovács Péter", multi_html)
        self.assertIn("BEST_OVERALL", multi_html)
        self.assertIn("Tökéletes elhelyezkedés", multi_html)


if __name__ == "__main__":
    unittest.main()
