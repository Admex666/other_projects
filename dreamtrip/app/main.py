from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from concurrent.futures import ThreadPoolExecutor
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
from app.scrapers.scraper import get_kiwi_tokens, search_flights_by_city_name_v2, create_return_combinations
from app.scrapers.accommodation_scraper import get_all_stays, parse_accommodation_results
import os
import secrets
import json
import math
import gc
import pandas as pd
import numpy as np
import requests
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.scrapers import scraper # Kiwi scraper
from app.scrapers import accommodation_scraper
from contextlib import asynccontextmanager
from app.models.models import TravelPreferences, Trip, ItineraryDay, ItineraryItem
from app.services import scoring_service
from app.services import itinerary_service
from app.services.exchange_service import get_eur_huf_rate
from app.services import maps_service


# Felhasználók
USERS = {"admin": "optivoya2024", "demo": "demo123", "bean": "bean", 
         "wayzio": "demo", "utazasmagus": "demo"}
sessions = {}
raw_flights_cache = {}
results = {"status": "idle", "data": None, "error": None}
accommodation_results = {"status": "idle", "data": None, "error": None}

def verify_credentials(username: str, password: str):
    return username in USERS and USERS[username] == password

def create_session(username: str):
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token

def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    return sessions.get(token) if token else None

class DestConstraints(BaseModel):
    month: str
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

class DestPreferenceDetails(BaseModel):
    weather_temp: float = 24.0
    weight_flight: float = 25.0
    weight_cost: float = 25.0
    weight_weather: float = 25.0
    weight_safety: float = 25.0

destination_db = []
destination_sessions = {}
unique_user_id_counter = 0

def load_destinations():
    global destination_db
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.abspath(os.path.join(base_dir, "..", "data", "destinations.json"))
        with open(json_path, "r", encoding="utf-8") as f:
            destination_db = json.load(f)
        print(f"Loaded {len(destination_db)} destinations from {json_path}")
    except Exception as e:
        print(f"Error loading destinations: {e}")
        destination_db = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("SERVER STARTING - RELOADED LATEST CODE")
    load_destinations()
    yield

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = (APP_ENV == "production")
print(f"[CONFIG] DreamTrip futási mód: {APP_ENV.upper()} (IS_PRODUCTION={IS_PRODUCTION})")

app = FastAPI(lifespan=lifespan)

# Static és templates
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))

security = HTTPBasic()

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if verify_credentials(username, password):
        token = create_session(username)
        response = RedirectResponse(url="/home", status_code=303)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    return RedirectResponse(url="/?error=invalid", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token in sessions:
        del sessions[token]
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    return response

@app.get("/home", response_class=HTMLResponse)
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

@app.get("/destination-matcher", response_class=HTMLResponse)
async def destination_matcher(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    # PROD módban csak a Flight és Accommodation Intelligence érhető el
    if IS_PRODUCTION:
        return RedirectResponse(url="/home", status_code=303)
    return templates.TemplateResponse("destination/destination_matcher.html", {"request": request})

@app.get("/flight-intelligence", response_class=HTMLResponse)
async def flight_intelligence(
    request: Request, 
    destination: Optional[str] = None, 
    origin: Optional[str] = None, 
    out_from: Optional[str] = None, 
    out_to: Optional[str] = None, 
    in_from: Optional[str] = None, 
    in_to: Optional[str] = None,
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
            "adults": adults,
            "children": children,
            "duration": duration,
            "from_matcher": bool(from_matcher)
        }
    })

@app.get("/accommodation-intelligence", response_class=HTMLResponse)
async def accommodation_intelligence(request: Request, city: Optional[str] = None, country: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
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

# ===== ACCOMMODATION UI REDESIGN MOCKUP PREVIEWS =====
@app.get("/accommodation-ui-v1", response_class=HTMLResponse)
async def accommodation_ui_v1(request: Request):
    return templates.TemplateResponse("accommodation/preview_v1.html", {"request": request})

@app.get("/accommodation-ui-v2", response_class=HTMLResponse)
async def accommodation_ui_v2(request: Request):
    return templates.TemplateResponse("accommodation/preview_v2.html", {"request": request})

@app.get("/accommodation-ui-v3", response_class=HTMLResponse)
async def accommodation_ui_v3(request: Request):
    return templates.TemplateResponse("accommodation/preview_v3.html", {"request": request})

@app.get("/accommodation-ui-v2.2", response_class=HTMLResponse)
@app.get("/accommodation-ui-v2-2", response_class=HTMLResponse)
async def accommodation_ui_v2_2(request: Request):
    return templates.TemplateResponse("accommodation/preview_v2_2.html", {"request": request})

# ===== LOCATION AUTOCOMPLETE API =====
location_autocomplete_cache = {}

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

@app.get("/api/locations/autocomplete")
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
            results = []
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
                
                # Duplikáció szűrése
                if mode == "destination":
                    dedup_key = (city_name.strip().lower(), country_name.strip().lower())
                else:
                    dedup_key = (display_str.strip().lower(), country_name.strip().lower())
                
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                
                sub = "Minden repülőtér" if loc_type == "city" else name
                
                results.append({
                    "id": loc.get("id"),
                    "code": code,
                    "name": name,
                    "city_name": city_name,
                    "country_name": country_name,
                    "type": loc_type,
                    "display": display_str,
                    "sub": f"{country_name} • {sub}" if country_name else sub
                })
                if len(results) >= 8:
                    break
            location_autocomplete_cache[cache_key] = results
            return JSONResponse(content=results)
    except Exception as e:
        print(f"[WARN] Error fetching locations for '{clean_term}': {e}")
    
    return JSONResponse(content=[])

# Ezt add hozzá a main.py-hoz a többi végpont mellé
@app.get("/search-status")
async def get_search_status():
    global results
    return JSONResponse(content=results)

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

# Globális tároló a nyers adatoknak
raw_flight_data = {"data": None, "count": 0}
raw_stay_data = {"data": None, "count": 0}

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

# Módosított háttérfolyamat
def run_intelligence_scraper(p: SearchParams):
    global results, raw_flight_data
    results = {"status": "running", "progress": 0, "status_text": "Keresési paraméterek ellenőrzése...", "data": None, "error": None}
    
    def update_progress(base, scale, p):
        current = base + (p * scale / 100)
        results["progress"] = int(current)
    
    try:
        from app.scrapers.scraper import get_city_id_api
        
        # 1. Előzetes validáció: létezik-e reptérrel rendelkező város/reptér
        origin_id = get_city_id_api(p.origin)
        if not origin_id:
            results = {
                "status": "error", 
                "error": f"Nem található érvényes repülőtér a megadott indulási városhoz: '{p.origin}'. Kérlek válassz egy várost a felajánlott listából!"
            }
            return
            
        dest_id = get_city_id_api(p.destination)
        if not dest_id:
            results = {
                "status": "error", 
                "error": f"Nem található érvényes repülőtér a megadott célállomáshoz: '{p.destination}'. Kérlek válassz egy várost a felajánlott listából!"
            }
            return

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
            limit=50,
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
            limit=50,
            progress_callback=lambda p_val: update_progress(45, 40, p_val)
        )
        
        results["progress"] = 90
        results["status_text"] = "Útvonalak kombinálása és ellenőrzése..."
        
        if outbound.empty or inbound.empty:
            results = {"status": "done", "progress": 100, "data": [], "count": 0, "error": "Nincs járat a megadott feltételekkel."}
            return

        # Rugalmas kinttartózkodás figyelembe vétele
        min_stay = max(1, p.duration - 2) if p.duration else 1
        max_stay = (p.duration + 2) if p.duration else None
        combinations = create_return_combinations(outbound, inbound, min_stay_days=min_stay, max_stay_days=max_stay)
        
        # ✅ MÓDOSÍTÁS: Mentés a raw_flight_data globális változóba
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

@app.post("/start-intelligence-search")
async def start_search(params: SearchParams, background_tasks: BackgroundTasks):
    global results
    results = {"status": "running", "data": None, "error": None}
    background_tasks.add_task(run_intelligence_scraper, params)
    return {"message": "Search started"}

# ===== ACCOMMODATION SCRAPER API =====
def run_accommodation_scraper(p: StaySearchParams):
    global accommodation_results, raw_stay_data
    accommodation_results = {"status": "running", "progress": 0, "data": None, "error": None}
    
    def update_progress(p_val):
        accommodation_results["progress"] = p_val
        if p_val < 10:
             accommodation_results["status_text"] = "Böngésző indítása..."
        elif p_val < 20:
             accommodation_results["status_text"] = "Csatlakozás a szolgáltatóhoz..."
        else:
             accommodation_results["status_text"] = f"Szállásadatok betöltése... ({p_val}%)"

    try:
        # Éjszakák számának kiszámítása
        try:
            from datetime import datetime as dt
            d_start = dt.strptime(p.start_date, "%Y-%m-%d")
            d_end = dt.strptime(p.end_date, "%Y-%m-%d")
            num_nights = max(1, (d_end - d_start).days)
        except Exception:
            num_nights = 1

        # A Cozycozy a TELJES tartózkodás árára szűr EUR-ban (nem éjszakánkénti árra)
        # Bőkezű plafont adunk meg, hogy minden releváns szállást letöltsön
        eur_rate = get_eur_huf_rate()
        p_min_eur = (p.price_min * num_nights) / eur_rate
        p_max_eur = (p.price_max * num_nights) / eur_rate if p.price_max < 900000 else 9007199254740991
        
        # Min rating a Cozycozy API-ban 0-100 skálán mozog (pl. 7.0 -> 70, 8.0 -> 80)
        cozy_min_rating = (p.min_rating * 10) if (0 < p.min_rating <= 10) else p.min_rating
        
        city_clean = p.city.strip()
        country_clean = p.country.strip() if p.country else ""
        
        if "," in city_clean and not country_clean:
            parts = city_clean.split(",", 1)
            city_clean = parts[0].strip()
            country_clean = parts[1].strip()
            
        # Alapértelmezett szűrők az első keresésnél
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
        
        # Mentés a raw_stay_data-ba
        raw_stay_data["data"] = parsed
        raw_stay_data["count"] = len(parsed)

        accommodation_results = {
            "status": "done", 
            "count": len(parsed),
            "error": None
        }
    except Exception as e:
        accommodation_results = {"status": "error", "error": str(e)}

@app.post("/start-accommodation-search")
async def start_accommodation_search(params: StaySearchParams, background_tasks: BackgroundTasks):
    global accommodation_results
    accommodation_results = {"status": "running", "data": None, "error": None}
    background_tasks.add_task(run_accommodation_scraper, params)
    return {"message": "Accommodation search started"}

@app.get("/api/accommodation-status")
async def get_accommodation_status():
    return JSONResponse(accommodation_results)

@app.get("/flight-intelligence-filter", response_class=HTMLResponse)
async def flight_intelligence_filter(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # ✅ JAVÍTÁS: is None ellenőrzés
    if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
        return RedirectResponse(url="/flight-intelligence", status_code=303)
    
    return templates.TemplateResponse("flights/flight_filter.html", {
        "request": request,
        "user": user,  # ✅ EZ HIÁNYZOTT!
        "flight_count": raw_flight_data["count"]
    })

# Szűrési API endpoint
class FilterParams(BaseModel):
    # Szűrők
    out_time_min: int = 0  # 0-23 óra
    out_time_max: int = 23
    in_time_min: int = 0
    in_time_max: int = 23
    out_days: list = []  # ["monday", "tuesday", ...]
    in_days: list = []
    max_stops: int = 2
    price_min: float = 0
    price_max: float = 500000
    stay_min: int = 1
    stay_max: int = 30
    max_total_duration: float = 24.0  # órában

# Szűrés + tárolás sessionbe
filtered_flights = {}
user_filter_params = {}

filtered_stays = {}
user_stay_filter_params = {}

class StayFilterParams(BaseModel):
    price_min: float = 0
    price_max: float = 1000000 # HUF (majd euróra váltjuk a scrapernek)
    min_rating: float = 0
    accommodation_types: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    breakfast: bool = False

@app.post("/api/preview-filter-count")
async def preview_filter_count(p: FilterParams, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    
    if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
        return JSONResponse({"total_count": 0, "matching_count": 0})
    
    try:
        df = raw_flight_data["data"].copy()
        
        # Időpontok
        df['out_hour'] = pd.to_datetime(df['out_dep_time']).dt.hour
        df = df[(df['out_hour'] >= p.out_time_min) & (df['out_hour'] <= p.out_time_max)]
        
        df['in_hour'] = pd.to_datetime(df['in_dep_time']).dt.hour
        df = df[(df['in_hour'] >= p.in_time_min) & (df['in_hour'] <= p.in_time_max)]
        
        # Napok
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
        
        # Technikai szűrők
        df = df[df['total_stops'] <= p.max_stops]
        df = df[(df['total_price_huf'] >= p.price_min) & (df['total_price_huf'] <= p.price_max)]
        df = df[(df['stay_days'] >= p.stay_min) & (df['stay_days'] <= p.stay_max)]
        df['total_duration'] = df['out_duration_h'] + df['in_duration_h']
        df = df[df['total_duration'] <= p.max_total_duration]
        
        matching = len(df)
        del df
        return JSONResponse({
            "total_count": raw_flight_data["count"],
            "matching_count": matching
        })
    except Exception as e:
        print(f"[WARN] Error in preview_filter_count: {e}")
        return JSONResponse({"total_count": raw_flight_data.get("count", 0), "matching_count": 0, "error": str(e)})

@app.post("/api/apply-filters")
async def apply_filters(params: FilterParams, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    
    background_tasks.add_task(run_filter_scraper, user, params)
    return {"message": "Scraping started"}

@app.get("/api/filter-status/{username}")
async def filter_status(username: str):
    return JSONResponse(filtered_flights.get(username, {"status": "idle"}))

def run_filter_scraper(username: str, p: FilterParams):
    global filtered_flights, raw_flight_data, user_filter_params
    filtered_flights[username] = {"status": "running", "progress": 0, "status_text": "Szűrés előkészítése...", "count": None, "error": None}
    user_filter_params[username] = p
    
    try:
        # ✅ JAVÍTÁS: is None ellenőrzés
        if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
            filtered_flights[username] = {"status": "error", "progress": 0, "count": 0, "error": "Nincs adat a memóriában. Kérlek indíts új járatkeresést!"}
            return
        
        filtered_flights[username]["progress"] = 10
        df = raw_flight_data["data"].copy()
        
        # SZŰRÉSEK ALKALMAZÁSA
        # Indulási idő szűrés
        filtered_flights[username]["status_text"] = "Időpontok szűrése..."
        df['out_hour'] = pd.to_datetime(df['out_dep_time']).dt.hour
        df = df[(df['out_hour'] >= p.out_time_min) & (df['out_hour'] <= p.out_time_max)]
        
        df['in_hour'] = pd.to_datetime(df['in_dep_time']).dt.hour
        df = df[(df['in_hour'] >= p.in_time_min) & (df['in_hour'] <= p.in_time_max)]
        
        filtered_flights[username]["progress"] = 30
        
        # Napok szűrése
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
        
        filtered_flights[username]["progress"] = 50
        filtered_flights[username]["status_text"] = "Technikai szűrők alkalmazása..."
        
        # Átszállások
        df = df[df['total_stops'] <= p.max_stops]
        
        # Ár
        df = df[(df['total_price_huf'] >= p.price_min) & (df['total_price_huf'] <= p.price_max)]
        
        # Tartózkodás
        df = df[(df['stay_days'] >= p.stay_min) & (df['stay_days'] <= p.stay_max)]
        
        # Összes utazási idő
        df['total_duration'] = df['out_duration_h'] + df['in_duration_h']
        df = df[df['total_duration'] <= p.max_total_duration]
        
        # ✅ 0 találat ellenőrzése
        if len(df) == 0:
            filtered_flights[username] = {
                "status": "error",
                "progress": 0,
                "count": 0,
                "error": "A megadott szűrőkkel 0 járatkombináció maradt. Kérlek állíts be enyhébb feltételeket!"
            }
            del df
            gc.collect()
            return

        filtered_flights[username]["progress"] = 80
        filtered_flights[username]["status_text"] = "Eredmények mentése..."
        
        # ✅ MEMÓRIA OPTIMALIZÁLÁS: Csak a szükséges oszlopokat hagyjuk meg
        # És ha túl sok (pl. > 1000), akkor vágjuk le az elejét (legolcsóbbak)
        if len(df) > 1000:
            df = df.sort_values('total_price_huf').head(1000)

        # Időpontok konvertálása stringre
        date_columns = ['out_dep_time', 'out_arr_time', 'in_dep_time', 'in_arr_time']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Mentés sessionbe
        filtered_flights[username] = {
            "status": "done",
            "progress": 100,
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "error": None
        }
        
        # Takarítás
        del df
        gc.collect()
        
    except Exception as e:
        filtered_flights[username] = {"status": "error", "progress": 0, "count": None, "error": str(e)}
        gc.collect()

@app.get("/flight-intelligence-ahp", response_class=HTMLResponse)
async def flight_intelligence_ahp(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Ellenőrizzük, hogy van-e szűrt adat és nem 0
    if user not in filtered_flights or filtered_flights[user].get("status") != "done" or filtered_flights[user].get("count", 0) == 0:
        return RedirectResponse(url="/flight-intelligence-filter", status_code=303)
    
    flight_data = filtered_flights[user]
    return templates.TemplateResponse("flights/flight_ahp.html", {
        "request": request, 
        "user": user,
        "flight_count": flight_data.get("count", 0)
    })

# --- ACCOMMODATION FILTER ---
# Ez az endpoint megszűnik, helyette az AHP-re megyünk közvetlenül.

@app.post("/api/apply-stay-filters")
async def apply_stay_filters(params: StayFilterParams, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user: raise HTTPException(status_code=401)
    
    background_tasks.add_task(run_stay_filter_task, user, params)
    return {"message": "Filtering started"}

@app.get("/api/stay-filter-status/{username}")
async def stay_filter_status(username: str):
    return JSONResponse(filtered_stays.get(username, {"status": "idle"}))

def filter_stays_dataframe(df, p: StayFilterParams):
    """Helper to apply filters to a DataFrame."""
    # Filter - Price
    eur_to_huf = get_eur_huf_rate()
    if 'price_huf' not in df.columns:
        df['price_huf'] = df['price_per_night_eur'] * eur_to_huf
    
    df = df[(df['price_huf'] >= p.price_min) & (df['price_huf'] <= p.price_max)]
    
    # Filter - Rating (kezeli a 0-10 és 0-100 skálákat is)
    target_rating = (p.min_rating * 10) if (0 < p.min_rating <= 10) else p.min_rating
    df = df[df['rating_score'] >= target_rating]
    
    # Filter - Accommodation Types
    if p.accommodation_types:
        def check_type(row_type):
            if not row_type: return False
            return any(t in row_type for t in p.accommodation_types)
        df = df[df['accommodation_type'].apply(check_type)]

    # Filter - Amenities
    if p.amenities:
        def check_amenities(row_amenities):
            if not row_amenities: return False
            current_set = set(row_amenities)
            required_set = set(p.amenities)
            return required_set.issubset(current_set)
        df = df[df['amenities'].apply(check_amenities)]
    
    return df

@app.post("/api/preview-stay-filter")
async def preview_stay_filter(p: StayFilterParams, request: Request):
    user = get_current_user(request)
    if not user or raw_stay_data.get("data") is None:
        return {"count": 0}
        
    try:
        df = pd.DataFrame(raw_stay_data["data"])
        filtered_df = filter_stays_dataframe(df, p)
        return {"count": len(filtered_df)}
    except Exception as e:
        print(f"Preview error: {e}")
        return {"count": 0}

@app.get("/api/stay-price-histogram")
async def stay_price_histogram(request: Request):
    user = get_current_user(request)
    if not user or raw_stay_data.get("data") is None:
        return {"buckets": []}
    
    try:
        df = pd.DataFrame(raw_stay_data["data"])
        if 'price_huf' not in df.columns:
            df['price_huf'] = df['price_per_night_eur'] * get_eur_huf_rate()
        
        # Calculate histogram
        prices = df['price_huf'].dropna()
        if len(prices) == 0:
            return {"buckets": [], "max_bin": 500000}
            
        # Dynamic max: actual max rounded up to nearest 10,000 or 50,000
        actual_max = float(prices.max())
        dynamic_max = math.ceil(actual_max / 10000) * 10000
        if dynamic_max < 10000: dynamic_max = 10000

        # Create buckets - dynamic range
        bins = np.linspace(0, dynamic_max, 41) # 40 buckets
        counts, edges = np.histogram(prices, bins=bins)
        
        buckets = []
        for i in range(len(counts)):
            buckets.append({
                "min": float(edges[i]),
                "max": float(edges[i+1]),
                "count": int(counts[i])
            })
            
        return {
            "buckets": buckets, 
            "min": float(prices.min()), 
            "max": actual_max, 
            "max_bin": dynamic_max
        }
    except Exception as e:
        print(f"Histogram error: {e}")
        return {"buckets": []}

def run_stay_filter_task(username: str, p: StayFilterParams):
    global filtered_stays, raw_stay_data, user_stay_filter_params
    filtered_stays[username] = {"status": "running", "count": None, "error": None}
    user_stay_filter_params[username] = p
    
    try:
        if raw_stay_data.get("data") is None or raw_stay_data["count"] == 0:
            filtered_stays[username] = {"status": "done", "count": 0, "error": "No data in memory"}
            return
        
        df = pd.DataFrame(raw_stay_data["data"])
        df = filter_stays_dataframe(df, p)
        
        # MEMÓRIA OPTIMALIZÁLÁS
        if len(df) > 1000:
            df = df.sort_values('price_huf').head(1000)

        filtered_stays[username] = {
            "status": "done",
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "error": None
        }
        del df
        gc.collect()
    except Exception as e:
        filtered_stays[username] = {"status": "error", "error": str(e)}

# --- ACCOMMODATION AHP ---
stay_ahp_weights = {}

@app.get("/accommodation-intelligence-ahp", response_class=HTMLResponse)
async def accommodation_ahp_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    
    # Ha nincs szűrt adat, használjuk az összeset
    if user not in filtered_stays or filtered_stays[user].get("status") != "done":
        if raw_stay_data.get("data") is None or raw_stay_data["count"] == 0:
            return RedirectResponse(url="/accommodation-intelligence", status_code=303)
        
        filtered_stays[user] = {
            "status": "done",
            "count": raw_stay_data["count"],
            "data": raw_stay_data["data"],
            "error": None
        }
    
    return templates.TemplateResponse("accommodation/accommodation_ahp.html", {
        "request": request,
        "user": user,
        "stay_count": filtered_stays[user]["count"]
    })

@app.post("/api/save-stay-ahp-weights")
async def save_stay_ahp_weights(weights: Dict[str, float], request: Request):
    user = get_current_user(request)
    if not user: raise HTTPException(status_code=401)
    
    # Expecting order: price, rating, reviews, distance
    # Removed "instant" as criteria
    ordered_keys = ["price", "rating", "reviews", "distance"]
    stay_ahp_weights[user] = [weights.get(k, 0.25) for k in ordered_keys]
    return {"message": "Súlyok mentve"}

# AHP súlyok tárolása
ahp_weights = {}

class AHPWeights(BaseModel):
    weights: list
    criteria: list

@app.post("/api/save-ahp-weights")
async def save_ahp_weights(data: AHPWeights, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    
    ahp_weights[user] = {
        "weights": data.weights,
        "criteria": data.criteria
    }
    return {"message": "Weights saved"}

# Adattárolók (a sessions és ahp_weights mellé)
user_preferences = {}
ranked_results = {}
dest_calculation_status = {}

# --- PROMETHEE Segédfüggvények ---
def preference_function(d, config):
    f_type = config['type']
    p = config.get('p', 0)
    q = config.get('q', 0)
    
    if d <= q: return 0
    if f_type == "usual": return 1
    if f_type == "v-shape": return min(1, d / p) if p > 0 else 1
    if f_type == "u-shape": return 1 if d > q else 0
    if f_type == "level": return 0.5 if d <= p else 1
    if f_type == "linear-indifference": 
        return min(1, (d - q) / (p - q)) if (p - q) > 0 else 1
    return 0

# --- ROUTES ---

@app.get("/flight-intelligence-preferences", response_class=HTMLResponse)
async def flight_preferences_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Ellenőrzés: van-e AHP súly
    if user not in ahp_weights:
        return RedirectResponse(url="/flight-intelligence-ahp", status_code=303)
    
    # Ellenőrzés: van-e szűrt adat
    if user not in filtered_flights or filtered_flights[user].get("status") != "done":
        return RedirectResponse(url="/flight-intelligence-filter", status_code=303)
    
    return templates.TemplateResponse("flights/flight_preferences.html", {
        "request": request,
        "user": user,
        "flight_count": filtered_flights[user]["count"],
        "filter_params": user_filter_params.get(user, FilterParams())
    })

class CriterionParam(BaseModel):
    type: str  # "usual", "v-shape", "u-shape", "level", "linear"
    p: float = 0.0
    q: float = 0.0

class PreferenceConfig(BaseModel):
    ideal_departure_hour: int
    ideal_stay_days: int
    # Kritériumonkénti beállítások: price, departure, travel_time, stops, stay
    configs: Dict[str, CriterionParam]

import numpy as np

def get_preference(d: float, config: CriterionParam) -> float:
    """PROMETHEE preferencia függvények megvalósítása."""
    if d <= config.q:
        return 0.0
    
    if config.type == "usual":
        return 1.0 if d > 0 else 0.0
    
    elif config.type == "v-shape":
        return min(1.0, d / config.p) if config.p > 0 else 1.0
    
    elif config.type == "u-shape":
        return 1.0 if d > config.q else 0.0
    
    elif config.type == "level":
        if d <= config.q: return 0.0
        if d <= config.p: return 0.5
        return 1.0
    
    elif config.type == "linear": # Linear with indifference
        if d <= config.q: return 0.0
        if d > config.p: return 1.0
        return (d - config.q) / (config.p - config.q)
    
    return 0.0

calculation_status = {}

@app.post("/api/calculate-results")
async def start_calculate_results(config: PreferenceConfig, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user or user not in filtered_flights or user not in ahp_weights:
        raise HTTPException(status_code=400, detail="Hiányzó szűrt adatok vagy AHP súlyok")
    
    background_tasks.add_task(run_calculation_task, user, config)
    return {"message": "Calculation started"}

@app.get("/api/calculation-status")
async def get_calculation_status(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401)
    return JSONResponse(calculation_status.get(user, {"status": "idle"}))

def run_calculation_task(user: str, config: PreferenceConfig):
    global ranked_results, calculation_status
    calculation_status[user] = {"status": "running", "progress": 0, "status_text": "Adatok előkészítése..."}
    
    try:
        # 1. Adatok előkészítése
        flight_data = filtered_flights[user].get("data", [])
        if not flight_data or len(flight_data) == 0:
            calculation_status[user] = {"status": "error", "progress": 0, "error": "Nincs értékelhető járat a szűrés után (0 találat). Kérlek állíts be enyhébb szűrőket!"}
            return
            
        df = pd.DataFrame(flight_data)
        if df.empty or 'total_price_huf' not in df.columns:
            calculation_status[user] = {"status": "error", "progress": 0, "error": "A szűrt adatok üresek vagy érvénytelenek. Kérlek indíts új keresést vagy módosíts a szűrőkön!"}
            return
            
        weights = ahp_weights[user]["weights"] # Sorrend: Ár, Időpont, Utazás, Átszállás, Tartózkodás
        
        calculation_status[user]["progress"] = 5
        calculation_status[user]["status_text"] = "Kritérium értékek számítása..."
        
        # Kritérium értékek kiszámítása (MINDEN MINIMALIZÁLANDÓ)
        df['g1'] = df['total_price_huf']
        
        def time_diff(row):
            dep_time = pd.to_datetime(row['out_dep_time'])
            diff = abs(dep_time.hour - config.ideal_departure_hour)
            return min(diff, 24 - diff)
        df['g2'] = df.apply(time_diff, axis=1)
        
        df['g3'] = df['out_duration_h'] + df['in_duration_h']
        df['g4'] = df['out_stops'] + df['in_stops']
        df['g5'] = (df['stay_days'] - config.ideal_stay_days).abs()
    
        criteria_cols = ['g1', 'g2', 'g3', 'g4', 'g5']
        criteria_keys = ['price', 'departure', 'travel_time', 'stops', 'stay']
        n = len(df)
        
        calculation_status[user]["progress"] = 10
        calculation_status[user]["status_text"] = f"Részletes összehasonlítás ({n} járat)..."
        
        # ✅ MEMÓRIA OPTIMALIZÁLÁS: Nincs pi_matrix szorzat, Flow-kat közvetlenül számoljuk (O(N^2) helyett O(1) memória)
        phi_plus = np.zeros(n)
        phi_minus = np.zeros(n)
        data_matrix = df[criteria_cols].values
        
        step = max(1, n // 50)
        
        for i in range(n):
            if i % step == 0:
                prog = 10 + int((i / n) * 80)
                calculation_status[user]["progress"] = prog
                
            for j in range(n):
                if i == j: continue
                
                total_pref = 0.0
                for k in range(len(criteria_cols)):
                    d = data_matrix[j, k] - data_matrix[i, k]
                    if d > 0:
                        pref_val = get_preference(d, config.configs[criteria_keys[k]])
                        total_pref += weights[k] * pref_val
                
                phi_plus[i] += total_pref
                phi_minus[j] += total_pref
    
        calculation_status[user]["progress"] = 90
        calculation_status[user]["status_text"] = "Rangsorolás és mentés..."
    
        # Flow számítás (átlagolás)
        if n > 1:
            phi_plus /= (n - 1)
            phi_minus /= (n - 1)
            # Normalizálás 0 és 1 közé: (phi + 1) / 2
            phi_net = (phi_plus - phi_minus + 1) / 2
        else:
            phi_net = np.zeros(n) + 1.0 # Egy elem esetén max pont

        df['phi_net'] = phi_net
        
        # 4. Normalizált pontszámok
        for i, col in enumerate(criteria_cols):
            c_min = df[col].min()
            c_max = df[col].max()
            if c_max == c_min:
                df[f'score_{criteria_keys[i]}'] = 1.0
            else:
                df[f'score_{criteria_keys[i]}'] = (c_max - df[col]) / (c_max - c_min)
    
        # Rangsorolás és mentés
        final_list = df.sort_values('phi_net', ascending=False).to_dict('records')
        ranked_results[user] = final_list
        
        calculation_status[user] = {
            "status": "done",
            "progress": 100,
            "count": n
        }
        
    except Exception as e:
        print(f"HIBA: {e}")
        calculation_status[user] = {
            "status": "error", 
            "progress": 0,
            "error": str(e)
        }

# --- ACCOMMODATION RESULTS ---
class StayPreferenceConfig(BaseModel):
    configs: Dict[str, CriterionParam]

stay_ranked_results = {}
stay_calculation_status = {}

@app.get("/api/stay-calculation-status")
async def get_stay_calculation_status(request: Request):
    user = get_current_user(request)
    if not user: raise HTTPException(status_code=401)
    return JSONResponse(stay_calculation_status.get(user, {"status": "idle"}))

@app.get("/accommodation-intelligence-preferences", response_class=HTMLResponse)
async def stay_preferences_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    if user not in stay_ahp_weights: return RedirectResponse(url="/accommodation-intelligence-ahp", status_code=303)
    if user not in filtered_stays or filtered_stays[user].get("status") != "done":
        if raw_stay_data.get("data") is None:
            return RedirectResponse(url="/accommodation-intelligence", status_code=303)
        filtered_stays[user] = {"status":"done", "data": raw_stay_data["data"], "count": raw_stay_data["count"]}
    
    return templates.TemplateResponse("accommodation/accommodation_preferences.html", {
        "request": request,
        "user": user,
        "stay_count": filtered_stays[user]["count"]
    })

@app.post("/api/calculate-stay-results")
async def calculate_stay_results(config: StayPreferenceConfig, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user or user not in filtered_stays or user not in stay_ahp_weights:
        raise HTTPException(status_code=400, detail="Missing data")

    background_tasks.add_task(run_stay_calculation_task, user, config)
    return {"message": "Calculation started"}

def run_stay_calculation_task(user: str, config: StayPreferenceConfig):
    global stay_calculation_status, stay_ranked_results
    stay_calculation_status[user] = {"status": "running", "progress": 0, "status_text": "Adatok előkészítése..."}

    try:
        df = pd.DataFrame(filtered_stays[user]["data"])
        weights = stay_ahp_weights[user] # price, rating, reviews, distance
        
        # Ensure price_huf exists (fallback for stale session data)
        if 'price_huf' not in df.columns:
            if 'price_per_night_eur' in df.columns:
                df['price_huf'] = df['price_per_night_eur'] * get_eur_huf_rate()
            else:
                df['price_huf'] = 0

        stay_calculation_status[user]["progress"] = 5
        stay_calculation_status[user]["status_text"] = "Kritériumok normalizálása..."

        # g1: Price - MIN
        df['g1'] = df['price_huf']
        # g2: Rating - MAX
        df['g2'] = df['rating_score']
        # g3: Reviews - MAX
        df['g3'] = df['rating_count']
        # g4: Distance - MIN
        df['g4'] = df['distance_km']

        # Direction: 1 for MAX, -1 for MIN (for the d = i - j logic)
        directions = [-1, 1, 1, -1]
        cols = ['g1', 'g2', 'g3', 'g4']
        keys = ['price', 'rating', 'reviews', 'distance']
        n = len(df)
        pi_matrix = np.zeros((n, n))
        data = df[cols].values

        stay_calculation_status[user]["progress"] = 10
        stay_calculation_status[user]["status_text"] = f"Részletes összehasonlítás ({n} szállás)..."

        step = max(1, n // 50) 
        
        for i in range(n):
            if i % step == 0:
                prog = 10 + int((i / n) * 80)
                stay_calculation_status[user]["progress"] = prog

            for j in range(n):
                if i == j: continue
                total_pref = 0.0
                for k in range(len(cols)):
                    # We want i > j
                    if directions[k] == 1:
                        d = data[i, k] - data[j, k]
                    else:
                        d = data[j, k] - data[i, k]
                    
                    if d > 0:
                        pref_val = get_preference(d, config.configs[keys[k]])
                        total_pref += weights[k] * pref_val
                pi_matrix[i, j] = total_pref

        stay_calculation_status[user]["progress"] = 90
        stay_calculation_status[user]["status_text"] = "Rangsorolás és mentés..."

        if n > 1:
            phi_plus = np.sum(pi_matrix, axis=1) / (n - 1)
            phi_minus = np.sum(pi_matrix, axis=0) / (n - 1)
            # Normalizálás 0 és 1 közé: (phi + 1) / 2
            df['phi_net'] = (phi_plus - phi_minus + 1) / 2
        else:
            df['phi_net'] = np.ones(n)

        # Scores for UI
        for i, col in enumerate(cols):
            c_min, c_max = df[col].min(), df[col].max()
            if c_max == c_min:
                df[f'score_{keys[i]}'] = 1.0
            else:
                if directions[i] == 1: # MAX
                    df[f'score_{keys[i]}'] = (df[col] - c_min) / (c_max - c_min)
                else: # MIN
                    df[f'score_{keys[i]}'] = (c_max - df[col]) / (c_max - c_min)

        stay_ranked_results[user] = df.sort_values('phi_net', ascending=False).to_dict('records')
        
        stay_calculation_status[user] = {
            "status": "done",
            "progress": 100,
            "count": n
        }
    except Exception as e:
        stay_calculation_status[user] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }

@app.get("/accommodation-intelligence-results", response_class=HTMLResponse)
async def stay_results_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    if user not in stay_ranked_results: return RedirectResponse(url="/accommodation-intelligence", status_code=303)
    
    return templates.TemplateResponse("accommodation/accommodation_results.html", {
        "request": request, 
        "user": user, 
        "results": stay_ranked_results[user],
        "weights": stay_ahp_weights[user],
        "criteria_names": ["Ár", "Értékelés", "Népszerűség", "Távolság"]
    })

@app.get("/destination-matcher", response_class=HTMLResponse)
async def destination_matcher_page(request: Request):
    user = get_current_user(request)
    if user:
        session = get_dest_session(user)
        session["results"] = []
        if user in dest_calculation_status:
            dest_calculation_status[user] = {"status": "idle", "progress": 0}
    return templates.TemplateResponse("destination/destination_matcher.html", {"request": request, "user": user})

@app.get("/destination-criteria", response_class=HTMLResponse)
async def destination_criteria_page(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("destination/destination_criteria.html", {"request": request, "user": user})

@app.get("/destination-ahp", response_class=HTMLResponse)
async def destination_ahp_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    
    # Transform simple list ["weather", "cost"] into objects for UI [{'id':'weather', 'name':'...'}]
    crit_map = {
        "weather": "Időjárás", "cost": "Költségek", "safety": "Biztonság", 
        "vibe": "Hangulat", "crowds": "Tömeg", "travel_time": "Utazás"
    }
    selected_criteria = [{"id": c, "name": crit_map.get(c, c)} for c in session.get("criteria", [])]

    return templates.TemplateResponse("destination/destination_ahp.html", {
        "request": request, 
        "selected_criteria": selected_criteria
    })

@app.get("/destination-preferences", response_class=HTMLResponse)
async def destination_preferences_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    
    # Töröljük a korábbi eredményeket, ha visszalépünk ide
    session["results"] = []
    if user in dest_calculation_status:
        dest_calculation_status[user] = {"status": "idle", "progress": 0}
    
    selected_criteria = [{"id": c} for c in session.get("criteria", [])]
    return templates.TemplateResponse("destination/destination_preferences.html", {
        "request": request, 
        "selected_criteria": selected_criteria
    })

@app.get("/destination-results", response_class=HTMLResponse)
async def destination_results_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    
    # Calculate pre-fill dates for next steps
    constraints = session.get("constraints", {})
    month = constraints.get("month", "6")
    if month == "any": month = "6"
    duration = constraints.get("duration", 7)
    
    # Simple logic: 10th of the selected month
    start_date = f"2026-{int(month):02d}-10"
    end_date = f"2026-{int(month):02d}-{10 + int(duration)}"
    
    response = templates.TemplateResponse("destination/destination_results.html", {
        "request": request, 
        "user": user, 
        "results": session.get("results", []),
        "constraints": constraints,
        "dates": {
            "start": start_date,
            "end": end_date
        }
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

# Helper to init session
def get_dest_session(user):
    if user not in destination_sessions:
        destination_sessions[user] = {"filtered": [], "criteria": [], "weights": [], "constraints": {}}
    return destination_sessions[user]

from app.services.destination_service import get_filtered_destinations
from app.services.destination_scoring_service import evaluate_destination_candidate, calculate_destination_rankings

@app.post("/api/destination-constraints")
async def save_constraints(data: DestConstraints, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    session = get_dest_session(user)
    session["constraints"] = data.dict()
    
    filtered = get_filtered_destinations(data.exclusions)
    session["filtered"] = filtered
    print(f"[INFO] Felhasználó ({user}) szűrt célállomásai: {len(filtered)} desztináció maradt (Kizárások: {data.exclusions}).")
    
    return {"status": "ok", "count": len(filtered)}

@app.post("/api/destination-criteria")
async def save_criteria(data: DestCriteria, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    session = get_dest_session(user)
    session["criteria"] = data.criteria
    print(f"User {user} selected criteria: {data.criteria}")
    
    return {"status": "ok"}

@app.post("/api/destination-ahp")
async def save_ahp(data: DestAHP, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    session = get_dest_session(user)
    criteria = session.get("criteria", [])
    if not criteria:
        return JSONResponse({"error": "No criteria selected"}, status_code=400)
    
    n = len(criteria)
    matrix = np.ones((n, n))
    
    # Fill matrix from pairwise inputs
    for key, val in data.comparisons.items():
        parts = key.split("_vs_")
        if len(parts) == 2:
            c1, c2 = parts
            if c1 in criteria and c2 in criteria:
                idx1 = criteria.index(c1)
                idx2 = criteria.index(c2)
                matrix[idx1, idx2] = val
                matrix[idx2, idx1] = 1.0 / val

    # Calculate weights
    row_products = np.prod(matrix, axis=1)
    if n > 0:
        weights = np.power(row_products, 1.0/n)
        total_w = np.sum(weights)
        if total_w > 0:
            normalized_weights = weights / total_w
        else:
            normalized_weights = np.ones(n) / n
    else:
        normalized_weights = []
    
    session["weights"] = normalized_weights.tolist()
    print(f"User {user} AHP weights computed: {session['weights']}")
    
    return {"status": "ok", "weights": session["weights"]}

@app.get("/api/destination-calculation-status")
async def get_destination_status(request: Request):
    user = get_current_user(request)
    if not user: raise HTTPException(status_code=401)
    status = dest_calculation_status.get(user, {"status": "idle"})
    return JSONResponse(status)

@app.post("/api/calculate-destinations")
async def calculate_destinations(prefs: DestPreferenceDetails, background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    session = get_dest_session(user)
    dests = session.get("filtered", [])
    if not dests:
        dests = get_filtered_destinations(session.get("constraints", {}).get("exclusions", []))
        session["filtered"] = dests

    if not dests:
        return JSONResponse({"error": "Nincs elérhető célállomás"}, status_code=400)

    dest_calculation_status[user] = {"status": "running", "progress": 0, "status_text": "Kalkuláció indítása..."}
    background_tasks.add_task(run_destination_calculation_task, user, prefs)
    
    return {"status": "ok", "message": "Calculation started"}

import threading
dest_calc_lock = threading.Lock()

def run_destination_calculation_task(user: str, prefs: DestPreferenceDetails):
    global dest_calculation_status, destination_sessions
    try:
        session = get_dest_session(user)
        dests = session.get("filtered", [])
        if not dests:
            dests = get_filtered_destinations(session.get("constraints", {}).get("exclusions", []))
            session["filtered"] = dests
        
        constraints = session.get("constraints", {})
        
        if not dests:
            dest_calculation_status[user] = {"status": "error", "error": "Nincs elérhető célállomás a megadott szűrőkkel."}
            return

        n = len(dests)
        origin_city = constraints.get("origin", "Budapest")
        # Tisztítsuk meg a repülőtéri kódtól ha szükséges (pl. "Budapest (BUD)" -> "Budapest")
        origin_clean = origin_city.split("(")[0].strip()

        month = constraints.get("month", "6")
        if month == "any": month = 6
        else: month = int(month)
        
        duration_days = int(constraints.get("duration", 7))
        target_temp = float(prefs.weather_temp) if prefs.weather_temp else 24.0
        adults = int(constraints.get("adults", 2))
        children = int(constraints.get("children", 0))

        dest_calculation_status[user] = {
            "status": "running", 
            "progress": 5, 
            "status_text": "Kiwi és Open-Meteo adatkapcsolat inicializálása..."
        }

        tokens = scraper.get_kiwi_tokens()
        print(f"\n[DESTINATION PIPELINE] {n} célállomás elemzése indul (Indulás: {origin_clean}, Hónap: {month}, Időtartam: {duration_days} nap, Utasok: {adults} felnőtt + {children} gyerek, Célhőm: {target_temp}°C)...")

        # Párhuzamos adatgyűjtés a valós API-kból
        completed_count = 0
        def process_candidate(dest):
            nonlocal completed_count
            res = evaluate_destination_candidate(
                dest=dest,
                origin_city=origin_clean,
                month=month,
                duration_days=duration_days,
                tokens=tokens,
                target_temp=target_temp,
                adults=adults,
                children=children
            )
            with dest_calc_lock:
                completed_count += 1
                prog = 5 + int((completed_count / n) * 80)
                dest_calculation_status[user]["progress"] = prog
                dest_calculation_status[user]["status_text"] = f"Valós adatok gyűjtése ({completed_count}/{n}): {dest.get('name')}..."
            return res

        with ThreadPoolExecutor(max_workers=10) as executor:
            candidates_raw = list(executor.map(process_candidate, dests))

        dest_calculation_status[user]["status_text"] = "Determinisztikus pontszámok és indoklások számítása..."
        dest_calculation_status[user]["progress"] = 90

        # Súlyok kinyerése közvetlenül a 2. lépés preferenciáiból
        weights_dict = {
            "flight": float(prefs.weight_flight),
            "cost": float(prefs.weight_cost),
            "weather": float(prefs.weight_weather),
            "safety": float(prefs.weight_safety)
        }

        ranked_results = calculate_destination_rankings(
            candidates_raw=candidates_raw,
            weights=weights_dict,
            target_temp=target_temp,
            adults=adults
        )

        for idx, r in enumerate(ranked_results):
            r["rank"] = idx + 1

        session["results"] = ranked_results
        dest_calculation_status[user] = {
            "status": "done", 
            "progress": 100, 
            "count": len(ranked_results)
        }
        print(f"[DESTINATION PIPELINE SIKERES] {len(ranked_results)} célállomás rangsorolva és elmentve a munkamenetbe.\n")
    except Exception as e:
        print(f"[DESTINATION PIPELINE HIBA] {e}")
        dest_calculation_status[user] = {"status": "error", "error": str(e)}

@app.get("/flight-intelligence-results", response_class=HTMLResponse)
async def results_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if user not in ranked_results:
        return RedirectResponse(url="/flight-intelligence", status_code=303)
    
    return templates.TemplateResponse("flights/flight_results.html", {
        "request": request, 
        "user": user, 
        "results": ranked_results[user],
        "weights": ahp_weights[user]["weights"],
        "criteria_names": ["Ár", "Időpont", "Utazás", "Átszállás", "Tartózkodás"]
    })

# --- DREAMTRIP V2 PAGE ROUTERS ---

@app.get("/dreamtrip-discover", response_class=HTMLResponse)
async def dreamtrip_discover_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("dreamtrip_discover.html", {"request": request, "user": user})

@app.get("/dreamtrip-planner", response_class=HTMLResponse)
async def dreamtrip_planner_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("dreamtrip_planner.html", {"request": request, "user": user})

# --- DREAMTRIP V2 API ENDPOINTS ---

class DiscoverRequest(BaseModel):
    origin: str
    month: int
    preferences: TravelPreferences
    exclusions: List[str] = []
    budget_daily: float = 0.0
    budget_strictness: str = "soft"

class GenerateTripRequest(BaseModel):
    city_id: str
    city_name: str
    lat: float
    lng: float
    start_date: str
    end_date: str

class ReoptimizeRequest(BaseModel):
    day_data: ItineraryDay
    city_id: str
    city_name: str
    lat: float
    lng: float

@app.post("/api/v2/discover")
async def api_discover(req: DiscoverRequest, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Betöltjük a város adatbázist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dest_path = os.path.join(base_dir, "data", "destinations.json")
    if not os.path.exists(dest_path):
        raise HTTPException(status_code=404, detail="Destinations database not found")
        
    with open(dest_path, "r", encoding="utf-8") as f:
        dests = json.load(f)
        
    # Szűrés kizárásokra
    if req.exclusions:
        dests = [d for d in dests if d.get("region") not in req.exclusions]
        
    # Pontszámok számítása
    try:
        scored_cities = scoring_service.calculate_city_scores(
            dests=dests,
            prefs=req.preferences,
            origin_city=req.origin,
            month=req.month
        )
        
        # JSON formátumra alakítás (explanation-nel együtt)
        results = []
        for c in scored_cities:
            c_dict = c.dict()
            c_dict["explanation"] = c.__dict__.get("explanation", "Optimális választás a szempontjaid alapján.")
            results.append(c_dict)
            
        return results
    except Exception as e:
        print(f"ERROR in api_discover: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/trip/generate")
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
        print(f"ERROR in api_generate_trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/trip/reoptimize")
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
        print(f"ERROR in api_reoptimize_trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/poi/search")
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
        print(f"ERROR in api_search_poi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)