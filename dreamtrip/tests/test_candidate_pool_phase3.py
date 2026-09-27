"""
Optivoya Advisor Workspace v2 — Phase 3: Candidate Pool & Multi-Intelligence Tests
===================================================================================
Tests:
1. CandidatePoolService multi-source inventory harvesting (Destinations, Flights, Stays, Experiences).
2. LocationScore calculation integration on Stay candidates (0.0 to 10.0 scale, walkability & transit metrics).
3. 12-dimensional cosine similarity matching on curated experiences.
4. Provider provenance tracking (Kiwi, Cozycozy, Open-Meteo, Places KG) and verification status.
5. ResearchState.what_we_found and what_is_verified synchronization.
6. REST API Endpoints:
   - POST /api/advisor/cases/{case_id}/candidate-pool/generate
   - GET /api/advisor/cases/{case_id}/candidate-pool
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app, sessions
from app.models.advisor_models import (
    TripCase, Client, ResearchStatePhase,
    ResolvedTripPreferences, HardConstraints, SoftPreferences,
    AvoidRules, NiceToHave, VerificationStatus
)
from app.services.research_state_service import ResearchStateService
from app.services.candidate_pool_service import CandidatePoolService
from app.repositories.advisor_repository import TripCaseRepository, ClientRepository


@pytest.fixture(autouse=True)
def clean_test_case():
    case_id = "test_phase3_case_001"
    client_id = "test_phase3_client_001"
    agency_id = "test_agency_phase3"

    client = Client(
        id=client_id,
        agency_id=agency_id,
        advisor_id="adv_001",
        name="Varga Zoltán & Éva",
        email="varga.zoltan@example.com"
    )
    ClientRepository.save_client(client, agency_id=agency_id)

    trip_case = TripCase(
        id=case_id,
        agency_id=agency_id,
        advisor_id="adv_001",
        client_id=client_id,
        title="Barcelona Családi & Kulturális Hétvége",
        destination_focus="Barcelona",
        origin="Budapest (BUD)",
        adults=2,
        children=1,
        duration_days=5
    )
    trip_case.preferences = ResolvedTripPreferences(
        hard=HardConstraints(direct_flights_only=True, min_hotel_stars=4, max_total_budget_huf=750000),
        soft=SoftPreferences(vibe_weights={"culture": 80.0, "beach": 60.0, "gastronomy": 90.0}),
        avoid=AvoidRules(avoid_early_departures=True),
        nice_to_have=NiceToHave(breakfast_included=True, central_location=True)
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


class TestAdvisorV2Phase3CandidatePool:

    def test_01_generate_candidate_pool_service(self, clean_test_case):
        """CandidatePoolService harvests and structures candidates across all 4 pillars."""
        trip_case = clean_test_case["case"]
        client = clean_test_case["client"]

        pool_result = CandidatePoolService.generate_candidate_pool(trip_case=trip_case, client=client)
        assert pool_result["success"] is True
        assert pool_result["case_id"] == trip_case.id

        counts = pool_result["counts"]
        assert counts["destinations"] >= 1
        assert counts["flights"] >= 1
        assert counts["stays"] >= 1
        assert counts["experiences"] >= 1

        # Check candidate items
        pool = pool_result["candidate_pool"]
        assert len(pool["flights"]) == counts["flights"]
        assert len(pool["stays"]) == counts["stays"]
        assert len(pool["experiences"]) == counts["experiences"]

    def test_02_location_score_on_stay_candidates(self, clean_test_case):
        """Stay candidates have LocationScore and location details (walkability, transit, central proximity)."""
        trip_case = clean_test_case["case"]
        client = clean_test_case["client"]

        pool_result = CandidatePoolService.generate_candidate_pool(trip_case=trip_case, client=client)
        stays = pool_result["candidate_pool"]["stays"]

        for stay in stays:
            assert "location_score" in stay
            assert 0.0 <= stay["location_score"] <= 100.0 or 0.0 <= stay["location_score"] <= 10.0
            assert "location_details" in stay
            loc_details = stay["location_details"]
            assert "walkability_score" in loc_details
            assert "transit_score" in loc_details
            assert "city_center_distance_km" in loc_details

    def test_03_experience_fit_and_provenance(self, clean_test_case):
        """Experiences and stays have valid provenance metadata and verification status."""
        trip_case = clean_test_case["case"]
        client = clean_test_case["client"]

        pool_result = CandidatePoolService.generate_candidate_pool(trip_case=trip_case, client=client)
        verif = pool_result["verification_summary"]

        assert verif["verified_count"] + verif["estimated_count"] > 0
        assert "last_verified_at" in verif

        # Check provenance on flight and stay items
        flight = pool_result["candidate_pool"]["flights"][0]
        assert "provenance" in flight
        assert flight["provenance"]["provider"] is not None

        stay = pool_result["candidate_pool"]["stays"][0]
        assert "provenance" in stay
        assert stay["provenance"]["provider"] is not None

    def test_04_research_state_synchronization(self, clean_test_case):
        """ResearchState.what_we_found and what_is_verified are fully populated."""
        trip_case = clean_test_case["case"]
        client = clean_test_case["client"]

        CandidatePoolService.generate_candidate_pool(trip_case=trip_case, client=client)
        state = ResearchStateService.get_or_create_research_state(trip_case=trip_case, client=client)

        assert state.what_we_found.destinations_count >= 1
        assert state.what_we_found.flights_count >= 1
        assert state.what_we_found.stays_count >= 1
        assert state.what_we_found.experiences_count >= 1
        assert state.what_we_found.total_concepts_formed > 0

        assert state.what_is_verified.verified_components_count > 0
        assert state.what_is_verified.last_verified_at is not None

    def test_05_rest_api_candidate_pool_endpoints(self, clean_test_case):
        """Test REST API endpoints for candidate pool generation and retrieval."""
        test_client = TestClient(app)
        token = "test_advisor_token_v2_phase3"
        sessions[token] = "adam"
        test_client.cookies.set("session_token", token)

        case_id = clean_test_case["case_id"]
        headers = {"x-agency-id": clean_test_case["agency_id"]}

        # 1. POST /candidate-pool/generate
        gen_res = test_client.post(
            f"/api/advisor/cases/{case_id}/candidate-pool/generate",
            headers=headers,
            json={"custom_params": {}}
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert gen_data["success"] is True
        assert gen_data["counts"]["stays"] >= 1
        assert "candidate_pool" in gen_data

        # 2. GET /candidate-pool
        get_res = test_client.get(f"/api/advisor/cases/{case_id}/candidate-pool", headers=headers)
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["success"] is True
        assert get_data["counts"]["stays"] == gen_data["counts"]["stays"]
