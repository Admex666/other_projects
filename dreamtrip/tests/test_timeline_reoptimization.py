"""
Unit and Integration Tests for Timeline, Feedback & Re-Optimization Service (Phase 9)
=====================================================================================
Verifies:
1. Audit event logging and reverse chronological ordering.
2. Structured client feedback capture with sentiment.
3. 1-click re-optimization generating Proposal v2 with modified constraints.
4. REST API endpoints for timeline, manual notes, feedback, and re-optimization.
"""

import pytest
from app.services.timeline_reoptimization_service import TimelineReoptimizationService
from app.services.proposal_service import ProposalService
from app.models.advisor_models import TripCase, Client, ResolvedTripPreferences, TripCaseStatus
from app.routers.advisor_api import router, CASES_STORE, CLIENTS_STORE, PROPOSALS_STORE
from app.services.advisor_orchestration_service import AdvisorOrchestrationService
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestTimelineReoptimization:

    @pytest.fixture
    def mock_candidates(self):
        return [
            {
                "id": "cand_1",
                "title": "Nice Balanced Stay & Flight",
                "total_price_huf": 350000,
                "price_per_person_huf": 175000,
                "flight": {"airline": "Wizz Air", "stops": 0, "duration_minutes": 130},
                "stay": {"name": "Hotel Le Negresco", "stars": 5, "rating_normalized": 9.2},
                "destination": {"city": "Nizza", "country": "Franciaország"},
                "why_this_option": "Kiváló elhelyezkedés a tengerparton.",
                "tradeoffs": []
            },
            {
                "id": "cand_2",
                "title": "Nice Budget Hotel & Flight",
                "total_price_huf": 220000,
                "price_per_person_huf": 110000,
                "flight": {"airline": "Ryanair", "stops": 0, "duration_minutes": 135},
                "stay": {"name": "Ibis Centre", "stars": 3, "rating_normalized": 8.0},
                "destination": {"city": "Nizza", "country": "Franciaország"},
                "why_this_option": "Legjobb ár-érték arány.",
                "tradeoffs": []
            }
        ]

    def test_timeline_event_logging_and_retrieval(self):
        """Verifies chronological event logging and audit integrity."""
        case_id = "case_timeline_test_1"
        
        # Log 2 events
        e1 = TimelineReoptimizationService.log_event(
            case_id=case_id,
            event_type="BRIEF_RECORDED",
            title="Brief Rögzítve",
            description="Ügyfél 400.000 Ft büdzsével indul."
        )
        e2 = TimelineReoptimizationService.log_event(
            case_id=case_id,
            event_type="RESEARCH_EXECUTED",
            title="Kutatás Lefutott",
            description="12 járat és 8 hotel jelölt találat."
        )

        events = TimelineReoptimizationService.get_case_timeline(case_id)
        assert len(events) >= 2
        assert events[0]["id"] == e2["id"]  # Most recent first

    def test_client_feedback_recording(self):
        """Verifies recording structured feedback against proposal."""
        case_id = "case_feedback_test"
        prop_id = "prop_fb_1"

        feedback = TimelineReoptimizationService.record_feedback(
            case_id=case_id,
            proposal_id=prop_id,
            feedback_category="hotel_change",
            feedback_text="A szálloda túl messze van a központtól, kérünk közelebbit.",
            client_sentiment="CRITICAL"
        )

        assert feedback["feedback_category"] == "hotel_change"
        assert feedback["client_sentiment"] == "CRITICAL"

        # Verify an event was logged in timeline
        timeline = TimelineReoptimizationService.get_case_timeline(case_id)
        assert any(evt["event_type"] == "CLIENT_FEEDBACK" for evt in timeline)

    def test_execute_reoptimization_creates_v2(self, mock_candidates):
        """Verifies 1-click reoptimization generates v2 and updates state."""
        trip_case = TripCase(
            id="case_reopt_unit",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_reopt_unit",
            title="Nizza Reopt Unit",
            destination_focus="Nizza",
            total_budget_huf=400000
        )
        test_client = Client(
            id="client_reopt_unit",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            name="Varga Zoltán",
            email="zoltan.varga@example.com"
        )

        base_prop = ProposalService.create_proposal(
            trip_case=trip_case,
            client=test_client,
            options=mock_candidates
        )
        assert base_prop["version"] == 1

        # Execute re-optimization with tighter budget
        result = TimelineReoptimizationService.execute_reoptimization(
            trip_case=trip_case,
            client=test_client,
            base_proposal=base_prop,
            candidates_pool=mock_candidates,
            constraint_overrides={"total_budget_huf": 300000},
            reoptimization_reason="Ügyfél alacsonyabb árat kért"
        )

        assert result["status"] == "success"
        assert result["version"] == 2
        assert result["new_proposal"]["version"] == 2
        assert trip_case.total_budget_huf == 300000

        # Check timeline event
        timeline = TimelineReoptimizationService.get_case_timeline("case_reopt_unit")
        assert any(evt["event_type"] == "REOPTIMIZATION_EXECUTED" for evt in timeline)

    def test_api_timeline_and_reoptimization_lifecycle(self, mock_candidates):
        """Tests full REST API endpoints for timeline, feedback, manual note, and re-optimization."""
        case_id = "case_api_timeline"
        client_id = "client_api_timeline"

        test_client = Client(
            id=client_id,
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            name="Németh Éva",
            email="eva.nemeth@example.com"
        )
        CLIENTS_STORE[client_id] = test_client

        test_case = TripCase(
            id=case_id,
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id=client_id,
            title="Németh Éva Nizza Tervezés",
            destination_focus="Nizza",
            total_budget_huf=450000
        )
        CASES_STORE[case_id] = test_case
        AdvisorOrchestrationService._CANDIDATES_POOL[case_id] = mock_candidates

        # 1. Base proposal v1
        base_prop = ProposalService.create_proposal(
            trip_case=test_case,
            client=test_client,
            options=mock_candidates
        )
        PROPOSALS_STORE[base_prop["id"]] = base_prop

        # 2. GET /cases/{id}/timeline
        get_res = client.get(f"/api/advisor/cases/{case_id}/timeline")
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "success"

        # 3. POST /cases/{id}/timeline (Manual Note)
        note_res = client.post(f"/api/advisor/cases/{case_id}/timeline", json={
            "event_type": "MANUAL_NOTE",
            "title": "Ügyfél Hívás",
            "description": "Beszéltünk Évával, örül az ajánlatnak."
        })
        assert note_res.status_code == 201
        assert note_res.json()["event"]["title"] == "Ügyfél Hívás"

        # 4. POST /cases/{id}/feedback
        fb_res = client.post(f"/api/advisor/cases/{case_id}/feedback", json={
            "proposal_id": base_prop["id"],
            "feedback_category": "hotel_change",
            "feedback_text": "A hotel tetszik, de 4 csillagos elég lenne.",
            "client_sentiment": "POSITIVE"
        })
        assert fb_res.status_code == 201
        assert CASES_STORE[case_id].status == TripCaseStatus.REVISION

        # 5. POST /cases/{id}/reoptimize (1-click reoptimization)
        reopt_res = client.post(f"/api/advisor/cases/{case_id}/reoptimize", json={
            "proposal_id": base_prop["id"],
            "reoptimization_reason": "4 csillagos hotel keresése",
            "constraint_overrides": {"total_budget_huf": 380000}
        })
        assert reopt_res.status_code == 200
        reopt_data = reopt_res.json()
        assert reopt_data["version"] == 2
        assert reopt_data["proposal"]["version"] == 2
        assert reopt_data["new_proposal_id"] in PROPOSALS_STORE
