"""
Optivoya B2B Advisor Workspace — Domain & Aggregate Models
Defines multi-tenant organization models, Client Profiles, Trip Cases, Hard/Soft Constraints,
Provenance tracking, 3-Option archetypes, and Versioned Proposal models.
"""

from enum import Enum
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import uuid


def generate_uuid(prefix: str = "") -> str:
    """Generates a prefixed UUID string."""
    uid = str(uuid.uuid4())
    return f"{prefix}_{uid}" if prefix else uid


def utc_now() -> datetime:
    """Returns the current UTC datetime."""
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────
# 1. ENUMS
# ─────────────────────────────────────────────────────────────

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"          # Live verified by provider API within TTL
    ESTIMATED = "ESTIMATED"        # Estimated via benchmark or historical average
    STALE = "STALE"                # Previously fetched, but exceeded freshness TTL
    NEEDS_REVIEW = "NEEDS_REVIEW"  # Requires manual advisor confirmation
    UNAVAILABLE = "UNAVAILABLE"    # Provider unreachable or out of stock


class OptionArchetype(str, Enum):
    BEST_OVERALL = "best_overall"        # Highest balanced composite score
    BEST_VALUE = "best_value"            # Budget-optimized, highest value per forint
    BEST_EXPERIENCE = "best_experience"  # Premium quality, maximum vibe/activity fit
    CUSTOM = "custom"                    # Manually assembled by advisor


class TripCaseStatus(str, Enum):
    BRIEF = "brief"                      # Intake / Brief stage
    RESEARCH = "research"                # Live search & ranking in progress
    SHORTLIST = "shortlist"              # 3 options generated and under review
    PROPOSAL = "proposal"                # Proposal created & ready
    WAITING_FOR_CLIENT = "waiting"       # Sent to client for review
    REVISION = "revision"                # Client requested changes / re-optimization
    CLOSED = "closed"                    # Finalized / Booked / Archived


class BudgetMode(str, Enum):
    TOTAL_BUDGET = "total"               # Single ceiling (e.g., max 350 000 Ft total)
    COMPONENT_BUDGETS = "component"      # Component limits (flight max, stay max, etc.)
    SCOPE_ONLY = "scope_only"            # Value-oriented research without strict ceiling


class ResearchScope(str, Enum):
    FULL_TRIP = "full_trip"              # Destination + Flight + Stay + Activities
    DESTINATION_DISCOVERY = "dest_disc"  # Destination ranking & discovery only
    FLIGHT_AND_STAY = "flight_stay"      # Known city -> Flights & Hotels only
    FLIGHT_ONLY = "flight_only"          # Specific flight search only
    STAY_ONLY = "stay_only"              # Specific stay search only
    ACTIVITIES_ONLY = "activities_only"  # Program & POI planning only


class ResearchRunStatus(str, Enum):
    QUEUED = "queued"                    # Research request submitted to async pool
    RUNNING = "running"                  # Providers currently executing queries
    PARTIAL = "partial"                  # Some providers returned results, others failed/cached
    COMPLETED = "completed"              # All required providers finished and synthesized
    FAILED = "failed"                    # Critical unrecoverable failure across all providers
    CANCELLED = "cancelled"              # Cancelled by advisor


class BudgetHardness(str, Enum):
    HARD = "hard"                        # Strict ceiling, must NOT be exceeded automatically
    TARGET = "target"                    # Target budget, suggestions/relaxations allowed with advisor approval


class BudgetBasis(str, Enum):
    PER_PERSON = "per_person"            # Budget given on a per-traveler basis
    GROUP = "group"                      # Budget given for the entire party


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REVISED = "revised"


# ─────────────────────────────────────────────────────────────
# 1.5. BUDGET CONSTRAINT MODEL (HARDENED)
# ─────────────────────────────────────────────────────────────

class ComponentBudget(BaseModel):
    """
    Sub-budget limit for a specific travel component (flight, stay, activities, etc.).
    """
    amount: Optional[float] = None
    basis: BudgetBasis = BudgetBasis.GROUP
    hardness: BudgetHardness = BudgetHardness.HARD
    currency: str = "HUF"


class TotalBudget(BaseModel):
    """
    All-inclusive trip budget ceiling or target.
    """
    amount: Optional[float] = None
    basis: BudgetBasis = BudgetBasis.GROUP
    hardness: BudgetHardness = BudgetHardness.HARD
    relaxation_allowed: bool = False
    max_relaxation_pct: float = 10.0      # Maximum allowed relaxation suggestion (e.g., +10%)
    currency: str = "HUF"


class BudgetComponents(BaseModel):
    flight: Optional[ComponentBudget] = None
    stay: Optional[ComponentBudget] = None
    activities: Optional[ComponentBudget] = None
    local_transport: Optional[ComponentBudget] = None


class BudgetConstraint(BaseModel):
    """
    Explicit, multi-currency budget model supporting full-trip and component scopes,
    per-person / group basis, and strict hardness invariant.
    """
    currency: str = "HUF"
    total: TotalBudget = Field(default_factory=TotalBudget)
    components: BudgetComponents = Field(default_factory=BudgetComponents)

    def get_effective_total_ceiling_huf(self, adults: int = 1, children: int = 0) -> Optional[float]:
        """Calculates total budget in HUF accounting for group vs per-person basis."""
        if not self.total.amount:
            return None
        travelers = max(adults + children, 1)
        if self.total.basis == BudgetBasis.PER_PERSON:
            return float(self.total.amount * travelers)
        return float(self.total.amount)

    def is_hard(self) -> bool:
        return self.total.hardness == BudgetHardness.HARD


# ─────────────────────────────────────────────────────────────
# 2. PROVENANCE & DATA FRESHNESS MODEL
# ─────────────────────────────────────────────────────────────

class ProviderProvenance(BaseModel):
    """
    Tracks origin, provider freshness TTL, deep links, and verification status for every data point.
    """
    model_config = ConfigDict(extra="ignore")

    provider: str = "Optivoya"                 # "Kiwi", "Cozycozy", "Open-Meteo", "Numbeo", "OSM", "Manual"
    source_type: str = "api"                   # "api", "aggregator", "website", "manual", "cache", "estimate"
    source_url: Optional[str] = None
    deep_link: Optional[str] = None
    booking_url: Optional[str] = None
    checked_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    freshness_ttl_seconds: int = 1800          # Default 30 min TTL
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    raw_reference: Optional[str] = None        # Provider item ID (e.g., Kiwi booking token, Cozy ID)
    is_estimated: bool = False
    price_currency: str = "HUF"
    original_price: Optional[float] = None
    original_currency: Optional[str] = None

    def is_fresh(self) -> bool:
        if not self.expires_at:
            age = (utc_now() - self.checked_at).total_seconds()
            return age < self.freshness_ttl_seconds
        return utc_now() < self.expires_at


# ─────────────────────────────────────────────────────────────
# 3. MULTI-TENANT AGENCY & ADVISOR MODELS
# ─────────────────────────────────────────────────────────────

class AgencyBranding(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#2563eb"
    accent_color: str = "#0ea5e9"
    company_name: str = "Optivoya Travel Advisory"
    tagline: str = "Intelligens Utazástervezés & Döntéstámogatás"
    contact_email: str = "advisor@optivoya.com"
    contact_phone: Optional[str] = None
    footer_text: Optional[str] = "Hivatalos utazási árajánlat."


class Agency(BaseModel):
    id: str = Field(default_factory=lambda: generate_uuid("agency"))
    name: str
    slug: str
    branding: AgencyBranding = Field(default_factory=AgencyBranding)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class Advisor(BaseModel):
    id: str = Field(default_factory=lambda: generate_uuid("adv"))
    agency_id: str
    name: str
    email: str
    role: str = "advisor"                      # "owner", "lead_advisor", "advisor"
    avatar_url: Optional[str] = None
    is_active: bool = True
    default_origin: str = "Budapest (BUD)"
    default_currency: str = "HUF"
    created_at: datetime = Field(default_factory=utc_now)


# ─────────────────────────────────────────────────────────────
# 4. CLIENT PROFILE & PERSISTENT PREFERENCES
# ─────────────────────────────────────────────────────────────

class ClientPreferences(BaseModel):
    """
    Persistent travel profile associated with a client.
    """
    preferred_origins: List[str] = Field(default_factory=lambda: ["Budapest (BUD)"])
    preferred_airlines: List[str] = Field(default_factory=list)
    avoid_airlines: List[str] = Field(default_factory=list)
    preferred_hotel_chains: List[str] = Field(default_factory=list)
    hotel_min_stars: int = 3
    hotel_min_rating: float = 7.5
    preferred_room_type: str = "double"
    direct_flights_only: bool = False
    max_stops: int = 1
    seat_preference: str = "window"            # "window", "aisle", "any"
    dietary_requirements: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=lambda: ["culture", "gastronomy"])
    travel_style: str = "balanced"             # "luxury", "balanced", "budget", "adventure"


class Client(BaseModel):
    id: str = Field(default_factory=lambda: generate_uuid("cli"))
    agency_id: str
    advisor_id: str
    name: str
    email: str
    phone: Optional[str] = None
    passport_country: str = "Hungary"
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    preferences: ClientPreferences = Field(default_factory=ClientPreferences)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ─────────────────────────────────────────────────────────────
# 5. HARD VS. SOFT CONSTRAINT MODEL
# ─────────────────────────────────────────────────────────────

class HardConstraints(BaseModel):
    """
    Mandatory constraints that MUST be satisfied. Failing candidates are excluded.
    """
    max_total_budget_huf: Optional[float] = None
    max_flight_budget_huf: Optional[float] = None
    max_stay_budget_huf: Optional[float] = None
    direct_flights_only: Optional[bool] = None
    max_stops: Optional[int] = None
    min_hotel_stars: Optional[int] = None
    min_hotel_rating: Optional[float] = None
    min_safety_score: Optional[int] = None
    min_temp_celsius: Optional[float] = None
    max_temp_celsius: Optional[float] = None
    max_flight_duration_h: Optional[float] = None
    required_amenities: List[str] = Field(default_factory=list)
    required_regions: List[str] = Field(default_factory=list)


class SoftPreferences(BaseModel):
    """
    Weighted preferences evaluated via AHP and PROMETHEE II scoring.
    """
    target_temperature: float = 24.0
    vibe_weights: Dict[str, float] = Field(default_factory=lambda: {
        "culture": 50.0,
        "gastronomy": 50.0,
        "beach": 30.0,
        "nature": 40.0,
        "nightlife": 25.0
    })
    ahp_pillar_weights: Dict[str, float] = Field(default_factory=lambda: {
        "destination": 25.0,
        "flight": 25.0,
        "accommodation": 25.0,
        "experience": 25.0
    })
    flight_priority_weights: Dict[str, float] = Field(default_factory=lambda: {
        "price": 40.0,
        "duration": 35.0,
        "stops": 25.0
    })
    budget_flexibility_pct: float = 10.0       # Willing to exceed budget by 10% for exceptional option


class AvoidRules(BaseModel):
    """
    Elements explicitly forbidden or penalized.
    """
    avoid_airlines: List[str] = Field(default_factory=list)
    avoid_early_departures: bool = False       # Before 06:00
    avoid_late_arrivals: bool = False          # After 23:00
    avoid_destinations: List[str] = Field(default_factory=list)
    avoid_hotel_types: List[str] = Field(default_factory=list)


class NiceToHave(BaseModel):
    """
    Positive bonuses that enhance score if present.
    """
    breakfast_included: bool = False
    pool_available: bool = False
    sea_view: bool = False
    free_cancellation: bool = True
    central_location: bool = True


class AdvisorOverrideEntry(BaseModel):
    """
    Individual audited advisor override record.
    """
    id: str = Field(default_factory=lambda: generate_uuid("ovr"))
    actor_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    field: str
    previous_value: Any = None
    new_value: Any = None
    reason: Optional[str] = None


class AdvisorOverrides(BaseModel):
    """
    Manual advisor overrides and pinned selections with audit trail.
    """
    pinned_destination: Optional[str] = None
    pinned_flight_id: Optional[str] = None
    pinned_stay_id: Optional[str] = None
    custom_markup_huf: float = 0.0
    manual_notes: Optional[str] = None
    history: List[AdvisorOverrideEntry] = Field(default_factory=list)


class ResolvedTripPreferences(BaseModel):
    """
    Complete resolved preference hierarchy:
    Hierarchy: Advisor Overrides > Case Brief > Client Profile > System Defaults
    """
    hard: HardConstraints = Field(default_factory=HardConstraints)
    soft: SoftPreferences = Field(default_factory=SoftPreferences)
    avoid: AvoidRules = Field(default_factory=AvoidRules)
    nice_to_have: NiceToHave = Field(default_factory=NiceToHave)
    overrides: AdvisorOverrides = Field(default_factory=AdvisorOverrides)


# ─────────────────────────────────────────────────────────────
# 6. TRIP CASE & BRIEF AGGREGATE
# ─────────────────────────────────────────────────────────────

class TripCase(BaseModel):
    """
    The central B2B Trip Case aggregate managing the full advisor decision flow.
    """
    id: str = Field(default_factory=lambda: generate_uuid("case"))
    agency_id: str
    advisor_id: str
    client_id: str

    title: str = "Új Utazási Terv"
    status: TripCaseStatus = TripCaseStatus.BRIEF
    scope: ResearchScope = ResearchScope.FULL_TRIP
    budget_mode: BudgetMode = BudgetMode.TOTAL_BUDGET

    # Hardened Budget model
    budget_constraint: BudgetConstraint = Field(default_factory=BudgetConstraint)

    # Travel logistics
    origin: str = "Budapest (BUD)"
    destination_focus: Optional[str] = None    # Specific city or None for discovery
    adults: int = 2
    children: int = 0
    duration_days: int = 7

    # Dates
    date_mode: str = "exact"                   # "exact", "interval", "month"
    out_date: Optional[str] = None
    in_date: Optional[str] = None
    out_window_start: Optional[str] = None
    out_window_end: Optional[str] = None
    min_stay_nights: Optional[int] = None
    max_stay_nights: Optional[int] = None

    # Budget ceilings (Legacy compatibility properties)
    total_budget_huf: Optional[float] = None
    flight_budget_huf: Optional[float] = None
    stay_budget_huf: Optional[float] = None

    # Preferences & Constraints
    preferences: ResolvedTripPreferences = Field(default_factory=ResolvedTripPreferences)

    # Generated Options
    selected_option_ids: List[str] = Field(default_factory=list)
    shortlist_ids: List[str] = Field(default_factory=list)

    # Telemetry
    research_time_saved_minutes: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def sync_budget_models(self) -> None:
        """Syncs legacy budget fields with the hardened BudgetConstraint model."""
        if self.total_budget_huf is not None and not self.budget_constraint.total.amount:
            self.budget_constraint.total.amount = self.total_budget_huf
            self.budget_constraint.total.currency = "HUF"
        elif self.budget_constraint.total.amount is not None:
            self.total_budget_huf = self.budget_constraint.total.amount

        if self.flight_budget_huf is not None:
            if not self.budget_constraint.components.flight:
                self.budget_constraint.components.flight = ComponentBudget(amount=self.flight_budget_huf)
            else:
                self.budget_constraint.components.flight.amount = self.flight_budget_huf

        if self.stay_budget_huf is not None:
            if not self.budget_constraint.components.stay:
                self.budget_constraint.components.stay = ComponentBudget(amount=self.stay_budget_huf)
            else:
                self.budget_constraint.components.stay.amount = self.stay_budget_huf


# ─────────────────────────────────────────────────────────────
# 6.5. RESEARCH RUNS & RESEARCH CANDIDATES
# ─────────────────────────────────────────────────────────────

class ResearchCandidate(BaseModel):
    """
    Individual raw or intermediate inventory candidate generated during research.
    """
    id: str = Field(default_factory=lambda: generate_uuid("cand"))
    case_id: str
    research_run_id: Optional[str] = None
    type: str                                  # "destination", "flight", "stay", "activity", "package"
    name: str
    provider: str = "Optivoya"
    source_url: Optional[str] = None
    deep_link: Optional[str] = None
    booking_url: Optional[str] = None
    price: float = 0.0
    currency: str = "HUF"
    availability_status: str = "available"     # "available", "limited", "sold_out", "cached"
    metrics: Dict[str, Any] = Field(default_factory=dict)
    constraint_fit: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    provenance: ProviderProvenance = Field(default_factory=ProviderProvenance)
    raw_reference: Optional[str] = None


class ResearchRun(BaseModel):
    """
    Persistent Async Research Run aggregate tracking provider lifecycle and errors.
    """
    id: str = Field(default_factory=lambda: generate_uuid("run"))
    case_id: str
    agency_id: str = "agency_default_lux"
    advisor_id: str = "adv_default"
    strategy: str = "full_trip_optimization"
    status: ResearchRunStatus = ResearchRunStatus.QUEUED
    scope: ResearchScope = ResearchScope.FULL_TRIP
    progress_pct: int = 0
    step_details: List[str] = Field(default_factory=list)
    steps_completed: List[str] = Field(default_factory=list)
    providers_status: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "kiwi": {"status": "pending", "count": 0, "error": None},
        "cozycozy": {"status": "pending", "count": 0, "error": None},
        "open_meteo": {"status": "pending", "count": 0, "error": None},
        "poi_wikidata": {"status": "pending", "count": 0, "error": None}
    })
    candidate_counts: Dict[str, int] = Field(default_factory=dict)
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    destinations_pool: List[Dict[str, Any]] = Field(default_factory=list)
    flights_pool: List[Dict[str, Any]] = Field(default_factory=list)
    stays_pool: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    elapsed_seconds: Optional[float] = None
    options_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None


class OptionSet(BaseModel):
    """
    Versioned set of synthesized decision options associated with a research run.
    """
    id: str = Field(default_factory=lambda: generate_uuid("optset"))
    case_id: str
    research_run_id: Optional[str] = None
    options: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ProposalShare(BaseModel):
    """
    Cryptographically secure, revocable token for public client-facing proposal access.
    """
    id: str = Field(default_factory=lambda: generate_uuid("share"))
    proposal_id: str
    proposal_version_number: int = 1
    token: str = Field(default_factory=lambda: str(uuid.uuid4()).replace("-", ""))
    token_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_revoked: bool = False
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        if self.is_revoked or self.revoked_at is not None:
            return False
        if self.expires_at and utc_now() > self.expires_at:
            return False
        return True


# ─────────────────────────────────────────────────────────────
# 7. TRIP OPTIONS & ARCHETYPES (3-OPTION DECISION ENGINE)
# ─────────────────────────────────────────────────────────────

class OptionComponent(BaseModel):
    """
    Individual element of a trip option (flight segment, hotel, activity) with attached provenance.
    """
    component_type: str                        # "destination", "flight", "accommodation", "activity", "transfer"
    title: str
    provider: str = "Optivoya"
    price_huf: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    provenance: ProviderProvenance = Field(default_factory=ProviderProvenance)


class TripOption(BaseModel):
    """
    Complete, standalone trip option representing 1 of the 3 decision archetypes.
    """
    id: str = Field(default_factory=lambda: generate_uuid("opt"))
    case_id: str
    archetype: OptionArchetype = OptionArchetype.BEST_OVERALL
    title: str = "Klasszikus Utazási Csomag"
    tagline: str = "Kiegyensúlyozott ár-érték és kényelem"

    # Pricing
    total_price_huf: float = 0.0
    price_per_person_huf: float = 0.0
    currency: str = "HUF"

    # Core Components
    destination: Dict[str, Any] = Field(default_factory=dict)
    flight: Dict[str, Any] = Field(default_factory=dict)
    stay: Dict[str, Any] = Field(default_factory=dict)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    # Holistic Scoring
    trip_score: int = 85
    pillar_scores: Dict[str, float] = Field(default_factory=lambda: {
        "destination": 85.0,
        "flight": 85.0,
        "accommodation": 85.0,
        "experience": 85.0
    })
    effective_vacation_hours: float = 16.0

    # Decision Explanations
    why_this_option: str = "Kiemelkedő illeszkedés a megadott preferenciákhoz."
    tradeoffs: List[str] = Field(default_factory=list)
    key_highlights: List[str] = Field(default_factory=list)

    # Verification & Risk Summary
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    risk_warnings: List[Dict[str, str]] = Field(default_factory=list)

    is_pinned: bool = False
    created_at: datetime = Field(default_factory=utc_now)


# ─────────────────────────────────────────────────────────────
# 8. SHORTLIST, ADVISOR NOTES & AUDIT TIMELINE
# ─────────────────────────────────────────────────────────────

class AdvisorNote(BaseModel):
    id: str = Field(default_factory=lambda: generate_uuid("note"))
    case_id: str
    advisor_id: str
    content: str
    is_client_visible: bool = False            # Private internal advisor note by default
    created_at: datetime = Field(default_factory=utc_now)


class CaseEvent(BaseModel):
    """
    Audit log entry recording steps, re-optimizations, and client interactions.
    """
    id: str = Field(default_factory=lambda: generate_uuid("evt"))
    case_id: str
    event_type: str                            # "brief_created", "research_completed", "options_generated", "proposal_sent", "client_feedback", "re_optimized"
    title: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


# ─────────────────────────────────────────────────────────────
# 9. PROPOSAL & VERSIONING
# ─────────────────────────────────────────────────────────────

class ProposalVersion(BaseModel):
    version_number: int = 1
    title: str = "Utazási Javaslat"
    intro_message: Optional[str] = None
    conclusion_message: Optional[str] = None
    option_ids: List[str] = Field(default_factory=list)
    snapshot_options: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: generate_uuid("prop"))
    case_id: str
    agency_id: str
    advisor_id: str
    client_id: str

    title: str = "Személyre Szabott Utazási Javaslat"
    status: ProposalStatus = ProposalStatus.DRAFT
    current_version: int = 1
    versions: List[ProposalVersion] = Field(default_factory=list)

    shareable_token: str = Field(default_factory=lambda: str(uuid.uuid4()).replace("-", "")[:16])
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
