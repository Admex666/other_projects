"""
Unit and Integration Tests for Constraint Relaxation, Verification & Risk Engine (Phase 7)
==========================================================================================
Verifies:
1. ConstraintRelaxationService dead-end diagnosis & quantified 1-click relaxation pathways.
2. VerificationService provenance confidence, cache timestamps, and status rules.
3. TripRiskService operational risk detection (tight layovers, night arrivals, city taxes).
4. REST API endpoints for relaxation, verification, and operational risks.
"""

import pytest
from app.services.constraint_relaxation_service import ConstraintRelaxationService
from app.services.verification_service import VerificationService
from app.services.trip_risk_service import TripRiskService, RiskSeverity
from app.models.advisor_models import (
    TripCase, HardConstraints, ResolvedTripPreferences, VerificationStatus
)
from app.routers.advisor_api import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestRelaxationVerificationRisk:

    @pytest.fixture
    def mock_inventory(self):
        return [
            # 1. Direct, 4-star, 280 000 Ft
            {
                "id": "cand_1",
                "title": "Direct 4-Star Package",
                "total_price_huf": 280000,
                "flight": {"airline": "Wizz Air", "stops": 0, "duration_minutes": 140, "price_huf": 80000, "is_live": True, "freshness_minutes": 10},
                "stay": {"name": "Hotel Arts", "stars": 4, "rating_normalized": 8.8, "price_huf": 200000, "is_live": True, "freshness_minutes": 10},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "activities": [{"name": "Sagrada Familia"}]
            },
            # 2. 1-stop, 3-star, 190 000 Ft
            {
                "id": "cand_2",
                "title": "1-Stop Budget Package",
                "total_price_huf": 190000,
                "flight": {"airline": "Lufthansa", "stops": 1, "layover_minutes": 45, "duration_minutes": 260, "price_huf": 60000, "is_live": True, "freshness_minutes": 30},
                "stay": {"name": "Hostal Ramblas", "stars": 3, "rating_normalized": 8.1, "price_huf": 130000, "is_live": True, "freshness_minutes": 30},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "activities": []
            },
            # 3. Direct, 5-star, 420 000 Ft
            {
                "id": "cand_3",
                "title": "Luxury Direct Package",
                "total_price_huf": 420000,
                "flight": {"airline": "Iberia", "stops": 0, "arrival_time": "23:45", "duration_minutes": 140, "price_huf": 120000, "is_live": True, "freshness_minutes": 120},
                "stay": {"name": "Mandarin Oriental", "stars": 5, "rating_normalized": 9.4, "price_huf": 300000, "is_live": True, "freshness_minutes": 120},
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "activities": [{"name": "City Museum"}]
            }
        ]

    def test_constraint_relaxation_diagnosis(self, mock_inventory):
        """Tests that strict constraints returning 0 results produce actionable relaxation proposals."""
        trip_case = TripCase(
            id="case_strict_test",
            agency_id="agency_optivoya",
            advisor_id="adv_test",
            client_id="client_1",
            title="Strict Case",
            total_budget_huf=200000, # Very low budget
            preferences=ResolvedTripPreferences(
                hard=HardConstraints(
                    direct_flights_only=True, # cand_2 excluded (stops=1)
                    min_hotel_stars=4         # cand_2 excluded (stars=3)
                    # cand_1 price 280k > 200k * 1.25 (250k) -> excluded!
                    # cand_3 price 420k > 250k -> excluded!
                )
            )
        )

        diagnosis = ConstraintRelaxationService.diagnose_and_suggest(
            trip_case=trip_case,
            preferences=trip_case.preferences,
            raw_inventory_pool=mock_inventory
        )

        assert diagnosis["is_dead_end"] is True
        assert diagnosis["currently_valid_count"] == 0
        suggestions = diagnosis["suggested_relaxations"]
        assert len(suggestions) > 0

        # Should propose relaxing stops or budget or hotel stars
        sug_ids = [s["id"] for s in suggestions]
        assert "relax_budget_15" in sug_ids or "relax_flight_stops" in sug_ids or "relax_hotel_stars" in sug_ids

    def test_verification_service_provenance(self, mock_inventory):
        """Tests provenance freshness evaluation and overall option status."""
        opt_1 = mock_inventory[0]
        ver_1 = VerificationService.verify_trip_option(opt_1)
        assert ver_1["overall_status"] == VerificationStatus.VERIFIED.value
        assert ver_1["confidence_score"] >= 0.90

        # Stale item (>1440 min)
        stale_opt = {
            "id": "opt_stale",
            "flight": {"freshness_minutes": 2000, "is_live": False},
            "stay": {"freshness_minutes": 5, "is_live": True}
        }
        ver_stale = VerificationService.verify_trip_option(stale_opt)
        assert ver_stale["overall_status"] == VerificationStatus.NEEDS_REVIEW.value

    def test_trip_risk_service_hazards(self, mock_inventory):
        """Tests detection of tight layover, late arrival, and destination city tax."""
        opt_2 = mock_inventory[1] # 45 min layover
        risks_2 = TripRiskService.evaluate_option_risks(opt_2)
        assert any(r["risk_id"] == "TIGHT_LAYOVER" and r["severity"] == RiskSeverity.CRITICAL.value for r in risks_2)

        opt_3 = mock_inventory[2] # 23:45 arrival + Barcelona city tax
        risks_3 = TripRiskService.evaluate_option_risks(opt_3)
        assert any(r["risk_id"] == "LATE_NIGHT_ARRIVAL" for r in risks_3)
        assert any(r["risk_id"] == "RESORT_FEE_RISK" for r in risks_3)

    def test_api_relaxation_verification_and_risks(self, mock_inventory):
        """Tests full REST API flow for diagnose, apply relaxation, verification and risks."""
        # 1. Get active case
        res = client.get("/api/advisor/cases")
        cases = res.json().get("cases", [])
        assert len(cases) > 0
        case_id = cases[0]["id"]

        # 2. POST /cases/{case_id}/diagnose-constraints
        diag_res = client.post(f"/api/advisor/cases/{case_id}/diagnose-constraints")
        assert diag_res.status_code == 200
        diag_data = diag_res.json()
        assert diag_data["status"] == "success"
        assert "diagnosis" in diag_data

        # 3. POST /cases/{case_id}/apply-relaxation
        relax_res = client.post(f"/api/advisor/cases/{case_id}/apply-relaxation", json={
            "relaxation_id": "relax_budget_15",
            "patch": {"total_budget_huf": 350000}
        })
        assert relax_res.status_code == 200
        assert relax_res.json()["status"] == "success"

        # 4. GET /cases/{case_id}/verification-status
        ver_res = client.get(f"/api/advisor/cases/{case_id}/verification-status")
        assert ver_res.status_code == 200
        assert ver_res.json()["status"] == "success"
        assert "verifications" in ver_res.json()

        # 5. GET /cases/{case_id}/risks
        risk_res = client.get(f"/api/advisor/cases/{case_id}/risks")
        assert risk_res.status_code == 200
        assert risk_res.json()["status"] == "success"
        assert "risks" in risk_res.json()
