"""
Unit & Integration Tests for Optivoya Beta Usage Analytics & Admin Dashboard
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

from app.models.analytics_models import init_analytics_db, get_db_connection
from app.services.user_service import create_beta_user, verify_user_login, get_all_beta_users
from app.services.analytics_service import record_telemetry_event, get_analytics_kpis, get_user_timeline

client = TestClient(app)

def test_database_init():
    init_analytics_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    conn.close()
    assert "beta_users" in tables
    assert "telemetry_events" in tables
    assert "user_sessions" in tables

import uuid

def test_beta_user_lifecycle():
    username = f"test_advisor_{uuid.uuid4().hex[:6]}"
    res = create_beta_user(
        username=username,
        password="secret_password_123",
        full_name="Teszt Éva",
        company_name="Boutique Travel Agency",
        email="eva@testtravel.hu",
        notes="Beta cohort 1"
    )
    assert res["status"] == "ok"

    
    # Verification
    assert verify_user_login(username, "secret_password_123") is True
    assert verify_user_login(username, "wrong_password") is False

    # Directory query
    users = get_all_beta_users()
    found = any(u["username"] == username for u in users)
    assert found is True

def test_telemetry_recording_and_kpis():
    user = "test_advisor_eva"
    session_id = "sess_test_12345"

    # 1. Search started event
    evt1 = record_telemetry_event(
        user_id=user,
        session_id=session_id,
        event_type="search_started",
        module="destination_matcher",
        search_params={"origin": "Budapest", "month": "9", "duration": 7}
    )
    assert evt1.startswith("evt_")

    # 2. Search completed event
    evt2 = record_telemetry_event(
        user_id=user,
        session_id=session_id,
        event_type="search_completed",
        module="destination_matcher",
        search_params={"origin": "Budapest", "month": "9", "duration": 7},
        duration_ms=1450.0,
        results_count=18,
        success=True
    )
    assert evt2.startswith("evt_")

    # 3. Flight search completed event
    evt3 = record_telemetry_event(
        user_id=user,
        session_id=session_id,
        event_type="search_completed",
        module="flight_intelligence",
        search_params={"origin": "BUD", "destination": "FCO"},
        duration_ms=2100.0,
        results_count=45,
        success=True
    )
    assert evt3.startswith("evt_")

    # 4. Proposal Exported
    evt4 = record_telemetry_event(
        user_id=user,
        session_id=session_id,
        event_type="proposal_exported",
        module="proposal",
        search_params={"destination": "Róma", "trip_id": "trip_test_999"},
        results_count=1,
        success=True
    )
    assert evt4.startswith("evt_")

    # KPI Calculation Check
    kpis = get_analytics_kpis()
    assert kpis["total_searches"] >= 2
    assert kpis["successful_searches"] >= 2
    assert kpis["success_rate_pct"] > 0
    assert kpis["total_time_saved_hours"] > 0
    assert kpis["proposals_exported"] >= 1

    # User Timeline Check
    timeline = get_user_timeline(user_id=user)
    assert len(timeline) >= 4
    assert timeline[0]["user_id"] == user

def test_admin_authentication_and_endpoints():
    # 1. Unauthorized access to dashboard
    res_unauth = client.get("/admin/dashboard", follow_redirects=False)
    assert res_unauth.status_code == 302
    assert res_unauth.headers["location"] == "/admin"

    # 2. Login with wrong password
    res_bad_login = client.post("/admin/login", data={"password": "wrong_password_xyz"})
    assert res_bad_login.status_code == 401

    # 3. Login with correct password from .env
    admin_pw = os.getenv("ADMIN_PASSWORD", "optivoya_admin_2026")
    res_good_login = client.post("/admin/login", data={"password": admin_pw}, follow_redirects=False)
    assert res_good_login.status_code == 302
    assert "optivoya_admin_token" in res_good_login.cookies

    # 4. Access dashboard with cookie
    cookies = {"optivoya_admin_token": res_good_login.cookies["optivoya_admin_token"]}
    res_dash = client.get("/admin/dashboard", cookies=cookies)
    assert res_dash.status_code == 200
    assert "B2B Beta Usage Dashboard" in res_dash.text
    assert "Megtakarított Idő" in res_dash.text

    # 5. API timeline endpoint
    res_api_timeline = client.get("/api/admin/timeline", cookies=cookies)
    assert res_api_timeline.status_code == 200
    json_data = res_api_timeline.json()
    assert json_data["status"] == "ok"
    assert len(json_data["events"]) > 0

if __name__ == "__main__":
    print("Running test_database_init()...")
    test_database_init()
    print("[PASS] test_database_init passed!")

    print("Running test_beta_user_lifecycle()...")
    test_beta_user_lifecycle()
    print("[PASS] test_beta_user_lifecycle passed!")

    print("Running test_telemetry_recording_and_kpis()...")
    test_telemetry_recording_and_kpis()
    print("[PASS] test_telemetry_recording_and_kpis passed!")

    print("Running test_admin_authentication_and_endpoints()...")
    test_admin_authentication_and_endpoints()
    print("[PASS] test_admin_authentication_and_endpoints passed!")

    print("\n>>> ALL ANALYTICS & ADMIN DASHBOARD TESTS PASSED 100%! <<<")


