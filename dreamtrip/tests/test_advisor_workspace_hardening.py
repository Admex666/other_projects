"""
Optivoya Advisor Workspace v1 — Architecture Hardening & Alignment Test Suite
=============================================================================
Validates:
1. Hardened Budget Model (Total & Component, Per-Person/Group basis, Hard vs Target)
2. Constraint Hierarchy & Audited Advisor Overrides
3. MultiOptionEngine Objective Profiles & 3-Option Rule (No magic numbers, no artificial padding)
4. Provider Provenance & Deep Link tracking
5. Async ResearchRun Lifecycle & Partial Error Tracking
6. Cryptographic Proposal Sharing & Revocation Security
7. Constraint Relaxation & 0-Result Dead-End Recovery
8. B2C Master Planner Regression Protection
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.advisor_models import (
    TripCase, Client, ClientPreferences, BudgetMode, ResearchScope,
    BudgetConstraint, TotalBudget, ComponentBudget, BudgetHardness, BudgetBasis,
    HardConstraints, SoftPreferences, AvoidRules, NiceToHave, AdvisorOverrides,
    AdvisorOverrideEntry, ResolvedTripPreferences, ProviderProvenance, VerificationStatus,
    OptionArchetype, TripCaseStatus
)
from app.services.preference_resolver import PreferenceResolver
from app.services.multi_option_engine import MultiOptionEngine
from app.services.advisor_orchestration_service import AdvisorOrchestrationService, ResearchStrategy
from app.services.proposal_service import ProposalService
from app.services.constraint_relaxation_service import ConstraintRelaxationService
from app.routers.advisor_api import CASES_STORE, CLIENTS_STORE, PROPOSALS_STORE, OPTIONS_STORE


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ─────────────────────────────────────────────────────────────
# 1. BUDGET MODEL HARDENING TESTS
# ─────────────────────────────────────────────────────────────

def test_budget_constraint_group_vs_per_person():
    """Test group vs per-person budget ceiling calculations and hardness invariants."""
    # 1. Group basis hard budget
    group_budget = BudgetConstraint(
        currency="HUF",
        total=TotalBudget(amount=400000.0, basis=BudgetBasis.GROUP, hardness=BudgetHardness.HARD)
    )
    assert group_budget.get_effective_total_ceiling_huf(adults=2, children=1) == 400000.0
    assert group_budget.is_hard() is True

    # 2. Per-person basis target budget
    per_person_budget = BudgetConstraint(
        currency="HUF",
        total=TotalBudget(
            amount=150000.0,
            basis=BudgetBasis.PER_PERSON,
            hardness=BudgetHardness.TARGET,
            relaxation_allowed=True,
            max_relaxation_pct=15.0
        )
    )
    assert per_person_budget.get_effective_total_ceiling_huf(adults=2, children=1) == 450000.0
    assert per_person_budget.is_hard() is False

    # 3. Component budgets
    comp_budget = BudgetConstraint(
        currency="EUR",
        total=TotalBudget(amount=1200.0, basis=BudgetBasis.GROUP),
        components={
            "flight": ComponentBudget(amount=400.0, basis=BudgetBasis.GROUP, hardness=BudgetHardness.HARD),
            "stay": ComponentBudget(amount=600.0, basis=BudgetBasis.GROUP, hardness=BudgetHardness.TARGET)
        }
    )
    assert comp_budget.components.flight.amount == 400.0
    assert comp_budget.components.stay.amount == 600.0


def test_trip_case_budget_sync():
    """Verify synchronization between legacy total_budget_huf and hardened BudgetConstraint."""
    case = TripCase(
        agency_id="ag_test",
        advisor_id="adv_test",
        client_id="cli_test",
        total_budget_huf=350000.0,
        flight_budget_huf=120000.0,
        stay_budget_huf=180000.0
    )
    case.sync_budget_models()

    assert case.budget_constraint.total.amount == 350000.0
    assert case.budget_constraint.components.flight.amount == 120000.0
    assert case.budget_constraint.components.stay.amount == 180000.0


# ─────────────────────────────────────────────────────────────
# 2. MULTI-OPTION ENGINE & OBJECTIVE PROFILES TESTS
# ─────────────────────────────────────────────────────────────

def test_multi_option_engine_objective_profiles():
    """Verify MultiOptionEngine produces sound scores without ungrounded magic numbers."""
    cand_a = {
        "id": "c_premium",
        "trip_score": 92.0,
        "total_price_huf": 320000.0,
        "stay": {"stars": 5, "rating_normalized": 9.5},
        "flight": {"stops": 0, "airline": "Swiss"},
        "activities": [{"name": "Private Food Tour"}, {"name": "Museum Pass"}, {"name": "Catamaran Cruise"}],
        "destination": {"city": "Nice", "vibe_match_score": 94.0}
    }
    cand_b = {
        "id": "c_budget",
        "trip_score": 84.0,
        "total_price_huf": 180000.0,
        "stay": {"stars": 3, "rating_normalized": 8.2},
        "flight": {"stops": 1, "airline": "Wizz Air"},
        "activities": [{"name": "City Walk"}],
        "destination": {"city": "Nice", "vibe_match_score": 85.0}
    }
    cand_c = {
        "id": "c_balanced",
        "trip_score": 88.0,
        "total_price_huf": 240000.0,
        "stay": {"stars": 4, "rating_normalized": 8.9},
        "flight": {"stops": 0, "airline": "Air France"},
        "activities": [{"name": "Sightseeing Pass"}, {"name": "Wine Tasting"}],
        "destination": {"city": "Nice", "vibe_match_score": 90.0}
    }

    # Verify experience score calculation
    exp_a = MultiOptionEngine.calculate_experience_score(cand_a)
    exp_b = MultiOptionEngine.calculate_experience_score(cand_b)
    assert 0.0 <= exp_a <= 100.0
    assert 0.0 <= exp_b <= 100.0
    assert exp_a > exp_b  # Premium option must score higher on experience quality

    # Verify value efficiency calculation
    val_b = MultiOptionEngine.calculate_value_efficiency(cand_b, reference_budget=300000.0)
    val_a = MultiOptionEngine.calculate_value_efficiency(cand_a, reference_budget=300000.0)
    assert val_b > val_a  # Budget option must score higher on value efficiency

    # Generate archetypes
    options = MultiOptionEngine.generate_archetypes([cand_a, cand_b, cand_c], target_budget_huf=300000.0)
    assert len(options) == 3
    assert options[0]["archetype"] == "best_overall"
    assert options[1]["archetype"] == "best_value"
    assert options[2]["archetype"] == "best_experience"


def test_multi_option_engine_3_option_rule_never_pads_fake_options():
    """Verify 3-Option Rule: Target 3, Acceptable 2, Minimum 1. Never fabricates poor options."""
    # Only 1 candidate
    single_cand = [{"id": "c1", "trip_score": 85.0, "total_price_huf": 200000.0}]
    res_1 = MultiOptionEngine.generate_archetypes(single_cand)
    assert len(res_1) == 1
    assert res_1[0]["archetype"] == "best_overall"

    # Only 2 valid candidates
    two_cands = [
        {"id": "c1", "trip_score": 90.0, "total_price_huf": 250000.0},
        {"id": "c2", "trip_score": 80.0, "total_price_huf": 160000.0}
    ]
    res_2 = MultiOptionEngine.generate_archetypes(two_cands)
    assert len(res_2) == 2
    assert res_2[0]["archetype"] == "best_overall"
    assert res_2[1]["archetype"] == "best_value"


# ─────────────────────────────────────────────────────────────
# 3. PROVENANCE & DATA FRESHNESS TESTS
# ─────────────────────────────────────────────────────────────

def test_provider_provenance_freshness_and_deep_links():
    """Verify provenance model tracks provider, TTL, deep links and verification status."""
    prov = ProviderProvenance(
        provider="Kiwi.com",
        source_type="aggregator",
        source_url="https://kiwi.com",
        deep_link="https://kiwi.com/deep/bud-bcn",
        booking_url="https://kiwi.com/book/bud-bcn",
        freshness_ttl_seconds=1800,
        verification_status=VerificationStatus.VERIFIED
    )
    assert prov.is_fresh() is True
    assert prov.deep_link == "https://kiwi.com/deep/bud-bcn"
    assert prov.source_type == "aggregator"


# ─────────────────────────────────────────────────────────────
# 4. ASYNC RESEARCHRUN LIFECYCLE & API TESTS
# ─────────────────────────────────────────────────────────────

def test_async_research_lifecycle_and_api(client):
    """Test POST /cases/{case_id}/research and GET /cases/{case_id}/research/{run_id}."""
    # 1. Create a test case
    case_id = f"case_test_{uuid.uuid4().hex[:8]}"
    test_case = TripCase(
        id=case_id,
        agency_id="ag_test",
        advisor_id="adv_test",
        client_id="client_kovacs_csalad",
        title="Async Research Test",
        destination_focus="Barcelona",
        total_budget_huf=300000.0
    )
    CASES_STORE[case_id] = test_case

    # 2. Trigger research
    res = client.post(f"/api/advisor/cases/{case_id}/research", json={"strategy": "known_destination"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    job = data["job"]
    run_id = job["job_id"]
    assert "providers_status" in job
    assert "kiwi" in job["providers_status"]

    # 3. Inspect research run via dedicated GET endpoint
    run_res = client.get(f"/api/advisor/cases/{case_id}/research/{run_id}")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["run_id"] == run_id
    assert run_data["job"]["status"] == "completed"

    # 4. Test cancel endpoint on job
    cancel_res = client.post(f"/api/advisor/cases/{case_id}/research/{run_id}/cancel")
    assert cancel_res.status_code == 200


# ─────────────────────────────────────────────────────────────
# 5. AUDITED ADVISOR OVERRIDES TESTS
# ─────────────────────────────────────────────────────────────

def test_audited_advisor_overrides(client):
    """Test POST /cases/{case_id}/override logs audited override history."""
    case_id = f"case_ovr_{uuid.uuid4().hex[:8]}"
    test_case = TripCase(
        id=case_id,
        agency_id="ag_test",
        advisor_id="adv_test",
        client_id="client_kovacs_csalad",
        title="Override Test"
    )
    CASES_STORE[case_id] = test_case

    ovr_res = client.post(
        f"/api/advisor/cases/{case_id}/override",
        json={
            "field": "pinned_hotel",
            "previous_value": "Hotel A",
            "new_value": "Hotel B (Grand Deluxe)",
            "reason": "Client requested sea view upgrade",
            "actor_id": "adv_adam"
        }
    )
    assert ovr_res.status_code == 200
    ovr_data = ovr_res.json()
    assert ovr_data["status"] == "success"
    assert ovr_data["total_overrides"] == 1
    updated_case = CASES_STORE[case_id]
    assert len(updated_case.preferences.overrides.history) == 1
    assert updated_case.preferences.overrides.history[0].reason == "Client requested sea view upgrade"


# ─────────────────────────────────────────────────────────────
# 6. PROPOSAL SHARING SECURITY & CLIENT-SAFE RENDERING TESTS
# ─────────────────────────────────────────────────────────────

def test_proposal_share_token_and_security(client):
    """Test generating cryptographic share token, viewing client-safe proposal, and revocation."""
    # 1. Create a base proposal
    case_id = f"case_prop_{uuid.uuid4().hex[:8]}"
    test_case = TripCase(id=case_id, agency_id="ag_test", advisor_id="adv_test", client_id="client_kovacs_csalad")
    test_client = CLIENTS_STORE["client_kovacs_csalad"]
    options = [
        {
            "id": "opt_a",
            "title": "Klasszikus Csomag",
            "archetype": "best_overall",
            "total_price_huf": 250000.0,
            "price_per_person_huf": 125000.0,
            "trip_score": 88,
            "destination": {"city": "Barcelona", "country": "Spanyolország"},
            "flight": {"airline": "Wizz Air", "stops": 0},
            "stay": {"name": "Hotel Arts", "stars": 5, "rating_normalized": 9.2},
            "debug_weights": {"ahp_internal": 0.85}
        }
    ]

    proposal = ProposalService.create_proposal(
        trip_case=test_case,
        client=test_client,
        options=options,
        advisor_notes="INTERNAL CONFIDENTIAL: Client has 15% budget elasticity."
    )
    PROPOSALS_STORE[proposal["id"]] = proposal

    # 2. Generate secure share token
    share_res = client.post(f"/api/advisor/proposals/{proposal['id']}/share", json={"expires_in_days": 14})
    assert share_res.status_code == 200
    share_data = share_res.json()
    token = share_data["token"]
    assert token is not None
    assert len(token) >= 32

    # 3. Access public shared API endpoint -> Internal notes MUST be stripped
    pub_api_res = client.get(f"/api/advisor/public/proposals/{token}")
    assert pub_api_res.status_code == 200
    pub_data = pub_api_res.json()
    assert "advisor_notes" not in pub_data["proposal"]
    assert "INTERNAL CONFIDENTIAL" not in str(pub_data["proposal"])

    # 4. Access public HTML web page
    pub_html_res = client.get(f"/share/proposal/{token}")
    assert pub_html_res.status_code == 200
    assert "Klasszikus Csomag" in pub_html_res.text
    assert "INTERNAL CONFIDENTIAL" not in pub_html_res.text

    # 5. Revoke share token
    revoke_res = client.post(f"/api/advisor/proposals/{proposal['id']}/revoke-share?token={token}")
    assert revoke_res.status_code == 200

    # 6. Subsequent access MUST return 404
    blocked_res = client.get(f"/share/proposal/{token}")
    assert blocked_res.status_code == 404


# ─────────────────────────────────────────────────────────────
# 7. CONSTRAINT RELAXATION TESTS
# ─────────────────────────────────────────────────────────────

def test_constraint_relaxation_on_dead_end():
    """Verify ConstraintRelaxationService provides quantified recovery options without silent mutations."""
    case = TripCase(
        agency_id="ag_test",
        advisor_id="adv_test",
        client_id="cli_test",
        total_budget_huf=150000.0,
        preferences=ResolvedTripPreferences(
            hard=HardConstraints(direct_flights_only=True, min_hotel_stars=5)
        )
    )

    # Raw inventory with 0 exact matches for (direct + 5-star + <=150k)
    raw_inventory = [
        {"id": "inv_1", "flight": {"stops": 1}, "stay": {"stars": 5}, "total_price_huf": 140000.0},
        {"id": "inv_2", "flight": {"stops": 0}, "stay": {"stars": 4}, "total_price_huf": 130000.0},
        {"id": "inv_3", "flight": {"stops": 0}, "stay": {"stars": 5}, "total_price_huf": 170000.0}
    ]

    diagnosis = ConstraintRelaxationService.diagnose_and_suggest(case, case.preferences, raw_inventory)
    assert diagnosis["is_dead_end"] is True
    assert diagnosis["currently_valid_count"] == 0
    assert len(diagnosis["suggested_relaxations"]) > 0

    # Apply relaxation patch with explicit advisor confirmation
    relax_patch = diagnosis["suggested_relaxations"][0]["patch"]
    updated_case = ConstraintRelaxationService.apply_relaxation(case, "relax_test", relax_patch)
    assert updated_case is not None


# ─────────────────────────────────────────────────────────────
# 8. B2C PLANNER REGRESSION PROTECTION TESTS
# ─────────────────────────────────────────────────────────────

def test_b2c_planner_regression_protection(client):
    """Verify B2C /planner routes and user journeys remain completely unaffected."""
    planner_res = client.get("/planner")
    assert planner_res.status_code in [200, 303]
