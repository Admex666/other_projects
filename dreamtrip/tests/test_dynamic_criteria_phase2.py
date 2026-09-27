"""
Optivoya Advisor Workspace v2 — Phase 2: Dynamic Requirement Discovery & Preference Model Tests
=================================================================================================
Tests:
1. Two-Stage Preference Discovery: Dimension catalog & active dimension filtering.
2. Minimal pairwise AHP comparison generation (n*(n-1)/2 pairs).
3. AHP mathematical calculation: Geometric mean / Logarithmic least squares, Eigenvalues,
   Consistency Ratio (CR), and tolerance handling.
4. 4-Level Structured Criteria Management (HARD, SOFT, AVOID, NICE_TO_HAVE).
5. Synchronization between TripCase.preferences and ResearchState.what_matters.
6. Criteria approval and Phase State Machine transition (DEFINE -> RESEARCH).
7. REST API endpoints: GET /criteria, POST /calculate-ahp, POST /update, POST /approve.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app, sessions
from app.models.advisor_models import (
    TripCase, Client, ResearchStatePhase,
    ResolvedTripPreferences, HardConstraints, SoftPreferences,
    AvoidRules, NiceToHave
)
from app.services.research_state_service import ResearchStateService
from app.services.preference_discovery_service import (
    PreferenceDiscoveryService, CANONICAL_DIMENSIONS
)
from app.repositories.advisor_repository import TripCaseRepository, ClientRepository


@pytest.fixture(autouse=True)
def clean_test_case():
    case_id = "test_phase2_case_001"
    client_id = "test_phase2_client_001"
    agency_id = "test_agency_phase2"

    client = Client(
        id=client_id,
        agency_id=agency_id,
        advisor_id="adv_001",
        name="Kovács Katalin & Dániel",
        email="kovacs.katalin@example.com"
    )
    ClientRepository.save_client(client, agency_id=agency_id)

    trip_case = TripCase(
        id=case_id,
        agency_id=agency_id,
        advisor_id="adv_001",
        client_id=client_id,
        title="Róma & Firenze Gasztro és Kulturális Utazás",
        destination_focus="Róma",
        origin="Budapest (BUD)",
        adults=2,
        children=0,
        duration_days=5
    )
    trip_case.preferences = ResolvedTripPreferences(
        hard=HardConstraints(direct_flights_only=True, min_hotel_stars=4, max_total_budget_huf=600000),
        soft=SoftPreferences(vibe_weights={"culture": 50.0, "gastronomy": 50.0}),
        avoid=AvoidRules(avoid_early_departures=True, avoid_airlines=["Ryanair"]),
        nice_to_have=NiceToHave(breakfast_included=True, free_cancellation=True)
    )
    TripCaseRepository.save_case(trip_case, agency_id=agency_id)

    # Pre-build research state
    state = ResearchStateService.get_or_create_research_state(trip_case=trip_case, client=client, force_rebuild=True)
    ResearchStateService.confirm_intent(case_id=case_id, confirmed=True)

    yield {
        "case_id": case_id,
        "client_id": client_id,
        "agency_id": agency_id,
        "case": trip_case,
        "client": client,
        "state": state
    }


class TestAdvisorV2Phase2DynamicCriteria:

    def test_01_dimension_catalog_and_selection(self, clean_test_case):
        """Stage 1: Dimension catalog contains 9 canonical dimensions and filters correctly."""
        catalog = PreferenceDiscoveryService.get_dimension_catalog()
        assert len(catalog) == 9
        dim_ids = [d["id"] for d in catalog]
        assert "price" in dim_ids
        assert "flight_comfort" in dim_ids
        assert "location" in dim_ids
        assert "hotel_quality" in dim_ids
        assert "beach" in dim_ids
        assert "gastronomy" in dim_ids
        assert "culture_sightseeing" in dim_ids
        assert "relaxation_wellness" in dim_ids
        assert "family_friendliness" in dim_ids

    def test_02_minimal_ahp_pairs_generation(self, clean_test_case):
        """Stage 2: Minimal pairwise comparisons generation creates n*(n-1)/2 pairs."""
        # 2 dimensions -> 1 pair
        pairs_2 = PreferenceDiscoveryService.generate_minimal_ahp_pairs(["price", "location"])
        assert len(pairs_2) == 1
        assert pairs_2[0]["dim_a"] == "price"
        assert pairs_2[0]["dim_b"] == "location"

        # 3 dimensions -> 3 pairs
        pairs_3 = PreferenceDiscoveryService.generate_minimal_ahp_pairs(["price", "location", "hotel_quality"])
        assert len(pairs_3) == 3

        # 4 dimensions -> 6 pairs
        pairs_4 = PreferenceDiscoveryService.generate_minimal_ahp_pairs(["price", "flight_comfort", "location", "hotel_quality"])
        assert len(pairs_4) == 6

    def test_03_ahp_mathematical_solver_and_consistency(self, clean_test_case):
        """AHP Geometric Mean solver produces normalized weights (sum=1.0) and evaluates CR."""
        dims = ["price", "location", "hotel_quality"]
        # Price is 2x more important than location, 3x more than hotel_quality
        comparisons = [
            {"dim_a": "price", "dim_b": "location", "ratio": 2.0},
            {"dim_a": "price", "dim_b": "hotel_quality", "ratio": 3.0},
            {"dim_a": "location", "dim_b": "hotel_quality", "ratio": 1.5}
        ]

        res = PreferenceDiscoveryService.calculate_ahp_weights(dims, comparisons)
        weights = res["weights"]
        
        # Check sum of weights is 1.0 (within rounding)
        total_w = sum(weights.values())
        assert abs(total_w - 1.0) < 0.01

        # Price must have the highest weight
        assert weights["price"] > weights["location"]
        assert weights["location"] > weights["hotel_quality"]

        # Consistency check (should be consistent with CR < 0.10)
        assert res["is_consistent"] is True
        assert res["consistency_ratio"] <= 0.12

    def test_04_four_tier_criteria_synchronization(self, clean_test_case):
        """4-tier criteria updates synchronize with TripCase preferences and ResearchState.what_matters."""
        trip_case = clean_test_case["case"]
        case_id = trip_case.id

        updated = PreferenceDiscoveryService.update_case_criteria(
            trip_case=trip_case,
            selected_dimensions=["price", "gastronomy", "culture_sightseeing"],
            ahp_weights={"price": 0.3, "gastronomy": 0.4, "culture_sightseeing": 0.3},
            hard_updates={"min_hotel_stars": 5, "direct_flights_only": True},
            avoid_updates={"avoid_early_departures": True},
            nice_to_have_updates={"pool_available": True},
            date_flexibility_days=2,
            budget_relaxation_allowed=True
        )

        assert updated["selected_dimensions"] == ["price", "gastronomy", "culture_sightseeing"]
        assert updated["ahp_weights"]["gastronomy"] == 0.4
        assert updated["hard_constraints"]["min_hotel_stars"] == 5
        assert updated["nice_to_have"]["pool_available"] is True

        # Verify state synchronization
        state = ResearchStateService.get_or_create_research_state(trip_case=trip_case)
        assert state.what_matters.selected_dimensions == ["price", "gastronomy", "culture_sightseeing"]
        assert state.what_is_flexible.date_flexibility_days == 2
        assert state.what_is_flexible.budget_relaxation_allowed is True

    def test_05_criteria_approval_and_phase_transition(self, clean_test_case):
        """Approving criteria sets criteria_approved: True and transitions phase from DEFINE to RESEARCH."""
        trip_case = clean_test_case["case"]
        state = ResearchStateService.get_or_create_research_state(trip_case=trip_case)
        assert state.phase == ResearchStatePhase.DEFINE

        approved = PreferenceDiscoveryService.approve_case_criteria(trip_case=trip_case, notes="Advisor approved.")
        assert approved["criteria_approved"] is True

        # Phase must now be RESEARCH
        assert state.phase == ResearchStatePhase.RESEARCH

    def test_06_rest_api_criteria_endpoints(self, clean_test_case):
        """Test full REST API lifecycle for Phase 2 criteria endpoints."""
        client = TestClient(app)
        token = "test_advisor_token_v2_phase2"
        sessions[token] = "adam"
        client.cookies.set("session_token", token)

        case_id = clean_test_case["case_id"]
        headers = {"x-agency-id": clean_test_case["agency_id"]}

        # 1. GET /criteria
        get_res = client.get(f"/api/advisor/cases/{case_id}/criteria", headers=headers)
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["success"] is True
        assert len(get_data["dimension_catalog"]) == 9
        assert "selected_dimensions" in get_data
        assert "hard_constraints" in get_data

        # 2. POST /criteria/calculate-ahp
        calc_res = client.post(
            f"/api/advisor/cases/{case_id}/criteria/calculate-ahp",
            headers=headers,
            json={
                "selected_dimensions": ["price", "location", "hotel_quality"],
                "comparisons": [
                    {"dim_a": "price", "dim_b": "location", "ratio": 2.0},
                    {"dim_a": "price", "dim_b": "hotel_quality", "ratio": 2.0},
                    {"dim_a": "location", "dim_b": "hotel_quality", "ratio": 1.0}
                ]
            }
        )
        assert calc_res.status_code == 200
        calc_data = calc_res.json()
        assert calc_data["is_consistent"] is True
        assert "weights" in calc_data
        assert calc_data["weights"]["price"] > calc_data["weights"]["location"]

        # 3. POST /criteria/update
        update_res = client.post(
            f"/api/advisor/cases/{case_id}/criteria/update",
            headers=headers,
            json={
                "selected_dimensions": ["price", "gastronomy", "culture_sightseeing"],
                "ahp_weights": calc_data["weights"],
                "hard_constraints": {"min_hotel_stars": 4, "direct_flights_only": True},
                "avoid_rules": {"avoid_early_departures": True},
                "nice_to_have": {"breakfast_included": True}
            }
        )
        assert update_res.status_code == 200
        up_data = update_res.json()
        assert up_data["selected_dimensions"] == ["price", "gastronomy", "culture_sightseeing"]

        # 4. POST /criteria/approve
        approve_res = client.post(
            f"/api/advisor/cases/{case_id}/criteria/approve",
            headers=headers,
            json={"notes": "Final client requirements vetted by advisor."}
        )
        assert approve_res.status_code == 200
        appr_data = approve_res.json()
        assert appr_data["criteria_approved"] is True
        assert appr_data["phase"] == "research"
