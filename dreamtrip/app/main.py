"""
Optivoya (DreamTrip) — Master Application Entrypoint
Structured according to Architecture Rules (v2.0): Modular Routers & Application Services.
"""
import os
import uvicorn
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.core.config import STATIC_DIR, APP_ENV, IS_PRODUCTION
from app.core.auth import USERS, sessions, verify_credentials, create_session, get_current_user
from app.services.destination_service import load_all_destinations

# Import Modular Routers
from app.routers import auth, planner, flights, stays, destinations, trip, admin, b2b, advisor_api
from app.services.analytics_service import record_telemetry_event
from fastapi.templating import Jinja2Templates
from app.core.config import TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)

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

# Telemetry Middleware: Latency Measurement & Server-Timing Header Injection
@app.middleware("http")
async def performance_telemetry_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    # Attach industry-standard Server-Timing & X-Process-Time headers
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    existing_timing = response.headers.get("Server-Timing", "")
    server_timing_val = f"total;dur={duration_ms};desc=\"Total Process Time\""
    if existing_timing:
        response.headers["Server-Timing"] = f"{server_timing_val}, {existing_timing}"
    else:
        response.headers["Server-Timing"] = server_timing_val

    if duration_ms > 3500 and not request.url.path.startswith("/static"):
        print(f"[PERFORMANCE WARNING] High latency on {request.method} {request.url.path}: {duration_ms} ms (SLA p95 target: 3500ms)")
        
    return response

# Mount Static Assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Analytics Client Ingestion API
@app.post("/api/analytics/event")
async def api_record_client_event(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id") or get_current_user(request) or "anonymous_advisor"
        event_id = record_telemetry_event(
            user_id=user_id,
            session_id=data.get("session_id"),
            event_type=data.get("event_type", "custom_event"),
            module=data.get("module", "general"),
            search_params=data.get("search_params"),
            duration_ms=data.get("duration_ms"),
            results_count=data.get("results_count"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            meta_data=data.get("meta_data")
        )
        return {"status": "ok", "event_id": event_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Register Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(planner.router)
app.include_router(flights.router)
app.include_router(stays.router)
app.include_router(destinations.router)
app.include_router(trip.router)
app.include_router(b2b.router)
app.include_router(advisor_api.router)

from fastapi.responses import RedirectResponse
from app.core.auth import is_advisor_user, get_user_role

@app.get("/advisor")
async def advisor_workspace_view(request: Request):
    """Desktop-first B2B Advisor Workspace v2 (Default)."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if not is_advisor_user(user):
        return RedirectResponse(url="/planner?error=advisor_access_required", status_code=303)
    role = get_user_role(user)
    return templates.TemplateResponse("advisor/advisor_workspace.html", {
        "request": request,
        "user": user,
        "role": role,
        "is_advisor": True,
        "workspace_version": "v2",
        "is_admin": role == "ADMIN"
    })


@app.get("/advisor/v1")
async def advisor_workspace_v1_legacy_view(request: Request):
    """Legacy Advisor Workspace v1 Shell (Accessible for Admin / Compatibility)."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if not is_advisor_user(user):
        return RedirectResponse(url="/planner?error=advisor_access_required", status_code=303)
    role = get_user_role(user)
    return templates.TemplateResponse("advisor/advisor_workspace.html", {
        "request": request,
        "user": user,
        "role": role,
        "is_advisor": True,
        "workspace_version": "v1",
        "is_admin": role == "ADMIN"
    })



@app.get("/share/proposal/{token}")
async def public_shared_proposal_view(request: Request, token: str):
    """Publicly viewable client proposal snapshot accessed via secure share token."""
    from app.services.proposal_service import ProposalService
    from app.repositories.advisor_repository import ProposalRepository
    from fastapi import HTTPException

    share = ProposalService.get_share_by_token(token)
    if not share:
        raise HTTPException(status_code=404, detail="Érvénytelen, lejárt vagy visszavont ajánlat link.")

    proposal = ProposalRepository.get_proposal_doc(share.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Ajánlat nem található.")

    client_safe = ProposalService.get_client_safe_proposal(proposal)

    return templates.TemplateResponse(
        request=request,
        name="advisor/proposal_print.html",
        context={
            "proposal": client_safe,
            "is_public_share": True,
            "share_info": {
                "token": token,
                "version": share.proposal_version_number
            }
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)