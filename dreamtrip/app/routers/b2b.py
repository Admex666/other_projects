# -*- coding: utf-8 -*-
"""
Optivoya — B2B Landing & Beta Lead Router
Handles the B2B advisor landing page, value calculator telemetry, and lead attribution capture.
"""

import os
import json
import sqlite3
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr

from app.core.config import TEMPLATES_DIR
from app.services.analytics_service import record_telemetry_event

router = APIRouter(tags=["B2B & Beta"])
templates = Jinja2Templates(directory=TEMPLATES_DIR)

AI_OPS_DB_PATH = r"E:\Data\AI_ops\store\ai_ops.db"

class B2BLeadRequest(BaseModel):
    name: str
    email: EmailStr
    agency_name: Optional[str] = None
    agency_type: Optional[str] = "independent_advisor" # independent_advisor, boutique_agency, corporate_concierge, other
    clients_per_month: Optional[int] = 10
    research_hours_per_client: Optional[float] = 4.0
    hourly_rate_huf: Optional[int] = 12000
    estimated_monthly_saving_huf: Optional[int] = 0
    current_tools: Optional[str] = None
    message: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    referrer: Optional[str] = None
    client_session_id: Optional[str] = None

@router.get("/b2b", response_class=HTMLResponse)
@router.get("/beta", response_class=HTMLResponse)
@router.get("/for-advisors", response_class=HTMLResponse)
async def get_b2b_landing(request: Request):
    """Renders the B2B Beta Landing Page for travel advisors."""
    return templates.TemplateResponse("b2b/landing.html", {
        "request": request,
        "title": "Optivoya for Travel Advisors — A világ első B2B Travel Decision Engine-je",
        "is_b2b": True
    })

@router.post("/api/b2b/lead")
async def api_submit_b2b_lead(req: B2BLeadRequest, request: Request):
    """
    Saves a B2B beta applicant lead with full attribution into telemetry and central AI Ops Hub.
    """
    lead_dict = req.model_dump()
    
    # 1. Telemetry Event logging
    event_id = record_telemetry_event(
        user_id=req.email,
        session_id=req.client_session_id or "b2b_beta_lead",
        event_type="b2b_beta_lead_submitted",
        module="b2b_landing",
        search_params={
            "agency_name": req.agency_name,
            "agency_type": req.agency_type,
            "clients_per_month": req.clients_per_month,
            "hourly_rate_huf": req.hourly_rate_huf,
            "estimated_saving_huf": req.estimated_monthly_saving_huf
        },
        meta_data={
            "name": req.name,
            "utm_source": req.utm_source,
            "utm_medium": req.utm_medium,
            "utm_campaign": req.utm_campaign,
            "referrer": req.referrer,
            "current_tools": req.current_tools,
            "message": req.message
        }
    )
    
    # 2. Persist to Central AI Ops Hub (ai_ops.db tasks & memories)
    try:
        if os.path.exists(AI_OPS_DB_PATH):
            conn = sqlite3.connect(AI_OPS_DB_PATH)
            c = conn.cursor()
            
            # Create a task for B2B onboarding
            task_title = f"B2B Beta Jelentkező: {req.name} ({req.agency_name or 'Egyéni Advisor'})"
            task_desc = (
                f"Email: {req.email}\n"
                f"Típus: {req.agency_type}, Havi ügyfélszám: {req.clients_per_month}\n"
                f"Kalkulált havi megtakarítás: ~{req.estimated_monthly_saving_huf:,.0f} Ft\n"
                f"Forrás / UTM: {req.utm_source or 'direct'} / {req.utm_campaign or 'none'}\n"
                f"Jelenlegi eszközök: {req.current_tools or 'n/a'}\n"
                f"Üzenet: {req.message or '-'}"
            )
            c.execute("""
                INSERT INTO tasks (project_id, title, description, assigned_agent, status, priority, created_at, updated_at)
                VALUES ('Dreamtrip', ?, ?, 'b2b_growth', 'pending', 'high', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (task_title, task_desc))
            
            # Save memory of lead attribution
            c.execute("""
                INSERT INTO memories (project_id, category, key, value, tags, created_at, updated_at)
                VALUES ('Dreamtrip', 'domain', ?, ?, 'b2b_lead,advisor,beta', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, category, key) DO UPDATE SET
                    value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (f"lead_{req.email}", json.dumps(lead_dict, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[B2B LEAD WARNING] Could not persist to ai_ops.db: {e}")
        
    return {
        "status": "ok",
        "lead_id": event_id,
        "message": "Sikeres jelentkezés! Köszönjük az érdeklődést, a hozzáférési adataidat hamarosan elküldjük az email címedre."
    }
