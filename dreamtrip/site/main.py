from fastapi import FastAPI, Request, Form, BackgroundTasks, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
from scraper import get_kiwi_tokens, search_flights_by_city_name_v2, create_return_combinations
import os
import secrets
from pydantic import BaseModel

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

# Módosított háttérfolyamat
def run_intelligence_scraper(p: SearchParams):
    global results, raw_flight_data
    results = {"status": "running", "data": None, "error": None}
    try:
        tokens = get_kiwi_tokens(headless=True)
        
        outbound = search_flights_by_city_name_v2(
            origin_name=p.origin,
            destination_name=p.destination,
            tokens=tokens,
            date_from=p.out_from,
            date_to=p.out_to
        )
        
        inbound = search_flights_by_city_name_v2(
            origin_name=p.destination,
            destination_name=p.origin,
            tokens=tokens,
            date_from=p.in_from,
            date_to=p.in_to
        )
        
        if outbound.empty or inbound.empty:
            results = {"status": "done", "data": [], "count": 0, "error": "Nincs járat."}
            return

        combinations = create_return_combinations(outbound, inbound)
        
        # ✅ MÓDOSÍTÁS: Mentés a raw_flight_data globális változóba
        raw_flight_data["data"] = combinations
        raw_flight_data["count"] = len(combinations)

        results = {
            "status": "done", 
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
    global filtered_flights, raw_flight_data
    filtered_flights[username] = {"status": "running", "count": None, "error": None}
    
    try:
        # ✅ JAVÍTÁS: is None ellenőrzés
        if raw_flight_data.get("data") is None or raw_flight_data["count"] == 0:
            filtered_flights[username] = {"status": "done", "count": 0, "error": "Nincs adat a memóriában"}
            return
        
        df = raw_flight_data["data"].copy()
        
        # SZŰRÉSEK ALKALMAZÁSA
        # Indulási idő szűrés
        df['out_hour'] = pd.to_datetime(df['out_dep_time']).dt.hour
        df = df[(df['out_hour'] >= p.out_time_min) & (df['out_hour'] <= p.out_time_max)]
        
        df['in_hour'] = pd.to_datetime(df['in_dep_time']).dt.hour
        df = df[(df['in_hour'] >= p.in_time_min) & (df['in_hour'] <= p.in_time_max)]
        
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
        
        # Átszállások
        df = df[df['total_stops'] <= p.max_stops]
        
        # Ár
        df = df[(df['total_price_huf'] >= p.price_min) & (df['total_price_huf'] <= p.price_max)]
        
        # Tartózkodás
        df = df[(df['stay_days'] >= p.stay_min) & (df['stay_days'] <= p.stay_max)]
        
        # Összes utazási idő
        df['total_duration'] = df['out_duration_h'] + df['in_duration_h']
        df = df[df['total_duration'] <= p.max_total_duration]
        
        # ✅ JAVÍTÁS: Timestamp oszlopok konvertálása stringre JSON szerializáláshoz
        date_columns = ['out_dep_time', 'out_arr_time', 'in_dep_time', 'in_arr_time']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        # Mentés sessionbe
        filtered_flights[username] = {
            "status": "done",
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "error": None
        }
        
    except Exception as e:
        filtered_flights[username] = {"status": "error", "count": None, "error": str(e)}

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)