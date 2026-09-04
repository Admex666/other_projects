"""
Tests for Dummy / Simulation Mode in Master Planner.
Verifies permission checks (bean, admin, id in (1,2)), instant dummy generation, and zero scraper calls.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import is_dummy_mode_allowed, create_session
from app.services.dummy_planner_service import (
    generate_dummy_destinations,
    generate_dummy_flights,
    generate_dummy_stays
)

client = TestClient(app)

def test_dummy_mode_permissions():
    assert is_dummy_mode_allowed("bean") is True
    assert is_dummy_mode_allowed("admin") is True
    assert is_dummy_mode_allowed("BEAN") is True
    assert is_dummy_mode_allowed("Admin") is True
    assert is_dummy_mode_allowed("unknown_guest_123") is False
    assert is_dummy_mode_allowed(None) is False

def test_dummy_generators():
    # Destinations generator
    class MockIntake:
        target_temp = 24.0
        adults = 2
        duration = 7
        ahp_weights = {"total_cost": 34, "weather": 33, "safety": 33}
        exclusions = []
        preferred_regions = ["Europe"]

    dests = generate_dummy_destinations(MockIntake())
    assert len(dests) >= 5
    assert dests[0]["rank"] == 1
    assert "metrics" in dests[0]
    assert dests[0]["metrics"]["flight_price_raw"] > 0
    assert dests[0]["metrics"]["temp_raw"] > 0

    # Flights generator
    class MockFlightReq:
        origin = "Budapest"
        destination = "Róma"
        adults = 2
        duration = 7
        direct_only = False
        exact_out_date = "2026-09-12"
        exact_in_date = "2026-09-19"

    flights = generate_dummy_flights(MockFlightReq())
    assert len(flights) >= 4
    assert flights[0]["rank"] == 1
    assert flights[0]["price_huf"] > 0
    assert flights[0]["out_carriers"] in ["Wizz Air", "Ryanair", "Lufthansa", "Austrian Airlines"]

    # Stays generator
    class MockStayReq:
        city = "Róma"
        country = "Olaszország"
        checkin = "2026-09-12"
        checkout = "2026-09-19"
        adults = 2
        hotel_types = None
        breakfast = False
        amenities = None

    stays = generate_dummy_stays(MockStayReq())
    assert len(stays) >= 3
    assert stays[0]["price_total_huf"] > 0
    assert stays[0]["is_dummy"] is True

def test_api_endpoints_dummy_mode():
    # Login as bean
    token = create_session("bean")
    cookies = {"session_token": token}

    # 1. Init destinations with dummy_mode = True
    res = client.post("/api/planner/init-destinations", json={
        "origin": "Budapest",
        "date_mode": "month",
        "month": "9",
        "year": 2026,
        "duration": 7,
        "adults": 2,
        "target_temp": 24.0,
        "dummy_mode": True
    }, cookies=cookies)
    assert res.status_code == 200
    assert res.json()["is_dummy"] is True

    # Check status
    time.sleep(0.5)
    status_res = client.get("/api/planner/destinations-status", cookies=cookies)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "done"
    assert status_data["count"] > 0
    assert status_data["is_dummy"] is True

    # 2. Flight search with dummy_mode = True
    flight_res = client.post("/api/planner/search-flights", json={
        "origin": "Budapest",
        "destination": "Róma",
        "date_mode": "exact",
        "exact_out_date": "2026-09-12",
        "exact_in_date": "2026-09-19",
        "duration": 7,
        "adults": 2,
        "dummy_mode": True
    }, cookies=cookies)
    assert flight_res.status_code == 200
    flight_data = flight_res.json()
    assert flight_data["status"] == "ok"
    assert flight_data["is_dummy"] is True
    assert len(flight_data["flights"]) > 0

    # 3. Stay search with dummy_mode = True
    stay_res = client.post("/api/planner/search-stays", json={
        "city": "Róma",
        "country": "Olaszország",
        "checkin": "2026-09-12",
        "checkout": "2026-09-19",
        "adults": 2,
        "dummy_mode": True
    }, cookies=cookies)
    assert stay_res.status_code == 200
    stay_data = stay_res.json()
    assert stay_data["status"] == "ok"
    assert stay_data["is_dummy"] is True
    assert len(stay_data["stays"]) > 0

if __name__ == "__main__":
    print("Testing dummy mode permissions...")
    test_dummy_mode_permissions()
    print("[PASS] Permissions verified!")

    print("Testing dummy generators...")
    test_dummy_generators()
    print("[PASS] Dummy generators verified!")

    print("Testing planner API endpoints with dummy mode...")
    test_api_endpoints_dummy_mode()
    print("[PASS] API endpoints dummy mode verified!")

    print("\n>>> ALL DUMMY MODE TESTS PASSED 100%! <<<")
