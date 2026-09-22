"""
Unit and Integration Tests for Multi-Option Proposal Service (Phase 8)
======================================================================
Verifies:
1. Proposal creation with 1-3 shortlisted options and default metadata.
2. Proposal editing (title, personal intro, private advisor notes, option toggles).
3. Proposal versioning (v1 -> v2 branch creation).
4. REST API endpoints and printable HTML preview rendering.
"""

import pytest
from app.services.proposal_service import ProposalService
from app.models.advisor_models import TripCase, Client, ResolvedTripPreferences
from app.routers.advisor_api import router, CASES_STORE, CLIENTS_STORE, OPTIONS_STORE, PROPOSALS_STORE
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestProposalService:

    @pytest.fixture
    def mock_options(self):
        return [
            {
                "id": "opt_a",
                "archetype": "best_overall",
                "title": "Barcelona Balanced Premium",
                "total_price_huf": 320000,
                "price_per_person_huf": 160000,
                "flight": {"airline": "Wizz Air", "stops": 0, "duration_minutes": 140},
                "stay": {"name": "Hotel Arts Barcelona", "stars": 4, "rating_normalized": 8.9},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "why_this_option": "Kiváló ár-érték arány és közvetlen járat.",
                "tradeoffs": []
            },
            {
                "id": "opt_b",
                "archetype": "best_value",
                "title": "Barcelona Budget Smart",
                "total_price_huf": 210000,
                "price_per_person_huf": 105000,
                "flight": {"airline": "Ryanair", "stops": 0, "duration_minutes": 145},
                "stay": {"name": "Hostal Jazz", "stars": 3, "rating_normalized": 8.2},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "why_this_option": "Legkedvezőbb ár.",
                "tradeoffs": []
            },
            {
                "id": "opt_c",
                "archetype": "best_experience",
                "title": "Barcelona Luxury & Deep Culture",
                "total_price_huf": 460000,
                "price_per_person_huf": 230000,
                "flight": {"airline": "Iberia", "stops": 0, "duration_minutes": 140},
                "stay": {"name": "Mandarin Oriental", "stars": 5, "rating_normalized": 9.5},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "why_this_option": "Exkluzív 5 csillagos luxus.",
                "tradeoffs": []
            }
        ]

    def test_proposal_service_creation_and_update(self, mock_options):
        """Tests core proposal service initialization and subsequent edit mutations."""
        trip_case = TripCase(
            id="case_prop_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_prop_test",
            title="Barcelona Proposal Test Case",
            destination_focus="Barcelona",
            total_budget_huf=400000
        )
        test_client = Client(
            id="client_prop_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            name="Kovács Péter",
            email="peter.kovacs@example.com"
        )

        # 1. Create Proposal v1
        proposal = ProposalService.create_proposal(
            trip_case=trip_case,
            client=test_client,
            options=mock_options,
            title="Egyedi Ajánlat: Barcelona",
            advisor_notes="Ügyfél a központi elhelyezkedést preferálja."
        )

        assert proposal["version"] == 1
        assert proposal["title"] == "Egyedi Ajánlat: Barcelona"
        assert proposal["client_name"] == "Kovács Péter"
        assert len(proposal["options_snapshot"]) == 3
        assert proposal["advisor_notes"] == "Ügyfél a központi elhelyezkedést preferálja."

        # 2. Update Proposal
        updated = ProposalService.update_proposal(
            proposal=proposal,
            title="Módosított Ajánlat: Barcelona",
            selected_option_ids=["opt_a", "opt_c"] # Exclude opt_b
        )

        assert updated["title"] == "Módosított Ajánlat: Barcelona"
        assert updated["total_options_count"] == 2
        assert "opt_b" not in updated["selected_option_ids"]

    def test_proposal_service_versioning(self, mock_options):
        """Tests branching a new version (v1 -> v2) with modified options."""
        trip_case = TripCase(
            id="case_ver_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_ver_test",
            title="Versioning Test Case"
        )
        test_client = Client(
            id="client_ver_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            name="Szabó Anna",
            email="szabo.anna@example.com"
        )

        # Base v1
        v1 = ProposalService.create_proposal(
            trip_case=trip_case,
            client=test_client,
            options=mock_options
        )
        assert v1["version"] == 1

        # Branch v2 with only 2 options
        v2 = ProposalService.create_next_version(
            base_proposal=v1,
            updated_options=mock_options[:2],
            reason="Ügyfél a budget és balanced opciókat kérte"
        )

        assert v2["version"] == 2
        assert v2["id"] != v1["id"]
        assert len(v2["options_snapshot"]) == 2
        assert "v2 Módosítás" in v2["advisor_notes"]

    def test_api_proposals_full_lifecycle(self, mock_options):
        """Tests full REST API lifecycle: Create -> List -> Get -> Put -> Branch -> Preview."""
        # 1. Setup Client, Case, and Options
        test_client = Client(
            id="client_api_prop",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            name="Tóth Júlia",
            email="julia.toth@example.com"
        )
        CLIENTS_STORE["client_api_prop"] = test_client

        test_case = TripCase(
            id="case_api_prop",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_api_prop",
            title="Tóth Júlia Barcelona Ajánlat",
            total_budget_huf=500000
        )
        CASES_STORE["case_api_prop"] = test_case
        OPTIONS_STORE["case_api_prop"] = mock_options

        # 2. POST /cases/{case_id}/proposals
        create_res = client.post("/api/advisor/cases/case_api_prop/proposals", json={
            "title": "Tóth Júlia — Prémium Barcelona Ajánlat",
            "client_intro": "Kedves Júlia, összeállítottuk az utazási opciókat.",
            "advisor_notes": "Belső margin: 12%"
        })
        assert create_res.status_code == 201
        prop_data = create_res.json()["proposal"]
        prop_id = prop_data["id"]
        assert prop_data["version"] == 1
        assert prop_data["title"] == "Tóth Júlia — Prémium Barcelona Ajánlat"

        # 3. GET /cases/{case_id}/proposals
        list_res = client.get("/api/advisor/cases/case_api_prop/proposals")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 4. GET /proposals/{proposal_id}
        get_res = client.get(f"/api/advisor/proposals/{prop_id}")
        assert get_res.status_code == 200
        assert get_res.json()["proposal"]["id"] == prop_id

        # 5. PUT /proposals/{proposal_id}
        put_res = client.put(f"/api/advisor/proposals/{prop_id}", json={
            "title": "Tóth Júlia — Véglegesített Ajánlat",
            "status": "SENT"
        })
        assert put_res.status_code == 200
        assert put_res.json()["proposal"]["status"] == "SENT"

        # 6. POST /proposals/{proposal_id}/new-version
        branch_res = client.post(f"/api/advisor/proposals/{prop_id}/new-version", json={
            "reason": "Ügyfél új időpontot kért"
        })
        assert branch_res.status_code == 200
        v2_data = branch_res.json()["proposal"]
        assert v2_data["version"] == 2
        v2_id = v2_data["id"]

        # 7. GET /proposals/{proposal_id}/preview (HTML print view)
        preview_res = client.get(f"/api/advisor/proposals/{v2_id}/preview")
        assert preview_res.status_code == 200
        assert "text/html" in preview_res.headers.get("content-type", "")
        html_text = preview_res.text
        assert "Optivoya" in html_text
        assert "Tóth Júlia" in html_text or "Barcelona" in html_text
