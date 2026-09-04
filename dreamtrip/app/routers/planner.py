import os
import time
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


from app.core.config import templates, IS_PRODUCTION
from app.core.auth import get_current_user, is_dummy_mode_allowed
from app.models.models import UnifiedTrip
from app.services.planner_service import (
    calculate_planner_destinations_sync,
    search_and_rank_planner_flights
)
from app.services.dummy_planner_service import (
    generate_dummy_destinations,
    generate_dummy_flights,
    generate_dummy_stays
)
from app.services.exchange_service import get_eur_huf_rate
from app.services.analytics_service import record_telemetry_event
from app.scrapers.accommodation_scraper import get_all_stays, parse_accommodation_results

router = APIRouter(tags=["Master Planner"])


# In-memory status & active trips
planner_dest_status: Dict[str, Any] = {}
active_trips: Dict[str, Any] = {}

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
    dummy_mode: Optional[bool] = False

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
    dummy_mode: Optional[bool] = False

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
    dummy_mode: Optional[bool] = False

# Background Task
def run_planner_destinations_task(user_key: str, data: MasterPlannerIntake, is_dummy: bool = False, session_id: Optional[str] = None):
    global planner_dest_status
    planner_dest_status[user_key] = {
        "status": "running",
        "progress": 25,
        "status_text": "[Szimulációs mód] Célállomások gyors betöltése..." if is_dummy else "Célállomások éghajlati és repülési adatainak elemzése..."
    }
    try:
        if is_dummy:
            time.sleep(0.35)
            results = generate_dummy_destinations(data)
            planner_dest_status[user_key] = {
                "status": "done",
                "progress": 100,
                "count": len(results),
                "results": results,
                "is_dummy": True
            }
            record_telemetry_event(
                user_id=user_key.replace("planner_", ""),
                session_id=session_id,
                event_type="search_completed",
                module="destination_matcher",
                search_params={
                    "origin": data.origin,
                    "month": data.month,
                    "duration": data.duration,
                    "adults": data.adults,
                    "dummy_mode": True
                },
                results_count=len(results),
                success=True
            )
            return

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
        record_telemetry_event(
            user_id=user_key.replace("planner_", ""),
            session_id=session_id,
            event_type="search_completed",
            module="destination_matcher",
            search_params={
                "origin": data.origin,
                "month": data.month,
                "duration": data.duration,
                "adults": data.adults,
                "target_temp": data.target_temp,
                "min_safety": data.min_safety
            },
            results_count=len(results),
            success=True
        )
    except Exception as e:
        print(f"[PLANNER ERROR] {e}")
        planner_dest_status[user_key] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }
        record_telemetry_event(
            user_id=user_key.replace("planner_", ""),
            session_id=session_id,
            event_type="search_completed",
            module="destination_matcher",
            search_params={"origin": data.origin, "month": data.month},
            success=False,
            error_message=str(e)
        )

# HTML View
@router.get("/planner", response_class=HTMLResponse)
async def master_planner_page(request: Request):
    user = get_current_user(request)
    dummy_allowed = is_dummy_mode_allowed(user)
    return templates.TemplateResponse("planner/planner_wizard.html", {
        "request": request,
        "user": user,
        "dummy_mode_allowed": dummy_allowed,
        "is_production": IS_PRODUCTION
    })

# API Endpoints
@router.post("/api/planner/init-destinations")
async def init_planner_destinations(data: MasterPlannerIntake, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request) or "guest_planner"
    session_id = request.headers.get("x-session-id") or request.cookies.get("optivoya_session_id")
    user_key = f"planner_{user}"
    is_dummy = is_dummy_mode_allowed(user) and (
        bool(data.dummy_mode)
        or request.headers.get("x-planner-dummy-mode") == "true"
        or request.cookies.get("planner_dummy_mode") == "1"
        or request.query_params.get("dummy") == "1"
    )
    planner_dest_status[user_key] = {
        "status": "running",
        "progress": 0,
        "status_text": "[Szimulációs mód] Célállomások indítása..." if is_dummy else "Keresés indítása..."
    }
    background_tasks.add_task(run_planner_destinations_task, user_key, data, is_dummy, session_id)
    return JSONResponse({"status": "ok", "message": "Destination calculation started", "is_dummy": is_dummy})

@router.get("/api/planner/destinations-status")
async def get_planner_destinations_status(request: Request):
    user = get_current_user(request) or "guest_planner"
    user_key = f"planner_{user}"
    return JSONResponse(planner_dest_status.get(user_key, {"status": "idle"}))

@router.post("/api/planner/search-flights")
async def api_planner_search_flights(req: PlannerFlightSearchRequest, request: Request):
    t0 = time.perf_counter()
    user = get_current_user(request) or "guest_planner"
    session_id = request.headers.get("x-session-id") or request.cookies.get("optivoya_session_id")
    is_dummy = is_dummy_mode_allowed(user) and (
        bool(req.dummy_mode)
        or request.headers.get("x-planner-dummy-mode") == "true"
        or request.cookies.get("planner_dummy_mode") == "1"
        or request.query_params.get("dummy") == "1"
    )
    if is_dummy:
        flights = generate_dummy_flights(req)
        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="flight_intelligence",
            search_params={
                "origin": req.origin,
                "destination": req.destination,
                "dummy_mode": True
            },
            duration_ms=duration_ms,
            results_count=len(flights),
            success=True
        )
        return JSONResponse({"status": "ok", "count": len(flights), "flights": flights, "is_dummy": True})

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

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="flight_intelligence",
            search_params={
                "origin": req.origin,
                "destination": req.destination,
                "date_mode": req.date_mode,
                "month": req.month,
                "duration": req.duration,
                "adults": req.adults
            },
            duration_ms=duration_ms,
            results_count=len(flights),
            success=True
        )

        return JSONResponse({"status": "ok", "count": len(flights), "flights": flights})
    except Exception as e:
        print(f"[PLANNER FLIGHT ERROR] {e}")
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="flight_intelligence",
            search_params={"origin": req.origin, "destination": req.destination},
            success=False,
            error_message=str(e)
        )
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


_PLANNER_STAYS_CACHE: Dict[str, List[Dict[str, Any]]] = {}

@router.post("/api/planner/search-stays")
async def api_planner_search_stays(req: PlannerStaySearchRequest, request: Request):
    t_start = time.perf_counter()
    user = get_current_user(request) or "guest_planner"
    session_id = request.headers.get("x-session-id") or request.cookies.get("optivoya_session_id")
    is_dummy = is_dummy_mode_allowed(user) and (
        bool(req.dummy_mode)
        or request.headers.get("x-planner-dummy-mode") == "true"
        or request.cookies.get("planner_dummy_mode") == "1"
        or request.query_params.get("dummy") == "1"
    )
    if is_dummy:
        stays = generate_dummy_stays(req)
        duration_ms = round((time.perf_counter() - t_start) * 1000, 1)
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="accommodation_intelligence",
            search_params={
                "city": req.city,
                "country": req.country or "",
                "dummy_mode": True
            },
            duration_ms=duration_ms,
            results_count=len(stays),
            success=True
        )
        return JSONResponse({
            "status": "ok",
            "count": len(stays),
            "stays": stays[:35],
            "meta": {
                "source": "dummy_simulation_mode",
                "timings_ms": { "stays_fetch": duration_ms }
            },
            "is_dummy": True
        })

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

        cache_key = f"{city_clean.lower()}_{country_clean.lower()}_{req.checkin}_{req.checkout}_{req.adults}_{req.min_stars}_{req.min_rating}_{req.breakfast}"
        
        # 1. Ellenőrizzük a szerveroldali memóriagyorsítótárat (0 ms)
        if cache_key in _PLANNER_STAYS_CACHE and _PLANNER_STAYS_CACHE[cache_key]:
            cached_stays = _PLANNER_STAYS_CACHE[cache_key]
            duration_ms = round((time.perf_counter() - t_start) * 1000, 1)
            return JSONResponse({
                "status": "ok",
                "count": len(cached_stays),
                "stays": cached_stays[:35],
                "meta": {
                    "source": "server_memory_cache",
                    "timings_ms": { "stays_fetch": duration_ms }
                }
            })

        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

        raw_results = None
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                get_all_stays,
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
            # Várunk a valós Cozycozy scraperre (max 28 másodperc hidegen)
            raw_results = future.result(timeout=28.0)
        except (FuturesTimeoutError, TimeoutError):
            print(f"[PLANNER STAY INFO] Cozycozy live scraper timed out for {city_clean}, using verified Cozycozy Market Benchmark.")
            raw_results = None
        except Exception as se:
            print(f"[PLANNER STAY WARN] Scraper exception for {city_clean}: {se}")
            raw_results = None
        finally:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass

        parsed = []
        if raw_results and 'entries' in raw_results and raw_results['entries'] and not raw_results.get('error'):
            parsed = parse_accommodation_results(raw_results)
            for st in parsed:
                nightly_huf = st.get('price_huf', 0)
                st['price_per_night_huf'] = nightly_huf
                st['price_total_huf'] = nightly_huf * num_nights
                st['stay_nights'] = num_nights
                st['is_market_benchmark'] = False
            
            # Mentés a szerveroldali memóriagyorsítótárba
            if parsed:
                _PLANNER_STAYS_CACHE[cache_key] = parsed

        if not parsed:
            from app.services.accommodation_market_service import generate_market_benchmark_stays
            parsed = generate_market_benchmark_stays(
                city=city_clean,
                country=country_clean,
                checkin=req.checkin,
                checkout=req.checkout,
                adults=req.adults,
                hotel_types=req.hotel_types,
                breakfast=req.breakfast,
                amenities=req.amenities
            )

        duration_ms = round((time.perf_counter() - t_start) * 1000, 1)
        user = get_current_user(request) or "guest_planner"
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="accommodation_intelligence",
            search_params={
                "city": req.city,
                "country": req.country or "",
                "checkin": req.checkin,
                "checkout": req.checkout,
                "adults": req.adults,
                "min_stars": req.min_stars,
                "min_rating": req.min_rating
            },
            duration_ms=duration_ms,
            results_count=len(parsed),
            success=True
        )

        return JSONResponse({
            "status": "ok",
            "count": len(parsed),
            "stays": parsed[:35],
            "meta": {
                "source": "live_cozycozy_scraper" if (raw_results and raw_results.get('entries')) else "market_benchmark",
                "timings_ms": {
                    "stays_fetch": duration_ms
                }
            }
        })

    except Exception as e:
        print(f"[PLANNER STAY ERROR] {e}")
        user = get_current_user(request) or "guest_planner"
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="search_completed",
            module="accommodation_intelligence",
            search_params={"city": req.city, "checkin": req.checkin, "checkout": req.checkout},
            success=False,
            error_message=str(e)
        )
        from app.services.accommodation_market_service import generate_market_benchmark_stays
        fallback_stays = generate_market_benchmark_stays(
            city=req.city,
            country=req.country or "",
            checkin=req.checkin,
            checkout=req.checkout,
            adults=req.adults
        )
        return JSONResponse({"status": "ok", "count": len(fallback_stays), "stays": fallback_stays, "is_fallback": True})


@router.get("/api/numbeo/breakdown")
async def get_numbeo_breakdown(city: str, country: Optional[str] = "", region: Optional[str] = ""):
    from app.services.numbeo_service import get_city_cost_and_safety
    daily_cost_eur, safety_index, breakdown = get_city_cost_and_safety(city, country, region)
    return JSONResponse({
        "status": "ok",
        "city": city,
        "country": country,
        "daily_cost_eur": daily_cost_eur,
        "safety_index": safety_index,
        "breakdown": breakdown
    })

@router.post("/api/trip/sync")
async def sync_unified_trip(trip: UnifiedTrip, request: Request):
    user = get_current_user(request) or "default_user"
    session_id = request.headers.get("x-session-id") or request.cookies.get("optivoya_session_id")
    data = trip.model_dump()
    active_trips[user] = data
    active_trips[trip.trip_id] = data

    # Rögzítjük az ajánlat export / szinkron eseményt ha az utazás elkészült
    if data.get("destination") and data.get("flight", {}).get("selected_flight") and data.get("accommodation", {}).get("selected_accommodation"):
        dest_name = data["destination"].get("name") or data["destination"].get("city") or "Célpont"
        record_telemetry_event(
            user_id=user,
            session_id=session_id,
            event_type="proposal_exported",
            module="proposal",
            search_params={
                "destination": dest_name, 
                "trip_id": trip.trip_id,
                "airline": data["flight"]["selected_flight"].get("airline"),
                "hotel": data["accommodation"]["selected_accommodation"].get("name")
            },
            results_count=1,
            success=True
        )

    return JSONResponse({"status": "ok", "trip_id": trip.trip_id})


@router.get("/api/trip/active")
async def get_active_trip(request: Request, trip_id: Optional[str] = None):
    user = get_current_user(request) or "default_user"
    if trip_id and trip_id in active_trips:
        return JSONResponse(active_trips[trip_id])
    if user in active_trips:
        return JSONResponse(active_trips[user])
    return JSONResponse({"trip_id": None, "status": "empty"})

@router.post("/api/trip/clear")
async def clear_active_trip(request: Request):
    user = get_current_user(request) or "default_user"
    if user in active_trips:
        del active_trips[user]
    return JSONResponse({"status": "ok"})
