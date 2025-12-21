from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
from scraper import get_kiwi_tokens, search_one_way_flights, create_return_combinations
import os

app = FastAPI()

# Static fájlok szolgálása
app.mount("/static", StaticFiles(directory="static"), name="static")

# Globális változó az eredményekhez
results = {"status": "idle", "data": None, "error": None}

@app.get("/")
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/search")
async def search_flights(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scraper)
    return JSONResponse({"message": "Scraping elindult..."})

@app.get("/status")
async def get_status():
    return JSONResponse(results)

def run_scraper():
    global results
    results = {"status": "running", "data": None, "error": None}
    
    try:
        # Token megszerzése
        tokens = get_kiwi_tokens(headless=True)
        
        # Oda járatok
        outbound = search_one_way_flights(
            origin="budapest_hu",
            destination="barcelona_es",
            tokens=tokens,
            date_from="2026-01-25",
            date_to="2026-01-26",
            limit=50
        )
        
        # Vissza járatok
        inbound = search_one_way_flights(
            origin="barcelona_es",
            destination="budapest_hu",
            tokens=tokens,
            date_from="2026-02-01",
            date_to="2026-02-09",
            limit=50
        )
        
        # Kombinációk
        combinations = create_return_combinations(outbound, inbound, min_stay_days=5, max_stay_days=15)
        
        # Top 10 JSON formátumra
        top10 = combinations.head(10).to_dict(orient="records")
        
        # Dátumok string-re
        for row in top10:
            for key in row:
                if pd.notna(row[key]) and isinstance(row[key], pd.Timestamp):
                    row[key] = row[key].strftime("%Y-%m-%d %H:%M")
        
        results = {"status": "done", "data": top10, "error": None}
        
    except Exception as e:
        results = {"status": "error", "data": None, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
