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
    "demo": "demo123"
}

# Session tárolás (production-ben használj Redis-t vagy JWT-t)
sessions = {}

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

# Módosított háttérfolyamat
def run_intelligence_scraper(p: SearchParams):
    global results
    results = {"status": "running", "data": None, "error": None}
    try:
        # 1. Tokenek
        tokens = get_kiwi_tokens(headless=True)
        
        # 2. Odaút keresés - JAVÍTOTT PARAMÉTERNEVEK
        outbound = search_flights_by_city_name_v2(
            origin_name=p.origin,        # 'origin' helyett 'origin_name'
            destination_name=p.destination, # 'destination' helyett 'destination_name'
            tokens=tokens,
            date_from=p.out_from,
            date_to=p.out_to
        )
        
        # 3. Visszaút keresés - JAVÍTOTT PARAMÉTERNEVEK
        inbound = search_flights_by_city_name_v2(
            origin_name=p.destination,   # Itt is!
            destination_name=p.origin,      # Itt is!
            tokens=tokens,
            date_from=p.in_from,
            date_to=p.in_to
        )
        
        if outbound.empty or inbound.empty:
            results = {"status": "done", "data": [], "error": "Nem található járat ezekre a dátumokra."}
            return

        # 4. Kombinálás
        combinations = create_return_combinations(outbound, inbound)
        top10 = combinations.head(10).to_dict(orient="records")
        
        # Dátum formázás JSON-hoz
        for row in top10:
            for key in ['out_dep_time', 'out_arr_time', 'in_dep_time', 'in_arr_time']:
                if isinstance(row[key], pd.Timestamp):
                    row[key] = row[key].strftime('%Y-%m-%d %H:%M')

        results = {"status": "done", "data": top10, "error": None}
    except Exception as e:
        results = {"status": "error", "data": None, "error": str(e)}

@app.post("/start-intelligence-search")
async def start_search(params: SearchParams, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_intelligence_scraper, params)
    return {"message": "Search started"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)