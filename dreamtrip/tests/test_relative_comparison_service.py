"""
Unit and Integration Tests for Relative Comparison & Advisor Overrides (Phase 6)
================================================================================
Verifies:
1. RelativeComparisonService matrix and delta percentage calculation.
2. Natural language trade-off pros & cons generator without hallucinations.
3. Whitebox Advisor Override API (edit title, price, manual reason).
4. Component swapping and price recalculation API.
5. Option reordering API.
6. Find Better targeted component search API.
"""

import pytest
from app.services.relative_comparison_service import RelativeComparisonService
from app.services.advisor_orchestration_service import AdvisorOrchestrationService
from app.routers.advisor_api import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestRelativeComparisonEngine:

    @pytest.fixture
    def sample_options(self):
        return [
            {
                "id": "opt_a",
                "archetype": "best_overall",
                "title": "Barcelona Balanced Choice",
                "total_price_huf": 300000,
                "price_per_person_huf": 150000,
                "trip_score": 90,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Wizz Air", "stops": 0, "duration_minutes": 160, "price_huf": 80000},
                "stay": {"name": "Hotel Arts", "stars": 4, "rating_normalized": 8.8, "price_huf": 180000},
                "activities": [{"name": "Sagrada"}, {"name": "Park Guell"}]
            },
            {
                "id": "opt_b",
                "archetype": "best_value",
                "title": "Barcelona Smart Saver",
                "total_price_huf": 210000,
                "price_per_person_huf": 105000,
                "trip_score": 83,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Ryanair", "stops": 0, "duration_minutes": 160, "price_huf": 50000},
                "stay": {"name": "Hostal Ramblas", "stars": 3, "rating_normalized": 8.0, "price_huf": 120000},
                "activities": [{"name": "Gothic Walk"}]
            },
            {
                "id": "opt_c",
                "archetype": "best_experience",
                "title": "Barcelona Ultra Luxury",
                "total_price_huf": 450000,
                "price_per_person_huf": 225000,
                "trip_score": 93,
                "destination": {"city": "Barcelona", "country": "Spanyolország"},
                "flight": {"airline": "Lufthansa", "stops": 0, "duration_minutes": 150, "price_huf": 110000},
                "stay": {"name": "Mandarin Oriental", "stars": 5, "rating_normalized": 9.5, "price_huf": 300000},
                "activities": [{"name": "Gaudi Private Tour"}, {"name": "Michelin Dinner"}, {"name": "Catamaran"}]
            }
        ]

    def test_compute_comparison_matrix(self, sample_options):
        """Tests that matrix dimensions and deltas are calculated accurately."""
        matrix = RelativeComparisonService.compute_comparison_matrix(sample_options)
        assert "options" in matrix
        assert len(matrix["options"]) == 3
        assert "dimensions" in matrix
        assert len(matrix["dimensions"]) >= 5

        # Check Price dimension
        price_dim = next(d for d in matrix["dimensions"] if d["id"] == "price")
        # Option B vs Base Option A: (210000 - 300000) = -90000 (-30.0%)
        val_b = price_dim["values"][1]
        assert val_b["delta_from_base"] == -90000
        assert val_b["delta_pct"] == -30.0

        # Option C vs Base Option A: (450000 - 300000) = +150000 (+50.0%)
        val_c = price_dim["values"][2]
        assert val_c["delta_from_base"] == 150000
        assert val_c["delta_pct"] == 50.0

    def test_relative_narratives(self, sample_options):
        """Tests natural-language narrative pros & cons generation."""
        matrix = RelativeComparisonService.compute_comparison_matrix(sample_options)
        narratives = matrix.get("relative_tradeoffs", [])
        assert len(narratives) == 3

        # Option B should highlight cost savings
        b_narrative = narratives[1]
        assert any("kedvezőbb" in p or "Ft" in p for p in b_narrative["pros"])

        # Option C should highlight higher accommodation / experience
        c_narrative = narratives[2]
        assert any("5★" in p or "élmény" in p or "szállás" in p for p in c_narrative["pros"])
        assert any("árprémium" in c or "Ft" in c for c in c_narrative["cons"])

    def test_api_compare_and_override_workflow(self, sample_options):
        """Tests full API flow for comparison, editing, swapping, and reordering."""
        # 1. Get active case
        res = client.get("/api/advisor/cases")
        cases = res.json().get("cases", [])
        assert len(cases) > 0
        case_id = cases[0]["id"]

        # Seed candidate pool and generate options
        AdvisorOrchestrationService._CANDIDATES_POOL[case_id] = sample_options
        gen_res = client.post(f"/api/advisor/cases/{case_id}/options/generate")
        assert gen_res.status_code == 200
        options = gen_res.json().get("options", [])
        assert len(options) == 3
        opt_id = options[0]["id"]

        # 2. GET /cases/{case_id}/compare
        comp_res = client.get(f"/api/advisor/cases/{case_id}/compare")
        assert comp_res.status_code == 200
        data = comp_res.json()
        assert data["status"] == "success"
        assert len(data["comparison"]["options"]) == 3

        # 3. PUT /cases/{case_id}/options/{option_id} (Advisor Override)
        upd_res = client.put(f"/api/advisor/cases/{case_id}/options/{opt_id}", json={
            "title": "Barcelona Egyedi VIP Csomag",
            "total_price_huf": 315000,
            "override_reason": "Ügyfél kérésre hozzáadott transzfer és biztosítás"
        })
        assert upd_res.status_code == 200
        updated = upd_res.json().get("updated_option", {})
        assert updated["title"] == "Barcelona Egyedi VIP Csomag"
        assert updated["total_price_huf"] == 315000

        # 4. POST /cases/{case_id}/options/{option_id}/swap-component
        swap_res = client.post(f"/api/advisor/cases/{case_id}/options/{opt_id}/swap-component", json={
            "component_type": "stay",
            "new_component_id": sample_options[2]["id"],
            "override_reason": "Csere 5 csillagos Mandarin Oriental szállodára"
        })
        assert swap_res.status_code == 200
        swapped = swap_res.json().get("option", {})
        assert swapped["stay"]["name"] == "Mandarin Oriental"

        # 5. POST /cases/{case_id}/options/reorder
        reorder_res = client.post(f"/api/advisor/cases/{case_id}/options/reorder", json={
            "ordered_option_ids": [options[2]["id"], options[0]["id"], options[1]["id"]],
            "override_reason": "A prémium csomag ajánlása első helyen"
        })
        assert reorder_res.status_code == 200
        reordered = reorder_res.json().get("options", [])
        assert reordered[0]["id"] == options[2]["id"]

        # 6. POST /cases/{case_id}/find-better
        from unittest.mock import patch
        with patch("app.services.accommodation_intelligence_service.AccommodationIntelligenceService.search_and_rank_stays") as mock_stays:
            mock_stays.return_value = [{"id": "alt_1", "name": "Hilton Diagonal Mar", "stars": 4, "price_huf": 170000, "rating_normalized": 8.9}]
            fb_res = client.post(f"/api/advisor/cases/{case_id}/find-better", json={
                "option_id": opt_id,
                "target_component": "stay",
                "goal": "higher_stars"
            })
            assert fb_res.status_code == 200
            assert fb_res.json()["status"] == "success"
