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
