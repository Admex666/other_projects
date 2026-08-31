"""
Optivoya (DreamTrip) — Master Application Entrypoint
Structured according to Architecture Rules (v2.0): Modular Routers & Application Services.
"""
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import STATIC_DIR, APP_ENV, IS_PRODUCTION
from app.core.auth import USERS, sessions, verify_credentials, create_session, get_current_user
from app.services.destination_service import load_all_destinations

# Import Modular Routers
from app.routers import auth, planner, flights, stays, destinations, trip

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[OPTIVOYA STARTUP] Environment: {APP_ENV.upper()} (IS_PRODUCTION={IS_PRODUCTION})")
    dests = load_all_destinations()
    print(f"[OPTIVOYA STARTUP] Loaded {len(dests)} canonical destinations.")
    yield
    print("[OPTIVOYA SHUTDOWN] Application shutting down cleanly.")

app = FastAPI(
    title="Optivoya Travel Decision Intelligence",
    description="Unified Travel Intelligence Platform: Destination Matching, Flight PROMETHEE II Ranking, Accommodation Aggregation & Master Planner.",
    version="2.0.0",
    lifespan=lifespan
)

# Mount Static Assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register Routers
app.include_router(auth.router)
app.include_router(planner.router)
app.include_router(flights.router)
app.include_router(stays.router)
app.include_router(destinations.router)
app.include_router(trip.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)