"""
Optivoya Router: Trip & Itinerary V2 Module (Home, Trip Generation, Reoptimization & POI Search)
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import templates, IS_PRODUCTION, APP_ENV
from app.core.auth import get_current_user
from app.models.models import TravelPreferences
from app.services import scoring_service, itinerary_service, maps_service

router = APIRouter(tags=["Trip & Itinerary"])

class DiscoverRequest(BaseModel):
    preferences: TravelPreferences
    origin: str = "Budapest"
    month: Optional[str] = "any"

class GenerateTripRequest(BaseModel):
    city_id: str
    city_name: str
    lat: float
    lng: float
    start_date: str
    end_date: str

class ReoptimizeRequest(BaseModel):
    city_id: str
    city_name: str
    lat: float
    lng: float
    day_data: Dict[str, Any]

@router.get("/home", response_class=HTMLResponse)
@router.get("/tools", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("home.html", {
        "request": request, 
        "user": user,
        "is_production": IS_PRODUCTION,
        "app_env": APP_ENV
    })

@router.post("/api/v2/trip/discover")
async def api_discover(req: DiscoverRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from app.services.destination_service import load_all_destinations
        dests = load_all_destinations()
        scored_cities = scoring_service.calculate_city_scores(
            dests=dests,
            prefs=req.preferences,
            origin_city=req.origin,
            month=req.month
        )
        results = []
        for c in scored_cities:
            c_dict = c.dict()
            c_dict["explanation"] = c.__dict__.get("explanation", "Optimális választás a szempontjaid alapján.")
            results.append(c_dict)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v2/trip/generate")
async def api_generate_trip(req: GenerateTripRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        itinerary = itinerary_service.generate_default_itinerary(
            city_id=req.city_id,
            city_name=req.city_name,
            lat=req.lat,
            lng=req.lng,
            start_date_str=req.start_date,
            end_date_str=req.end_date
        )
        return itinerary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v2/trip/reoptimize")
async def api_reoptimize_trip(req: ReoptimizeRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        updated_day = itinerary_service.reoptimize_itinerary_day(
            day_data=req.day_data,
            city_id=req.city_id,
            city_name=req.city_name,
            lat=req.lat,
            lng=req.lng
        )
        return updated_day
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v2/poi/search")
async def api_search_poi(city_name: str, city_id: str, lat: float, lng: float, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        pois = maps_service.get_city_pois(
            city_name=city_name,
            city_id=city_id,
            lat=lat,
            lng=lng
        )
        return pois
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
