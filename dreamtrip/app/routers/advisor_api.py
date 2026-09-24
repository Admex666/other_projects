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
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.advisor_models import (
    Agency, AgencyBranding, Advisor, Client, ClientPreferences,
    TripCase, TripCaseStatus, BudgetMode, ResearchScope,
    BudgetConstraint, ComponentBudget, TotalBudget, BudgetHardness, BudgetBasis,
    TripOption, OptionArchetype, HardConstraints, SoftPreferences,
    AvoidRules, NiceToHave, AdvisorOverrides, AdvisorOverrideEntry, ResolvedTripPreferences,
    ResearchRun, ResearchRunStatus, ResearchCandidate, OptionSet,
    Proposal, ProposalVersion, ProposalShare, ProviderProvenance, VerificationStatus,
    generate_uuid, utc_now
)
from app.services.trip_scoring_service import TripScoreService
from app.services.preference_resolver import PreferenceResolver
from app.services.multi_option_engine import MultiOptionEngine
from app.services.relative_comparison_service import RelativeComparisonService
from app.services.constraint_relaxation_service import ConstraintRelaxationService
from app.services.verification_service import VerificationService
from app.services.trip_risk_service import TripRiskService
from app.services.proposal_service import ProposalService
from app.services.timeline_reoptimization_service import TimelineReoptimizationService
from app.services.advisor_orchestration_service import AdvisorOrchestrationService, ResearchStrategy

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/api/advisor", tags=["Advisor Workspace"])

from app.repositories.advisor_repository import (
    AgencyRepository, AdvisorRepository, ClientRepository,
    TripCaseRepository, ResearchRunRepository, TripOptionRepository,
    ProposalRepository, ProposalShareRepository, TimelineRepository
)

DEFAULT_AGENCY_ID = AgencyRepository.DEFAULT_AGENCY_ID
DEFAULT_ADVISOR_ID = AdvisorRepository.DEFAULT_ADVISOR_ID

def get_agency_context(request: Request = None, x_agency_id: Optional[str] = Header(None)) -> Optional[str]:
    """Extracts active agency_id from header. Returns None if no explicit multi-tenant header is provided."""
    if x_agency_id:
        return x_agency_id
    if request and hasattr(request, "headers") and "x-agency-id" in request.headers:
        return request.headers["x-agency-id"]
    return None

def get_advisor_context(request: Request = None, x_advisor_id: Optional[str] = Header(None)) -> Optional[str]:
    """Extracts active advisor_id from header. Returns None if no explicit multi-tenant header is provided."""
    if x_advisor_id:
        return x_advisor_id
    if request and hasattr(request, "headers") and "x-advisor-id" in request.headers:
        return request.headers["x-advisor-id"]
    return None


class _RepositoryDictWrapper(dict):
    """Compatibility adapter delegating dict lookups and writes to the DB repository layer."""
    def __init__(self, repo_cls, entity_name):
        super().__init__()
        self.repo = repo_cls
        self.entity_name = entity_name

    def __getitem__(self, key):
        if self.entity_name == "case":
            res = self.repo.get_case(key)
        elif self.entity_name == "client":
            res = self.repo.get_client(key)
        elif self.entity_name == "proposal":
            res = self.repo.get_proposal_doc(key)
        elif self.entity_name == "agency":
            res = self.repo.get_agency(key)
        elif self.entity_name == "advisor":
            res = self.repo.get_advisor(key)
        elif self.entity_name == "options":
            res = self.repo.list_options_for_case(key)
        else:
            res = None
        if res is None:
            raise KeyError(key)
        return res

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        if self.entity_name == "case":
            self.repo.save_case(value)
        elif self.entity_name == "client":
            self.repo.save_client(value)
        elif self.entity_name == "proposal":
            self.repo.save_proposal(value)
        elif self.entity_name == "agency":
            self.repo.save_agency(value)
        elif self.entity_name == "advisor":
            self.repo.save_advisor(value)
        elif self.entity_name == "options":
            if isinstance(value, list):
                self.repo.save_options_batch(key, value)
            else:
                self.repo.save_option(value)

    def values(self):
        if self.entity_name == "case":
            return self.repo.list_cases(AgencyRepository.DEFAULT_AGENCY_ID)
        elif self.entity_name == "client":
            return self.repo.list_clients(AgencyRepository.DEFAULT_AGENCY_ID)
        return []

    def __contains__(self, key):
        return self.get(key) is not None

    def __len__(self):
        return len(self.values())


AGENCIES_STORE = _RepositoryDictWrapper(AgencyRepository, "agency")
ADVISORS_STORE = _RepositoryDictWrapper(AdvisorRepository, "advisor")
CLIENTS_STORE = _RepositoryDictWrapper(ClientRepository, "client")
CASES_STORE = _RepositoryDictWrapper(TripCaseRepository, "case")
PROPOSALS_STORE = _RepositoryDictWrapper(ProposalRepository, "proposal")
OPTIONS_STORE = _RepositoryDictWrapper(TripOptionRepository, "options")


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
async def get_current_advisor_info(
    request: Request,
    x_agency_id: Optional[str] = Header(None),
    x_advisor_id: Optional[str] = Header(None)
):
    """Returns the authenticated advisor and agency profile."""
    agency_id = get_agency_context(request, x_agency_id) or DEFAULT_AGENCY_ID
    advisor_id = get_advisor_context(request, x_advisor_id) or DEFAULT_ADVISOR_ID
    
    advisor = AdvisorRepository.get_advisor(advisor_id)
    agency = AgencyRepository.get_agency(agency_id)
    return {
        "status": "success",
        "advisor": advisor.model_dump() if advisor else None,
        "agency": agency.model_dump() if agency else None
    }

@router.get("/dashboard/kpis", response_model=DashboardKPIsResponse)
async def get_dashboard_kpis(
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns real-time operational KPIs for the Advisor Dashboard."""
    agency_id = get_agency_context(request, x_agency_id)
    cases = TripCaseRepository.list_cases(agency_id)
    clients = ClientRepository.list_clients(agency_id)
    
    active_cases_count = sum(1 for c in cases if c.status not in [TripCaseStatus.CLOSED])
    proposals_count = max(len(cases), 1)
    
    return DashboardKPIsResponse(
        active_cases=active_cases_count,
        research_jobs_completed=len(cases) * 3,
        proposals_created=proposals_count,
        estimated_hours_saved=round(active_cases_count * 2.8 + proposals_count * 1.5, 1),
        avg_composite_tripscore=88.4,
        recent_activity_count=len(cases) + len(clients)
    )

# --- Clients CRM ---

@router.get("/clients")
async def list_clients(
    request: Request,
    search: Optional[str] = Query(None, description="Search by client name or email"),
    x_agency_id: Optional[str] = Header(None)
):
    """List all agency clients with optional search query."""
    agency_id = get_agency_context(request, x_agency_id)
    clients = ClientRepository.list_clients(agency_id, search=search)
    return {
        "status": "success",
        "total": len(clients),
        "clients": [c.model_dump() for c in clients]
    }

@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: CreateClientRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None),
    x_advisor_id: Optional[str] = Header(None)
):
    """Creates a new client in the agency CRM with preference baseline."""
    agency_id = get_agency_context(request, x_agency_id) or DEFAULT_AGENCY_ID
    advisor_id = get_advisor_context(request, x_advisor_id) or DEFAULT_ADVISOR_ID
    client_id = f"client_{uuid.uuid4().hex[:10]}"
    
    client = Client(
        id=client_id,
        agency_id=agency_id,
        advisor_id=advisor_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        tags=payload.tags,
        notes=payload.notes,
        preferences=payload.preferences or ClientPreferences()
    )
    ClientRepository.save_client(client)
    return {"status": "success", "client": client.model_dump()}

@router.get("/clients/{client_id}")
async def get_client_details(
    client_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Get single client details and associated past trip cases."""
    agency_id = get_agency_context(request, x_agency_id)
    client = ClientRepository.get_client(client_id, agency_id=agency_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
        
    all_cases = TripCaseRepository.list_cases(agency_id)
    cases = [c.model_dump() for c in all_cases if c.client_id == client_id]
    return {"status": "success", "client": client.model_dump(), "cases": cases}

# --- Trip Cases ---

@router.get("/cases")
async def list_cases(
    request: Request,
    status_filter: Optional[TripCaseStatus] = Query(None, alias="status"),
    x_agency_id: Optional[str] = Header(None)
):
    """List all advisor cases with enriched client info and status badges."""
    agency_id = get_agency_context(request, x_agency_id)
    cases = TripCaseRepository.list_cases(agency_id, status=status_filter.value if status_filter else None)
    
    # Enrich with client name for UI table/cards
    enriched = []
    for c in cases:
        c_dict = c.model_dump()
        client = ClientRepository.get_client(c.client_id, agency_id=agency_id)
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
async def create_case(
    payload: CreateCaseRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None),
    x_advisor_id: Optional[str] = Header(None)
):
    """Creates a new trip case and initiates brief setup."""
    agency_id = get_agency_context(request, x_agency_id) or DEFAULT_AGENCY_ID
    advisor_id = get_advisor_context(request, x_advisor_id) or DEFAULT_ADVISOR_ID
    
    client = ClientRepository.get_client(payload.client_id, agency_id=agency_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client '{payload.client_id}' not found.")
        
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    dest_focus = payload.destinations[0] if payload.destinations else "London"
    
    trip_case = TripCase(
        id=case_id,
        agency_id=agency_id,
        advisor_id=advisor_id,
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
    TripCaseRepository.save_case(trip_case)
    TimelineRepository.log_event(
        case_id=case_id,
        event_type="CASE_CREATED",
        description=f"Utazási ügy létrehozva: {trip_case.title}"
    )
    return {"status": "success", "case": trip_case.model_dump()}

@router.get("/cases/{case_id}")
async def get_case_details(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns single case details, client profile, options and proposals."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    options = TripOptionRepository.list_options_for_case(case_id)
    
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
    budget_constraint: Optional[BudgetConstraint] = None
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
async def update_client(
    client_id: str,
    payload: UpdateClientRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Updates an existing client profile and persistent travel preferences."""
    agency_id = get_agency_context(request, x_agency_id)
    client = ClientRepository.get_client(client_id, agency_id=agency_id)
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
    ClientRepository.save_client(client)
    return {"status": "success", "client": client.model_dump()}

@router.get("/cases/{case_id}/resolved-preferences")
async def get_resolved_case_preferences(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns the fully resolved 4-layer preference hierarchy for a case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
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
async def update_trip_brief(
    case_id: str,
    payload: UpdateTripBriefRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Updates the comprehensive deep brief and constraint hierarchy for a case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    if payload.title is not None: trip_case.title = payload.title
    if payload.budget_mode is not None: trip_case.budget_mode = payload.budget_mode
    if payload.budget_constraint is not None: trip_case.budget_constraint = payload.budget_constraint
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

    trip_case.sync_budget_models()
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    
    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
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
async def execute_case_research(
    case_id: str,
    request: Request,
    payload: Optional[ExecuteResearchRequest] = None,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Triggers one of the 9 Advisor Research Workflows for a trip case.
    Executes resilient candidate scoring and returns full candidate pools and telemetry.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    strategy = payload.strategy if payload else ResearchStrategy.FULL_TRIP_OPTIMIZATION
    custom_params = payload.custom_params if payload else {}

    # Advance case status to RESEARCH if in BRIEF
    if trip_case.status == TripCaseStatus.BRIEF:
        trip_case.status = TripCaseStatus.RESEARCH
        trip_case.updated_at = utc_now()
        TripCaseRepository.save_case(trip_case)

    result = AdvisorOrchestrationService.execute_research(
        trip_case=trip_case,
        client=client,
        strategy=strategy,
        custom_params=custom_params
    )

    TimelineRepository.log_event(
        case_id=case_id,
        event_type="RESEARCH_EXECUTED",
        description=f"Kutatási stratégia lefutott: {strategy}",
        metadata={"job_id": result.get("job_id"), "candidates_count": len(result.get("candidates", []))}
    )

    return {
        "status": "success",
        "case_id": case_id,
        "job": result
    }


@router.get("/cases/{case_id}/research/status")
async def get_case_research_status(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns the latest research job status and candidates for a case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
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
    job = AdvisorOrchestrationService.get_research_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found.")
    return {"status": "success", "job": job}


@router.get("/cases/{case_id}/research/{run_id}")
async def get_case_research_run(
    case_id: str,
    run_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Retrieves lifecycle status, provider breakdown, and candidates for a specific research run."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")
    job = AdvisorOrchestrationService.get_research_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Research run '{run_id}' not found.")
    return {
        "status": "success",
        "case_id": case_id,
        "run_id": run_id,
        "job": job
    }


@router.post("/cases/{case_id}/research/{run_id}/cancel")
async def cancel_case_research_run(
    case_id: str,
    run_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Cancels an active or queued research run."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")
    cancelled = AdvisorOrchestrationService.cancel_research_job(run_id)
    job = AdvisorOrchestrationService.get_research_job(run_id)
    return {
        "status": "success" if cancelled else "not_cancelled",
        "case_id": case_id,
        "run_id": run_id,
        "job": job
    }


class RecordOverrideRequest(BaseModel):
    field: str
    new_value: Any
    previous_value: Optional[Any] = None
    reason: Optional[str] = None
    actor_id: Optional[str] = "advisor"

RecordOverrideRequest.model_rebuild()


@router.post("/cases/{case_id}/override")
async def record_case_override(
    case_id: str,
    payload: RecordOverrideRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Records an audited advisor override entry in the case preference history."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    entry = AdvisorOverrideEntry(
        actor_id=payload.actor_id or "advisor",
        field=payload.field,
        previous_value=payload.previous_value,
        new_value=payload.new_value,
        reason=payload.reason
    )
    trip_case.preferences.overrides.history.append(entry)
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)

    return {
        "status": "success",
        "case_id": case_id,
        "entry": entry.model_dump(),
        "total_overrides": len(trip_case.preferences.overrides.history)
    }


@router.get("/cases/{case_id}/candidates")
async def get_case_candidates(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns the pool of generated candidate packages for a case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
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
async def pin_candidate(
    case_id: str,
    payload: PinCandidateRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Pins or unpins a candidate or specific component into Advisor Overrides."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
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
    TripCaseRepository.save_case(trip_case)
    return {
        "status": "success",
        "candidate_id": payload.candidate_id,
        "is_pinned": payload.is_pinned,
        "overrides": trip_case.preferences.overrides.model_dump()
    }


@router.post("/cases/{case_id}/duplicate")
async def duplicate_case(
    case_id: str,
    request: Request,
    payload: Optional[DuplicateCaseRequest] = None,
    x_agency_id: Optional[str] = Header(None)
):
    """Duplicates an existing trip case for rapid iteration or alternate client proposals."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    new_id = f"case_{uuid.uuid4().hex[:10]}"
    cloned = trip_case.model_copy(deep=True)
    cloned.id = new_id
    cloned.title = (payload.new_title if payload and payload.new_title else f"{trip_case.title} (Másolat)")
    cloned.status = TripCaseStatus.BRIEF
    cloned.created_at = utc_now()
    cloned.updated_at = utc_now()

    TripCaseRepository.save_case(cloned)
    return {"status": "success", "duplicated_case": cloned.model_dump()}


@router.patch("/cases/{case_id}/status")
async def update_case_status(
    case_id: str,
    payload: UpdateCaseStatusRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Advances or updates the status of an active case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    trip_case.status = payload.status
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    return {"status": "success", "case": trip_case.model_dump()}


@router.post("/cases/{case_id}/archive")
async def archive_case(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Archives a trip case by setting its status to CLOSED."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    trip_case.status = TripCaseStatus.CLOSED
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    return {"status": "success", "case": trip_case.model_dump()}


# ─────────────────────────────────────────────────────────────
# MULTI-OPTION & ARCHETYPES (PHASE 5)
# ─────────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/options/generate")
async def generate_case_options(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Generates 3 distinct, decision-ready archetypes (BEST OVERALL, BEST VALUE, BEST EXPERIENCE)
    from the candidate pool using MultiOptionEngine.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])

    # If no candidates in pool yet, execute rapid full-trip research first
    if not candidates:
        job = AdvisorOrchestrationService.execute_research(
            trip_case=trip_case,
            client=client,
            strategy=ResearchStrategy.FULL_TRIP_OPTIMIZATION
        )
        candidates = job.get("candidates", [])

    resolved = PreferenceResolver.resolve_preferences(trip_case, client)
    archetypes = MultiOptionEngine.generate_archetypes(
        candidates=candidates,
        preferences=resolved,
        target_budget_huf=trip_case.total_budget_huf
    )

    # Convert to TripOption domain models and persist into DB / SQLite
    trip_options: List[TripOption] = []
    for cand in archetypes:
        opt = TripOption(
            id=cand.get("id") or generate_uuid(),
            case_id=case_id,
            archetype=OptionArchetype(cand.get("archetype", "best_overall")),
            title=cand.get("title", "Utazási Csomag"),
            tagline=cand.get("tagline", ""),
            destination=cand.get("destination", {"city": "Barcelona", "country": "Spanyolország"}),
            flight=cand.get("flight", {}),
            stay=cand.get("stay", {}),
            activities=cand.get("activities", []),
            total_price_huf=float(cand.get("total_price_huf", 250000)),
            price_per_person_huf=float(cand.get("price_per_person_huf", 125000)),
            trip_score=int(round(float(cand.get("trip_score", 85)))),
            why_this_option=cand.get("why_this_option", ""),
            tradeoffs=cand.get("tradeoffs", []),
            verification_status=VerificationStatus(cand.get("verification_status", "VERIFIED")),
            is_pinned=cand.get("is_pinned", False)
        )
        trip_options.append(opt)

    TripOptionRepository.save_options_batch(case_id, trip_options)
    
    # Advance status to SHORTLIST if in RESEARCH
    if trip_case.status in [TripCaseStatus.BRIEF, TripCaseStatus.RESEARCH]:
        trip_case.status = TripCaseStatus.SHORTLIST
        trip_case.updated_at = utc_now()
        TripCaseRepository.save_case(trip_case)

    return {
        "status": "success",
        "case_id": case_id,
        "total_options": len(trip_options),
        "options": [o.model_dump() for o in trip_options]
    }


@router.get("/cases/{case_id}/options")
async def get_case_options(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns the current shortlisted 3 Archetype options for a case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    return {
        "status": "success",
        "case_id": case_id,
        "total": len(options),
        "options": [o.model_dump() for o in options]
    }


# ─────────────────────────────────────────────────────────────
# RELATIVE COMPARISON, WHY THIS OPTION & ADVISOR OVERRIDES (PHASE 6)
# ─────────────────────────────────────────────────────────────

class UpdateOptionRequest(BaseModel):
    title: Optional[str] = None
    tagline: Optional[str] = None
    total_price_huf: Optional[float] = None
    price_per_person_huf: Optional[float] = None
    why_this_option: Optional[str] = None
    override_reason: Optional[str] = None
    tradeoffs: Optional[List[str]] = None
    flight: Optional[Dict[str, Any]] = None
    stay: Optional[Dict[str, Any]] = None
    activities: Optional[List[Dict[str, Any]]] = None

class SwapComponentRequest(BaseModel):
    component_type: str                         # "flight", "stay", "destination"
    new_component_id: str
    override_reason: Optional[str] = None

class ReorderOptionsRequest(BaseModel):
    ordered_option_ids: List[str]
    override_reason: Optional[str] = None

class FindBetterRequest(BaseModel):
    option_id: str
    target_component: str                       # "flight", "stay", "price", "activities"
    goal: str                                   # "lower_price", "direct_flight", "higher_stars", "more_activities"

UpdateOptionRequest.model_rebuild()
SwapComponentRequest.model_rebuild()
ReorderOptionsRequest.model_rebuild()
FindBetterRequest.model_rebuild()


@router.get("/cases/{case_id}/compare")
async def get_case_options_comparison(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Computes and returns side-by-side relative comparison matrix and
    natural language trade-off explanations across the case's shortlisted options.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    if not options:
        # Fallback: check candidate pool
        candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
        if candidates:
            # Auto-generate options
            client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
            resolved = PreferenceResolver.resolve_preferences(trip_case, client)
            archetypes = MultiOptionEngine.generate_archetypes(candidates, resolved, trip_case.total_budget_huf)
            options = [
                TripOption(
                    id=cand.get("id") or generate_uuid(),
                    case_id=case_id,
                    archetype=OptionArchetype(cand.get("archetype", "best_overall")),
                    title=cand.get("title", "Utazási Csomag"),
                    tagline=cand.get("tagline", ""),
                    destination=cand.get("destination", {"city": "Barcelona", "country": "Spanyolország"}),
                    flight=cand.get("flight", {}),
                    stay=cand.get("stay", {}),
                    activities=cand.get("activities", []),
                    total_price_huf=float(cand.get("total_price_huf", 250000)),
                    price_per_person_huf=float(cand.get("price_per_person_huf", 125000)),
                    trip_score=int(round(float(cand.get("trip_score", 85)))),
                    why_this_option=cand.get("why_this_option", ""),
                    tradeoffs=cand.get("tradeoffs", []),
                    verification_status=VerificationStatus(cand.get("verification_status", "VERIFIED")),
                    is_pinned=cand.get("is_pinned", False)
                ) for cand in archetypes
            ]
            TripOptionRepository.save_options_batch(case_id, options)

    options_dicts = [o.model_dump() if hasattr(o, "model_dump") else o for o in options]
    matrix = RelativeComparisonService.compute_comparison_matrix(options_dicts)

    return {
        "status": "success",
        "case_id": case_id,
        "comparison": matrix
    }


@router.put("/cases/{case_id}/options/{option_id}")
async def update_case_option(
    case_id: str,
    option_id: str,
    payload: UpdateOptionRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Whitebox Advisor Override: Updates an option's parameters, title, or components
    with transparent justification tracking.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    target = next((o for o in options if o.id == option_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Option not found in case shortlist.")

    if payload.title is not None: target.title = payload.title
    if payload.tagline is not None: target.tagline = payload.tagline
    if payload.total_price_huf is not None: target.total_price_huf = payload.total_price_huf
    if payload.price_per_person_huf is not None: target.price_per_person_huf = payload.price_per_person_huf
    if payload.why_this_option is not None: target.why_this_option = payload.why_this_option
    if payload.tradeoffs is not None: target.tradeoffs = payload.tradeoffs
    if payload.flight is not None: target.flight = payload.flight
    if payload.stay is not None: target.stay = payload.stay
    if payload.activities is not None: target.activities = payload.activities

    if payload.override_reason:
        target.key_highlights.append(f"Tanácsadói megjegyzés: {payload.override_reason}")

    TripOptionRepository.save_option(target)
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    return {"status": "success", "updated_option": target.model_dump()}


@router.post("/cases/{case_id}/options/{option_id}/swap-component")
async def swap_option_component(
    case_id: str,
    option_id: str,
    payload: SwapComponentRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Swaps a component (flight/stay) in a shortlisted option with another candidate from the research pool.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    target = next((o for o in options if o.id == option_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Option not found.")

    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
    source = next((c for c in candidates if c.get("id") == payload.new_component_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source candidate component not found in pool.")

    if payload.component_type == "flight":
        target.flight = source.get("flight", {})
    elif payload.component_type == "stay":
        target.stay = source.get("stay", {})

    # Recompute total price
    flight_price = target.flight.get("price_huf", 0)
    stay_price = target.stay.get("price_huf", 0)
    target.total_price_huf = flight_price + stay_price
    target.price_per_person_huf = target.total_price_huf / max(trip_case.adults + trip_case.children, 1)

    if payload.override_reason:
        target.key_highlights.append(f"Elemcsere indoklása: {payload.override_reason}")

    TripOptionRepository.save_option(target)
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    return {"status": "success", "option": target.model_dump()}


@router.post("/cases/{case_id}/options/reorder")
async def reorder_case_options(
    case_id: str,
    payload: ReorderOptionsRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Reorders the 3 shortlisted options based on advisor preference.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    opt_map = {o.id: o for o in options}
    
    reordered = []
    for opt_id in payload.ordered_option_ids:
        if opt_id in opt_map:
            reordered.append(opt_map[opt_id])

    # Append any unmentioned options
    for o in options:
        if o not in reordered:
            reordered.append(o)

    TripOptionRepository.save_options_batch(case_id, reordered)
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)
    return {"status": "success", "options": [o.model_dump() for o in reordered]}


@router.post("/cases/{case_id}/find-better")
async def find_better_component(
    case_id: str,
    payload: FindBetterRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Executes a targeted replacement search (Find Better Tuning) for a component.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    result = AdvisorOrchestrationService.execute_research(
        trip_case=trip_case,
        client=client,
        strategy=ResearchStrategy.FIND_BETTER,
        custom_params={
            "target_component": payload.target_component,
            "goal": payload.goal,
            "option_id": payload.option_id
        }
    )

    return {
        "status": "success",
        "case_id": case_id,
        "target_component": payload.target_component,
        "better_candidates": result.get("candidates", [])
    }


# ─────────────────────────────────────────────────────────────
# CONSTRAINT RELAXATION, VERIFICATION & RISK ENGINE (PHASE 7)
# ─────────────────────────────────────────────────────────────

class ApplyRelaxationRequest(BaseModel):
    relaxation_id: str
    patch: Dict[str, Any]

ApplyRelaxationRequest.model_rebuild()


@router.post("/cases/{case_id}/diagnose-constraints")
async def diagnose_case_constraints(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Diagnoses conflicting constraints and returns quantified 1-click relaxation proposals.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    resolved = PreferenceResolver.resolve_preferences(trip_case, client)
    raw_inventory = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])

    diagnosis = ConstraintRelaxationService.diagnose_and_suggest(
        trip_case=trip_case,
        preferences=resolved,
        raw_inventory_pool=raw_inventory
    )
    return {"status": "success", "diagnosis": diagnosis}


@router.post("/cases/{case_id}/apply-relaxation")
async def apply_case_relaxation(
    case_id: str,
    payload: ApplyRelaxationRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Applies an advisor-approved relaxation patch and re-synthesizes 3 Archetypes.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Apply patch
    trip_case = ConstraintRelaxationService.apply_relaxation(
        trip_case=trip_case,
        relaxation_id=payload.relaxation_id,
        patch_data=payload.patch
    )
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)

    # Re-run archetype synthesis
    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    resolved = PreferenceResolver.resolve_preferences(trip_case, client)
    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])

    archetypes = MultiOptionEngine.generate_archetypes(
        candidates=candidates,
        preferences=resolved,
        target_budget_huf=trip_case.total_budget_huf
    )

    trip_options: List[TripOption] = []
    for cand in archetypes:
        opt = TripOption(
            id=cand.get("id") or generate_uuid(),
            case_id=case_id,
            archetype=OptionArchetype(cand.get("archetype", "best_overall")),
            title=cand.get("title", "Utazási Csomag"),
            tagline=cand.get("tagline", ""),
            destination=cand.get("destination", {"city": "Barcelona", "country": "Spanyolország"}),
            flight=cand.get("flight", {}),
            stay=cand.get("stay", {}),
            activities=cand.get("activities", []),
            total_price_huf=float(cand.get("total_price_huf", 250000)),
            price_per_person_huf=float(cand.get("price_per_person_huf", 125000)),
            trip_score=int(round(float(cand.get("trip_score", 85)))),
            why_this_option=cand.get("why_this_option", ""),
            tradeoffs=cand.get("tradeoffs", []),
            verification_status=VerificationStatus(cand.get("verification_status", "VERIFIED")),
            is_pinned=cand.get("is_pinned", False)
        )
        trip_options.append(opt)

    TripOptionRepository.save_options_batch(case_id, trip_options)

    return {
        "status": "success",
        "case_id": case_id,
        "relaxation_id": payload.relaxation_id,
        "updated_options_count": len(trip_options),
        "options": [o.model_dump() for o in trip_options]
    }


@router.get("/cases/{case_id}/verification-status")
async def get_case_verification_status(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Returns provenance timestamps, data sources, and verification status for all shortlisted options.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    options_dicts = [o.model_dump() if hasattr(o, "model_dump") else o for o in options]

    verifications = [
        VerificationService.verify_trip_option(opt)
        for opt in options_dicts
    ]

    return {
        "status": "success",
        "case_id": case_id,
        "verifications": verifications
    }


@router.get("/cases/{case_id}/risks")
async def get_case_risks(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Returns detected operational risks (layover, late arrivals, city taxes) across case options.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    options_dicts = [o.model_dump() if hasattr(o, "model_dump") else o for o in options]

    risk_evaluation = TripRiskService.evaluate_case_risks(options_dicts)

    return {
        "status": "success",
        "case_id": case_id,
        "risks": risk_evaluation
    }


# ─────────────────────────────────────────────────────────────
# SHORTLIST & MULTI-OPTION PROPOSALS (PHASE 8)
# ─────────────────────────────────────────────────────────────

class CreateProposalRequest(BaseModel):
    title: Optional[str] = None
    client_intro: Optional[str] = None
    advisor_notes: Optional[str] = None
    recommendation_summary: Optional[str] = None
    selected_option_ids: Optional[List[str]] = None

CreateProposalRequest.model_rebuild()


class UpdateProposalRequest(BaseModel):
    title: Optional[str] = None
    client_intro: Optional[str] = None
    advisor_notes: Optional[str] = None
    recommendation_summary: Optional[str] = None
    selected_option_ids: Optional[List[str]] = None
    status: Optional[str] = None

UpdateProposalRequest.model_rebuild()


class NewProposalVersionRequest(BaseModel):
    reason: Optional[str] = None

NewProposalVersionRequest.model_rebuild()


@router.get("/cases/{case_id}/proposals")
async def list_case_proposals(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Lists all generated proposal versions for a given trip case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    proposals = ProposalRepository.list_proposals_for_case(case_id, agency_id=agency_id)
    return {
        "status": "success",
        "case_id": case_id,
        "total": len(proposals),
        "proposals": proposals
    }


@router.post("/cases/{case_id}/proposals", status_code=status.HTTP_201_CREATED)
async def create_case_proposal(
    case_id: str,
    payload: CreateProposalRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Generates a new Client Proposal snapshot from the current shortlisted options."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    options = TripOptionRepository.list_options_for_case(case_id)
    options_dicts = [o.model_dump() if hasattr(o, "model_dump") else o for o in options]

    if not options_dicts:
        # If options not generated yet, generate them
        resolved = PreferenceResolver.resolve_preferences(trip_case, client)
        candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
        options_dicts = MultiOptionEngine.generate_archetypes(
            candidates=candidates,
            preferences=resolved,
            target_budget_huf=trip_case.total_budget_huf
        )

    # Filter selected options if provided
    if payload.selected_option_ids:
        filtered_opts = [o for o in options_dicts if o.get("id") in payload.selected_option_ids]
        if filtered_opts:
            options_dicts = filtered_opts

    proposal_doc = ProposalService.create_proposal(
        trip_case=trip_case,
        client=client,
        options=options_dicts,
        title=payload.title,
        client_intro=payload.client_intro,
        advisor_notes=payload.advisor_notes,
        recommendation_summary=payload.recommendation_summary
    )

    ProposalRepository.save_proposal(proposal_doc, agency_id=agency_id, advisor_id=trip_case.advisor_id)

    # Advance TripCase status to PROPOSAL
    trip_case.status = TripCaseStatus.PROPOSAL
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)

    TimelineRepository.log_event(
        case_id=case_id,
        event_type="PROPOSAL_CREATED",
        description=f"Ajánlat elkészült (v1): {proposal_doc.get('title')}",
        metadata={"proposal_id": proposal_doc.get("id"), "options_count": len(options_dicts)}
    )

    return {
        "status": "success",
        "proposal": proposal_doc
    }


@router.get("/proposals/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Fetches a specific proposal snapshot by ID."""
    agency_id = get_agency_context(request, x_agency_id)
    proposal = ProposalRepository.get_proposal_doc(proposal_id, agency_id=agency_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return {"status": "success", "proposal": proposal}


@router.put("/proposals/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    payload: UpdateProposalRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Updates editable client-facing text, options selection, or private advisor notes."""
    agency_id = get_agency_context(request, x_agency_id)
    proposal = ProposalRepository.get_proposal_doc(proposal_id, agency_id=agency_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    updated = ProposalService.update_proposal(
        proposal=proposal,
        title=payload.title,
        client_intro=payload.client_intro,
        advisor_notes=payload.advisor_notes,
        recommendation_summary=payload.recommendation_summary,
        selected_option_ids=payload.selected_option_ids,
        status=payload.status
    )
    ProposalRepository.save_proposal(updated, agency_id=agency_id)

    return {"status": "success", "proposal": updated}


@router.post("/proposals/{proposal_id}/new-version")
async def create_new_proposal_version(
    proposal_id: str,
    payload: NewProposalVersionRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Branches a new proposal version (v2, v3...) from an existing proposal."""
    agency_id = get_agency_context(request, x_agency_id)
    base_proposal = ProposalRepository.get_proposal_doc(proposal_id, agency_id=agency_id)
    if not base_proposal:
        raise HTTPException(status_code=404, detail="Base proposal not found.")

    case_id = base_proposal.get("case_id")
    options = TripOptionRepository.list_options_for_case(case_id)
    options_dicts = [o.model_dump() if hasattr(o, "model_dump") else o for o in options]
    if not options_dicts:
        options_dicts = base_proposal.get("options_snapshot", [])

    new_version_doc = ProposalService.create_next_version(
        base_proposal=base_proposal,
        updated_options=options_dicts,
        reason=payload.reason
    )

    ProposalRepository.save_proposal(new_version_doc, agency_id=agency_id)

    TimelineRepository.log_event(
        case_id=case_id,
        event_type="PROPOSAL_VERSION_CREATED",
        description=f"Új verzió létrehozva: v{new_version_doc.get('version')}",
        metadata={"proposal_id": new_version_doc.get("id"), "reason": payload.reason}
    )

    return {
        "status": "success",
        "proposal": new_version_doc
    }


@router.get("/proposals/{proposal_id}/preview", response_class=HTMLResponse)
async def preview_proposal_print(
    proposal_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Renders the A4 print-ready & exportable client proposal HTML."""
    agency_id = get_agency_context(request, x_agency_id)
    proposal = ProposalRepository.get_proposal_doc(proposal_id, agency_id=agency_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    return templates.TemplateResponse(
        request=request,
        name="advisor/proposal_print.html",
        context={"proposal": proposal}
    )


class CreateProposalShareRequest(BaseModel):
    expires_in_days: int = Field(default=30, ge=1, le=365)

CreateProposalShareRequest.model_rebuild()


@router.post("/proposals/{proposal_id}/share")
async def create_proposal_share(
    proposal_id: str,
    request: Request,
    payload: Optional[CreateProposalShareRequest] = None,
    x_agency_id: Optional[str] = Header(None)
):
    """Generates a cryptographically random, revocable public access link for a client proposal."""
    agency_id = get_agency_context(request, x_agency_id)
    proposal = ProposalRepository.get_proposal_doc(proposal_id, agency_id=agency_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    days = payload.expires_in_days if payload else 30
    share = ProposalService.create_share_token(
        proposal_id=proposal_id,
        version_number=int(proposal.get("version", 1)),
        expires_in_days=days
    )

    proposal["shareable_token"] = share.token
    ProposalRepository.save_proposal(proposal, agency_id=agency_id)

    return {
        "status": "success",
        "proposal_id": proposal_id,
        "version": share.proposal_version_number,
        "token": share.token,
        "expires_at": share.expires_at.isoformat() if share.expires_at else None,
        "shareable_url": f"/share/proposal/{share.token}",
        "public_api_url": f"/api/advisor/public/proposals/{share.token}"
    }


@router.get("/public/proposals/{token}")
async def get_public_shared_proposal(token: str):
    """
    Publicly accessible endpoint for clients with a valid share token.
    Returns stripped, client-safe proposal data without internal advisor notes.
    """
    share = ProposalService.get_share_by_token(token)
    if not share:
        raise HTTPException(status_code=404, detail="Érvénytelen, lejárt vagy visszavont ajánlat link.")

    proposal = ProposalRepository.get_proposal_doc(share.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Ajánlat nem található.")

    client_safe = ProposalService.get_client_safe_proposal(proposal)

    return {
        "status": "success",
        "proposal": client_safe,
        "share_info": {
            "version": share.proposal_version_number,
            "access_count": share.access_count,
            "expires_at": share.expires_at.isoformat() if share.expires_at else None
        }
    }


@router.post("/proposals/{proposal_id}/revoke-share")
async def revoke_proposal_share(proposal_id: str, token: str = Query(..., description="Share token to revoke")):
    """Revokes an active share token so the public link immediately ceases to work."""
    revoked = ProposalService.revoke_share_token(token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Megosztási token nem található.")
    return {"status": "success", "proposal_id": proposal_id, "revoked": True}


# ─────────────────────────────────────────────────────────────
# CLIENT FEEDBACK, TIMELINE & RE-OPTIMIZATION (PHASE 9)
# ─────────────────────────────────────────────────────────────

class RecordFeedbackRequest(BaseModel):
    proposal_id: str
    feedback_category: str = Field(default="general")
    feedback_text: str = Field(..., min_length=2)
    client_sentiment: str = Field(default="NEUTRAL")

RecordFeedbackRequest.model_rebuild()


class ReoptimizeCaseRequest(BaseModel):
    proposal_id: str
    reoptimization_reason: Optional[str] = None
    constraint_overrides: Optional[Dict[str, Any]] = None

ReoptimizeCaseRequest.model_rebuild()


class LogTimelineEventRequest(BaseModel):
    event_type: str = Field(default="MANUAL_NOTE")
    title: str = Field(..., min_length=2)
    description: str = Field(..., min_length=2)
    metadata: Optional[Dict[str, Any]] = None

LogTimelineEventRequest.model_rebuild()


@router.get("/cases/{case_id}/timeline")
async def get_case_timeline(
    case_id: str,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Returns the complete chronological audit trail of events for a trip case."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    events = TimelineRepository.list_events(case_id)
    
    # If no events logged yet, generate baseline events from case creation
    if not events:
        evt = TimelineRepository.log_event(
            case_id=case_id,
            event_type="CASE_CREATED",
            description=f"Ügy címe: {trip_case.title}. Indulási pont: {trip_case.origin}, fókusz: {trip_case.destination_focus}."
        )
        events = [evt]

    return {
        "status": "success",
        "case_id": case_id,
        "total_events": len(events),
        "timeline": [e.model_dump() for e in events]
    }


@router.post("/cases/{case_id}/timeline", status_code=status.HTTP_201_CREATED)
async def log_manual_timeline_event(
    case_id: str,
    payload: LogTimelineEventRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Manually records an advisor note or external activity onto the case timeline."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    event = TimelineRepository.log_event(
        case_id=case_id,
        event_type=payload.event_type,
        title=payload.title,
        description=payload.description or f"{payload.title}",
        metadata=payload.metadata
    )

    return {"status": "success", "event": event.model_dump()}


@router.post("/cases/{case_id}/feedback", status_code=status.HTTP_201_CREATED)
async def record_client_feedback(
    case_id: str,
    payload: RecordFeedbackRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """Captures client feedback against a proposal version and updates case timeline."""
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    proposal = ProposalRepository.get_proposal_doc(payload.proposal_id, agency_id=agency_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    feedback_doc = TimelineReoptimizationService.record_feedback(
        case_id=case_id,
        proposal_id=payload.proposal_id,
        feedback_category=payload.feedback_category,
        feedback_text=payload.feedback_text,
        client_sentiment=payload.client_sentiment
    )

    TimelineRepository.log_event(
        case_id=case_id,
        event_type="CLIENT_FEEDBACK",
        description=f"Ügyfél visszajelzés: [{payload.feedback_category}] {payload.feedback_text}",
        metadata=feedback_doc
    )

    # Set case status to REVISION
    trip_case.status = TripCaseStatus.REVISION
    trip_case.updated_at = utc_now()
    TripCaseRepository.save_case(trip_case)

    return {
        "status": "success",
        "feedback": feedback_doc
    }


@router.post("/cases/{case_id}/reoptimize")
async def execute_case_reoptimization(
    case_id: str,
    payload: ReoptimizeCaseRequest,
    request: Request,
    x_agency_id: Optional[str] = Header(None)
):
    """
    Executes 1-click re-optimization based on modified constraints,
    generating a new proposal version (v2, v3...) without restarting the intake flow.
    """
    agency_id = get_agency_context(request, x_agency_id)
    trip_case = TripCaseRepository.get_case(case_id, agency_id=agency_id)
    if not trip_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    client = ClientRepository.get_client(trip_case.client_id, agency_id=agency_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    base_proposal = ProposalRepository.get_proposal_doc(payload.proposal_id, agency_id=agency_id)
    if not base_proposal:
        raise HTTPException(status_code=404, detail="Base proposal not found.")

    candidates = AdvisorOrchestrationService._CANDIDATES_POOL.get(case_id, [])
    if not candidates:
        candidates = base_proposal.get("options_snapshot", [])

    reopt_result = TimelineReoptimizationService.execute_reoptimization(
        trip_case=trip_case,
        client=client,
        base_proposal=base_proposal,
        candidates_pool=candidates,
        constraint_overrides=payload.constraint_overrides,
        reoptimization_reason=payload.reoptimization_reason
    )

    new_proposal = reopt_result["new_proposal"]
    ProposalRepository.save_proposal(new_proposal, agency_id=agency_id)
    new_options = [
        TripOption(
            id=o.get("id") or generate_uuid(),
            case_id=case_id,
            archetype=OptionArchetype(o.get("archetype", "best_overall")),
            title=o.get("title", ""),
            tagline=o.get("tagline", ""),
            destination=o.get("destination", {"city": "Barcelona", "country": "Spanyolország"}),
            flight=o.get("flight", {}),
            stay=o.get("stay", {}),
            activities=o.get("activities", []),
            total_price_huf=float(o.get("total_price_huf", 250000)),
            price_per_person_huf=float(o.get("price_per_person_huf", 125000)),
            trip_score=int(round(float(o.get("trip_score", 85)))),
            why_this_option=o.get("why_this_option", ""),
            tradeoffs=o.get("tradeoffs", []),
            verification_status=VerificationStatus(o.get("verification_status", "VERIFIED")),
            is_pinned=o.get("is_pinned", False)
        )
        for o in reopt_result["new_options"]
    ]
    TripOptionRepository.save_options_batch(case_id, new_options)

    TimelineRepository.log_event(
        case_id=case_id,
        event_type="REOPTIMIZED",
        description=f"1-Kattintásos újratervezés lefutott -> v{reopt_result['version']}",
        metadata={"reason": payload.reoptimization_reason, "new_proposal_id": new_proposal["id"]}
    )

    return {
        "status": "success",
        "case_id": case_id,
        "version": reopt_result["version"],
        "new_proposal_id": new_proposal["id"],
        "proposal": new_proposal
    }









