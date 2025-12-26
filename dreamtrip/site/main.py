from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
from scraper import get_kiwi_tokens, search_flights_by_city_name_v2, create_return_combinations
from accommodation_scraper import get_all_stays, parse_accommodation_results
import os
import secrets
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import numpy as np
import json

app = FastAPI()

# Static és templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBasic()

# Felhasználók (username: password)
USERS = {
    "admin": "optivoya2024",
    "demo": "demo123",
    "bean": "bean",
}

# Session tárolás (production-ben használj Redis-t vagy JWT-t)
sessions = {}

raw_flights_cache = {}

# Globális változó a scraper eredményekhez
results = {"status": "idle", "data": None, "error": None}
accommodation_results = {"status": "idle", "data": None, "error": None}

# ===== AUTH =====
def verify_credentials(username: str, password: str):
    if username in USERS and USERS[username] == password:
        return True
    return False

def create_session(username: str):
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token

def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token or token not in sessions:
        return None
    return sessions[token]

# ===== ROUTES =====
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ===== DESTINATION MATCHING MODELS =====
class DestConstraints(BaseModel):
    month: str # "any" or "1"-"12"
    duration: int
    origin: str
    budget_daily: float
    budget_strictness: str
    exclusions: List[str]

class DestCriteria(BaseModel):
    criteria: List[str]

class DestAHP(BaseModel):
    comparisons: Dict[str, float]

class DestPreferenceDetails(BaseModel):
    weather_temp: float
    weather_rain: str # strict, moderate, loose
    cost_pref: str # min, value
    vibe_urban_nature: int # 0-100
    vibe_calm_party: int # 0-100
    vibe_history: int # 0-10
    safety_level: str # high, mid, low
    crowds_pref: str # hidden, balanced, popular
    travel_time_max: int

# Global Data
destination_db = []
destination_sessions = {} # user_id -> { "filtered": [], "criteria": [], "weights": [], "constraints": {} }
unique_user_id_counter = 0

def load_destinations():
    global destination_db
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "data", "destinations.json")
        with open(json_path, "r", encoding="utf-8") as f:
            destination_db = json.load(f)
        print(f"Loaded {len(destination_db)} destinations from {json_path}")
    except Exception as e:
        print(f"Error loading destinations: {e}")
        destination_db = []

load_destinations()

@app.on_event("startup")
async def startup_event():
    print("SERVER RESTARTING - RELOADED LATEST CODE")
    load_destinations()

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if verify_credentials(username, password):
        token = create_session(username)
        response = RedirectResponse(url="/home", status_code=303)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    return RedirectResponse(url="/?error=invalid", status_code=303)


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
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/destination-matcher", response_class=HTMLResponse)
async def destination_matcher(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("destination_matcher.html", {"request": request})

@app.get("/flight-intelligence", response_class=HTMLResponse)
async def flight_intelligence(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("flight_intelligence.html", {"request": request})

@app.get("/accommodation-intelligence", response_class=HTMLResponse)
async def accommodation_intelligence(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("accommodation_intelligence.html", {"request": request})

# ===== FLIGHT SCRAPER API =====
@app.post("/api/search-flights")
async def search_flights(background_tasks: BackgroundTasks, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    background_tasks.add_task(run_intelligence_scraper)
    return JSONResponse({"message": "Scraping elindult..."})

@app.get("/api/flight-status")
async def get_status(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return JSONResponse(results)

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

# Módosított háttérfolyamat
def run_intelligence_scraper(p: SearchParams):
    global results, raw_flight_data
    results = {"status": "running", "progress": 0, "status_text": "Keresés indítása...", "data": None, "error": None}
    
    def update_progress(base, scale, p):
        current = base + (p * scale / 100)
        results["progress"] = int(current)
    
    try:
        results["status_text"] = "Adatkapcsolat megteremtése..."
        tokens = get_kiwi_tokens(headless=True)
        
        results["status_text"] = f"Odaút keresése ({p.origin} -> {p.destination})..."
        outbound = search_flights_by_city_name_v2(
            origin_name=p.origin,
            destination_name=p.destination,
            tokens=tokens,
            date_from=p.out_from,
            date_to=p.out_to,
            progress_callback=lambda p: update_progress(5, 40, p)
        )
        
        results["progress"] = 45
        results["status_text"] = f"Visszaút keresése ({p.destination} -> {p.origin})..."
        
        inbound = search_flights_by_city_name_v2(
            origin_name=p.destination,
            destination_name=p.origin,
            tokens=tokens,
            date_from=p.in_from,
            date_to=p.in_to,
            progress_callback=lambda p: update_progress(45, 40, p)
        )
        
        results["progress"] = 90
        results["status_text"] = "Útvonalak kombinálása és ellenőrzése..."
        
        if outbound.empty or inbound.empty:
            results = {"status": "done", "progress": 100, "data": [], "count": 0, "error": "Nincs járat."}
            return

        combinations = create_return_combinations(outbound, inbound)
        
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
        # Árváltás (becsült 400 HUF/EUR) a scrapernek
        p_min_eur = p.price_min / 400 if hasattr(p, 'price_min') else 0
        p_max_eur = p.price_max / 400 if hasattr(p, 'price_max') else 9007199254740991
        
        # Alapértelmezett szűrők az első keresésnél (szinte semmi)
        raw_results = get_all_stays(
            city=p.city,
            country=p.country,
            start_date=p.start_date,
            end_date=p.end_date,
            rooms=p.rooms,
            adults=p.adults,
            children=p.children,
            progress_callback=update_progress
        )
        
        if not raw_results or 'entries' not in raw_results or not raw_results['entries']:
            accommodation_results = {"status": "done", "data": [], "count": 0, "error": "Nincs szállás."}
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
    
    return templates.TemplateResponse("flight_filter.html", {
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
            filtered_flights[username] = {"status": "done", "progress": 100, "count": 0, "error": "Nincs adat a memóriában"}
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
            allowed_days = [day_map[d] for d in p.out_days]
            df['out_weekday'] = pd.to_datetime(df['out_dep_time']).dt.dayofweek
            df = df[df['out_weekday'].isin(allowed_days)]
        
        if p.in_days:
            day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            allowed_days = [day_map[d] for d in p.in_days]
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
        
        filtered_flights[username]["progress"] = 80
        filtered_flights[username]["status_text"] = "Eredmények mentése..."
        
        # ✅ JAVÍTÁS: Timestamp oszlopok konvertálása stringre JSON szerializáláshoz
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
        
    except Exception as e:
        filtered_flights[username] = {"status": "error", "progress": 0, "count": None, "error": str(e)}

@app.get("/flight-intelligence-ahp", response_class=HTMLResponse)
async def flight_intelligence_ahp(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Ellenőrizzük, hogy van-e szűrt adat
    if user not in filtered_flights or filtered_flights[user].get("status") != "done":
        return RedirectResponse(url="/flight-intelligence-filter", status_code=303)
    
    flight_data = filtered_flights[user]
    
    return templates.TemplateResponse("flight_ahp.html", {
        "request": request, 
        "user": user,
        "flight_count": flight_data["count"]
    })

# --- ACCOMMODATION FILTER ---
@app.get("/accommodation-intelligence-filter", response_class=HTMLResponse)
async def accommodation_filter_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if raw_stay_data.get("data") is None or raw_stay_data["count"] == 0:
        return RedirectResponse(url="/accommodation-intelligence", status_code=303)
    
    return templates.TemplateResponse("accommodation_filter.html", {
        "request": request,
        "user": user,
        "stay_count": raw_stay_data["count"]
    })

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
    eur_to_huf = 400
    if 'price_huf' not in df.columns:
        df['price_huf'] = df['price_per_night_eur'] * eur_to_huf
    
    df = df[(df['price_huf'] >= p.price_min) & (df['price_huf'] <= p.price_max)]
    
    # Filter - Rating
    df = df[df['rating_score'] >= p.min_rating]
    
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
        
        filtered_stays[username] = {
            "status": "done",
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "error": None
        }
    except Exception as e:
        filtered_stays[username] = {"status": "error", "error": str(e)}

# --- ACCOMMODATION AHP ---
stay_ahp_weights = {}

@app.get("/accommodation-intelligence-ahp", response_class=HTMLResponse)
async def accommodation_ahp_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    
    if user not in filtered_stays or filtered_stays[user].get("status") != "done":
        return RedirectResponse(url="/accommodation-intelligence-filter", status_code=303)
    
    return templates.TemplateResponse("accommodation_ahp.html", {
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
    
    return templates.TemplateResponse("flight_preferences.html", {
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
        flight_data = filtered_flights[user]["data"]
        df = pd.DataFrame(flight_data)
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
        
        # 2. PROMETHEE Páros összehasonlítás
        pi_matrix = np.zeros((n, n))
        data_matrix = df[criteria_cols].values
        
        step = max(1, n // 50)  # Update progress 50 times max
        
        for i in range(n):
            if i % step == 0:
                # 10% -> 90% range
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
                
                pi_matrix[i, j] = total_pref
    
        calculation_status[user]["progress"] = 90
        calculation_status[user]["status_text"] = "Rangsorolás és mentés..."
    
        # 3. Flow számítás
        phi_plus = np.sum(pi_matrix, axis=1) / (n - 1)
        phi_minus = np.sum(pi_matrix, axis=0) / (n - 1)
        phi_net = phi_plus - phi_minus
    
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
        return RedirectResponse(url="/accommodation-intelligence-filter", status_code=303)
    
    return templates.TemplateResponse("accommodation_preferences.html", {
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
                df['price_huf'] = df['price_per_night_eur'] * 400
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

        phi_plus = np.sum(pi_matrix, axis=1) / (n - 1)
        phi_minus = np.sum(pi_matrix, axis=0) / (n - 1)
        df['phi_net'] = phi_plus - phi_minus

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
    
    return templates.TemplateResponse("accommodation_results.html", {
        "request": request, 
        "user": user, 
        "results": stay_ranked_results[user],
        "weights": stay_ahp_weights[user],
        "criteria_names": ["Ár", "Értékelés", "Népszerűség", "Távolság"]
    })

@app.get("/destination-matcher", response_class=HTMLResponse)
async def destination_matcher_page(request: Request):
    return templates.TemplateResponse("destination_matcher.html", {"request": request})

@app.get("/destination-criteria", response_class=HTMLResponse)
async def destination_criteria_page(request: Request):
    return templates.TemplateResponse("destination_criteria.html", {"request": request})

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

    return templates.TemplateResponse("destination_ahp.html", {
        "request": request, 
        "selected_criteria": selected_criteria
    })

@app.get("/destination-preferences", response_class=HTMLResponse)
async def destination_preferences_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    
    selected_criteria = [{"id": c} for c in session.get("criteria", [])]
    return templates.TemplateResponse("destination_preferences.html", {
        "request": request,
        "selected_criteria": selected_criteria
    })

@app.get("/destination-results", response_class=HTMLResponse)
async def destination_results_page(request: Request):
    user = get_current_user(request)
    if not user: return RedirectResponse(url="/", status_code=303)
    session = get_dest_session(user)
    
    return templates.TemplateResponse("destination_results.html", {
        "request": request,
        "results": session.get("results", [])
    })

# Helper to init session
def get_dest_session(user):
    if user not in destination_sessions:
        destination_sessions[user] = {"filtered": [], "criteria": [], "weights": [], "constraints": {}}
    return destination_sessions[user]

@app.post("/api/destination-constraints")
async def save_constraints(data: DestConstraints, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    global destination_db
    if not destination_db:
        print("Destination DB empty, attempting reload...")
        try:
            # Use absolute path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_dir, "data", "destinations.json")
            with open(json_path, "r", encoding="utf-8") as f:
                destination_db = json.load(f)
            print(f"Reloaded {len(destination_db)} destinations from {json_path}")
        except Exception as e:
            print(f"Error re-loading destinations: {e}")

    session = get_dest_session(user)
    session["constraints"] = data.dict()
    
    filtered = []
    print(f"Filtering {len(destination_db)} destinations with exclusions: {data.exclusions}")
    
    for dest in destination_db:
        keep = True
        
        # 1. Exclusions
        for excl in data.exclusions:
            # Region checks
            if excl == "region_asia" and dest.get("region") == "Asia": keep = False
            if excl == "region_america" and dest.get("region") == "America": keep = False
            if excl == "region_europe" and dest.get("region") == "Europe": keep = False
            
            # Type checks (using vibe/tags logic)
            # We map "type_city" to high urban_scale, "type_beach" to high beach_scale
            vibe = dest.get("vibe_metrics", {})
            if excl == "type_city" and vibe.get("urban_scale", 0) > 0.7: keep = False
            if excl == "type_beach" and vibe.get("beach_scale", 0) > 0.7: keep = False
            
            # Simple metadata checks? (visa not yet in DB, ignoring)

        # 2. Budget (Simple pre-filter)
        # If strict, filter out if cost > budget + 10% buffer
        if keep and data.budget_strictness == "hard" and data.budget_daily > 0:
            cost = dest["metrics"].get("cost_index_daily_eur", 0)
            if cost > (data.budget_daily * 1.1):
                keep = False

        if keep:
            filtered.append(dest)
    
    session["filtered"] = filtered
    print(f"User {user} filtered destinations: {len(filtered)} remaining.")
    
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
        # Fallback if empty (should not happen if flow followed)
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
    print(f"User {user} AHP weights computed.")
    
    return {"status": "ok", "weights": session["weights"]}

@app.post("/api/calculate-destinations")
async def calculate_destinations(prefs: DestPreferenceDetails, request: Request):
    user = get_current_user(request)
    if not user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    session = get_dest_session(user)
    dests = session.get("filtered", [])
    criteria = session.get("criteria", [])
    weights = session.get("weights", [])
    
    if not dests or not criteria:
        return JSONResponse({"error": "Missing data (Dests or Criteria)"}, status_code=400)

    n = len(dests)
    k = len(criteria)
    
    # Default weights if missing
    if not weights or len(weights) != k:
        print(f"Warning: Weights missing or mismatch ({len(weights)} vs {k}). Using equal weights.")
        weights = [1.0/k] * k
    
    # 1. Prepare Data Matrix (Raw extraction & normalization logic)
    # We need to map criteria ID -> Value for each dest
    # Higher is BETTER for logic below unless specified otherwise
    
    matrix = np.zeros((n, k))
    
    # Pre-computation helper
    def get_criterion_value(dest, crit_id):
        # WEATHER: |Optimal - Actual| (Lower is better) -> We'll invert later or handle in P function
        if crit_id == "weather":
            # Find closest month avg temp to ideal
            # Simple approach: average of weather_by_month["temp"] vs prefs.weather_temp
            # Actually, let's pick the BEST month in the dataset for simplicity or avg of season
            # User selected Month/Time in constraints. If "any", check all.
            # Assuming "any" -> best possible match.
            best_diff = 999
            for m, data in dest["metrics"]["weather_by_month"].items():
                diff = abs(data["temp"] - prefs.weather_temp)
                if diff < best_diff: best_diff = diff
            return best_diff # Lower is better (0 = perfect)

        # COST: Daily Cost (Lower is better usually, unless value seeking?)
        if crit_id == "cost":
            return dest["metrics"]["cost_index_daily_eur"]
            
        # SAFETY: Index (Higher is better)
        if crit_id == "safety":
            return dest["metrics"]["safety_index"]
            
        # VIBE: Euclidean distance from ideal profile (Lower is better)
        if crit_id == "vibe":
            # User: urban (0-100) -> 0.0-1.0
            u_ideal = prefs.vibe_urban_nature / 100.0
            # dest has 'urban_scale' (0-1). 
            # If user wants 50/50 (0.5), and dest is 0.9 (Urban), diff is 0.4.
            # We combine multiple dimensions?
            v_metrics = dest.get("vibe_metrics", {})
            
            diff_urban = abs((v_metrics.get("urban_scale", 0.5)) - u_ideal)
            # Calm vs Party (Nightlife)
            p_ideal = prefs.vibe_calm_party / 100.0
            diff_party = abs((v_metrics.get("nightlife_scale", 0.5)) - p_ideal)
            
            # History
            h_ideal = prefs.vibe_history / 10.0
            diff_hist = abs((v_metrics.get("historical_scale", 0.5)) - h_ideal)
            
            return (diff_urban + diff_party + diff_hist) / 3.0 # Lower is better
            
        # CROWDS: Assuming we don't have real "crowd index" in dummy, use 'popularity'? 
        # Using cost or known big cities as proxy?
        # For MVP let's assume random or static logic: "Big cities = crowded"
        if crit_id == "crowds":
            # If user wants "Hidden" (val=hidden), we penalize result.
            # Let's mock: 
            return 0.5 # Default placeholder
            
        return 0.0

    # Fill matrix
    for i in range(n):
        for j in range(k):
            matrix[i, j] = get_criterion_value(dests[i], criteria[j])

    # 2. PROMETHEE Calculation
    # Preference functions:
    # We define 'directions': 1 (Max), -1 (Min)
    # Weather diff: Min (-1)
    # Cost: Min (-1) (Usually)
    # Safety: Max (1)
    # Vibe diff: Min (-1)
    # Crowds: Min (-1) ?
    
    directions = []
    thresholds = [] # q, p (indifference, preference)
    
    for c in criteria:
        if c == "weather": 
            directions.append(-1)
            thresholds.append((2, 10)) # Indiff if diff < 2C, Max pref if diff > 10C
        elif c == "cost": 
            directions.append(-1)
            thresholds.append((10, 50)) # 10 EUR, 50 EUR
        elif c == "safety": 
            directions.append(1)
            thresholds.append((5, 20))
        elif c == "vibe": 
            directions.append(-1)
            thresholds.append((0.1, 0.4))
        else: 
            directions.append(1) # Default Max
            thresholds.append((0, 1))

    pi_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i == j: continue
            
            total_p = 0.0
            for idx_c in range(k):
                val_i = matrix[i, idx_c]
                val_j = matrix[j, idx_c]
                
                # Difference d
                diff = (val_i - val_j) if directions[idx_c] == 1 else (val_j - val_i)
                
                # Pref func (Linear V-shape)
                q, p = thresholds[idx_c]
                pref = 0.0
                if diff <= q: pref = 0.0
                elif diff >= p: pref = 1.0
                else: pref = (diff - q) / (p - q)
                
                total_p += weights[idx_c] * pref
            
            pi_matrix[i, j] = total_p

    # Flows
    phi_plus = np.sum(pi_matrix, axis=1) / (n - 1)
    phi_minus = np.sum(pi_matrix, axis=0) / (n - 1)
    phi_net = phi_plus - phi_minus

    # 3. Format Results & Explanations
    formatted_results = []
    
    for i in range(n):
        dest = dests[i]
        
        # Generation Explanation
        # Why is this good? Look at criteria where this destination beat others (high partial net flow?)
        # For simplicity MVP: Pick the best performing raw metric relative to request
        reasons = []
        if "weather" in criteria:
            val = matrix[i, criteria.index("weather")]
            if val < 3: reasons.append(f"Tökéletes időjárás ({int(val)}°C eltérés)")
        if "cost" in criteria:
            val = dest["metrics"]["cost_index_daily_eur"]
            if val < prefs.budget_daily: reasons.append(f"Költségkereten belül ({val}€)")
        if "safety" in criteria:
            if dest["metrics"]["safety_index"] > 70: reasons.append("Nagyon biztonságos")
        if "vibe" in criteria:
            # If match was good (diff low)
            val = matrix[i, criteria.index("vibe")]
            if val < 0.2: reasons.append("A hangulat pont olyan, amilyet kerestél")

        explanation_text = " • ".join(reasons) if reasons else "Kiegyensúlyozott választás a szempontjaid alapján."
        
        # Add basic display metrics
        display_metrics = {
            "temp": f"{dest['metrics'].get('weather_by_month', {}).get('6', {}).get('temp', '?')}°C", # Demo: Pick June
            "cost": f"{dest['metrics']['cost_index_daily_eur']}€/nap",
            "safety": f"{dest['metrics']['safety_index']}/100",
            "vibe": "Egyező" # Placeholder
        }

        formatted_results.append({
            "rank": 0, # To be filled
            "id": dest["id"],
            "name": dest["name"],
            "country": dest["country"],
            "score": round((phi_net[i] + 1) * 50), # Normalize -1..1 to 0..100
            "phi_net": phi_net[i],
            "image": dest.get("image", ""),
            "explanation": explanation_text,
            "metrics": display_metrics
        })
        
    # Sort by Score
    formatted_results.sort(key=lambda x: x["phi_net"], reverse=True)
    
    # Assign Ranks
    for i, res in enumerate(formatted_results):
        res["rank"] = i + 1
        
    session["results"] = formatted_results
    return {"status": "ok", "count": len(formatted_results)}

@app.get("/flight-intelligence-results", response_class=HTMLResponse)
async def results_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if user not in ranked_results:
        return RedirectResponse(url="/flight-intelligence", status_code=303)
    
    return templates.TemplateResponse("flight_results.html", {
        "request": request, 
        "user": user, 
        "results": ranked_results[user],
        "weights": ahp_weights[user]["weights"],
        "criteria_names": ["Ár", "Időpont", "Utazás", "Átszállás", "Tartózkodás"]
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)