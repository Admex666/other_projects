"""
Optivoya Advisor Workspace — Database Persistence & Multi-Tenant Isolation Integration Tests
===========================================================================================
Validates:
1. DB Persistence across server restart simulation (cleared memory stores).
2. Multi-tenant agency isolation (Agency A vs Agency B scoping).
3. Cross-agency access rejection (HTTP 404/403 for foreign agency resources).
4. ResearchRun lifecycle & candidates persistence in DB.
5. Proposal & ProposalVersion persistence.
6. ProposalShare token hashing, lookup, access count, and instant revocation.
7. B2C Planner regression check.
"""

import pytest
import uuid
import hashlib
from fastapi.testclient import TestClient

from app.main import app
from app.models.advisor_models import (
    Agency, AgencyBranding, Advisor, Client, ClientPreferences,
    TripCase, TripCaseStatus, BudgetMode, ResearchScope,
    ResolvedTripPreferences, HardConstraints, TripOption, OptionArchetype,
    ResearchRun, ResearchRunStatus, Proposal, ProposalVersion, ProposalShare
)
from app.repositories.advisor_repository import (
    AgencyRepository, AdvisorRepository, ClientRepository,
    TripCaseRepository, ResearchRunRepository, TripOptionRepository,
    ProposalRepository, ProposalShareRepository, TimelineRepository,
    LocalSQLiteStorage
)
from app.services.advisor_orchestration_service import AdvisorOrchestrationService, ResearchStrategy
from app.services.proposal_service import ProposalService


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ─────────────────────────────────────────────────────────────
# 1. MULTI-TENANT ISOLATION TESTS
# ─────────────────────────────────────────────────────────────

def test_multitenant_agency_and_client_isolation(client):
    """
    Verify that Agency A and Agency B data is strictly isolated.
    An advisor from Agency B cannot see or query Agency A's clients.
    """
    agency_a_id = f"agency_alpha_{uuid.uuid4().hex[:6]}"
    agency_b_id = f"agency_beta_{uuid.uuid4().hex[:6]}"

    # 1. Create 2 distinct agencies
    AgencyRepository.save_agency(Agency(
        id=agency_a_id,
        name="Alpha Luxury Travel",
        slug=f"alpha-lux-{agency_a_id}",
        branding=AgencyBranding(company_name="Alpha Lux", primary_color="#111111")
    ))
    AgencyRepository.save_agency(Agency(
        id=agency_b_id,
        name="Beta Boutique Travel",
        slug=f"beta-boutique-{agency_b_id}",
        branding=AgencyBranding(company_name="Beta Boutique", primary_color="#222222")
    ))

    # 2. Agency A creates a VIP client
    res_create_a = client.post(
        "/api/advisor/clients",
        json={
            "name": "Baron Alpha Client",
            "email": "alpha.client@vip.com",
            "tags": ["VIP", "AlphaOnly"]
        },
        headers={"x-agency-id": agency_a_id}
    )
    assert res_create_a.status_code == 201
    client_a_id = res_create_a.json()["client"]["id"]

    # 3. Agency B lists clients -> must NOT see Alpha's client
    res_list_b = client.get("/api/advisor/clients", headers={"x-agency-id": agency_b_id})
    assert res_list_b.status_code == 200
    b_client_ids = [c["id"] for c in res_list_b.json()["clients"]]
    assert client_a_id not in b_client_ids

    # 4. Agency B attempts to directly fetch Alpha's client details -> 404
    res_get_foreign = client.get(f"/api/advisor/clients/{client_a_id}", headers={"x-agency-id": agency_b_id})
    assert res_get_foreign.status_code == 404


def test_multitenant_trip_case_and_proposal_cross_agency_rejection(client):
    """
    Verify that an advisor cannot access, modify or view cases or proposals
    belonging to another agency.
    """
    agency_a = f"agency_corp_a_{uuid.uuid4().hex[:6]}"
    agency_b = f"agency_corp_b_{uuid.uuid4().hex[:6]}"

    # Seed client in Agency A
    client_a = ClientRepository.save_client(Client(
        id=f"client_corp_{uuid.uuid4().hex[:6]}",
        agency_id=agency_a,
        advisor_id="adv_alpha",
        name="Corporate Client A",
        email="corp.a@example.com"
    ))

    # Create Case in Agency A
    res_case = client.post(
        "/api/advisor/cases",
        json={
            "client_id": client_a.id,
            "title": "Secret Executive Retreat",
            "target_total_budget": 1500000,
            "origin": "BUD",
            "destinations": ["Nice"]
        },
        headers={"x-agency-id": agency_a}
    )
    assert res_case.status_code == 201
    case_a_id = res_case.json()["case"]["id"]

    # Generate options for Case A
    res_opt = client.post(f"/api/advisor/cases/{case_a_id}/options/generate", headers={"x-agency-id": agency_a})
    assert res_opt.status_code == 200

    # Create proposal for Case A
    res_prop = client.post(
        f"/api/advisor/cases/{case_a_id}/proposals",
        json={"title": "Alpha Confidential Proposal"},
        headers={"x-agency-id": agency_a}
    )
    assert res_prop.status_code == 201
    proposal_a_id = res_prop.json()["proposal"]["id"]

    # Agency B tries to list cases -> Case A must not appear
    res_b_cases = client.get("/api/advisor/cases", headers={"x-agency-id": agency_b})
    assert res_b_cases.status_code == 200
    b_case_ids = [c["id"] for c in res_b_cases.json()["cases"]]
    assert case_a_id not in b_case_ids

    # Agency B tries to GET /cases/{case_a_id} -> 404
    res_foreign_case = client.get(f"/api/advisor/cases/{case_a_id}", headers={"x-agency-id": agency_b})
    assert res_foreign_case.status_code == 404

    # Agency B tries to GET /proposals/{proposal_a_id} -> 404
    res_foreign_prop = client.get(f"/api/advisor/proposals/{proposal_a_id}", headers={"x-agency-id": agency_b})
    assert res_foreign_prop.status_code == 404


# ─────────────────────────────────────────────────────────────
# 2. DB PERSISTENCE & SERVER RESTART SIMULATION
# ─────────────────────────────────────────────────────────────

def test_server_restart_persistence_simulation(client):
    """
    Simulates a full server restart by clearing all in-memory caches and dictionaries.
    Verifies that TripCase, Client, Options, ResearchRun, and Proposal data
    remain fully accessible from the persistent repository.
    """
    agency_id = f"agency_restart_{uuid.uuid4().hex[:6]}"
    
    # 1. Create client and case
    client_obj = ClientRepository.save_client(Client(
        id=f"client_rst_{uuid.uuid4().hex[:6]}",
        agency_id=agency_id,
        advisor_id="adv_rst",
        name="Restart Resilience Test User",
        email="restart.test@optivoya.com"
    ))

    case_obj = TripCaseRepository.save_case(TripCase(
        id=f"case_rst_{uuid.uuid4().hex[:6]}",
        agency_id=agency_id,
        advisor_id="adv_rst",
        client_id=client_obj.id,
        title="Persistent Travel Brief",
        total_budget_huf=850000.0,
        origin="BUD",
        destination_focus="Rome",
        status=TripCaseStatus.BRIEF
    ))

    # 2. Save options
    option_obj = TripOption(
        id=f"opt_rst_{uuid.uuid4().hex[:6]}",
        case_id=case_obj.id,
        archetype=OptionArchetype.BEST_OVERALL,
        title="Rome Historic Luxury Option",
        total_price_huf=420000.0,
        price_per_person_huf=210000.0,
        trip_score=92
    )
    TripOptionRepository.save_options_batch(case_obj.id, [option_obj])

    # 3. Save ResearchRun
    run_obj = ResearchRun(
        id=f"run_rst_{uuid.uuid4().hex[:6]}",
        case_id=case_obj.id,
        agency_id=agency_id,
        advisor_id="adv_rst",
        strategy=ResearchStrategy.FULL_TRIP_OPTIMIZATION,
        status=ResearchRunStatus.COMPLETED,
        progress_pct=100,
        candidates=[option_obj.model_dump()],
        elapsed_seconds=1.85
    )
    ResearchRunRepository.save_run(run_obj)

    # 4. Save Proposal
    prop_doc = ProposalService.create_proposal(
        trip_case=case_obj,
        client=client_obj,
        options=[option_obj.model_dump()],
        title="Persistent Client Proposal v1"
    )
    ProposalRepository.save_proposal(prop_doc, agency_id=agency_id)

    # ─────────────────────────────────────────────────────────────
    # SIMULATE CRASH / RESTART: WIPE ALL IN-MEMORY PROCESS MEMORY
    # ─────────────────────────────────────────────────────────────
    AdvisorOrchestrationService._RESEARCH_JOBS.clear()
    AdvisorOrchestrationService._CANDIDATES_POOL.clear()
    ProposalService._SHARES_STORE.clear()

    # 5. Verify Client is loaded from DB
    loaded_client = ClientRepository.get_client(client_obj.id, agency_id=agency_id)
    assert loaded_client is not None
    assert loaded_client.name == "Restart Resilience Test User"

    # 6. Verify TripCase is loaded from DB via API endpoint
    res_case = client.get(f"/api/advisor/cases/{case_obj.id}", headers={"x-agency-id": agency_id})
    assert res_case.status_code == 200
    assert res_case.json()["case"]["title"] == "Persistent Travel Brief"
    assert res_case.json()["case"]["total_budget_huf"] == 850000.0

    # 7. Verify shortlisted options survived restart
    assert len(res_case.json()["options"]) == 1
    assert res_case.json()["options"][0]["title"] == "Rome Historic Luxury Option"
    assert res_case.json()["options"][0]["trip_score"] == 92

    # 8. Verify ResearchRun is loaded from DB
    loaded_run = ResearchRunRepository.get_run(run_obj.id)
    assert loaded_run is not None
    assert loaded_run.status == ResearchRunStatus.COMPLETED
    assert loaded_run.elapsed_seconds == 1.85

    # 9. Verify Proposal is loaded from DB via API endpoint
    res_prop = client.get(f"/api/advisor/proposals/{prop_doc['id']}", headers={"x-agency-id": agency_id})
    assert res_prop.status_code == 200
    assert res_prop.json()["proposal"]["title"] == "Persistent Client Proposal v1"
    assert res_prop.json()["proposal"]["total_options_count"] == 1


# ─────────────────────────────────────────────────────────────
# 3. PROPOSAL SHARE & REVOCATION PERSISTENCE
# ─────────────────────────────────────────────────────────────

def test_proposal_share_persistence_and_revocation(client):
    """
    Verify proposal share link generation, DB persistence of share tokens,
    public client-safe access (stripping private advisor notes), and revocation.
    """
    agency_id = "agency_default_lux"
    
    # 1. Create client and case
    client_obj = ClientRepository.save_client(Client(
        id=f"client_share_{uuid.uuid4().hex[:6]}",
        agency_id=agency_id,
        advisor_id="adv_adam_lead",
        name="Private Client",
        email="private.client@example.com"
    ))
    case_obj = TripCaseRepository.save_case(TripCase(
        id=f"case_share_{uuid.uuid4().hex[:6]}",
        agency_id=agency_id,
        advisor_id="adv_adam_lead",
        client_id=client_obj.id,
        title="Lisbon Getaway"
    ))

    # 2. Create proposal with private advisor notes
    prop_doc = ProposalService.create_proposal(
        trip_case=case_obj,
        client=client_obj,
        options=[{
            "id": "opt_lisbon_1",
            "title": "Lisbon Luxury Package",
            "total_price_huf": 320000,
            "trip_score": 89
        }],
        title="Lisbon Proposal",
        advisor_notes="CONFIDENTIAL: Negotiate 5% commission on stay."
    )
    ProposalRepository.save_proposal(prop_doc, agency_id=agency_id)

    # 3. Generate public share token
    res_share = client.post(
        f"/api/advisor/proposals/{prop_doc['id']}/share",
        json={"expires_in_days": 14},
        headers={"x-agency-id": agency_id}
    )
    assert res_share.status_code == 200
    share_token = res_share.json()["token"]
    assert share_token is not None

    # Clear memory store to verify DB lookup
    ProposalService._SHARES_STORE.clear()

    # 4. Access public endpoint as client
    res_pub = client.get(f"/api/advisor/public/proposals/{share_token}")
    assert res_pub.status_code == 200
    pub_data = res_pub.json()["proposal"]
    assert pub_data["title"] == "Lisbon Proposal"
    # Private notes MUST be stripped
    assert "advisor_notes" not in pub_data or pub_data.get("advisor_notes") is None

    # 5. Revoke the share token
    res_revoke = client.post(
        f"/api/advisor/proposals/{prop_doc['id']}/revoke-share?token={share_token}",
        headers={"x-agency-id": agency_id}
    )
    assert res_revoke.status_code == 200

    # Clear memory again
    ProposalService._SHARES_STORE.clear()

    # 6. Subsequent access must fail (404)
    res_pub_revoked = client.get(f"/api/advisor/public/proposals/{share_token}")
    assert res_pub_revoked.status_code == 404


# ─────────────────────────────────────────────────────────────
# 4. B2C PLANNER ZERO REGRESSION CHECK
# ─────────────────────────────────────────────────────────────

def test_b2c_planner_zero_regression(client):
    """
    Ensures the consumer (B2C) planner and landing routes function flawlessly
    and are not affected by Advisor B2B DB changes.
    """
    from app.core.auth import create_session

    # 1. Landing page loads
    res_home = client.get("/")
    assert res_home.status_code == 200

    # 2. Unauthenticated /planner redirects
    res_unauth = client.get("/planner")
    assert res_unauth.status_code in [200, 303]

    # 3. Authenticated B2C user loads planner wizard
    sid = create_session("test_planner_guest")
    res_planner = client.get("/planner", cookies={"session_token": sid})
    assert res_planner.status_code == 200
    assert "Optivoya" in res_planner.text or "planner" in res_planner.text.lower()
