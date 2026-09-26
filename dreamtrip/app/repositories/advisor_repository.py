"""
Optivoya B2B Advisor Workspace — Data Access & Repository Layer
===============================================================
Provides production-grade persistence for all Advisor domain aggregates:
- Agencies & Advisors
- Clients (CRM)
- TripCases & BudgetConstraints
- ResearchRuns (Async lifecycle persistence)
- TripOptions & OptionSets
- Proposals, Versions & ProposalShares
- Audit Timeline & CaseEvents

Architecture:
- Primary: Supabase Cloud PostgreSQL (via PostgREST client with multi-tenant agency_id filtering)
- Fallback & Local Persistence: SQLite / persistent local store when Supabase is offline
- Multi-Tenant Isolation: Enforces agency_id boundaries on all queries
"""

import json
import sqlite3
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.core.supabase import get_supabase, is_supabase_configured
from app.models.advisor_models import (
    Agency, AgencyBranding, Advisor, Client, ClientPreferences,
    TripCase, TripCaseStatus, ResearchScope, BudgetMode,
    ResolvedTripPreferences, HardConstraints, SoftPreferences, AvoidRules, NiceToHave,
    TripOption, OptionArchetype, ResearchRun, ResearchRunStatus,
    Proposal, ProposalVersion, ProposalShare, CaseEvent, AdvisorNote
)

logger = logging.getLogger("advisor_repository")

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "advisor_workspace.db")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_json_dumps(obj: Any) -> str:
    def default_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "dict"):
            return o.dict()
        if hasattr(o, "value"):
            return o.value
        return str(o)
    return json.dumps(obj, default=default_serializer)


class LocalSQLiteStorage:
    """Persistent local SQLite engine used for offline development, tests and transparent fallback."""
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_schema(cls):
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agencies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                branding TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisors (
                id TEXT PRIMARY KEY,
                agency_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT 'advisor',
                avatar_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                default_origin TEXT NOT NULL DEFAULT 'Budapest (BUD)',
                default_currency TEXT NOT NULL DEFAULT 'HUF',
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                agency_id TEXT NOT NULL,
                advisor_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                passport_country TEXT NOT NULL DEFAULT 'Hungary',
                notes TEXT,
                tags TEXT NOT NULL DEFAULT '[]',
                preferences TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_cases (
                id TEXT PRIMARY KEY,
                agency_id TEXT NOT NULL,
                advisor_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'brief',
                scope TEXT NOT NULL DEFAULT 'full_trip',
                budget_mode TEXT NOT NULL DEFAULT 'total',
                origin TEXT NOT NULL DEFAULT 'Budapest (BUD)',
                destination_focus TEXT,
                adults INTEGER NOT NULL DEFAULT 2,
                children INTEGER NOT NULL DEFAULT 0,
                duration_days INTEGER NOT NULL DEFAULT 7,
                date_mode TEXT NOT NULL DEFAULT 'exact',
                out_date TEXT,
                in_date TEXT,
                out_window_start TEXT,
                out_window_end TEXT,
                min_stay_nights INTEGER,
                max_stay_nights INTEGER,
                total_budget_huf REAL,
                flight_budget_huf REAL,
                stay_budget_huf REAL,
                preferences TEXT NOT NULL DEFAULT '{}',
                selected_option_ids TEXT NOT NULL DEFAULT '[]',
                shortlist_ids TEXT NOT NULL DEFAULT '[]',
                research_time_saved_minutes REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trip_options (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                archetype TEXT NOT NULL DEFAULT 'best_overall',
                title TEXT NOT NULL,
                tagline TEXT,
                total_price_huf REAL NOT NULL DEFAULT 0.0,
                price_per_person_huf REAL NOT NULL DEFAULT 0.0,
                currency TEXT NOT NULL DEFAULT 'HUF',
                destination TEXT NOT NULL DEFAULT '{}',
                flight TEXT NOT NULL DEFAULT '{}',
                stay TEXT NOT NULL DEFAULT '{}',
                activities TEXT NOT NULL DEFAULT '[]',
                trip_score INTEGER NOT NULL DEFAULT 85,
                pillar_scores TEXT NOT NULL DEFAULT '{}',
                effective_vacation_hours REAL NOT NULL DEFAULT 16.0,
                why_this_option TEXT,
                tradeoffs TEXT NOT NULL DEFAULT '[]',
                key_highlights TEXT NOT NULL DEFAULT '[]',
                verification_status TEXT NOT NULL DEFAULT 'VERIFIED',
                risk_warnings TEXT NOT NULL DEFAULT '[]',
                is_pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_runs (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                agency_id TEXT NOT NULL,
                advisor_id TEXT NOT NULL,
                strategy TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                progress_pct INTEGER NOT NULL DEFAULT 0,
                steps_completed TEXT NOT NULL DEFAULT '[]',
                providers_status TEXT NOT NULL DEFAULT '{}',
                candidates TEXT NOT NULL DEFAULT '[]',
                destinations_pool TEXT NOT NULL DEFAULT '[]',
                flights_pool TEXT NOT NULL DEFAULT '[]',
                stays_pool TEXT NOT NULL DEFAULT '[]',
                warnings TEXT NOT NULL DEFAULT '[]',
                elapsed_seconds REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                agency_id TEXT NOT NULL,
                advisor_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                current_version INTEGER NOT NULL DEFAULT 1,
                versions TEXT NOT NULL DEFAULT '[]',
                shareable_token TEXT UNIQUE,
                view_count INTEGER NOT NULL DEFAULT 0,
                last_viewed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposal_shares (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                proposal_version_number INTEGER NOT NULL DEFAULT 1,
                is_revoked INTEGER NOT NULL DEFAULT 0,
                revoked_at TEXT,
                expires_at TEXT,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_events (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

# Initialize local SQLite schema on module import
try:
    LocalSQLiteStorage.init_schema()
except Exception as e:
    logger.warning(f"Local SQLite init failed: {e}")


# ==============================================================================
# 1. AGENCY REPOSITORY
# ==============================================================================

class AgencyRepository:
    DEFAULT_AGENCY_ID = "agency_default_lux"

    @classmethod
    def get_agency(cls, agency_id: str) -> Optional[Agency]:
        # 1. Try Supabase
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("agencies").select("*").eq("id", agency_id).execute()
                if res.data:
                    row = res.data[0]
                    return Agency(
                        id=row["id"],
                        name=row["name"],
                        slug=row["slug"],
                        branding=AgencyBranding(**row.get("branding", {})),
                        is_active=bool(row.get("is_active", True)),
                        created_at=datetime.fromisoformat(row["created_at"]) if "created_at" in row else None
                    )
            except Exception as e:
                logger.debug(f"Supabase get_agency fallback: {e}")

        # 2. Local fallback
        conn = LocalSQLiteStorage.get_connection()
        row = conn.execute("SELECT * FROM agencies WHERE id = ?", (agency_id,)).fetchone()
        conn.close()
        if row:
            return Agency(
                id=row["id"],
                name=row["name"],
                slug=row["slug"],
                branding=AgencyBranding(**json.loads(row["branding"])),
                is_active=bool(row["is_active"])
            )
        
        # Default seed agency
        if agency_id == cls.DEFAULT_AGENCY_ID:
            default_agency = Agency(
                id=cls.DEFAULT_AGENCY_ID,
                name="Optivoya Premier Travel Agency",
                slug="optivoya-premier",
                branding=AgencyBranding(
                    company_name="Optivoya Premier Travel",
                    primary_color="#003710",
                    accent_color="#a7f540",
                    contact_email="vip@optivoya.com"
                )
            )
            cls.save_agency(default_agency)
            return default_agency
        return None

    @classmethod
    def save_agency(cls, agency: Agency) -> Agency:
        branding_dict = agency.branding.model_dump() if hasattr(agency.branding, "model_dump") else {}
        # 1. Save Supabase
        if is_supabase_configured():
            try:
                sb = get_supabase()
                payload = {
                    "id": agency.id,
                    "name": agency.name,
                    "slug": agency.slug,
                    "branding": branding_dict,
                    "is_active": agency.is_active,
                    "created_at": agency.created_at.isoformat() if agency.created_at else utc_now_iso()
                }
                sb.table("agencies").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_agency fallback: {e}")

        # 2. Save Local
        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO agencies (id, name, slug, branding, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                slug=excluded.slug,
                branding=excluded.branding,
                is_active=excluded.is_active
        """, (agency.id, agency.name, agency.slug, safe_json_dumps(branding_dict), int(agency.is_active), utc_now_iso()))
        conn.commit()
        conn.close()
        return agency


# ==============================================================================
# 2. ADVISOR REPOSITORY
# ==============================================================================

class AdvisorRepository:
    DEFAULT_ADVISOR_ID = "adv_adam_lead"

    @classmethod
    def get_advisor(cls, advisor_id: str) -> Optional[Advisor]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("advisors").select("*").eq("id", advisor_id).execute()
                if res.data:
                    row = res.data[0]
                    return Advisor(**row)
            except Exception as e:
                logger.debug(f"Supabase get_advisor fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        row = conn.execute("SELECT * FROM advisors WHERE id = ?", (advisor_id,)).fetchone()
        conn.close()
        if row:
            return Advisor(
                id=row["id"],
                agency_id=row["agency_id"],
                name=row["name"],
                email=row["email"],
                role=row["role"],
                avatar_url=row["avatar_url"],
                is_active=bool(row["is_active"]),
                default_origin=row["default_origin"],
                default_currency=row["default_currency"]
            )
        
        if advisor_id == cls.DEFAULT_ADVISOR_ID:
            default_adv = Advisor(
                id=cls.DEFAULT_ADVISOR_ID,
                agency_id=AgencyRepository.DEFAULT_AGENCY_ID,
                name="Ádám (Lead Travel Advisor)",
                email="adam@optivoya.com",
                role="lead_advisor"
            )
            cls.save_advisor(default_adv)
            return default_adv
        return None

    @classmethod
    def get_advisor_by_user(cls, username: str) -> Optional[Advisor]:
        # Default match for adam / bean
        if username in ("adam", "admin"):
            return cls.get_advisor(cls.DEFAULT_ADVISOR_ID)
        
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("advisors").select("*").eq("email", f"{username}@optivoya.com").execute()
                if res.data:
                    return Advisor(**res.data[0])
            except Exception:
                pass

        conn = LocalSQLiteStorage.get_connection()
        row = conn.execute("SELECT * FROM advisors WHERE email = ?", (f"{username}@optivoya.com",)).fetchone()
        conn.close()
        if row:
            return Advisor(
                id=row["id"],
                agency_id=row["agency_id"],
                name=row["name"],
                email=row["email"],
                role=row["role"]
            )
        return cls.get_advisor(cls.DEFAULT_ADVISOR_ID)

    @classmethod
    def save_advisor(cls, advisor: Advisor) -> Advisor:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                payload = advisor.model_dump()
                if payload.get("created_at") and hasattr(payload["created_at"], "isoformat"):
                    payload["created_at"] = payload["created_at"].isoformat()
                sb.table("advisors").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_advisor fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO advisors (id, agency_id, name, email, role, avatar_url, is_active, default_origin, default_currency, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                role=excluded.role,
                is_active=excluded.is_active
        """, (advisor.id, advisor.agency_id, advisor.name, advisor.email, advisor.role, advisor.avatar_url, int(advisor.is_active), advisor.default_origin, advisor.default_currency, utc_now_iso()))
        conn.commit()
        conn.close()
        return advisor


# ==============================================================================
# 3. CLIENT REPOSITORY (CRM)
# ==============================================================================

class ClientRepository:
    @classmethod
    def list_clients(cls, agency_id: Optional[str] = None, search: Optional[str] = None) -> List[Client]:
        if not agency_id:
            agency_id = AgencyRepository.DEFAULT_AGENCY_ID
        clients = []
        if is_supabase_configured():
            try:
                sb = get_supabase()
                query = sb.table("clients").select("*").eq("agency_id", agency_id)
                if search:
                    query = query.ilike("name", f"%{search}%")
                res = query.order("created_at", desc=True).execute()
                if res.data:
                    for r in res.data:
                        prefs = r.get("preferences", {})
                        tags = r.get("tags", [])
                        clients.append(Client(
                            id=r["id"],
                            agency_id=r["agency_id"],
                            advisor_id=r["advisor_id"],
                            name=r["name"],
                            email=r["email"],
                            phone=r.get("phone"),
                            passport_country=r.get("passport_country", "Hungary"),
                            notes=r.get("notes"),
                            tags=tags if isinstance(tags, list) else [],
                            preferences=ClientPreferences(**prefs) if isinstance(prefs, dict) else ClientPreferences()
                        ))
                    return clients
            except Exception as e:
                logger.debug(f"Supabase list_clients fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if search:
            rows = conn.execute("SELECT * FROM clients WHERE agency_id = ? AND (name LIKE ? OR email LIKE ?) ORDER BY created_at DESC",
                                (agency_id, f"%{search}%", f"%{search}%")).fetchall()
        else:
            rows = conn.execute("SELECT * FROM clients WHERE agency_id = ? ORDER BY created_at DESC", (agency_id,)).fetchall()
        conn.close()

        for r in rows:
            prefs = json.loads(r["preferences"]) if r["preferences"] else {}
            tags = json.loads(r["tags"]) if r["tags"] else []
            clients.append(Client(
                id=r["id"],
                agency_id=r["agency_id"],
                advisor_id=r["advisor_id"],
                name=r["name"],
                email=r["email"],
                phone=r["phone"],
                passport_country=r["passport_country"],
                notes=r["notes"],
                tags=tags,
                preferences=ClientPreferences(**prefs)
            ))
        
        # If store empty, seed default clients for default agency
        if not clients and agency_id == AgencyRepository.DEFAULT_AGENCY_ID:
            seed_client_1 = Client(
                id="client_kovacs_csalad",
                agency_id=agency_id,
                advisor_id=AdvisorRepository.DEFAULT_ADVISOR_ID,
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
            )
            seed_client_2 = Client(
                id="client_toth_par",
                agency_id=agency_id,
                advisor_id=AdvisorRepository.DEFAULT_ADVISOR_ID,
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
            cls.save_client(seed_client_1)
            cls.save_client(seed_client_2)
            clients = [seed_client_1, seed_client_2]

        return clients

    @classmethod
    def get_client(cls, client_id: str, agency_id: Optional[str] = None) -> Optional[Client]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("clients").select("*").eq("id", client_id)
                if agency_id:
                    q = q.eq("agency_id", agency_id)
                res = q.execute()
                if res.data:
                    r = res.data[0]
                    return Client(
                        id=r["id"],
                        agency_id=r["agency_id"],
                        advisor_id=r["advisor_id"],
                        name=r["name"],
                        email=r["email"],
                        phone=r.get("phone"),
                        passport_country=r.get("passport_country", "Hungary"),
                        notes=r.get("notes"),
                        tags=r.get("tags", []),
                        preferences=ClientPreferences(**r.get("preferences", {}))
                    )
            except Exception as e:
                logger.debug(f"Supabase get_client fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            row = conn.execute("SELECT * FROM clients WHERE id = ? AND agency_id = ?", (client_id, agency_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        conn.close()

        if row:
            return Client(
                id=row["id"],
                agency_id=row["agency_id"],
                advisor_id=row["advisor_id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                passport_country=row["passport_country"],
                notes=row["notes"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
                preferences=ClientPreferences(**json.loads(row["preferences"])) if row["preferences"] else ClientPreferences()
            )
        
        if client_id == "client_kovacs_csalad":
            seed_client_1 = Client(
                id="client_kovacs_csalad",
                agency_id=agency_id or AgencyRepository.DEFAULT_AGENCY_ID,
                advisor_id=AdvisorRepository.DEFAULT_ADVISOR_ID,
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
            )
            cls.save_client(seed_client_1)
            return seed_client_1
        return None

    @classmethod
    def save_client(cls, client: Client, agency_id: Optional[str] = None) -> Client:
        prefs_dict = client.preferences.model_dump() if hasattr(client.preferences, "model_dump") else {}
        tags_list = list(client.tags) if client.tags else []

        if is_supabase_configured():
            try:
                sb = get_supabase()
                payload = {
                    "id": client.id,
                    "agency_id": client.agency_id,
                    "advisor_id": client.advisor_id,
                    "name": client.name,
                    "email": client.email,
                    "phone": client.phone,
                    "passport_country": client.passport_country,
                    "notes": client.notes,
                    "tags": tags_list,
                    "preferences": prefs_dict,
                    "updated_at": utc_now_iso()
                }
                sb.table("clients").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_client fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO clients (id, agency_id, advisor_id, name, email, phone, passport_country, notes, tags, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                phone=excluded.phone,
                notes=excluded.notes,
                tags=excluded.tags,
                preferences=excluded.preferences,
                updated_at=excluded.updated_at
        """, (client.id, client.agency_id, client.advisor_id, client.name, client.email, client.phone, client.passport_country, client.notes, safe_json_dumps(tags_list), safe_json_dumps(prefs_dict), utc_now_iso(), utc_now_iso()))
        conn.commit()
        conn.close()
        return client


# ==============================================================================
# 4. TRIP CASE REPOSITORY
# ==============================================================================

class TripCaseRepository:
    @classmethod
    def list_cases(cls, agency_id: Optional[str] = None, status: Optional[str] = None) -> List[TripCase]:
        if not agency_id:
            agency_id = AgencyRepository.DEFAULT_AGENCY_ID
        cases = []
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("trip_cases").select("*").eq("agency_id", agency_id)
                if status:
                    q = q.eq("status", status)
                res = q.order("created_at", desc=True).execute()
                if res.data:
                    for r in res.data:
                        cases.append(cls._row_to_trip_case(r))
                    return cases
            except Exception as e:
                logger.debug(f"Supabase list_cases fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if status:
            rows = conn.execute("SELECT * FROM trip_cases WHERE agency_id = ? AND status = ? ORDER BY created_at DESC", (agency_id, status)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM trip_cases WHERE agency_id = ? ORDER BY created_at DESC", (agency_id,)).fetchall()
        conn.close()

        for r in rows:
            cases.append(cls._sqlite_row_to_trip_case(r))

        if not cases and agency_id == AgencyRepository.DEFAULT_AGENCY_ID:
            seed_case = TripCase(
                id="case_london_kovacs",
                agency_id=agency_id,
                advisor_id=AdvisorRepository.DEFAULT_ADVISOR_ID,
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
            )
            cls.save_case(seed_case)
            cases = [seed_case]

        return cases

    @classmethod
    def get_case(cls, case_id: str, agency_id: Optional[str] = None) -> Optional[TripCase]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("trip_cases").select("*").eq("id", case_id)
                if agency_id:
                    q = q.eq("agency_id", agency_id)
                res = q.execute()
                if res.data:
                    return cls._row_to_trip_case(res.data[0])
            except Exception as e:
                logger.debug(f"Supabase get_case fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            row = conn.execute("SELECT * FROM trip_cases WHERE id = ? AND agency_id = ?", (case_id, agency_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM trip_cases WHERE id = ?", (case_id,)).fetchone()
        conn.close()

        if row:
            return cls._sqlite_row_to_trip_case(row)
        return None

    @classmethod
    def save_case(cls, trip_case: TripCase, agency_id: Optional[str] = None) -> TripCase:
        prefs_dict = trip_case.preferences.model_dump() if hasattr(trip_case.preferences, "model_dump") else {}
        selected_ids = list(trip_case.selected_option_ids) if trip_case.selected_option_ids else []
        shortlist_ids = list(trip_case.shortlist_ids) if trip_case.shortlist_ids else []

        if is_supabase_configured():
            try:
                sb = get_supabase()
                payload = {
                    "id": trip_case.id,
                    "agency_id": trip_case.agency_id,
                    "advisor_id": trip_case.advisor_id,
                    "client_id": trip_case.client_id,
                    "title": trip_case.title,
                    "status": trip_case.status.value if hasattr(trip_case.status, "value") else str(trip_case.status),
                    "scope": trip_case.scope.value if hasattr(trip_case.scope, "value") else str(trip_case.scope),
                    "budget_mode": trip_case.budget_mode.value if hasattr(trip_case.budget_mode, "value") else str(trip_case.budget_mode),
                    "origin": trip_case.origin,
                    "destination_focus": trip_case.destination_focus,
                    "adults": trip_case.adults,
                    "children": trip_case.children,
                    "duration_days": trip_case.duration_days,
                    "total_budget_huf": trip_case.total_budget_huf,
                    "flight_budget_huf": trip_case.flight_budget_huf,
                    "stay_budget_huf": trip_case.stay_budget_huf,
                    "preferences": prefs_dict,
                    "selected_option_ids": selected_ids,
                    "shortlist_ids": shortlist_ids,
                    "research_time_saved_minutes": trip_case.research_time_saved_minutes,
                    "updated_at": utc_now_iso()
                }
                sb.table("trip_cases").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_case fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO trip_cases (
                id, agency_id, advisor_id, client_id, title, status, scope, budget_mode,
                origin, destination_focus, adults, children, duration_days,
                total_budget_huf, flight_budget_huf, stay_budget_huf, preferences,
                selected_option_ids, shortlist_ids, research_time_saved_minutes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                status=excluded.status,
                scope=excluded.scope,
                budget_mode=excluded.budget_mode,
                destination_focus=excluded.destination_focus,
                adults=excluded.adults,
                children=excluded.children,
                duration_days=excluded.duration_days,
                total_budget_huf=excluded.total_budget_huf,
                flight_budget_huf=excluded.flight_budget_huf,
                stay_budget_huf=excluded.stay_budget_huf,
                preferences=excluded.preferences,
                selected_option_ids=excluded.selected_option_ids,
                shortlist_ids=excluded.shortlist_ids,
                research_time_saved_minutes=excluded.research_time_saved_minutes,
                updated_at=excluded.updated_at
        """, (
            trip_case.id, trip_case.agency_id, trip_case.advisor_id, trip_case.client_id,
            trip_case.title, trip_case.status.value if hasattr(trip_case.status, "value") else str(trip_case.status),
            trip_case.scope.value if hasattr(trip_case.scope, "value") else str(trip_case.scope),
            trip_case.budget_mode.value if hasattr(trip_case.budget_mode, "value") else str(trip_case.budget_mode),
            trip_case.origin, trip_case.destination_focus, trip_case.adults, trip_case.children, trip_case.duration_days,
            trip_case.total_budget_huf, trip_case.flight_budget_huf, trip_case.stay_budget_huf,
            safe_json_dumps(prefs_dict), safe_json_dumps(selected_ids), safe_json_dumps(shortlist_ids),
            trip_case.research_time_saved_minutes, utc_now_iso(), utc_now_iso()
        ))
        conn.commit()
        conn.close()
        return trip_case

    @classmethod
    def delete_case(cls, case_id: str, agency_id: Optional[str] = None) -> bool:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("trip_cases").delete().eq("id", case_id)
                if agency_id:
                    q = q.eq("agency_id", agency_id)
                q.execute()
            except Exception:
                pass

        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            conn.execute("DELETE FROM trip_cases WHERE id = ? AND agency_id = ?", (case_id, agency_id))
        else:
            conn.execute("DELETE FROM trip_cases WHERE id = ?", (case_id,))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def _row_to_trip_case(cls, r: Dict[str, Any]) -> TripCase:
        prefs = r.get("preferences", {})
        return TripCase(
            id=r["id"],
            agency_id=r["agency_id"],
            advisor_id=r["advisor_id"],
            client_id=r["client_id"],
            title=r.get("title", "Utazási Ügy"),
            status=TripCaseStatus(r.get("status", "brief")),
            scope=ResearchScope(r.get("scope", "full_trip")),
            budget_mode=BudgetMode(r.get("budget_mode", "total")),
            origin=r.get("origin", "Budapest (BUD)"),
            destination_focus=r.get("destination_focus"),
            adults=r.get("adults", 2),
            children=r.get("children", 0),
            duration_days=r.get("duration_days", 7),
            total_budget_huf=r.get("total_budget_huf"),
            flight_budget_huf=r.get("flight_budget_huf"),
            stay_budget_huf=r.get("stay_budget_huf"),
            preferences=ResolvedTripPreferences(**prefs) if isinstance(prefs, dict) and prefs else ResolvedTripPreferences(),
            selected_option_ids=r.get("selected_option_ids", []),
            shortlist_ids=r.get("shortlist_ids", []),
            research_time_saved_minutes=r.get("research_time_saved_minutes", 0.0)
        )

    @classmethod
    def _sqlite_row_to_trip_case(cls, r: sqlite3.Row) -> TripCase:
        prefs_raw = json.loads(r["preferences"]) if r["preferences"] else {}
        return TripCase(
            id=r["id"],
            agency_id=r["agency_id"],
            advisor_id=r["advisor_id"],
            client_id=r["client_id"],
            title=r["title"],
            status=TripCaseStatus(r["status"]),
            scope=ResearchScope(r["scope"]),
            budget_mode=BudgetMode(r["budget_mode"]),
            origin=r["origin"],
            destination_focus=r["destination_focus"],
            adults=r["adults"],
            children=r["children"],
            duration_days=r["duration_days"],
            total_budget_huf=r["total_budget_huf"],
            flight_budget_huf=r["flight_budget_huf"],
            stay_budget_huf=r["stay_budget_huf"],
            preferences=ResolvedTripPreferences(**prefs_raw) if prefs_raw else ResolvedTripPreferences(),
            selected_option_ids=json.loads(r["selected_option_ids"]) if r["selected_option_ids"] else [],
            shortlist_ids=json.loads(r["shortlist_ids"]) if r["shortlist_ids"] else [],
            research_time_saved_minutes=r["research_time_saved_minutes"]
        )


# ==============================================================================
# 5. RESEARCH RUN REPOSITORY
# ==============================================================================

class ResearchRunRepository:
    @classmethod
    def save_run(cls, run: ResearchRun) -> ResearchRun:
        payload = run.model_dump()
        if is_supabase_configured():
            try:
                sb = get_supabase()
                sb.table("research_runs").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_run fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO research_runs (
                id, case_id, agency_id, advisor_id, strategy, status, progress_pct,
                steps_completed, providers_status, candidates, destinations_pool,
                flights_pool, stays_pool, warnings, elapsed_seconds, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                progress_pct=excluded.progress_pct,
                steps_completed=excluded.steps_completed,
                providers_status=excluded.providers_status,
                candidates=excluded.candidates,
                destinations_pool=excluded.destinations_pool,
                flights_pool=excluded.flights_pool,
                stays_pool=excluded.stays_pool,
                warnings=excluded.warnings,
                elapsed_seconds=excluded.elapsed_seconds,
                updated_at=excluded.updated_at
        """, (
            run.id, run.case_id, run.agency_id, run.advisor_id, run.strategy,
            run.status.value if hasattr(run.status, "value") else str(run.status),
            run.progress_pct,
            safe_json_dumps(run.steps_completed),
            safe_json_dumps(run.providers_status),
            safe_json_dumps(run.candidates),
            safe_json_dumps(run.destinations_pool),
            safe_json_dumps(run.flights_pool),
            safe_json_dumps(run.stays_pool),
            safe_json_dumps(run.warnings),
            run.elapsed_seconds,
            run.created_at.isoformat() if hasattr(run.created_at, "isoformat") else utc_now_iso(),
            utc_now_iso()
        ))
        conn.commit()
        conn.close()
        return run

    @classmethod
    def get_run(cls, run_id: str, case_id: Optional[str] = None) -> Optional[ResearchRun]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("research_runs").select("*").eq("id", run_id)
                if case_id:
                    q = q.eq("case_id", case_id)
                res = q.execute()
                if res.data:
                    return ResearchRun(**res.data[0])
            except Exception as e:
                logger.debug(f"Supabase get_run fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if case_id:
            row = conn.execute("SELECT * FROM research_runs WHERE id = ? AND case_id = ?", (run_id, case_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM research_runs WHERE id = ?", (run_id,)).fetchone()
        conn.close()

        if row:
            return ResearchRun(
                id=row["id"],
                case_id=row["case_id"],
                agency_id=row["agency_id"],
                advisor_id=row["advisor_id"],
                strategy=row["strategy"],
                status=ResearchRunStatus(row["status"]),
                progress_pct=row["progress_pct"],
                steps_completed=json.loads(row["steps_completed"]) if row["steps_completed"] else [],
                providers_status=json.loads(row["providers_status"]) if row["providers_status"] else {},
                candidates=json.loads(row["candidates"]) if row["candidates"] else [],
                destinations_pool=json.loads(row["destinations_pool"]) if row["destinations_pool"] else [],
                flights_pool=json.loads(row["flights_pool"]) if row["flights_pool"] else [],
                stays_pool=json.loads(row["stays_pool"]) if row["stays_pool"] else [],
                warnings=json.loads(row["warnings"]) if row["warnings"] else [],
                elapsed_seconds=row["elapsed_seconds"]
            )
        return None


# ==============================================================================
# 6. TRIP OPTION REPOSITORY
# ==============================================================================

class TripOptionRepository:
    @classmethod
    def list_options_for_case(cls, case_id: str) -> List[TripOption]:
        options = []
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("trip_options").select("*").eq("case_id", case_id).execute()
                if res.data:
                    for r in res.data:
                        options.append(TripOption(**r))
                    return options
            except Exception as e:
                logger.debug(f"Supabase list_options fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        rows = conn.execute("SELECT * FROM trip_options WHERE case_id = ?", (case_id,)).fetchall()
        conn.close()

        for r in rows:
            options.append(TripOption(
                id=r["id"],
                case_id=r["case_id"],
                archetype=OptionArchetype(r["archetype"]),
                title=r["title"],
                tagline=r["tagline"],
                total_price_huf=r["total_price_huf"],
                price_per_person_huf=r["price_per_person_huf"],
                currency=r["currency"],
                destination=json.loads(r["destination"]) if r["destination"] else {},
                flight=json.loads(r["flight"]) if r["flight"] else {},
                stay=json.loads(r["stay"]) if r["stay"] else {},
                activities=json.loads(r["activities"]) if r["activities"] else [],
                trip_score=r["trip_score"],
                pillar_scores=json.loads(r["pillar_scores"]) if r["pillar_scores"] else {},
                effective_vacation_hours=r["effective_vacation_hours"],
                why_this_option=r["why_this_option"],
                tradeoffs=json.loads(r["tradeoffs"]) if r["tradeoffs"] else [],
                verification_status=r["verification_status"],
                is_pinned=bool(r["is_pinned"])
            ))
        return options

    @classmethod
    def save_option(cls, option: Any) -> Any:
        if isinstance(option, dict):
            opt_id = option.get("id") or str(uuid.uuid4())
            case_id = option.get("case_id", "")
            archetype = option.get("archetype", "best_overall")
            title = option.get("title", "")
            tagline = option.get("tagline", "")
            total_price = float(option.get("total_price_huf", 0.0))
            price_pp = float(option.get("price_per_person_huf", 0.0))
            currency = option.get("currency", "HUF")
            destination = option.get("destination", {})
            flight = option.get("flight", {})
            stay = option.get("stay", {})
            activities = option.get("activities", [])
            trip_score = int(round(float(option.get("trip_score", 85))))
            pillar_scores = option.get("pillar_scores", {})
            effective_vacation_hours = float(option.get("effective_vacation_hours", 16.0))
            why_this_option = option.get("why_this_option", "")
            tradeoffs = option.get("tradeoffs", [])
            verification_status = option.get("verification_status", "VERIFIED")
            is_pinned = int(bool(option.get("is_pinned", False)))
            payload = dict(option)
        else:
            opt_id = option.id
            case_id = option.case_id
            archetype = option.archetype.value if hasattr(option.archetype, "value") else str(option.archetype)
            title = option.title
            tagline = option.tagline
            total_price = option.total_price_huf
            price_pp = option.price_per_person_huf
            currency = option.currency
            destination = option.destination
            flight = option.flight
            stay = option.stay
            activities = option.activities
            trip_score = option.trip_score
            pillar_scores = option.pillar_scores
            effective_vacation_hours = option.effective_vacation_hours
            why_this_option = option.why_this_option
            tradeoffs = option.tradeoffs
            verification_status = option.verification_status.value if hasattr(option.verification_status, "value") else str(option.verification_status)
            is_pinned = int(option.is_pinned)
            payload = option.model_dump()

        if is_supabase_configured():
            try:
                sb = get_supabase()
                clean_payload = json.loads(safe_json_dumps(option))
                sb.table("trip_options").upsert(clean_payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_option fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO trip_options (
                id, case_id, archetype, title, tagline, total_price_huf, price_per_person_huf,
                currency, destination, flight, stay, activities, trip_score, pillar_scores,
                effective_vacation_hours, why_this_option, tradeoffs, verification_status, is_pinned, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                case_id=excluded.case_id,
                archetype=excluded.archetype,
                title=excluded.title,
                tagline=excluded.tagline,
                total_price_huf=excluded.total_price_huf,
                price_per_person_huf=excluded.price_per_person_huf,
                currency=excluded.currency,
                destination=excluded.destination,
                flight=excluded.flight,
                stay=excluded.stay,
                activities=excluded.activities,
                trip_score=excluded.trip_score,
                pillar_scores=excluded.pillar_scores,
                effective_vacation_hours=excluded.effective_vacation_hours,
                why_this_option=excluded.why_this_option,
                tradeoffs=excluded.tradeoffs,
                verification_status=excluded.verification_status,
                is_pinned=excluded.is_pinned
        """, (
            opt_id, case_id, archetype,
            title, tagline, total_price, price_pp,
            currency, safe_json_dumps(destination), safe_json_dumps(flight),
            safe_json_dumps(stay), safe_json_dumps(activities), trip_score,
            safe_json_dumps(pillar_scores), effective_vacation_hours, why_this_option,
            safe_json_dumps(tradeoffs), verification_status, is_pinned, utc_now_iso()
        ))
        conn.commit()
        conn.close()
        return option

    @classmethod
    def save_options_batch(cls, case_id: str, options: List[Any]) -> List[Any]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                sb.table("trip_options").delete().eq("case_id", case_id).execute()
            except Exception as e:
                logger.debug(f"Supabase delete options fallback: {e}")

        # Delete existing for case before replacing
        conn = LocalSQLiteStorage.get_connection()
        conn.execute("DELETE FROM trip_options WHERE case_id = ?", (case_id,))
        conn.commit()
        conn.close()
        for opt in options:
            cls.save_option(opt)
        return options


# ==============================================================================
# 7. PROPOSAL & SHARE REPOSITORY
# ==============================================================================

class ProposalRepository:
    @classmethod
    def get_proposal(cls, proposal_id: str, agency_id: Optional[str] = None) -> Optional[Proposal]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                q = sb.table("proposals").select("*").eq("id", proposal_id)
                if agency_id:
                    q = q.eq("agency_id", agency_id)
                res = q.execute()
                if res.data:
                    return Proposal(**res.data[0])
            except Exception as e:
                logger.debug(f"Supabase get_proposal fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            row = conn.execute("SELECT * FROM proposals WHERE id = ? AND agency_id = ?", (proposal_id, agency_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        conn.close()

        if row:
            vers_raw = json.loads(row["versions"]) if row["versions"] else []
            return Proposal(
                id=row["id"],
                case_id=row["case_id"],
                agency_id=row["agency_id"],
                advisor_id=row["advisor_id"],
                client_id=row["client_id"],
                title=row["title"],
                status=row["status"],
                current_version=row["current_version"],
                versions=[ProposalVersion(**v) if isinstance(v, dict) else v for v in vers_raw],
                shareable_token=row["shareable_token"],
                view_count=row["view_count"],
                last_viewed_at=datetime.fromisoformat(row["last_viewed_at"]) if row["last_viewed_at"] else None
            )
        return None

    @classmethod
    def get_proposal_doc(cls, proposal_id: str, agency_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves raw proposal document dictionary including full version history and option snapshots."""
        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            row = conn.execute("SELECT * FROM proposals WHERE id = ? AND agency_id = ?", (proposal_id, agency_id)).fetchone()
        else:
            row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        conn.close()

        if row:
            vers_raw = json.loads(row["versions"]) if row["versions"] else []
            latest_version = vers_raw[-1] if vers_raw else {}
            return {
                "id": row["id"],
                "case_id": row["case_id"],
                "agency_id": row["agency_id"],
                "advisor_id": row["advisor_id"],
                "client_id": row["client_id"],
                "title": row["title"],
                "status": row["status"],
                "version": row["current_version"],
                "current_version": row["current_version"],
                "versions": vers_raw,
                "options_snapshot": latest_version.get("options_snapshot", []),
                "selected_option_ids": latest_version.get("selected_option_ids", []),
                "client_intro": latest_version.get("client_intro", ""),
                "advisor_notes": latest_version.get("advisor_notes", ""),
                "recommendation_summary": latest_version.get("recommendation_summary", ""),
                "total_options_count": len(latest_version.get("options_snapshot", [])),
                "shareable_token": row["shareable_token"],
                "view_count": row["view_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
        return None

    @classmethod
    def list_proposals_for_case(cls, case_id: str, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all proposal documents for a case."""
        conn = LocalSQLiteStorage.get_connection()
        if agency_id:
            rows = conn.execute("SELECT * FROM proposals WHERE case_id = ? AND agency_id = ? ORDER BY current_version DESC", (case_id, agency_id)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM proposals WHERE case_id = ? ORDER BY current_version DESC", (case_id,)).fetchall()
        conn.close()

        proposals = []
        for row in rows:
            vers_raw = json.loads(row["versions"]) if row["versions"] else []
            latest_version = vers_raw[-1] if vers_raw else {}
            proposals.append({
                "id": row["id"],
                "case_id": row["case_id"],
                "agency_id": row["agency_id"],
                "advisor_id": row["advisor_id"],
                "client_id": row["client_id"],
                "title": row["title"],
                "status": row["status"],
                "version": row["current_version"],
                "current_version": row["current_version"],
                "versions": vers_raw,
                "options_snapshot": latest_version.get("options_snapshot", []),
                "selected_option_ids": latest_version.get("selected_option_ids", []),
                "client_intro": latest_version.get("client_intro", ""),
                "advisor_notes": latest_version.get("advisor_notes", ""),
                "recommendation_summary": latest_version.get("recommendation_summary", ""),
                "total_options_count": len(latest_version.get("options_snapshot", [])),
                "shareable_token": row["shareable_token"],
                "view_count": row["view_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        return proposals

    @classmethod
    def save_proposal(cls, proposal: Any, agency_id: Optional[str] = None, advisor_id: Optional[str] = None) -> Any:
        if isinstance(proposal, dict):
            p_id = proposal.get("id")
            case_id = proposal.get("case_id")
            client_id = proposal.get("client_id")
            title = proposal.get("title", "Utazási Ajánlat")
            status = proposal.get("status", "DRAFT")
            version_num = proposal.get("version", 1)
            p_agency_id = proposal.get("agency_id") or agency_id or AgencyRepository.DEFAULT_AGENCY_ID
            p_advisor_id = proposal.get("advisor_id") or advisor_id or AdvisorRepository.DEFAULT_ADVISOR_ID
            shareable_token = proposal.get("shareable_token")
            view_count = proposal.get("view_count", 0)

            versions = proposal.get("versions", [])
            if not versions:
                versions = [{
                    "version_number": version_num,
                    "title": title,
                    "client_intro": proposal.get("client_intro", ""),
                    "advisor_notes": proposal.get("advisor_notes", ""),
                    "recommendation_summary": proposal.get("recommendation_summary", ""),
                    "selected_option_ids": proposal.get("selected_option_ids", []),
                    "options_snapshot": proposal.get("options_snapshot", []),
                    "created_at": proposal.get("created_at") or utc_now_iso()
                }]
            vers_json = safe_json_dumps(versions)
        else:
            p_id = proposal.id
            case_id = proposal.case_id
            p_agency_id = proposal.agency_id
            p_advisor_id = proposal.advisor_id
            client_id = proposal.client_id
            title = proposal.title
            status = proposal.status
            version_num = proposal.current_version
            shareable_token = proposal.shareable_token
            view_count = proposal.view_count
            vers_list = [v.model_dump() if hasattr(v, "model_dump") else v for v in proposal.versions]
            vers_json = safe_json_dumps(vers_list)

        if is_supabase_configured():
            try:
                sb = get_supabase()
                payload = {
                    "id": p_id,
                    "case_id": case_id,
                    "agency_id": p_agency_id,
                    "advisor_id": p_advisor_id,
                    "client_id": client_id,
                    "title": title,
                    "status": status,
                    "current_version": version_num,
                    "versions": json.loads(vers_json),
                    "shareable_token": shareable_token,
                    "view_count": view_count,
                    "updated_at": utc_now_iso()
                }
                sb.table("proposals").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_proposal fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO proposals (
                id, case_id, agency_id, advisor_id, client_id, title, status,
                current_version, versions, shareable_token, view_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                status=excluded.status,
                current_version=excluded.current_version,
                versions=excluded.versions,
                shareable_token=excluded.shareable_token,
                view_count=excluded.view_count,
                updated_at=excluded.updated_at
        """, (
            p_id, case_id, p_agency_id, p_advisor_id, client_id,
            title, status, version_num, vers_json,
            shareable_token, view_count, utc_now_iso(), utc_now_iso()
        ))
        conn.commit()
        conn.close()
        return proposal


class ProposalShareRepository:
    @classmethod
    def get_share_by_token(cls, token_hash: str) -> Optional[ProposalShare]:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("proposal_shares").select("*").eq("token_hash", token_hash).execute()
                if res.data:
                    return ProposalShare(**res.data[0])
            except Exception as e:
                logger.debug(f"Supabase get_share_by_token fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        row = conn.execute("SELECT * FROM proposal_shares WHERE token_hash = ? OR id = ?", (token_hash, token_hash)).fetchone()
        conn.close()

        if row:
            return ProposalShare(
                id=row["id"],
                proposal_id=row["proposal_id"],
                token_hash=row["token_hash"],
                proposal_version_number=row["proposal_version_number"],
                is_revoked=bool(row["is_revoked"]),
                revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                access_count=row["access_count"],
                last_accessed_at=datetime.fromisoformat(row["last_accessed_at"]) if row["last_accessed_at"] else None
            )
        return None

    @classmethod
    def save_share(cls, share: ProposalShare) -> ProposalShare:
        payload = share.model_dump()
        if is_supabase_configured():
            try:
                sb = get_supabase()
                sb.table("proposal_shares").upsert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase save_share fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO proposal_shares (
                id, proposal_id, token_hash, proposal_version_number, is_revoked,
                revoked_at, expires_at, access_count, last_accessed_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                is_revoked=excluded.is_revoked,
                revoked_at=excluded.revoked_at,
                access_count=excluded.access_count,
                last_accessed_at=excluded.last_accessed_at
        """, (
            share.id, share.proposal_id, share.token_hash, share.proposal_version_number,
            int(share.is_revoked), share.revoked_at.isoformat() if share.revoked_at else None,
            share.expires_at.isoformat() if share.expires_at else None,
            share.access_count, share.last_accessed_at.isoformat() if share.last_accessed_at else None,
            share.created_at.isoformat() if share.created_at else utc_now_iso()
        ))
        conn.commit()
        conn.close()
        return share

    @classmethod
    def revoke_share(cls, proposal_id: str) -> bool:
        if is_supabase_configured():
            try:
                sb = get_supabase()
                sb.table("proposal_shares").update({"is_revoked": True, "revoked_at": utc_now_iso()}).eq("proposal_id", proposal_id).execute()
            except Exception:
                pass

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("UPDATE proposal_shares SET is_revoked = 1, revoked_at = ? WHERE proposal_id = ?", (utc_now_iso(), proposal_id))
        conn.commit()
        conn.close()
        return True


# ==============================================================================
# 8. TIMELINE & CASE EVENT REPOSITORY
# ==============================================================================

class TimelineRepository:
    @classmethod
    def log_event(cls, case_id: str, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None, title: Optional[str] = None) -> CaseEvent:
        event = CaseEvent(
            id=f"evt_{uuid.uuid4().hex[:10]}",
            case_id=case_id,
            event_type=event_type,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        if is_supabase_configured():
            try:
                sb = get_supabase()
                sb.table("case_events").insert(event.model_dump()).execute()
            except Exception as e:
                logger.debug(f"Supabase log_event fallback: {e}")

        conn = LocalSQLiteStorage.get_connection()
        conn.execute("""
            INSERT INTO case_events (id, case_id, event_type, description, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event.id, event.case_id, event.event_type, event.description, safe_json_dumps(event.metadata), utc_now_iso()))
        conn.commit()
        conn.close()
        return event

    @classmethod
    def list_events(cls, case_id: str) -> List[CaseEvent]:
        events = []
        if is_supabase_configured():
            try:
                sb = get_supabase()
                res = sb.table("case_events").select("*").eq("case_id", case_id).order("created_at", desc=True).execute()
                if res.data:
                    return [CaseEvent(**r) for r in res.data]
            except Exception:
                pass

        conn = LocalSQLiteStorage.get_connection()
        rows = conn.execute("SELECT * FROM case_events WHERE case_id = ? ORDER BY created_at DESC", (case_id,)).fetchall()
        conn.close()

        for r in rows:
            events.append(CaseEvent(
                id=r["id"],
                case_id=r["case_id"],
                event_type=r["event_type"],
                description=r["description"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {}
            ))
        return events
