"""
Advisor Workspace v2 — Phase 0 Test Suite
==========================================
Validates:
1. ResearchState Domain Models & Defaults
2. "Mi van / Mi nincs?" Missing Info Matrix Evaluation
3. Intent Confirmation & Phase State Transitions (UNDERSTAND -> DEFINE)
4. Existing Components Detection & Re-optimization Intent
5. REST API Endpoints: GET /research-state, POST /intent/confirm, POST /research-state/update
6. Dual Version Routing (/advisor vs /advisor/v1)
"""

import pytest
from starlette.testclient import TestClient
from app.main import app, sessions
from app.models.advisor_models import (
    TripCase, Client, ResearchState, ResearchStatePhase,
    ComponentIntentAction, ExistingComponent
)
from app.services.research_state_service import ResearchStateService
from app.repositories.advisor_repository import TripCaseRepository, ClientRepository


@pytest.fixture
def authenticated_client():
    test_client = TestClient(app)
    token = "test_advisor_token_v2_phase0"
    sessions[token] = "adam"
    test_client.cookies.set("session_token", token)
    return test_client


class TestAdvisorV2Phase0ResearchState:
    """Unit and integration tests for Phase 0 ResearchState & Dual-Version Architecture."""

    def test_01_research_state_model_structure(self):
        """Validates ResearchState domain model serialization and defaults."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_test_1",
            title="Tokyo Luxus Utazás",
            destination_focus="Tokió",
            adults=2,
            children=1,
            total_budget_huf=1500000.0,
            date_mode="exact",
            out_date="2026-10-10",
            in_date="2026-10-20",
            duration_days=10
        )
        state = ResearchStateService.build_research_state(trip_case=case)

        assert state.case_id == case.id
        assert state.phase == ResearchStatePhase.UNDERSTAND
        assert state.what_we_know.adults == 2
        assert state.what_we_know.children == 1
        assert state.what_we_know.travelers_count == 3
        assert state.what_we_know.total_budget == 1500000.0
        assert state.what_is_fixed.locked_dates is True
        assert state.what_is_fixed.locked_destination == "Tokió"
        assert state.resolved_intent == "FLIGHT_FIRST"
        assert "Tokió" in state.intent_summary

    def test_02_missing_info_matrix_evaluation(self):
        """Validates the 'Mi van / Mi nincs?' matrix generation."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_test_2",
            title="Nyitott Célpontú Nyaralás",
            destination_focus=None,
            adults=2,
            total_budget_huf=800000.0,
            date_mode="month"
        )
        state = ResearchStateService.build_research_state(trip_case=case)
        matrix = ResearchStateService.generate_missing_info_matrix(state)

        assert len(matrix) >= 6
        matrix_dict = {item.field_key: item for item in matrix}

        assert matrix_dict["destination"].has_value is False
        assert matrix_dict["destination"].urgency == "required"
        assert "40+ európai város" in matrix_dict["destination"].system_action

        assert matrix_dict["budget"].has_value is True
        assert "800 000" in matrix_dict["budget"].current_value_repr

        assert matrix_dict["flight"].has_value is False
        assert "Élő Kiwi GraphQL" in matrix_dict["flight"].system_action

    def test_03_intent_confirmation_and_phase_transition(self):
        """Tests that confirming intent advances phase from UNDERSTAND to DEFINE."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_test_3",
            title="Római Hétvége",
            destination_focus="Róma",
            adults=2,
            total_budget_huf=400000.0
        )
        state = ResearchStateService.get_or_create_research_state(trip_case=case, force_rebuild=True)
        assert state.phase == ResearchStatePhase.UNDERSTAND
        assert state.intent_confirmed is False

        updated_state = ResearchStateService.confirm_intent(case_id=case.id, confirmed=True)
        assert updated_state is not None
        assert updated_state.intent_confirmed is True
        assert updated_state.phase == ResearchStatePhase.DEFINE

    def test_04_existing_components_intent_detection(self):
        """Validates that existing fixed flight and stay trigger RE_OPTIMIZATION intent."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_test_4",
            title="Barcelona Meglévő Jegyekkel",
            destination_focus="Barcelona",
            adults=2,
            total_budget_huf=600000.0
        )
        # Attach existing flight and stay components
        case.existing_components = [
            ExistingComponent(
                component_type="flight",
                action=ComponentIntentAction.KEEP,
                title="Wizz Air BUD-BCN",
                details={"id": "fl_123"},
                is_locked=True
            ),
            ExistingComponent(
                component_type="stay",
                action=ComponentIntentAction.KEEP,
                title="Hotel Arts Barcelona",
                details={"id": "st_456"},
                is_locked=True
            )
        ]

        state = ResearchStateService.build_research_state(trip_case=case)
        assert state.resolved_intent == "RE_OPTIMIZATION"
        assert "fl_123" in state.what_is_fixed.locked_flight_ids
        assert "st_456" in state.what_is_fixed.locked_stay_ids

    def test_05_api_get_and_update_research_state(self, authenticated_client):
        """Tests REST API GET & POST for research-state and intent confirmation."""
        # Create test client & case in repository
        cl = Client(
            agency_id="default_agency",
            advisor_id="default_advisor",
            name="Kovács Anna",
            email="anna@example.com"
        )
        ClientRepository.save_client(cl, agency_id="default_agency")

        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id=cl.id,
            title="Párizsi Gourmet Hétvége",
            destination_focus="Párizs",
            adults=2,
            total_budget_huf=750000.0
        )
        TripCaseRepository.save_case(case, agency_id="default_agency")

        # 1. GET research-state
        res = authenticated_client.get(
            f"/api/advisor/cases/{case.id}/research-state",
            headers={"x-agency-id": "default_agency"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["research_state"]["case_id"] == case.id
        assert data["research_state"]["phase"] == "understand"
        assert len(data["missing_info_matrix"]) >= 6

        # 2. POST confirm intent
        confirm_res = authenticated_client.post(
            f"/api/advisor/cases/{case.id}/intent/confirm",
            json={"confirmed": True},
            headers={"x-agency-id": "default_agency"}
        )
        assert confirm_res.status_code == 200
        confirm_data = confirm_res.json()
        assert confirm_data["success"] is True
        assert confirm_data["research_state"]["intent_confirmed"] is True
        assert confirm_data["research_state"]["phase"] == "define"

    def test_06_dual_version_html_shell_routing(self, authenticated_client):
        """Verifies that /advisor serves v2 and /advisor/v1 serves legacy v1."""
        res_v2 = authenticated_client.get("/advisor")
        assert res_v2.status_code == 200
        assert "Optivoya Advisor Workspace v2" in res_v2.text or "workspace" in res_v2.text.lower()

        res_v1 = authenticated_client.get("/advisor/v1")
        assert res_v1.status_code == 200
        assert "v1" in res_v1.text or "Advisor Workspace" in res_v1.text
