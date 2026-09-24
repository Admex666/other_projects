"""
Optivoya B2B Advisor Workspace — REST API & Endpoint Tests
Validates multi-tenant advisor contracts, client CRM, case lifecycle, KPIs and HTML workspace shell.
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAdvisorAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.core.auth import create_session
        cls.client = TestClient(app)
        sid = create_session("admin")
        cls.client.cookies.set("session_token", sid)

    def test_01_advisor_profile_me(self):
        res = self.client.get("/api/advisor/me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIsNotNone(data["advisor"])
        self.assertIsNotNone(data["agency"])
        self.assertEqual(data["agency"]["slug"], "optivoya-premier")

    def test_02_dashboard_kpis(self):
        res = self.client.get("/api/advisor/dashboard/kpis")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["active_cases"], 1)
        self.assertGreaterEqual(data["estimated_hours_saved"], 1.0)
        self.assertGreaterEqual(data["avg_composite_tripscore"], 80.0)

    def test_03_clients_crm_lifecycle(self):
        # 1. List clients
        list_res = self.client.get("/api/advisor/clients")
        self.assertEqual(list_res.status_code, 200)
        initial_count = list_res.json()["total"]
        self.assertGreaterEqual(initial_count, 1)

        # 2. Create new client
        new_client_payload = {
            "name": "Nagy Gergely & Anna",
            "email": "nagy.gergely@test.com",
            "phone": "+36 70 555 1234",
            "tags": ["Couples", "Honeymoon", "Luxury"],
            "notes": "Nászút célállomás keresés a Földközi-tengeren."
        }
        create_res = self.client.post("/api/advisor/clients", json=new_client_payload)
        self.assertEqual(create_res.status_code, 201)
        created_client = create_res.json()["client"]
        self.assertEqual(created_client["name"], "Nagy Gergely & Anna")
        client_id = created_client["id"]

        # 3. Retrieve client details
        detail_res = self.client.get(f"/api/advisor/clients/{client_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertEqual(detail_data["client"]["email"], "nagy.gergely@test.com")

    def test_04_cases_lifecycle_and_status(self):
        # 1. List active cases
        cases_res = self.client.get("/api/advisor/cases")
        self.assertEqual(cases_res.status_code, 200)
        cases = cases_res.json()["cases"]
        self.assertGreaterEqual(len(cases), 1)

        # 2. Create new case for client_kovacs_csalad
        case_payload = {
            "client_id": "client_kovacs_csalad",
            "title": "Róma Tavaszi Művészeti Hétvége",
            "target_total_budget": 550000,
            "travelers_adults": 2,
            "origin": "BUD",
            "destinations": ["Rome", "FCO"],
            "duration_days": 4,
            "direct_flights_only": True,
            "min_hotel_stars": 4,
            "min_hotel_rating": 8.5
        }
        create_case_res = self.client.post("/api/advisor/cases", json=case_payload)
        self.assertEqual(create_case_res.status_code, 201)
        new_case = create_case_res.json()["case"]
        self.assertEqual(new_case["title"], "Róma Tavaszi Művészeti Hétvége")
        case_id = new_case["id"]
        self.assertEqual(new_case["status"], "brief")

        # 3. Advance case status to 'research' then 'shortlist'
        status_patch = self.client.patch(f"/api/advisor/cases/{case_id}/status", json={"status": "research"})
        self.assertEqual(status_patch.status_code, 200)
        self.assertEqual(status_patch.json()["case"]["status"], "research")

        # 4. View case details
        case_det = self.client.get(f"/api/advisor/cases/{case_id}")
        self.assertEqual(case_det.status_code, 200)
        self.assertIn("Kovács Család", case_det.json()["client"]["name"])

    def test_05_advisor_workspace_html_shell(self):
        res = self.client.get("/advisor")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Optivoya Advisor Workspace", res.text)
        self.assertIn("advisor_state.js", res.text)
        self.assertIn("advisor_dashboard.js", res.text)
        self.assertIn("advisor_clients.js", res.text)
        self.assertIn("advisor_brief.js", res.text)

    def test_06_update_client_profile(self):
        # Update client preferences
        update_payload = {
            "name": "Kovács Család (Péter & Dóra - VIP)",
            "preferences": {
                "hotel_min_stars": 5,
                "hotel_min_rating": 9.0,
                "direct_flights_only": True
            }
        }
        res = self.client.put("/api/advisor/clients/client_kovacs_csalad", json=update_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["client"]["name"], "Kovács Család (Péter & Dóra - VIP)")
        self.assertEqual(res.json()["client"]["preferences"]["hotel_min_stars"], 5)

    def test_07_deep_brief_and_resolved_preferences(self):
        # 1. Update deep brief with Mode B (Component Limits)
        brief_payload = {
            "title": "London Luxus Családi Hétvége",
            "budget_mode": "component",
            "flight_budget_huf": 120000,
            "stay_budget_huf": 350000,
            "hard_constraints": {
                "max_flight_budget_huf": 120000,
                "max_stay_budget_huf": 350000,
                "direct_flights_only": True,
                "min_hotel_stars": 4,
                "min_hotel_rating": 8.8
            },
            "nice_to_have": {
                "breakfast_included": True,
                "pool_available": True,
                "central_location": True
            }
        }
        brief_res = self.client.put("/api/advisor/cases/case_london_kovacs/brief", json=brief_payload)
        self.assertEqual(brief_res.status_code, 200)
        case_data = brief_res.json()["case"]
        self.assertEqual(case_data["budget_mode"], "component")
        self.assertEqual(case_data["flight_budget_huf"], 120000)

        # 2. Get resolved preferences
        prefs_res = self.client.get("/api/advisor/cases/case_london_kovacs/resolved-preferences")
        self.assertEqual(prefs_res.status_code, 200)
        p_data = prefs_res.json()
        self.assertTrue(p_data["budget_validation"]["valid"])
        self.assertEqual(p_data["resolved_preferences"]["hard"]["min_hotel_stars"], 4)
        self.assertTrue(p_data["resolved_preferences"]["nice_to_have"]["pool_available"])

if __name__ == "__main__":
    unittest.main()

