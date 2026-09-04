import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.analytics_service import (
    record_telemetry_event,
    get_user_sessions_summary,
    get_db_connection
)

class TestUserJourneysAndClarity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_user = "test_journey_user"
        self.test_session = "sess_journey_12345"

    def tearDown(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM telemetry_events WHERE user_id = ? OR session_id = ?", (self.test_user, self.test_session))
        conn.commit()
        conn.close()

    def test_button_tracking_endpoint(self):
        # 1. Post button click event via /api/telemetry/event
        payload = {
            "session_id": self.test_session,
            "user_id": self.test_user,
            "event_type": "button_click",
            "module": "ui_interaction",
            "duration_ms": 3200,
            "meta_data": {
                "action": "destination_selected",
                "button_id": "btnSelectDest",
                "button_text": "Járatok keresése (Barcelona)",
                "planner_step": 1,
                "target_destination": "Barcelona",
                "dwell_sec": 3
            },
            "search_params": {"destination": "Barcelona"}
        }
        res = self.client.post("/api/telemetry/event", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")

    def test_user_journey_aggregation(self):
        # Simulate a full user journey in sequence
        # Step 0: Initial search
        record_telemetry_event(
            user_id=self.test_user,
            session_id=self.test_session,
            event_type="search_completed",
            module="destination_matcher",
            search_params={"origin": "Budapest"},
            results_count=10,
            duration_ms=800,
            success=True,
            meta_data={"dwell_sec": 5}
        )

        # Step 1: Button click to select destination
        record_telemetry_event(
            user_id=self.test_user,
            session_id=self.test_session,
            event_type="button_click",
            module="ui_interaction",
            search_params={"destination": "Barcelona"},
            duration_ms=2000,
            success=True,
            meta_data={"action": "destination_selected", "button_text": "Járatok keresése", "dwell_sec": 2}
        )

        # Step 2: Flight search completed
        record_telemetry_event(
            user_id=self.test_user,
            session_id=self.test_session,
            event_type="search_completed",
            module="flight_intelligence",
            search_params={"destination": "BCN"},
            results_count=6,
            duration_ms=1200,
            success=True,
            meta_data={"dwell_sec": 12}
        )

        # Step 3: Proposal export
        record_telemetry_event(
            user_id=self.test_user,
            session_id=self.test_session,
            event_type="proposal_exported",
            module="proposal",
            search_params={"destination": "Barcelona"},
            results_count=1,
            duration_ms=500,
            success=True,
            meta_data={"dwell_sec": 4}
        )

        # Aggregate sessions
        sessions = get_user_sessions_summary(user_id=self.test_user)
        self.assertGreaterEqual(len(sessions), 1)

        sess = next((s for s in sessions if s["session_id"] == self.test_session), None)
        self.assertIsNotNone(sess)
        self.assertEqual(sess["user_id"], self.test_user)
        self.assertGreaterEqual(sess["total_events"], 4)
        self.assertGreaterEqual(len(sess["journey_path"]), 3)

        # Check journey milestones
        milestones = [m["badge"] for m in sess["journey_path"]]
        self.assertTrue(any("Célpont" in m for m in milestones))
        self.assertTrue(any("Járat" in m for m in milestones))
        self.assertTrue(any("Ajánlat" in m for m in milestones))

    def test_admin_sessions_api(self):
        # Insert event
        record_telemetry_event(
            user_id=self.test_user,
            session_id=self.test_session,
            event_type="button_click",
            module="ui_interaction",
            meta_data={"button_text": "Teszt Gomb"}
        )

        # Login as admin to get auth cookie
        login_res = self.client.post("/admin/login", data={"password": os.getenv("ADMIN_PASSWORD", "optivoya2026admin")}, follow_redirects=False)
        self.assertIn("optivoya_admin_token", login_res.cookies)

        # Call /api/admin/sessions
        res = self.client.get(f"/api/admin/sessions?user={self.test_user}", cookies=login_res.cookies)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("sessions", data)
        self.assertGreaterEqual(len(data["sessions"]), 1)

if __name__ == "__main__":
    unittest.main()
