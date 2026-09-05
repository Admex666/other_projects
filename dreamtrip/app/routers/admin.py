"""
Optivoya Admin Router: Usage Analytics Dashboard & Beta User Management
Protected by ADMIN_PASSWORD configured in .env.
"""
import os
import secrets
from fastapi import APIRouter, Request, Response, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel

from app.core.config import templates, ENV_PATH, get_clarity_project_id
from app.services.analytics_service import (
    get_analytics_kpis,
    get_user_timeline,
    get_user_sessions_summary,
    record_telemetry_event
)
from app.services.user_service import get_all_beta_users, create_beta_user, toggle_user_active

router = APIRouter(tags=["Admin & Analytics"])

class ClientTelemetryEvent(BaseModel):
    event_type: str = "button_click"
    module: str = "master_planner"
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    duration_ms: Optional[float] = None
    search_params: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None

@router.post("/api/telemetry/event")
async def api_record_client_telemetry(event: ClientTelemetryEvent, request: Request):
    from app.core.auth import get_current_user
    user = get_current_user(request) or event.user_id or request.cookies.get("optivoya_user") or "guest"
    session_id = event.session_id or request.headers.get("x-session-id") or request.cookies.get("optivoya_session_id")
    
    evt_id = record_telemetry_event(
        user_id=user,
        session_id=session_id,
        event_type=event.event_type,
        module=event.module,
        duration_ms=event.duration_ms,
        search_params=event.search_params,
        meta_data=event.meta_data,
        success=True
    )
    return JSONResponse({"status": "ok", "event_id": evt_id})

ADMIN_SESSION_TOKEN = secrets.token_urlsafe(32)

def get_admin_password() -> str:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    raw = os.getenv("ADMIN_PASSWORD", "optivoya_admin_2026")
    return raw.strip().strip('"').strip("'")

def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("optivoya_admin_token")
    return token is not None and token == ADMIN_SESSION_TOKEN

@router.get("/admin", response_class=HTMLResponse)
async def admin_entry(request: Request):
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/admin_login.html", {"request": request, "error": None})

@router.post("/admin/login")
async def admin_login(request: Request, response: Response, password: str = Form(...)):
    global ADMIN_SESSION_TOKEN
    expected_password = get_admin_password()
    submitted_password = password.strip().strip('"').strip("'")

    if submitted_password == expected_password:
        ADMIN_SESSION_TOKEN = secrets.token_urlsafe(32)
        resp = RedirectResponse(url="/admin/dashboard", status_code=302)
        resp.set_cookie(
            key="optivoya_admin_token",
            value=ADMIN_SESSION_TOKEN,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7 # 7 nap
        )
        return resp
    return templates.TemplateResponse("admin/admin_login.html", {
        "request": request, 
        "error": "Hibás adminisztrátori jelszó! Kérlek ellenőrizd a .env beállítást."
    }, status_code=401)


@router.get("/admin/logout")
async def admin_logout():
    resp = RedirectResponse(url="/admin", status_code=302)
    resp.delete_cookie("optivoya_admin_token")
    return resp

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: Optional[str] = None):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    kpis = get_analytics_kpis(user_id=user)
    users = get_all_beta_users()
    timeline = get_user_timeline(user_id=user, limit=150)
    sessions = get_user_sessions_summary(user_id=user, limit=50)

    selected_users = [u.strip() for u in (user or "").split(",") if u.strip() and u.strip() != "all"]
    selected_user_str = ",".join(selected_users) if selected_users else "all"

    return templates.TemplateResponse("admin/admin_dashboard.html", {
        "request": request,
        "kpis": kpis,
        "users": users,
        "timeline": timeline,
        "sessions": sessions,
        "clarity_project_id": get_clarity_project_id(),
        "selected_users": selected_users,
        "selected_user": selected_user_str
    })

@router.get("/api/admin/kpis")
async def api_admin_kpis(request: Request, user: Optional[str] = "all"):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    kpis = get_analytics_kpis(user_id=user)
    return JSONResponse({"status": "ok", "kpis": kpis})

@router.get("/api/admin/timeline")
async def api_admin_timeline(request: Request, user: Optional[str] = "all"):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    timeline = get_user_timeline(user_id=user, limit=150)
    return JSONResponse({"status": "ok", "events": timeline})

@router.get("/api/admin/sessions")
async def api_admin_sessions(request: Request, user: Optional[str] = "all"):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    sessions = get_user_sessions_summary(user_id=user, limit=50)
    return JSONResponse({"status": "ok", "sessions": sessions, "clarity_project_id": get_clarity_project_id()})

@router.post("/api/admin/users")
async def api_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    company_name: str = Form(""),
    email: str = Form(""),
    notes: str = Form("")
):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    res = create_beta_user(
        username=username,
        password=password,
        full_name=full_name,
        company_name=company_name,
        email=email,
        notes=notes
    )
    if res.get("status") == "ok":
        return RedirectResponse(url="/admin/dashboard?msg=user_created", status_code=302)
    else:
        return JSONResponse(res, status_code=400)

@router.post("/api/admin/users/{user_id}/toggle")
async def api_toggle_user(request: Request, user_id: int):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = toggle_user_active(user_id)
    return JSONResponse({"status": "ok", "user_id": user_id, "updated": success})
