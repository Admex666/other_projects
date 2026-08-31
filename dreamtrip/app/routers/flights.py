"""
Optivoya Router: Flight Intelligence Module (Kiwi GraphQL Search, Filter, AHP & Proposal Export)
"""
import os
import gc
import json
import math
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import templates
from app.core.auth import get_current_user
from app.scrapers.scraper import get_kiwi_tokens, search_flights_by_city_name_v2, create_return_combinations

router = APIRouter(tags=["Flights"])

# State
results = {"status": "idle", "data": None, "error": None}
raw_flight_data = {"data": None, "count": 0}
filtered_flights = {}
user_filter_params = {}
user_ahp_weights = {}
ranked_results = {}
calculation_status = {}
shared_proposals = {}

# Popular Origins & Destinations
POPULAR_ORIGINS = [
    {"id": "budapest_hu", "code": "BUD", "name": "Budapest", "city_name": "Budapest", "country_name": "Magyarország", "type": "city", "display": "Budapest (BUD)", "sub": "Magyarország • Minden repülőtér"},
    {"id": "debrecen_hu", "code": "DEB", "name": "Debrecen", "city_name": "Debrecen", "country_name": "Magyarország", "type": "city", "display": "Debrecen (DEB)", "sub": "Magyarország • Minden repülőtér"},
    {"id": "vienna_at", "code": "VIE", "name": "Bécs", "city_name": "Bécs / Vienna", "country_name": "Ausztria", "type": "city", "display": "Bécs / Vienna (VIE)", "sub": "Ausztria • Minden repülőtér"},
    {"id": "bratislava_sk", "code": "BTS", "name": "Pozsony", "city_name": "Pozsony / Bratislava", "country_name": "Szlovákia", "type": "city", "display": "Pozsony / Bratislava (BTS)", "sub": "Szlovákia • Minden repülőtér"},
]

POPULAR_DESTINATIONS = [
    {"id": "barcelona_es", "code": "BCN", "name": "Barcelona", "city_name": "Barcelona", "country_name": "Spanyolország", "type": "city", "display": "Barcelona (BCN)", "sub": "Spanyolország • Minden repülőtér"},
    {"id": "rome_it", "code": "ROM", "name": "Róma", "city_name": "Róma / Rome", "country_name": "Olaszország", "type": "city", "display": "Róma (ROM)", "sub": "Olaszország • Minden repülőtér"},
    {"id": "london_gb", "code": "LON", "name": "London", "city_name": "London", "country_name": "Egyesült Királyság", "type": "city", "display": "London (LON)", "sub": "Egyesült Királyság • Minden repülőtér"},
    {"id": "paris_fr", "code": "PAR", "name": "Párizs", "city_name": "Párizs / Paris", "country_name": "Franciaország", "type": "city", "display": "Párizs (PAR)", "sub": "Franciaország • Minden repülőtér"},
    {"id": "milan_it", "code": "MIL", "name": "Milánó", "city_name": "Milánó / Milan", "country_name": "Olaszország", "type": "city", "display": "Milánó (MIL)", "sub": "Olaszország • Minden repülőtér"},
    {"id": "palma_de_mallorca_es", "code": "PMI", "name": "Palma de Mallorca", "city_name": "Mallorca (PMI)", "country_name": "Spanyolország", "type": "city", "display": "Mallorca (PMI)", "sub": "Spanyolország • Palma repülőtér"},
]

location_autocomplete_cache = {}

# Schemas
class SearchParams(BaseModel):
    origin: str
    destination: str
    out_from: str
    out_to: str
    in_from: str
    in_to: str
    adults: int = 1
    children: int = 0
    infants: int = 0
    duration: int = 7

class FilterParams(BaseModel):
    out_time_min: int = 0
    out_time_max: int = 23
    in_time_min: int = 0
    in_time_max: int = 23
    out_days: list = []
    in_days: list = []
    max_stops: int = 2
    price_min: float = 0
    price_max: float = 500000
    stay_min: int = 1
    stay_max: int = 30
    max_total_duration: float = 24.0

class AHPParams(BaseModel):
    price_vs_duration: float
    price_vs_stops: float
    duration_vs_stops: float

class FunctionConfig(BaseModel):
    type: str
    q: float
    p: float

class PreferenceConfig(BaseModel):
    price: FunctionConfig
    duration: FunctionConfig
    stops: FunctionConfig

class ProposalItem(BaseModel):
    rank: int
    airline: str
    out_flight_number: str
    in_flight_number: str
    out_departure: str
    out_arrival: str
    in_departure: str
    in_arrival: str
    out_duration: str
    in_duration: str
    total_stops: int
    price: str
    deep_link: str

class ProposalRequest(BaseModel):
    title: str
    client_name: str
    client_email: str
    notes: Optional[str] = ""
    flights: List[ProposalItem]

def run_intelligence_scraper(p: SearchParams):
    global results, raw_flight_data
    results = {"status": "running", "progress": 0, "status_text": "Keresési paraméterek ellenőrzése...", "data": None, "error": None}
    
    def update_progress(base, scale, p_val):
        current = base + (p_val * scale / 100)
        results["progress"] = int(current)
    
    try:
        from app.scrapers.scraper import get_city_id_api
        origin_id = get_city_id_api(p.origin)
        if not origin_id:
            results = {"status": "error", "error": f"Nem található érvényes repülőtér a megadott indulási városhoz: '{p.origin}'."}
            return
            
        dest_id = get_city_id_api(p.destination)
        if not dest_id:
            results = {"status": "error", "error": f"Nem található érvényes repülőtér a megadott célállomáshoz: '{p.destination}'."}
            return

        try:
            d_out_s = pd.to_datetime(p.out_from)
            d_out_e = pd.to_datetime(p.out_to)
            out_days = max(1, (d_out_e - d_out_s).days + 1)
            out_limit = int(min(150, max(30, out_days * 5)))
        except Exception:
            out_limit = 50

        try:
            d_in_s = pd.to_datetime(p.in_from)
            d_in_e = pd.to_datetime(p.in_to)
            in_days = max(1, (d_in_e - d_in_s).days + 1)
            in_limit = int(min(150, max(30, in_days * 5)))
        except Exception:
            in_limit = 50

        results["status_text"] = "Adatkapcsolat megteremtése..."
        tokens = get_kiwi_tokens(headless=True)

        results["status_text"] = f"Odaút keresése ({p.origin} -> {p.destination}, {p.adults} felnőtt)..."
        outbound = search_flights_by_city_name_v2(
            origin_name=p.origin,
            destination_name=p.destination,
            tokens=tokens,
            date_from=p.out_from,
            date_to=p.out_to,
            adults=p.adults,
            children=p.children,
            infants=p.infants,
            limit=out_limit,
            progress_callback=lambda p_val: update_progress(5, 40, p_val)
        )
        
        results["progress"] = 45
        results["status_text"] = f"Visszaút keresése ({p.destination} -> {p.origin}, {p.adults} felnőtt)..."
        
        inbound = search_flights_by_city_name_v2(
            origin_name=p.destination,
            destination_name=p.origin,
            tokens=tokens,
            date_from=p.in_from,
            date_to=p.in_to,
            adults=p.adults,
            children=p.children,
            infants=p.infants,
            limit=in_limit,
            progress_callback=lambda p_val: update_progress(45, 40, p_val)
        )
        
        results["progress"] = 90
        results["status_text"] = "Útvonalak kombinálása és ellenőrzése..."
        
        if outbound.empty or inbound.empty:
            results = {"status": "done", "progress": 100, "data": [], "count": 0, "error": "Nincs járat a megadott feltételekkel."}
            return

        min_stay = max(1, p.duration - 2) if p.duration else 1
        max_stay = (p.duration + 2) if p.duration else None
        combinations = create_return_combinations(outbound, inbound, min_stay_days=min_stay, max_stay_days=max_stay)
        
        raw_flight_data["data"] = combinations
        raw_flight_data["count"] = len(combinations)

        results = {
            "status": "done", 
            "progress": 100,
            "count": len(combinations),
            "error": None
        }
    except Exception as e:
        results = {"status": "error", "error": str(e)}

@router.get("/flight-intelligence", response_class=HTMLResponse)
async def flight_intelligence(
    request: Request, 
    destination: Optional[str] = None, 
    origin: Optional[str] = None, 
    out_from: Optional[str] = None, 
    out_to: Optional[str] = None, 
    in_from: Optional[str] = None, 
    in_to: Optional[str] = None,
    min_stay: Optional[int] = None,
    max_stay: Optional[int] = None,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    duration: Optional[int] = None,
    from_matcher: Optional[int] = None
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("flights/flight_intelligence.html", {
        "request": request, 
        "user": user,
        "prefill": {
            "destination": destination,
            "origin": origin,
            "out_from": out_from,
            "out_to": out_to,
            "in_from": in_from,
            "in_to": in_to,
            "min_stay": min_stay,
            "max_stay": max_stay,
            "adults": adults,
            "children": children,
            "duration": duration,
            "from_matcher": bool(from_matcher)
        }
    })

@router.get("/api/locations/autocomplete")
async def autocomplete_locations(term: str = "", mode: str = "all"):
    clean_term = term.strip()
    if not clean_term:
        if mode == "origin":
            return JSONResponse(content=POPULAR_ORIGINS)
        elif mode == "destination":
            return JSONResponse(content=POPULAR_DESTINATIONS)
        return JSONResponse(content=POPULAR_ORIGINS + POPULAR_DESTINATIONS[:2])
    
    cache_key = clean_term.lower()
    if cache_key in location_autocomplete_cache:
        return JSONResponse(content=location_autocomplete_cache[cache_key])
    
    url = f"https://api.skypicker.com/locations?term={requests.utils.quote(clean_term)}&limit=15&active_only=true"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json().get("locations", [])
            results_loc = []
            seen_keys = set()
            for loc in data:
                loc_type = loc.get("type")
                if loc_type not in ["city", "airport"]:
                    continue
                code = loc.get("code", "")
                name = loc.get("name", "")
                city = loc.get("city", {})
                city_name = city.get("name", name) if isinstance(city, dict) else name
                country = loc.get("country") or (loc.get("city", {}).get("country") if isinstance(loc.get("city"), dict) else {}) or {}
                country_name = country.get("name", "") if isinstance(country, dict) else ""
                display_str = f"{city_name} ({code})" if code else city_name
                dedup_key = (city_name.strip().lower(), country_name.strip().lower()) if mode == "destination" else (display_str.strip().lower(), country_name.strip().lower())
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                sub = "Minden repülőtér" if loc_type == "city" else name
                results_loc.append({
                    "id": loc.get("id"),
                    "code": code,
                    "name": name,
                    "city": city_name,
                    "country": country_name,
                    "display": display_str,
                    "sub": f"{country_name} • {sub}" if country_name else sub
                })
                if len(results_loc) >= 8:
                    break
            location_autocomplete_cache[cache_key] = results_loc
            return JSONResponse(content=results_loc)
    except Exception as e:
        print(f"[WARN] Error fetching locations: {e}")
    return JSONResponse(content=[])

@router.get("/search-status")
async def get_search_status():
    global results
    return JSONResponse(content=results)

@router.post("/start-intelligence-search")
async def start_search(params: SearchParams, background_tasks: BackgroundTasks):
    global results
    results = {"status": "running", "data": None, "error": None}
    background_tasks.add_task(run_intelligence_scraper, params)
    return {"message": "Search started"}

@router.get("/flight-intelligence-filter", response_class=HTMLResponse)
async def flight_intelligence_filter(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
        return RedirectResponse(url="/flight-intelligence", status_code=303)
    return templates.TemplateResponse("flights/flight_filter.html", {
        "request": request,
        "user": user,
        "flight_count": raw_flight_data["count"]
    })

@router.post("/api/preview-filter-count")
async def preview_filter_count(p: FilterParams, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
        return JSONResponse({"total_count": 0, "matching_count": 0})
    try:
        df = raw_flight_data["data"].copy()
        df['out_hour'] = pd.to_datetime(df['out_dep_time']).dt.hour
        df = df[(df['out_hour'] >= p.out_time_min) & (df['out_hour'] <= p.out_time_max)]
        df['in_hour'] = pd.to_datetime(df['in_dep_time']).dt.hour
        df = df[(df['in_hour'] >= p.in_time_min) & (df['in_hour'] <= p.in_time_max)]
        if p.out_days:
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            allowed_days = [day_map[d] for d in p.out_days if d in day_map]
            if allowed_days:
                df['out_weekday'] = pd.to_datetime(df['out_dep_time']).dt.dayofweek
                df = df[df['out_weekday'].isin(allowed_days)]
        if p.in_days:
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            allowed_days = [day_map[d] for d in p.in_days if d in day_map]
            if allowed_days:
                df['in_weekday'] = pd.to_datetime(df['in_dep_time']).dt.dayofweek
                df = df[df['in_weekday'].isin(allowed_days)]
        df = df[df['total_stops'] <= p.max_stops]
        df = df[(df['total_price_huf'] >= p.price_min) & (df['total_price_huf'] <= p.price_max)]
        df = df[(df['stay_days'] >= p.stay_min) & (df['stay_days'] <= p.stay_max)]
        df['total_duration'] = df['out_duration_h'] + df['in_duration_h']
        df = df[df['total_duration'] <= p.max_total_duration]
        matching = len(df)
        del df
        return JSONResponse({"total_count": raw_flight_data["count"], "matching_count": matching})
    except Exception as e:
        return JSONResponse({"total_count": raw_flight_data.get("count", 0), "matching_count": 0, "error": str(e)})

@router.post("/api/apply-filters")
async def apply_filters(params: FilterParams, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    background_tasks.add_task(run_filter_scraper_task, user, params)
    return {"message": "Filtering started"}

@router.get("/api/filter-status/{username}")
async def filter_status(username: str):
    return JSONResponse(filtered_flights.get(username, {"status": "idle"}))

def run_filter_scraper_task(username: str, p: FilterParams):
    global filtered_flights, raw_flight_data, user_filter_params
    filtered_flights[username] = {"status": "running", "progress": 0, "status_text": "Szűrés előkészítése...", "count": None, "error": None}
    user_filter_params[username] = p
    try:
        if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
            filtered_flights[username] = {"status": "error", "progress": 0, "count": 0, "error": "Nincs adat a memóriában."}
            return
        df = raw_flight_data["data"].copy()
        df['out_hour'] = pd.to_datetime(df['out_dep_time']).dt.hour
        df = df[(df['out_hour'] >= p.out_time_min) & (df['out_hour'] <= p.out_time_max)]
        df['in_hour'] = pd.to_datetime(df['in_dep_time']).dt.hour
        df = df[(df['in_hour'] >= p.in_time_min) & (df['in_hour'] <= p.in_time_max)]
        if p.out_days:
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            allowed_days = [day_map[d] for d in p.out_days if d in day_map]
            if allowed_days:
                df['out_weekday'] = pd.to_datetime(df['out_dep_time']).dt.dayofweek
                df = df[df['out_weekday'].isin(allowed_days)]
        if p.in_days:
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            allowed_days = [day_map[d] for d in p.in_days if d in day_map]
            if allowed_days:
                df['in_weekday'] = pd.to_datetime(df['in_dep_time']).dt.dayofweek
                df = df[df['in_weekday'].isin(allowed_days)]
        df = df[df['total_stops'] <= p.max_stops]
        df = df[(df['total_price_huf'] >= p.price_min) & (df['total_price_huf'] <= p.price_max)]
        df = df[(df['stay_days'] >= p.stay_min) & (df['stay_days'] <= p.stay_max)]
        df['total_duration'] = df['out_duration_h'] + df['in_duration_h']
        df = df[df['total_duration'] <= p.max_total_duration]
        if len(df) == 0:
            filtered_flights[username] = {"status": "error", "progress": 0, "count": 0, "error": "0 járatkombináció maradt."}
            del df
            gc.collect()
            return
        if len(df) > 1000:
            df = df.sort_values('total_price_huf').head(1000)
        date_columns = ['out_dep_time', 'out_arr_time', 'in_dep_time', 'in_arr_time']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        filtered_flights[username] = {
            "status": "done",
            "progress": 100,
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "error": None
        }
        del df
        gc.collect()
    except Exception as e:
        filtered_flights[username] = {"status": "error", "progress": 0, "count": None, "error": str(e)}

@router.get("/flight-intelligence-ahp", response_class=HTMLResponse)
async def flight_intelligence_ahp(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user not in filtered_flights or filtered_flights[user].get("status") != "done" or filtered_flights[user].get("count", 0) == 0:
        return RedirectResponse(url="/flight-intelligence-filter", status_code=303)
    return templates.TemplateResponse("flights/flight_ahp.html", {
        "request": request, 
        "user": user,
        "flight_count": filtered_flights[user].get("count", 0)
    })
