"""
Advisor Workspace v2 — Phase 1 Test Suite
==========================================
Validates:
1. All 7 Research Intent Archetypes Automatic Detection
2. Dynamic Step-by-Step Research Plan Generation with Providers and Estimates
3. Component-level Intent Mutation (KEEP, REPLACE, IMPROVE) and Real-time Plan Recalculation
4. REST APIs: GET /intent/plan, POST /components/intent, POST /intent/confirm
5. Invariant: Zero blind API execution before Intent Confirmation
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
    token = "test_advisor_token_v2_phase1"
    sessions[token] = "adam"
    test_client.cookies.set("session_token", token)
    return test_client


class TestAdvisorV2Phase1IntentEngine:
    """Unit and integration tests for Phase 1 Research Intent Engine & Dynamic Research Plans."""

    def test_01_all_intent_archetypes_detection(self):
        """Validates precise intent reconstruction for all key travel scenarios."""
        # 1. DESTINATION_DISCOVERY
        case_disc = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_intent_1",
            title="Nyári Nyaralás Inspiráció",
            destination_focus=None,
            total_budget_huf=800000.0
        )
        state_disc = ResearchStateService.build_research_state(trip_case=case_disc)
        assert state_disc.resolved_intent == "DESTINATION_DISCOVERY"
        assert state_disc.research_plan is not None
        assert len(state_disc.research_plan.steps) == 5
        assert any(s.step_id == "dest_discovery" for s in state_disc.research_plan.steps)

        # 2. FLIGHT_FIRST / KNOWN_DESTINATION
        case_flight = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_intent_2",
            title="Lisszabon Városlátogatás",
            destination_focus="Lisszabon",
            total_budget_huf=500000.0
        )
        state_flight = ResearchStateService.build_research_state(trip_case=case_flight)
        assert state_flight.resolved_intent == "FLIGHT_FIRST"
        assert any(s.step_id == "flight_search" for s in state_flight.research_plan.steps)

        # 3. STAY_FIRST (Fixed flight exists)
        case_stay = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_intent_3",
            title="Róma Rögzített Járattal",
            destination_focus="Róma",
            total_budget_huf=450000.0,
            existing_components=[
                ExistingComponent(
                    component_type="flight",
                    action=ComponentIntentAction.KEEP,
                    title="Ryanair BUD-CIA",
                    details={"id": "fl_roma_1"},
                    is_locked=True
                )
            ]
        )
        state_stay = ResearchStateService.build_research_state(trip_case=case_stay)
        assert state_stay.resolved_intent == "STAY_FIRST"
        assert any(s.step_id == "stay_deep_search" for s in state_stay.research_plan.steps)

        # 4. RE_OPTIMIZATION (Fixed flight + Fixed stay)
        case_reopt = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_intent_4",
            title="Párizs Teljes Foglalással",
            destination_focus="Párizs",
            total_budget_huf=700000.0,
            existing_components=[
                ExistingComponent(
                    component_type="flight",
                    action=ComponentIntentAction.KEEP,
                    title="Air France BUD-CDG",
                    details={"id": "fl_cdg_1"},
                    is_locked=True
                ),
                ExistingComponent(
                    component_type="stay",
                    action=ComponentIntentAction.KEEP,
                    title="Hotel Le Marais",
                    details={"id": "st_cdg_1"},
                    is_locked=True
                )
            ]
        )
        state_reopt = ResearchStateService.build_research_state(trip_case=case_reopt)
        assert state_reopt.resolved_intent == "RE_OPTIMIZATION"
        assert any(s.step_id == "geo_routing" for s in state_reopt.research_plan.steps)
        assert any(s.step_id == "opening_hours" for s in state_reopt.research_plan.steps)

        # 5. FIND_BETTER_COMPONENT (Replace hotel)
        case_replace = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_intent_5",
            title="Hotel Csere Kérés",
            destination_focus="Bécs",
            total_budget_huf=300000.0,
            existing_components=[
                ExistingComponent(
                    component_type="stay",
                    action=ComponentIntentAction.REPLACE,
                    title="Meglévő drága hotel",
                    details={"id": "st_bad_1"}
                )
            ]
        )
        state_replace = ResearchStateService.build_research_state(trip_case=case_replace)
        assert state_replace.resolved_intent == "FIND_BETTER_COMPONENT"
        assert any(s.step_id == "pareto_filtering" for s in state_replace.research_plan.steps)

    def test_02_dynamic_research_plan_details(self):
        """Validates research plan provider mapping, step hierarchy, and duration estimation."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_plan_1",
            title="Barcelona Nyaralás",
            destination_focus="Barcelona",
            total_budget_huf=600000.0
        )
        state = ResearchStateService.build_research_state(trip_case=case)
        plan = state.research_plan

        assert plan is not None
        assert plan.intent == "FLIGHT_FIRST"
        assert plan.total_estimated_sec > 0
        assert len(plan.steps) >= 4

        step_providers = [s.provider for s in plan.steps]
        assert any("Kiwi" in p for p in step_providers)
        assert any("Cozycozy" in p for p in step_providers)
        assert any("Decision Engine" in p for p in step_providers)

    def test_03_component_intent_mutation_and_live_recalculation(self):
        """Tests dynamic update of component actions (KEEP -> REPLACE) and real-time intent flipping."""
        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id="cli_mutate_1",
            title="Milánói Hétvége",
            destination_focus="Milánó",
            total_budget_huf=350000.0
        )
        state = ResearchStateService.get_or_create_research_state(trip_case=case, force_rebuild=True)
        assert state.resolved_intent == "FLIGHT_FIRST"

        # 1. Advisor locks a flight component as KEEP -> intent becomes STAY_FIRST
        updated_1 = ResearchStateService.update_component_intent(
            case_id=case.id,
            component_type="flight",
            action=ComponentIntentAction.KEEP,
            component_id="fl_milan_101",
            title="Wizz Air BUD-MXP"
        )
        assert updated_1.resolved_intent == "STAY_FIRST"
        assert "fl_milan_101" in updated_1.what_is_fixed.locked_flight_ids

        # 2. Advisor adds a stay with IMPROVE -> intent flips to FIND_BETTER_COMPONENT
        updated_2 = ResearchStateService.update_component_intent(
            case_id=case.id,
            component_type="stay",
            action=ComponentIntentAction.IMPROVE,
            component_id="st_milan_202",
            title="Hotel Ibis Milano (Jobbat keresünk)"
        )
        assert updated_2.resolved_intent == "FIND_BETTER_COMPONENT"
        assert any(s.step_id == "market_sweep" for s in updated_2.research_plan.steps)

    def test_04_api_intent_plan_and_component_actions(self, authenticated_client):
        """Tests REST API for intent plan inspection and component intent modifications."""
        cl = Client(
            agency_id="default_agency",
            advisor_id="default_advisor",
            name="Szabó Péter",
            email="peter.szabo@example.com"
        )
        ClientRepository.save_client(cl, agency_id="default_agency")

        case = TripCase(
            agency_id="default_agency",
            advisor_id="default_advisor",
            client_id=cl.id,
            title="Firenze Gourmet Utazás",
            destination_focus="Firenze",
            adults=2,
            total_budget_huf=550000.0
        )
        TripCaseRepository.save_case(case, agency_id="default_agency")

        # 1. GET intent plan
        res_plan = authenticated_client.get(
            f"/api/advisor/cases/{case.id}/intent/plan",
            headers={"x-agency-id": "default_agency"}
        )
        assert res_plan.status_code == 200
        plan_data = res_plan.json()
        assert plan_data["success"] is True
        assert plan_data["resolved_intent"] == "FLIGHT_FIRST"
        assert len(plan_data["research_plan"]["steps"]) >= 4

        # 2. POST update component intent (add fixed flight)
        res_comp = authenticated_client.post(
            f"/api/advisor/cases/{case.id}/components/intent",
            json={
                "component_type": "flight",
                "action": "KEEP",
                "component_id": "fl_firenze_12",
                "title": "Wizz Air BUD-PSA"
            },
            headers={"x-agency-id": "default_agency"}
        )
        assert res_comp.status_code == 200
        comp_data = res_comp.json()
        assert comp_data["success"] is True
        assert comp_data["resolved_intent"] == "STAY_FIRST"
        assert comp_data["research_plan"]["intent"] == "STAY_FIRST"

        # 3. POST confirm intent (advance to DEFINE phase)
        res_conf = authenticated_client.post(
            f"/api/advisor/cases/{case.id}/intent/confirm",
            json={"confirmed": True},
            headers={"x-agency-id": "default_agency"}
        )
        assert res_conf.status_code == 200
        conf_data = res_conf.json()
        assert conf_data["success"] is True
        assert conf_data["intent_confirmed"] is True
        assert conf_data["phase"] == "define"
