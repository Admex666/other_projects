"""
Optivoya Router: Accommodation Intelligence Module (Cozycozy Live Search, Filter, UI Previews & Results)
"""
import os
import math
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import templates
from app.core.auth import get_current_user
from app.services.exchange_service import get_eur_huf_rate
from app.scrapers.accommodation_scraper import get_all_stays, parse_accommodation_results

router = APIRouter(tags=["Accommodation"])

# State
accommodation_results = {"status": "idle", "data": None, "error": None}
raw_stay_data = {"data": None, "count": 0}
filtered_stays = {}
user_stay_filter_params = {}
stay_ahp_weights = {}
stay_ranked_results = {}
stay_calculation_status = {}

class StaySearchParams(BaseModel):
    city: str
    country: str
    start_date: str
    end_date: str
    rooms: int = 1
    adults: int = 2
    children: int = 0
    price_min: float = 0
    price_max: float = 9007199254740991
    min_rating: float = 0
    accommodation_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    breakfast: bool = False

class StayFilterParams(BaseModel):
    price_min: float = 0
    price_max: float = 1000000
    min_rating: float = 0
    accommodation_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    breakfast: bool = False

def run_accommodation_scraper_task(p: StaySearchParams):
    global accommodation_results, raw_stay_data
    accommodation_results = {"status": "running", "progress": 0, "data": None, "error": None}
    
    def update_progress(p_val):
        accommodation_results["progress"] = p_val
        accommodation_results["status_text"] = f"Szállásadatok betöltése... ({p_val}%)"

    try:
        try:
            from datetime import datetime as dt
            d_start = dt.strptime(p.start_date, "%Y-%m-%d")
            d_end = dt.strptime(p.end_date, "%Y-%m-%d")
            num_nights = max(1, (d_end - d_start).days)
        except Exception:
            num_nights = 1

        eur_rate = get_eur_huf_rate()
        p_min_eur = (p.price_min * num_nights) / eur_rate
        p_max_eur = (p.price_max * num_nights) / eur_rate if p.price_max < 900000 else 9007199254740991
        cozy_min_rating = (p.min_rating * 10) if (0 < p.min_rating <= 10) else p.min_rating
        
        city_clean = p.city.strip()
        country_clean = p.country.strip() if p.country else ""
        if "," in city_clean and not country_clean:
            parts = city_clean.split(",", 1)
            city_clean = parts[0].strip()
            country_clean = parts[1].strip()
            
        raw_results = get_all_stays(
            city=city_clean,
            country=country_clean,
            start_date=p.start_date,
            end_date=p.end_date,
            rooms=p.rooms,
            adults=p.adults,
            children=p.children,
            price_min=p_min_eur,
            price_max=p_max_eur,
            min_rating=cozy_min_rating,
            accommodation_types=p.accommodation_types,
            amenities=p.amenities,
            breakfast=p.breakfast,
            progress_callback=update_progress
        )
        
        if raw_results.get("error"):
            accommodation_results = {"status": "error", "error": raw_results["error"]}
            return

        if not raw_results or 'entries' not in raw_results or not raw_results['entries']:
            accommodation_results = {"status": "done", "data": [], "count": 0, "error": "Nincs szállás a megadott feltételekkel."}
            return

        parsed = parse_accommodation_results(raw_results)
        raw_stay_data["data"] = parsed
        raw_stay_data["count"] = len(parsed)

        accommodation_results = {
            "status": "done", 
            "count": len(parsed),
            "error": None
        }
    except Exception as e:
        accommodation_results = {"status": "error", "error": str(e)}

@router.get("/accommodation-intelligence", response_class=HTMLResponse)
async def accommodation_intelligence(
    request: Request, 
    city: Optional[str] = None, 
    country: Optional[str] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("accommodation/accommodation_intelligence.html", {
        "request": request, 
        "user": user,
        "prefill": {
            "city": city,
            "country": country,
            "start_date": start_date,
            "end_date": end_date
        }
    })

# UI Redesign Previews
@router.get("/accommodation-ui-v1", response_class=HTMLResponse)
async def accommodation_ui_v1(request: Request):
    return templates.TemplateResponse("accommodation/preview_v1.html", {"request": request})

@router.get("/accommodation-ui-v2", response_class=HTMLResponse)
async def accommodation_ui_v2(request: Request):
    return templates.TemplateResponse("accommodation/preview_v2.html", {"request": request})

@router.get("/accommodation-ui-v3", response_class=HTMLResponse)
async def accommodation_ui_v3(request: Request):
    return templates.TemplateResponse("accommodation/preview_v3.html", {"request": request})

@router.get("/accommodation-ui-v2.2", response_class=HTMLResponse)
@router.get("/accommodation-ui-v2-2", response_class=HTMLResponse)
async def accommodation_ui_v2_2(request: Request):
    return templates.TemplateResponse("accommodation/preview_v2_2.html", {"request": request})

@router.post("/start-accommodation-search")
async def start_accommodation_search(params: StaySearchParams, background_tasks: BackgroundTasks):
    global accommodation_results
    accommodation_results = {"status": "running", "data": None, "error": None}
    background_tasks.add_task(run_accommodation_scraper_task, params)
    return {"message": "Accommodation search started"}

@router.get("/api/accommodation-status")
async def get_accommodation_status():
    return JSONResponse(accommodation_results)

@router.get("/search-accommodation-status")
async def search_accommodation_status():
    return JSONResponse(accommodation_results)
