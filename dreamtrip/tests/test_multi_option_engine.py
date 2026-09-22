"""
Unit & Integration Tests for MultiOptionEngine (Phase 5)
Verifies:
1. Hard constraints filtering (flight stops, min hotel stars, rating, budget cap).
2. Generation of exactly 3 distinct Archetypes (BEST OVERALL, BEST VALUE, BEST EXPERIENCE).
3. Diversity separation (distinct IDs, price delta, or stay classes).
4. Deterministic 'why_this_option' and trade-offs metadata.
5. REST API contract for /api/advisor/cases/{case_id}/options/generate and /options.
"""

import pytest
from app.services.multi_option_engine import MultiOptionEngine
from app.routers.advisor_api import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestMultiOptionEngine:

    @pytest.fixture
    def mock_candidate_pool(self):
        return [
            {
                "id": "cand_1",
                "title": "Barcelona Balanced Premium",
                "total_price_huf": 320000,
                "price_per_person_huf": 160000,
                "trip_score": 92.5,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Wizz Air", "stops": 0, "price_huf": 80000},
                "stay": {"name": "Hotel Arts Barcelona", "stars": 4, "rating_normalized": 8.8, "price_huf": 200000},
                "activities": [{"name": "Sagrada Familia", "fit_score": 0.95}, {"name": "Tapas Tour", "fit_score": 0.90}]
            },
            {
                "id": "cand_2",
                "title": "Barcelona Smart Value",
                "total_price_huf": 190000,
                "price_per_person_huf": 95000,
                "trip_score": 84.0,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Ryanair", "stops": 0, "price_huf": 50000},
                "stay": {"name": "Catalonia Ramblas", "stars": 3, "rating_normalized": 8.2, "price_huf": 120000},
                "activities": [{"name": "Gothic Quarter Walk", "fit_score": 0.85}]
            },
            {
                "id": "cand_3",
                "title": "Barcelona Luxury & Deep Culture",
                "total_price_huf": 480000,
                "price_per_person_huf": 240000,
                "trip_score": 90.0,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Lufthansa", "stops": 0, "price_huf": 110000},
                "stay": {"name": "Mandarin Oriental", "stars": 5, "rating_normalized": 9.4, "price_huf": 320000},
                "activities": [
                    {"name": "Private Gaudi Tour", "fit_score": 0.98},
                    {"name": "Michelin Dining", "fit_score": 0.96},
                    {"name": "Wine Tasting", "fit_score": 0.92}
                ]
            }
        ]

    def test_archetype_assignment_and_diversity(self, mock_candidate_pool):
        """Tests that MultiOptionEngine generates the 3 required archetypes."""
        options = MultiOptionEngine.generate_archetypes(mock_candidate_pool)
        assert len(options) == 3

        archetypes = [opt["archetype"] for opt in options]
        assert "best_overall" in archetypes
        assert "best_value" in archetypes
        assert "best_experience" in archetypes

        # Verify Option A is highest overall score
        assert options[0]["archetype"] == "best_overall"
        assert options[0]["id"] == "cand_1"
        assert options[0]["trip_score"] == 92.5

        # Verify Option B is best value (lowest reasonable price with good ratio)
        assert options[1]["archetype"] == "best_value"
        assert options[1]["id"] == "cand_2"
        assert options[1]["total_price_huf"] < options[0]["total_price_huf"]

        # Verify Option C is best experience (5 stars, 3 activities)
        assert options[2]["archetype"] == "best_experience"
        assert options[2]["id"] == "cand_3"
        assert options[2]["stay"]["stars"] == 5

    def test_hard_constraint_filtering(self, mock_candidate_pool):
        """Tests that invalid options (e.g. 2 stops or low stars) are excluded."""
        pool_with_invalid = mock_candidate_pool + [{
            "id": "cand_invalid_stops",
            "title": "Barcelona Cheap 2 Stops",
            "total_price_huf": 140000,
            "trip_score": 70.0,
            "flight": {"airline": "Transit Air", "stops": 2},
            "stay": {"name": "Budget Hostel", "stars": 2, "rating_normalized": 6.5}
        }]

        class MockPref:
            hard = {
                "direct_flights_only": True,
                "min_hotel_stars": 3,
                "min_hotel_rating": 8.0
            }

        filtered = MultiOptionEngine._filter_hard_constraints(pool_with_invalid, MockPref(), target_budget_huf=500000)
        assert len(filtered) == 3
        assert all(c["id"] != "cand_invalid_stops" for c in filtered)
        assert all(c["id"] != "cand_invalid_stops" for c in filtered)

    def test_deterministic_why_and_tradeoffs(self, mock_candidate_pool):
        """Verifies that all archetypes contain structured why_this_option and tradeoffs."""
        options = MultiOptionEngine.generate_archetypes(mock_candidate_pool)
        for opt in options:
            assert "why_this_option" in opt
            assert len(opt["why_this_option"]) > 10
            assert "tradeoffs" in opt
            assert isinstance(opt["tradeoffs"], list)
            assert len(opt["tradeoffs"]) >= 1

    def test_api_generate_and_get_case_options(self, mock_candidate_pool):
        """Tests the REST API endpoint for generating case options."""
        from app.services.advisor_orchestration_service import AdvisorOrchestrationService
        from app.routers.advisor_api import CASES_STORE, CLIENTS_STORE, TripCase, Client

        # Create isolated test client & case
        test_client = Client(id="client_multi_test", agency_id="agency_optivoya", advisor_id="adv_test", name="Multi Test Client", email="multi@test.com")
        CLIENTS_STORE["client_multi_test"] = test_client
        
        test_case = TripCase(
            id="case_multi_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_multi_test",
            title="Multi Option Test Case",
            total_budget_huf=450000
        )
        CASES_STORE["case_multi_test"] = test_case
        case_id = "case_multi_test"

        # Seed candidate pool for rapid offline test
        AdvisorOrchestrationService._CANDIDATES_POOL[case_id] = mock_candidate_pool

        # Post generate options
        gen_res = client.post(f"/api/advisor/cases/{case_id}/options/generate")
        assert gen_res.status_code == 200
        data = gen_res.json()
        assert data["status"] == "success"
        assert data["total_options"] == 3

        # Get case options
        get_res = client.get(f"/api/advisor/cases/{case_id}/options")
        assert get_res.status_code == 200
        options = get_res.json().get("options", [])
        assert len(options) == 3
        archetypes = [o["archetype"] for o in options]
        assert "best_overall" in archetypes
        assert "best_value" in archetypes
        assert "best_experience" in archetypes
