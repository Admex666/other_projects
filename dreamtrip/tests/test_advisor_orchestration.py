"""
Unit Tests for Optivoya B2B Advisor Workspace — Research Orchestration Engine (Phase 4)
Tests all 9 Research Workflows, Resilience & Provenance, Candidate Generation, and API Endpoints.
"""

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.advisor_models import (
    TripCase, Client, ClientPreferences, HardConstraints, SoftPreferences,
    TripCaseStatus, ResearchScope, OptionArchetype
)
from app.services.advisor_orchestration_service import AdvisorOrchestrationService, ResearchStrategy
from app.routers.advisor_api import CASES_STORE, CLIENTS_STORE


class TestAdvisorOrchestrationEngine(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.test_case_id = "test_case_phase4"
        self.test_client_id = "test_client_phase4"

        self.mock_client = Client(
            id=self.test_client_id,
            agency_id="agency_test",
            advisor_id="adv_test",
            name="Nagy Család Teszt",
            email="nagy@example.com",
            preferences=ClientPreferences(
                hotel_min_stars=4,
                hotel_min_rating=8.5,
                direct_flights_only=True
            )
        )
        CLIENTS_STORE[self.test_client_id] = self.mock_client

        self.mock_case = TripCase(
            id=self.test_case_id,
            agency_id="agency_test",
            advisor_id="adv_test",
            client_id=self.test_client_id,
            title="Dél-Európa Nyaralás",
            status=TripCaseStatus.BRIEF,
            origin="Budapest",
            destination_focus="Barcelona",
            adults=2,
            children=1,
            duration_days=7,
            total_budget_huf=750000
        )
        CASES_STORE[self.test_case_id] = self.mock_case

        # Sample mock flight & stay return objects
        self.sample_flights = [
            {"id": "fl_1", "airline": "Wizz Air", "price_total_huf": 72000, "stops": 0, "total_duration_h": 2.5},
            {"id": "fl_2", "airline": "Ryanair", "price_total_huf": 85000, "stops": 0, "total_duration_h": 2.4},
            {"id": "fl_3", "airline": "Lufthansa", "price_total_huf": 110000, "stops": 1, "total_duration_h": 4.5}
        ]
        self.sample_stays = [
            {"id": "st_1", "name": "Hotel Arts Barcelona", "stars": 5, "rating_normalized": 9.4, "price_total_huf": 280000},
            {"id": "st_2", "name": "Catalonia Plaza Mayor", "stars": 4, "rating_normalized": 8.9, "price_total_huf": 175000},
            {"id": "st_3", "name": "Cozy Gothic Quarter Apt", "stars": 3, "rating_normalized": 8.4, "price_total_huf": 120000}
        ]

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_1_destination_discovery(self, mock_stays, mock_flights):
        """Workflow 1: Destination Discovery evaluates 45+ destinations and builds candidates."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        discovery_case = self.mock_case.model_copy(deep=True)
        discovery_case.destination_focus = None  # Open destination

        res = AdvisorOrchestrationService.execute_research(
            trip_case=discovery_case,
            client=self.mock_client,
            strategy=ResearchStrategy.DESTINATION_DISCOVERY
        )

        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["progress_pct"], 100)
        self.assertTrue(len(res["candidates"]) > 0)
        self.assertTrue(len(res["destinations_pool"]) > 0)
        cand = res["candidates"][0]
        self.assertIn("trip_score", cand)
        self.assertIn("pillar_scores", cand)
        self.assertIn("destination", cand)
        self.assertIn("flight", cand)
        self.assertIn("stay", cand)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_2_known_destination_research(self, mock_stays, mock_flights):
        """Workflow 2: Deep dive for a known destination generates 3 archetype candidates."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.KNOWN_DESTINATION
        )

        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["candidates"]), 3)
        archetypes = [c["archetype"] for c in res["candidates"]]
        self.assertIn(OptionArchetype.BEST_OVERALL.value, archetypes)
        self.assertIn(OptionArchetype.BEST_VALUE.value, archetypes)
        self.assertIn(OptionArchetype.BEST_EXPERIENCE.value, archetypes)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_3_flight_first_strategy(self, mock_stays, mock_flights):
        """Workflow 3: Flight-First prioritizes flight deals."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.FLIGHT_FIRST
        )
        self.assertEqual(res["status"], "completed")
        self.assertTrue(len(res["flights_pool"]) > 0)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_4_stay_first_strategy(self, mock_stays, mock_flights):
        """Workflow 4: Stay-First prioritizes 4*+ luxury & comfort accommodation."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.STAY_FIRST
        )
        self.assertEqual(res["status"], "completed")
        self.assertTrue(len(res["stays_pool"]) > 0)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_5_full_trip_optimization(self, mock_stays, mock_flights):
        """Workflow 5: Full package multi-criteria optimization."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.FULL_TRIP_OPTIMIZATION
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["candidates"]), 3)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_6_component_only_research(self, mock_stays, mock_flights):
        """Workflow 6: Flight-only or Stay-only research."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        fl_case = self.mock_case.model_copy(deep=True)
        fl_case.scope = ResearchScope.FLIGHT_ONLY
        res = AdvisorOrchestrationService.execute_research(
            trip_case=fl_case,
            client=self.mock_client,
            strategy=ResearchStrategy.COMPONENT_ONLY
        )
        self.assertEqual(res["status"], "completed")
        self.assertTrue(len(res["candidates"]) > 0)
        self.assertEqual(res["candidates"][0]["component_type"], "flight")

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_7_mixed_scope_research(self, mock_stays, mock_flights):
        """Workflow 7: Compares 3 cities side-by-side."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.MIXED_SCOPE,
            custom_params={"candidate_cities": ["Barcelona", "Rome", "Vienna"]}
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["candidates"]), 3)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_8_re_optimization(self, mock_stays, mock_flights):
        """Workflow 8: Re-optimizes based on modified parameters."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.RE_OPTIMIZATION,
            custom_params={"destination": "Rome"}
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["candidates"]), 3)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_workflow_9_find_better(self, mock_stays, mock_flights):
        """Workflow 9: Finds better stay alternative."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        res = AdvisorOrchestrationService.execute_research(
            trip_case=self.mock_case,
            client=self.mock_client,
            strategy=ResearchStrategy.FIND_BETTER,
            custom_params={"target_component": "stay"}
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(len(res["candidates"]), 3)

    def test_resilience_fallback_when_apis_fail(self):
        """Resilience: When external APIs fail with exceptions, fallback candidates are returned with warning."""
        with patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights", side_effect=TimeoutError("Kiwi timeout")):
            with patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays", side_effect=ConnectionError("Cozycozy unreachable")):
                res = AdvisorOrchestrationService.execute_research(
                    trip_case=self.mock_case,
                    client=self.mock_client,
                    strategy=ResearchStrategy.KNOWN_DESTINATION
                )
                self.assertEqual(res["status"], "completed")
                self.assertTrue(len(res["warnings"]) >= 2)
                self.assertEqual(len(res["candidates"]), 3)
                for cand in res["candidates"]:
                    self.assertIn("flight", cand)
                    self.assertIn("stay", cand)

    # ─────────────────────────────────────────────────────────────
    # API ENDPOINT TESTS
    # ─────────────────────────────────────────────────────────────

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_api_execute_research_and_status(self, mock_stays, mock_flights):
        """Test POST /api/advisor/cases/{case_id}/research and GET status."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        resp = self.client.post(
            f"/api/advisor/cases/{self.test_case_id}/research",
            json={"strategy": "full_trip_optimization"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("job", data)

        # Status endpoint
        status_resp = self.client.get(f"/api/advisor/cases/{self.test_case_id}/research/status")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertEqual(status_data["status"], "success")
        self.assertTrue(status_data["candidates_count"] > 0)

    @patch("app.services.flight_intelligence_service.FlightIntelligenceService.search_and_rank_flights")
    @patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays")
    def test_api_pin_candidate(self, mock_stays, mock_flights):
        """Test pinning candidate into Advisor Overrides."""
        mock_flights.return_value = self.sample_flights
        mock_stays.return_value = self.sample_stays

        # First execute research
        self.client.post(f"/api/advisor/cases/{self.test_case_id}/research")

        candidates_resp = self.client.get(f"/api/advisor/cases/{self.test_case_id}/candidates")
        candidates = candidates_resp.json()["candidates"]
        cand_id = candidates[0]["id"]

        pin_resp = self.client.post(
            f"/api/advisor/cases/{self.test_case_id}/candidates/pin",
            json={"candidate_id": cand_id, "is_pinned": True, "component_type": "destination"}
        )
        self.assertEqual(pin_resp.status_code, 200)
        pin_data = pin_resp.json()
        self.assertTrue(pin_data["is_pinned"])
        self.assertIsNotNone(pin_data["overrides"]["pinned_destination"])

    def test_api_duplicate_and_archive_case(self):
        """Test case duplication and archival."""
        dup_resp = self.client.post(
            f"/api/advisor/cases/{self.test_case_id}/duplicate",
            json={"new_title": "Másolt Eset Teszt"}
        )
        self.assertEqual(dup_resp.status_code, 200)
        dup_case = dup_resp.json()["duplicated_case"]
        self.assertEqual(dup_case["title"], "Másolt Eset Teszt")
        self.assertNotEqual(dup_case["id"], self.test_case_id)

        # Archive
        arch_resp = self.client.post(f"/api/advisor/cases/{self.test_case_id}/archive")
        self.assertEqual(arch_resp.status_code, 200)
        self.assertEqual(arch_resp.json()["case"]["status"], TripCaseStatus.CLOSED.value)



if __name__ == "__main__":
    unittest.main()
