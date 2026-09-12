"""
Optivoya Router: Destination Matcher Module (Candidate Scoring, Climate, Safety & Ranking)
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import templates, IS_PRODUCTION
from app.core.auth import get_current_user
from app.services.destination_service import get_filtered_destinations, load_all_destinations
from app.services.destination_scoring_service import calculate_destination_rankings

router = APIRouter(tags=["Destinations"])

destination_sessions: Dict[str, Any] = {}
dest_calculation_status: Dict[str, Any] = {}

class DestConstraints(BaseModel):
    date_mode: str = "month"
    exact_out_date: Optional[str] = None
    exact_in_date: Optional[str] = None
    out_from: Optional[str] = None
    out_to: Optional[str] = None
    in_from: Optional[str] = None
    in_to: Optional[str] = None
    min_stay: Optional[int] = None
    max_stay: Optional[int] = None
    month: str = "9"
    duration: int = 7
    origin: str = "Budapest"
    budget_daily: float = 150.0
    budget_strictness: str = "soft"
    exclusions: List[str] = []
    adults: int = 2
    children: int = 0

class DestCriteria(BaseModel):
    criteria: List[str]

class DestAHP(BaseModel):
    comparisons: Dict[str, float]

def get_dest_session(user: str):
    if user not in destination_sessions:
        destination_sessions[user] = {"filtered": [], "criteria": [], "weights": [], "constraints": {}}
    return destination_sessions[user]

@router.get("/destination-matcher", response_class=HTMLResponse)
async def destination_matcher_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if IS_PRODUCTION:
        return RedirectResponse(url="/home", status_code=303)
    if user:
        session = get_dest_session(user)
        session["results"] = []
        if user in dest_calculation_status:
            dest_calculation_status[user] = {"status": "idle", "progress": 0}
    return templates.TemplateResponse("destination/destination_matcher.html", {"request": request, "user": user})

@router.get("/destination-criteria", response_class=HTMLResponse)
async def destination_criteria_page(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("destination/destination_criteria.html", {"request": request, "user": user})

@router.get("/destination-ahp", response_class=HTMLResponse)
async def destination_ahp_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    crit_map = {
        "weather": "Időjárás", "cost": "Költségek", "safety": "Biztonság", 
        "vibe": "Hangulat", "crowds": "Tömeg", "travel_time": "Utazás"
    }
    selected_criteria = [{"id": c, "name": crit_map.get(c, c)} for c in session.get("criteria", [])]
    return templates.TemplateResponse("destination/destination_ahp.html", {
        "request": request, 
        "selected_criteria": selected_criteria
    })

@router.post("/api/destination-constraints")
async def save_constraints(data: DestConstraints, request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    session = get_dest_session(user)
    session["constraints"] = data.dict()
    filtered = get_filtered_destinations(data.exclusions)
    session["filtered"] = filtered
    return {"status": "ok", "count": len(filtered)}

@router.post("/api/destination-criteria")
async def save_criteria(data: DestCriteria, request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    session = get_dest_session(user)
    session["criteria"] = data.criteria
    return {"status": "ok"}


# ====================================================================
# EXPERIENCE & ACTIVITY INTELLIGENCE V2 ENDPOINTS
# ====================================================================

@router.get("/api/destinations/{destination_id}/experience-profile")
@router.get("/api/v2/destinations/{destination_id}/experience-profile")
async def get_destination_experience_profile(destination_id: str):
    """Instant lookup (<2ms) of pre-aggregated experience profile from ultra-fast cache."""
    from app.services.experience.cache import experience_cache
    profile = experience_cache.get_destination_profile(destination_id)
    if not profile and "bari" in destination_id.lower():
        profile = experience_cache.get_destination_profile("IT_BARI")
    if not profile:
        raise HTTPException(status_code=404, detail="Experience profile not found for destination")
    return profile

@router.get("/api/destinations/{destination_id}/activities")
@router.get("/api/v2/destinations/{destination_id}/activities")
async def get_destination_activities(
    destination_id: str,
    category: Optional[str] = None,
    persona: Optional[str] = None,
    price_level: Optional[str] = None,
    indoor_outdoor: Optional[str] = None
):
    """Returns canonical experience entities for destination with optional multi-dimensional filters."""
    from app.services.experience.cache import experience_cache
    dest_key = destination_id.upper()
    if not dest_key.startswith("IT_") and "bari" in dest_key.lower():
        dest_key = "IT_BARI"

    entities = experience_cache.get_destination_entities(dest_key, category=category)
    if not entities and "bari" in destination_id.lower():
        entities = experience_cache.get_destination_entities("IT_BARI", category=category)

    # Apply filters
    filtered = entities
    if persona:
        filtered = [e for e in filtered if persona in e.get("metadata", {}).get("persona_tags", [])]
    if price_level:
        filtered = [e for e in filtered if e.get("price_level") == price_level]
    if indoor_outdoor:
        filtered = [e for e in filtered if e.get("metadata", {}).get("indoor_outdoor") == indoor_outdoor]

    from app.services.experience.trip_generator import trip_generator
    recommended = trip_generator.generate_recommended_experiences(dest_key, persona=persona, limit=8)

    return {
        "destination_id": dest_key,
        "count": len(filtered),
        "activities": filtered,
        "recommended": recommended
    }

@router.get("/api/destinations/{destination_id}/itinerary")
@router.get("/api/v2/destinations/{destination_id}/itinerary")
async def get_destination_itinerary(
    destination_id: str,
    days: int = 3,
    start_date: Optional[str] = None,
    persona: Optional[str] = None,
    selected_activities: Optional[str] = None,
    day_start: Optional[str] = None,
    day_end: Optional[str] = None,
    max_walk: Optional[int] = None
):
    """Generates an intelligent multi-day activity itinerary using the walkability graph and temporal slots."""
    from app.services.experience.trip_generator import trip_generator
    dest_key = destination_id.upper()
    if not dest_key.startswith("IT_") and "bari" in dest_key.lower():
        dest_key = "IT_BARI"

    selected_ids = [s.strip() for s in selected_activities.split(",") if s.strip()] if selected_activities else None
    logistics = {}
    if day_start: logistics["day_start_time"] = day_start
    if day_end: logistics["day_end_time"] = day_end
    if max_walk: logistics["max_walking_minutes"] = max_walk

    itinerary = trip_generator.generate_trip_itinerary(
        destination_id=dest_key,
        num_days=days,
        start_date_str=start_date,
        persona=persona,
        selected_activity_ids=selected_ids,
        logistics=logistics
    )
    return itinerary
