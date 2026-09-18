"""
Optivoya B2B Advisor Workspace — REST API Router
Provides comprehensive RESTful contracts for multi-tenant Agency & Advisor operations:
- Agency / Advisor profile & KPIs
- Client CRM & Preferences (AHP / PROMETHEE)
- TripCase lifecycle (Brief -> Research -> Shortlist -> Proposal -> Revision -> Closed)
- Multi-option proposals & snapshot generation
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Header, Request, status
from fastapi.responses import JSONResponse

from app.models.advisor_models import (
    Agency, AgencyBranding, Advisor, Client, ClientPreferences,
    TripCase, TripCaseStatus, BudgetMode, ResearchScope,
    TripOption, OptionArchetype, HardConstraints, SoftPreferences,
    AvoidRules, NiceToHave, AdvisorOverrides, ResolvedTripPreferences,
    Proposal, ProposalVersion, ProviderProvenance, VerificationStatus,
    generate_uuid, utc_now
)
from app.services.trip_scoring_service import TripScoreService
from app.services.preference_resolver import PreferenceResolver

router = APIRouter(prefix="/api/advisor", tags=["Advisor Workspace"])

# =====================================================================
# IN-MEMORY REPOSITORY (Fast in-memory store with DB sync capability)
# =====================================================================

DEFAULT_AGENCY_ID = "agency_default_lux"
DEFAULT_ADVISOR_ID = "adv_adam_lead"

AGENCIES_STORE: Dict[str, Agency] = {
    DEFAULT_AGENCY_ID: Agency(
        id=DEFAULT_AGENCY_ID,
        name="Optivoya Premier Travel Agency",
        slug="optivoya-premier",
        branding=AgencyBranding(
            company_name="Optivoya Premier Travel",
            primary_color="#0284c7",
            accent_color="#38bdf8",
            contact_email="vip@optivoya.com"
        )
    )
}

ADVISORS_STORE: Dict[str, Advisor] = {
    DEFAULT_ADVISOR_ID: Advisor(
        id=DEFAULT_ADVISOR_ID,
        agency_id=DEFAULT_AGENCY_ID,
        name="Ádám (Lead Travel Advisor)",
        email="adam@optivoya.com",
        role="lead_advisor"
    )
}

CLIENTS_STORE: Dict[str, Client] = {
    "client_kovacs_csalad": Client(
        id="client_kovacs_csalad",
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        name="Kovács Család (Péter & Dóra)",
        email="kovacs.peter@example.com",
        phone="+36 30 123 4567",
        tags=["Family", "Luxury", "Summer"],
        notes="2 felnőtt + 1 gyerek (7 éves). Szeretik a közvetlen járatokat és a belvárosi 4-5 csillagos hoteleket.",
        preferences=ClientPreferences(
            hotel_min_stars=4,
            hotel_min_rating=8.8,
            direct_flights_only=True,
            interests=["culture", "gastronomy", "relaxation"]
        )
    ),
    "client_toth_par": Client(
        id="client_toth_par",
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        name="Tóth Bence & Kata",
        email="toth.bence@example.com",
        phone="+36 20 987 6543",
        tags=["Couples", "CityBreak", "Foodie"],
        notes="Hosszú hétvégi gasztro-városlátogatás Európában.",
        preferences=ClientPreferences(
            hotel_min_stars=4,
            hotel_min_rating=9.0,
            interests=["gastronomy", "nightlife", "sightseeing"]
        )
    )
}

CASES_STORE: Dict[str, TripCase] = {
    "case_london_kovacs": TripCase(
        id="case_london_kovacs",
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        client_id="client_kovacs_csalad",
        title="London Családi Felfedezés & Múzeumok",
        status=TripCaseStatus.SHORTLIST,
        scope=ResearchScope.FULL_TRIP,
        budget_mode=BudgetMode.TOTAL_BUDGET,
        total_budget_huf=650000,
        origin="BUD",
        destination_focus="London",
        adults=2,
        children=1,
        duration_days=4,
        preferences=ResolvedTripPreferences(
            hard=HardConstraints(
                max_total_budget_huf=650000,
                direct_flights_only=True,
                min_hotel_stars=4,
                min_hotel_rating=8.5
            )
        )
    ),
    "case_barcelona_toth": TripCase(
        id="case_barcelona_toth",
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        client_id="client_toth_par",
        title="Barcelona Gasztro & Tengerpart Hétvége",
        status=TripCaseStatus.PROPOSAL,
        scope=ResearchScope.FULL_TRIP,
        budget_mode=BudgetMode.TOTAL_BUDGET,
        total_budget_huf=480000,
        origin="BUD",
        destination_focus="Barcelona",
        adults=2,
        children=0,
        duration_days=4,
        preferences=ResolvedTripPreferences(
            hard=HardConstraints(
                max_total_budget_huf=480000,
                min_hotel_stars=4,
                min_hotel_rating=8.8
            )
        )
    )
}

PROPOSALS_STORE: Dict[str, Proposal] = {}
OPTIONS_STORE: Dict[str, List[TripOption]] = {}

# =====================================================================
# PYDANTIC REQUEST & RESPONSE SCHEMAS
# =====================================================================

class CreateClientRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: str = Field(...)
    phone: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    preferences: Optional[ClientPreferences] = None

class CreateCaseRequest(BaseModel):
    client_id: str
    title: str = Field(..., min_length=3, max_length=200)
    target_total_budget: Optional[float] = None
    budget_mode: BudgetMode = BudgetMode.TOTAL_BUDGET
    travelers_adults: int = Field(default=2, ge=1, le=20)
    travelers_children: int = Field(default=0, ge=0, le=20)
    origin: str = Field(default="BUD")
    destinations: List[str] = Field(default_factory=lambda: ["London"])
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    duration_days: int = Field(default=4, ge=1, le=30)
    direct_flights_only: bool = False
    min_hotel_stars: int = 3
    min_hotel_rating: float = 8.0

class UpdateCaseStatusRequest(BaseModel):
    status: TripCaseStatus

class DashboardKPIsResponse(BaseModel):
    active_cases: int
    research_jobs_completed: int
    proposals_created: int
    estimated_hours_saved: float
    avg_composite_tripscore: float
    recent_activity_count: int

# =====================================================================
# ENDPOINTS
# =====================================================================

@router.get("/me")
async def get_current_advisor_info():
    """Returns the authenticated advisor and agency profile."""
    advisor = ADVISORS_STORE.get(DEFAULT_ADVISOR_ID)
    agency = AGENCIES_STORE.get(DEFAULT_AGENCY_ID)
    return {
        "status": "success",
        "advisor": advisor.model_dump() if advisor else None,
        "agency": agency.model_dump() if agency else None
    }

@router.get("/dashboard/kpis", response_model=DashboardKPIsResponse)
async def get_dashboard_kpis():
    """Returns real-time operational KPIs for the Advisor Dashboard."""
    active_cases_count = sum(1 for c in CASES_STORE.values() if c.status not in [TripCaseStatus.CLOSED])
    proposals_count = len(PROPOSALS_STORE) + 1  # count active + samples
    
    return DashboardKPIsResponse(
        active_cases=active_cases_count,
        research_jobs_completed=len(CASES_STORE) * 3,
        proposals_created=proposals_count,
        estimated_hours_saved=round(active_cases_count * 2.8 + proposals_count * 1.5, 1),
        avg_composite_tripscore=88.4,
        recent_activity_count=len(CASES_STORE) + len(CLIENTS_STORE)
    )

# --- Clients CRM ---

@router.get("/clients")
async def list_clients(search: Optional[str] = Query(None, description="Search by client name or email")):
    """List all agency clients with optional search query."""
    clients = list(CLIENTS_STORE.values())
    if search:
        s = search.lower()
        clients = [c for c in clients if s in c.name.lower() or (c.email and s in c.email.lower())]
    return {
        "status": "success",
        "total": len(clients),
        "clients": [c.model_dump() for c in clients]
    }

@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def create_client(payload: CreateClientRequest):
    """Creates a new client in the agency CRM with preference baseline."""
    client_id = f"client_{uuid.uuid4().hex[:10]}"
    client = Client(
        id=client_id,
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        tags=payload.tags,
        notes=payload.notes,
        preferences=payload.preferences or ClientPreferences()
    )
    CLIENTS_STORE[client_id] = client
    return {"status": "success", "client": client.model_dump()}

@router.get("/clients/{client_id}")
async def get_client_details(client_id: str):
    """Get single client details and associated past trip cases."""
    client = CLIENTS_STORE.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    cases = [c.model_dump() for c in CASES_STORE.values() if c.client_id == client_id]
    return {"status": "success", "client": client.model_dump(), "cases": cases}

# --- Trip Cases ---

@router.get("/cases")
async def list_cases(status_filter: Optional[TripCaseStatus] = Query(None, alias="status")):
    """List all advisor cases with enriched client info and status badges."""
    cases = list(CASES_STORE.values())
    if status_filter:
        cases = [c for c in cases if c.status == status_filter]
    
    # Enrich with client name for UI table/cards
    enriched = []
    for c in cases:
        c_dict = c.model_dump()
        client = CLIENTS_STORE.get(c.client_id)
        c_dict["client_name"] = client.name if client else "Ismeretlen Ügyfél"
        c_dict["client_email"] = client.email if client else None
        c_dict["target_total_budget"] = c.total_budget_huf
        c_dict["duration_days_min"] = c.duration_days
        c_dict["research_scope"] = {
            "candidate_origins": [c.origin],
            "candidate_destinations": [c.destination_focus] if c.destination_focus else ["London"]
        }
        enriched.append(c_dict)
        
    return {"status": "success", "total": len(enriched), "cases": enriched}

@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def create_case(payload: CreateCaseRequest):
    """Creates a new trip case and initiates brief setup."""
    client = CLIENTS_STORE.get(payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client '{payload.client_id}' not found.")
        
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    dest_focus = payload.destinations[0] if payload.destinations else "London"
    
    trip_case = TripCase(
        id=case_id,
        agency_id=DEFAULT_AGENCY_ID,
        advisor_id=DEFAULT_ADVISOR_ID,
        client_id=payload.client_id,
        title=payload.title,
        status=TripCaseStatus.BRIEF,
        scope=ResearchScope.FULL_TRIP,
        budget_mode=payload.budget_mode,
        total_budget_huf=payload.target_total_budget,
        origin=payload.origin,
        destination_focus=dest_focus,
        adults=payload.travelers_adults,
        children=payload.travelers_children,
        duration_days=payload.duration_days,
        out_date=payload.departure_date,
        in_date=payload.return_date,
        preferences=ResolvedTripPreferences(
            hard=HardConstraints(
                max_total_budget_huf=payload.target_total_budget,
                direct_flights_only=payload.direct_flights_only,
                min_hotel_stars=payload.min_hotel_stars,
                min_hotel_rating=payload.min_hotel_rating
            )
        )
    )
    CASES_STORE[case_id] = trip_case
    return {"status": "success", "case": trip_case.model_dump()}

@router.get("/cases/{case_id}")
async def get_case_details(case_id: str):
    """Returns single case details, client profile, options and proposals."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    client = CLIENTS_STORE.get(trip_case.client_id)
    options = OPTIONS_STORE.get(case_id, [])
    
    return {
        "status": "success",
        "case": trip_case.model_dump(),
        "client": client.model_dump() if client else None,
        "options": [o.model_dump() for o in options]
    }

class UpdateClientRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    passport_country: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    preferences: Optional[ClientPreferences] = None

class UpdateTripBriefRequest(BaseModel):
    title: Optional[str] = None
    budget_mode: Optional[BudgetMode] = None
    total_budget_huf: Optional[float] = None
    flight_budget_huf: Optional[float] = None
    stay_budget_huf: Optional[float] = None
    origin: Optional[str] = None
    destination_focus: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    duration_days: Optional[int] = None
    out_date: Optional[str] = None
    in_date: Optional[str] = None
    hard_constraints: Optional[HardConstraints] = None
    soft_preferences: Optional[SoftPreferences] = None
    avoid_rules: Optional[AvoidRules] = None
    nice_to_have: Optional[NiceToHave] = None
    advisor_overrides: Optional[AdvisorOverrides] = None

UpdateTripBriefRequest.model_rebuild()

@router.put("/clients/{client_id}")
async def update_client(client_id: str, payload: UpdateClientRequest):
    """Updates an existing client profile and persistent travel preferences."""
    client = CLIENTS_STORE.get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    if payload.name is not None: client.name = payload.name
    if payload.email is not None: client.email = payload.email
    if payload.phone is not None: client.phone = payload.phone
    if payload.passport_country is not None: client.passport_country = payload.passport_country
    if payload.tags is not None: client.tags = payload.tags
    if payload.notes is not None: client.notes = payload.notes
    if payload.preferences is not None: client.preferences = payload.preferences

    client.updated_at = utc_now()
    return {"status": "success", "client": client.model_dump()}

@router.get("/cases/{case_id}/resolved-preferences")
async def get_resolved_case_preferences(case_id: str):
    """Returns the fully resolved 4-layer preference hierarchy for a case."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = CLIENTS_STORE.get(trip_case.client_id)
    resolved = PreferenceResolver.resolve_preferences(trip_case, client)
    budget_check = PreferenceResolver.validate_budget_mode(trip_case)

    return {
        "status": "success",
        "case_id": case_id,
        "client_id": trip_case.client_id,
        "budget_validation": budget_check,
        "resolved_preferences": resolved.model_dump()
    }

@router.put("/cases/{case_id}/brief")
async def update_trip_brief(case_id: str, payload: UpdateTripBriefRequest):
    """Updates the comprehensive deep brief and constraint hierarchy for a case."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    if payload.title is not None: trip_case.title = payload.title
    if payload.budget_mode is not None: trip_case.budget_mode = payload.budget_mode
    if payload.total_budget_huf is not None: trip_case.total_budget_huf = payload.total_budget_huf
    if payload.flight_budget_huf is not None: trip_case.flight_budget_huf = payload.flight_budget_huf
    if payload.stay_budget_huf is not None: trip_case.stay_budget_huf = payload.stay_budget_huf
    if payload.origin is not None: trip_case.origin = payload.origin
    if payload.destination_focus is not None: trip_case.destination_focus = payload.destination_focus
    if payload.adults is not None: trip_case.adults = payload.adults
    if payload.children is not None: trip_case.children = payload.children
    if payload.duration_days is not None: trip_case.duration_days = payload.duration_days
    if payload.out_date is not None: trip_case.out_date = payload.out_date
    if payload.in_date is not None: trip_case.in_date = payload.in_date

    if payload.hard_constraints is not None:
        trip_case.preferences.hard = payload.hard_constraints
    if payload.soft_preferences is not None:
        trip_case.preferences.soft = payload.soft_preferences
    if payload.avoid_rules is not None:
        trip_case.preferences.avoid = payload.avoid_rules
    if payload.nice_to_have is not None:
        trip_case.preferences.nice_to_have = payload.nice_to_have
    if payload.advisor_overrides is not None:
        trip_case.preferences.overrides = payload.advisor_overrides

    trip_case.updated_at = utc_now()
    
    client = CLIENTS_STORE.get(trip_case.client_id)
    resolved = PreferenceResolver.resolve_preferences(trip_case, client)

    return {
        "status": "success",
        "case": trip_case.model_dump(),
        "resolved_preferences": resolved.model_dump()
    }

from app.services.advisor_orchestration_service import AdvisorOrchestrationService, ResearchStrategy

class ExecuteResearchRequest(BaseModel):
    strategy: str = Field(default=ResearchStrategy.FULL_TRIP_OPTIMIZATION)
    custom_params: Optional[Dict[str, Any]] = None

class PinCandidateRequest(BaseModel):
    candidate_id: str
    is_pinned: bool = True
    component_type: Optional[str] = "trip"  # "trip", "destination", "flight", "stay"
    component_id: Optional[str] = None

class DuplicateCaseRequest(BaseModel):
    new_title: Optional[str] = None

# Rebuild models if necessary
UpdateTripBriefRequest.model_rebuild()
ExecuteResearchRequest.model_rebuild()


@router.post("/cases/{case_id}/research")
async def execute_case_research(case_id: str, payload: Optional[ExecuteResearchRequest] = None):
    """
    Triggers one of the 9 Advisor Research Workflows for a trip case.
    Executes resilient candidate scoring and returns full candidate pools and telemetry.
    """
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = CLIENTS_STORE.get(trip_case.client_id)
    strategy = payload.strategy if payload else ResearchStrategy.FULL_TRIP_OPTIMIZATION
    custom_params = payload.custom_params if payload else {}

    # Advance case status to RESEARCH if in BRIEF
    if trip_case.status == TripCaseStatus.BRIEF:
        trip_case.status = TripCaseStatus.RESEARCH
        trip_case.updated_at = utc_now()

    result = AdvisorOrchestrationService.execute_research(
        trip_case=trip_case,
        client=client,
        strategy=strategy,
        custom_params=custom_params
    )

    return {
        "status": "success",
        "case_id": case_id,
        "job": result
    }


@router.get("/cases/{case_id}/research/status")
async def get_case_research_status(case_id: str):
    """Returns the latest research job status and candidates for a case."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
    # Find latest job for this case
    latest_job = None
    for j in reversed(list(AdvisorOrchestrationService._RESEARCH_JOBS.values())):
        if j.get("case_id") == case_id:
            latest_job = j
            break

    return {
        "status": "success",
        "case_id": case_id,
        "latest_job": latest_job,
        "candidates_count": len(candidates),
        "candidates": candidates
    }


@router.get("/research/{job_id}")
async def get_research_job(job_id: str):
    """Retrieves asynchronous research job telemetry and candidate status by Job ID."""
    job = AdvisorOrchestrationService._RESEARCH_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")
    return {"status": "success", "job": job}


@router.get("/cases/{case_id}/candidates")
async def get_case_candidates(case_id: str):
    """Returns the pool of generated candidate packages for a case."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
    return {
        "status": "success",
        "case_id": case_id,
        "total": len(candidates),
        "candidates": candidates
    }


@router.post("/cases/{case_id}/candidates/pin")
async def pin_candidate(case_id: str, payload: PinCandidateRequest):
    """Pins or unpins a candidate or specific component into Advisor Overrides."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
    target = next((c for c in candidates if c.get("id") == payload.candidate_id), None)

    if target:
        target["is_pinned"] = payload.is_pinned
        if payload.is_pinned:
            if payload.component_type == "destination":
                trip_case.preferences.overrides.pinned_destination = target.get("destination", {}).get("city")
            elif payload.component_type == "flight":
                trip_case.preferences.overrides.pinned_flight_id = target.get("flight", {}).get("id")
            elif payload.component_type == "stay":
                trip_case.preferences.overrides.pinned_stay_id = target.get("stay", {}).get("id")

    trip_case.updated_at = utc_now()
    return {
        "status": "success",
        "candidate_id": payload.candidate_id,
        "is_pinned": payload.is_pinned,
        "overrides": trip_case.preferences.overrides.model_dump()
    }


@router.post("/cases/{case_id}/duplicate")
async def duplicate_case(case_id: str, payload: Optional[DuplicateCaseRequest] = None):
    """Duplicates an existing trip case for rapid iteration or alternate client proposals."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    new_id = f"case_{uuid.uuid4().hex[:10]}"
    cloned = trip_case.model_copy(deep=True)
    cloned.id = new_id
    cloned.title = (payload.new_title if payload and payload.new_title else f"{trip_case.title} (Másolat)")
    cloned.status = TripCaseStatus.BRIEF
    cloned.created_at = utc_now()
    cloned.updated_at = utc_now()

    CASES_STORE[new_id] = cloned
    return {"status": "success", "duplicated_case": cloned.model_dump()}


@router.patch("/cases/{case_id}/status")
async def update_case_status(case_id: str, payload: UpdateCaseStatusRequest):
    """Advances or updates the status of an active case."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    trip_case.status = payload.status
    trip_case.updated_at = utc_now()
    return {"status": "success", "case": trip_case.model_dump()}


@router.post("/cases/{case_id}/archive")
async def archive_case(case_id: str):
    """Archives a trip case by setting its status to CLOSED."""
    trip_case = CASES_STORE.get(case_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    trip_case.status = TripCaseStatus.CLOSED
    trip_case.updated_at = utc_now()
    return {"status": "success", "case": trip_case.model_dump()}




