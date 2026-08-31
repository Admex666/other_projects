"""
Optivoya API v2 — Planner Router
Handles Destination Calculation, Flight Ranking (PROMETHEE II), Stay Aggregation, and Trip State Sync.
"""

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import os

from app.models.models import UnifiedTrip
from app.services.planner_service import (
    calculate_planner_destinations_sync,
    search_and_rank_planner_flights
)
from app.services.exchange_service import get_eur_huf_rate
from app.scrapers.accommodation_scraper import get_all_stays, parse_accommodation_results

router = APIRouter(prefix="/api", tags=["Planner v2"])

# In-memory status & trip stores
planner_dest_status: Dict[str, Any] = {}
active_trips: Dict[str, Any] = {}

def get_current_user_from_req(request: Request) -> Optional[str]:
    # Lazy session lookup helper
    from app.main import sessions
    token = request.cookies.get("session_token")
    return sessions.get(token) if token else None

# Pydantic Schemas
class MasterPlannerIntake(BaseModel):
    origin: str = "Budapest"
    date_mode: str = "month"
    month: str = "9"
    year: int = 2026
    duration: int = 7
    exact_out_date: Optional[str] = None
    exact_in_date: Optional[str] = None
    out_from: Optional[str] = None
    out_to: Optional[str] = None
    in_from: Optional[str] = None
    in_to: Optional[str] = None
    min_stay: Optional[int] = None
    max_stay: Optional[int] = None
    adults: int = 2
    children: int = 0
    target_temp: float = 24.0
    min_safety: int = 50
    preferred_regions: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    flight_direct_only: bool = False
    flight_max_stops: int = 1
    preferred_departure_time: str = "any"
    max_flight_duration_h: Optional[float] = None
    hotel_min_stars: int = 3
    hotel_min_rating: float = 7.5
    hotel_types: Optional[List[str]] = None
    breakfast: bool = False
    amenities: Optional[List[str]] = None
    weight_total_cost: float = 34.0
    weight_weather: float = 33.0
    weight_safety: float = 33.0
    ahp_comparisons: Optional[Dict[str, float]] = None
    ahp_weights: Optional[Dict[str, float]] = None

class PlannerFlightSearchRequest(BaseModel):
    origin: str = "Budapest"
    destination: str = "Róma"
    date_mode: str = "month"
    month: int = 9
    year: int = 2026
    duration: int = 7
    exact_out_date: Optional[str] = None
    exact_in_date: Optional[str] = None
    out_from: Optional[str] = None
    out_to: Optional[str] = None
    in_from: Optional[str] = None
    in_to: Optional[str] = None
    min_stay: Optional[int] = None
    max_stay: Optional[int] = None
    adults: int = 2
    children: int = 0
    direct_only: bool = False
    max_stops: int = 1
    departure_pref: str = "any"
    max_duration_h: Optional[float] = None
    weights: Optional[Dict[str, float]] = None
    promethee_params: Optional[Dict[str, Any]] = None

class PlannerStaySearchRequest(BaseModel):
    city: str = "Róma"
    country: Optional[str] = "Olaszország"
    checkin: str = "2026-09-10"
    checkout: str = "2026-09-17"
    adults: int = 2
    min_stars: int = 3
    min_rating: float = 7.5
    price_min: float = 0.0
    price_max: Optional[float] = None
    hotel_types: Optional[List[str]] = None
    breakfast: bool = False
    amenities: Optional[List[str]] = None


def run_planner_destinations_task(user_key: str, data: MasterPlannerIntake):
    global planner_dest_status
    planner_dest_status[user_key] = {
        "status": "running",
        "progress": 5,
        "status_text": "Célállomások éghajlati és repülési adatainak elemzése..."
    }
    try:
        def on_prog(p, txt):
            planner_dest_status[user_key]["progress"] = p
            planner_dest_status[user_key]["status_text"] = txt

        weights = data.ahp_weights or {
            "total_cost": getattr(data, "weight_total_cost", 34.0),
            "weather": data.weight_weather,
            "safety": data.weight_safety
        }

        m_int = 9
        try:
            if data.month != "any":
                m_int = int(data.month)
        except Exception:
            m_int = 9

        results = calculate_planner_destinations_sync(
            origin=data.origin,
            adults=data.adults,
            children=data.children,
            date_mode=data.date_mode,
            month=m_int,
            duration_days=data.duration,
            exact_out_date=data.exact_out_date,
            exact_in_date=data.exact_in_date,
            out_from=data.out_from,
            out_to=data.out_to,
            in_from=data.in_from,
            in_to=data.in_to,
            min_stay=data.min_stay,
            max_stay=data.max_stay,
            year=data.year,
            target_temp=data.target_temp,
            min_safety=data.min_safety,
            preferred_regions=data.preferred_regions,
            exclusions=data.exclusions,
            weights=weights,
            ahp_comparisons=data.ahp_comparisons,
            progress_callback=on_prog
        )

        planner_dest_status[user_key] = {
            "status": "done",
            "progress": 100,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        print(f"[PLANNER ERROR] {e}")
        planner_dest_status[user_key] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }


@router.post("/planner/init-destinations")
async def init_planner_destinations(data: MasterPlannerIntake, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user_from_req(request) or "guest_planner"
    user_key = f"planner_{user}"
    planner_dest_status[user_key] = {"status": "running", "progress": 0, "status_text": "Keresés indítása..."}
    background_tasks.add_task(run_planner_destinations_task, user_key, data)
    return JSONResponse({"status": "ok", "message": "Destination calculation started"})


@router.get("/planner/destinations-status")
async def get_planner_destinations_status(request: Request):
    user = get_current_user_from_req(request) or "guest_planner"
    user_key = f"planner_{user}"
    return JSONResponse(planner_dest_status.get(user_key, {"status": "idle"}))


@router.post("/planner/search-flights")
async def api_planner_search_flights(req: PlannerFlightSearchRequest, request: Request):
    try:
        flights = search_and_rank_planner_flights(
            origin=req.origin,
            destination=req.destination,
            date_mode=req.date_mode,
            month=req.month,
            duration_days=req.duration,
            exact_out_date=req.exact_out_date,
            exact_in_date=req.exact_in_date,
            out_from=req.out_from,
            out_to=req.out_to,
            in_from=req.in_from,
            in_to=req.in_to,
            min_stay=req.min_stay,
            max_stay=req.max_stay,
            adults=req.adults,
            children=req.children,
            direct_only=req.direct_only,
            max_stops=req.max_stops,
            year=req.year,
            departure_pref=req.departure_pref,
            max_duration_h=req.max_duration_h,
            weights=req.weights,
            promethee_params=req.promethee_params
        )

        return JSONResponse({"status": "ok", "count": len(flights), "flights": flights})
    except Exception as e:
        print(f"[PLANNER FLIGHT ERROR] {e}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@router.post("/planner/search-stays")
async def api_planner_search_stays(req: PlannerStaySearchRequest, request: Request):
    try:
        from datetime import datetime as dt
        try:
            d_start = dt.strptime(req.checkin, "%Y-%m-%d")
            d_end = dt.strptime(req.checkout, "%Y-%m-%d")
            num_nights = max(1, (d_end - d_start).days)
        except Exception:
            num_nights = 7

        eur_rate = get_eur_huf_rate()
        p_min_eur = 0
        p_max_eur = (req.price_max * num_nights) / eur_rate if (req.price_max and req.price_max < 900000) else 9007199254740991
        cozy_min_rating = (req.min_rating * 10) if (0 < req.min_rating <= 10) else req.min_rating

        city_clean = req.city.strip()
        country_clean = req.country.strip() if req.country else ""
        if "," in city_clean and not country_clean:
            parts = city_clean.split(",", 1)
            city_clean = parts[0].strip()
            country_clean = parts[1].strip()

        raw_results = get_all_stays(
            city=city_clean,
            country=country_clean,
            start_date=req.checkin,
            end_date=req.checkout,
            adults=req.adults,
            price_min=p_min_eur,
            price_max=p_max_eur,
            min_rating=cozy_min_rating,
            accommodation_types=req.hotel_types,
            amenities=req.amenities,
            breakfast=req.breakfast
        )

        if not raw_results or 'entries' not in raw_results or not raw_results['entries'] or raw_results.get('error'):
            # Fallback helper
            from app.main import generate_mock_stays
            raw_results = generate_mock_stays(city_clean, country_clean)

        parsed = parse_accommodation_results(raw_results)
        
        for st in parsed:
            nightly_huf = st.get('price_huf', 0)
            st['price_per_night_huf'] = nightly_huf
            st['price_total_huf'] = nightly_huf * num_nights
            st['stay_nights'] = num_nights

        return JSONResponse({"status": "ok", "count": len(parsed), "stays": parsed[:25]})
    except Exception as e:
        print(f"[PLANNER STAY ERROR] {e}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@router.post("/trip/sync")
async def sync_unified_trip(trip: UnifiedTrip, request: Request):
    user = get_current_user_from_req(request) or "default_user"
    data = trip.model_dump()
    active_trips[user] = data
    active_trips[trip.trip_id] = data
    return JSONResponse({"status": "ok", "trip_id": trip.trip_id})


@router.get("/trip/active")
async def get_active_trip(request: Request, trip_id: Optional[str] = None):
    user = get_current_user_from_req(request) or "default_user"
    if trip_id and trip_id in active_trips:
        return JSONResponse(active_trips[trip_id])
    if user in active_trips:
        return JSONResponse(active_trips[user])
    return JSONResponse({"trip_id": None, "status": "empty"})
