-- ==============================================================================
-- OPTIVOYA B2B ADVISOR WORKSPACE — DATABASE MIGRATION 003
-- Multi-Tenant PostgreSQL Schema with Row Level Security (RLS) & Provenance
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. AGENCIES TABLE
CREATE TABLE IF NOT EXISTS agencies (
    id TEXT PRIMARY KEY DEFAULT ('agency_' || gen_random_uuid()),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    branding JSONB NOT NULL DEFAULT '{"primary_color": "#2563eb", "accent_color": "#0ea5e9", "company_name": "Optivoya Travel Advisory"}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. ADVISORS TABLE
CREATE TABLE IF NOT EXISTS advisors (
    id TEXT PRIMARY KEY DEFAULT ('adv_' || gen_random_uuid()),
    agency_id TEXT NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'advisor',
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    default_origin TEXT NOT NULL DEFAULT 'Budapest (BUD)',
    default_currency TEXT NOT NULL DEFAULT 'HUF',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_advisors_agency ON advisors(agency_id);

-- 4. CLIENTS TABLE
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY DEFAULT ('cli_' || gen_random_uuid()),
    agency_id TEXT NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    advisor_id TEXT NOT NULL REFERENCES advisors(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    passport_country TEXT NOT NULL DEFAULT 'Hungary',
    notes TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clients_agency ON clients(agency_id);
CREATE INDEX IF NOT EXISTS idx_clients_advisor ON clients(advisor_id);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);

-- 5. TRIP CASES TABLE (CENTRAL AGGREGATE)
CREATE TABLE IF NOT EXISTS trip_cases (
    id TEXT PRIMARY KEY DEFAULT ('case_' || gen_random_uuid()),
    agency_id TEXT NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    advisor_id TEXT NOT NULL REFERENCES advisors(id) ON DELETE RESTRICT,
    client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL DEFAULT 'Új Utazási Terv',
    status TEXT NOT NULL DEFAULT 'brief',
    scope TEXT NOT NULL DEFAULT 'full_trip',
    budget_mode TEXT NOT NULL DEFAULT 'total',
    
    origin TEXT NOT NULL DEFAULT 'Budapest (BUD)',
    destination_focus TEXT,
    adults INT NOT NULL DEFAULT 2,
    children INT NOT NULL DEFAULT 0,
    duration_days INT NOT NULL DEFAULT 7,
    
    date_mode TEXT NOT NULL DEFAULT 'exact',
    out_date DATE,
    in_date DATE,
    out_window_start DATE,
    out_window_end DATE,
    min_stay_nights INT,
    max_stay_nights INT,
    
    total_budget_huf NUMERIC,
    flight_budget_huf NUMERIC,
    stay_budget_huf NUMERIC,
    
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected_option_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    shortlist_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    research_time_saved_minutes NUMERIC NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_agency ON trip_cases(agency_id);
CREATE INDEX IF NOT EXISTS idx_cases_advisor ON trip_cases(advisor_id);
CREATE INDEX IF NOT EXISTS idx_cases_client ON trip_cases(client_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON trip_cases(status);

-- 6. TRIP OPTIONS TABLE (3 ARCHETYPES)
CREATE TABLE IF NOT EXISTS trip_options (
    id TEXT PRIMARY KEY DEFAULT ('opt_' || gen_random_uuid()),
    case_id TEXT NOT NULL REFERENCES trip_cases(id) ON DELETE CASCADE,
    archetype TEXT NOT NULL DEFAULT 'best_overall',
    title TEXT NOT NULL,
    tagline TEXT,
    
    total_price_huf NUMERIC NOT NULL DEFAULT 0.0,
    price_per_person_huf NUMERIC NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'HUF',
    
    destination JSONB NOT NULL DEFAULT '{}'::jsonb,
    flight JSONB NOT NULL DEFAULT '{}'::jsonb,
    stay JSONB NOT NULL DEFAULT '{}'::jsonb,
    activities JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    trip_score INT NOT NULL DEFAULT 85,
    pillar_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    effective_vacation_hours NUMERIC NOT NULL DEFAULT 16.0,
    
    why_this_option TEXT,
    tradeoffs JSONB NOT NULL DEFAULT '[]'::jsonb,
    key_highlights JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    verification_status TEXT NOT NULL DEFAULT 'VERIFIED',
    risk_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_options_case ON trip_options(case_id);
CREATE INDEX IF NOT EXISTS idx_options_archetype ON trip_options(archetype);

-- 7. PROPOSALS TABLE
CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY DEFAULT ('prop_' || gen_random_uuid()),
    case_id TEXT NOT NULL REFERENCES trip_cases(id) ON DELETE CASCADE,
    agency_id TEXT NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    advisor_id TEXT NOT NULL REFERENCES advisors(id) ON DELETE RESTRICT,
    client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL DEFAULT 'Személyre Szabott Utazási Javaslat',
    status TEXT NOT NULL DEFAULT 'draft',
    current_version INT NOT NULL DEFAULT 1,
    versions JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    shareable_token TEXT NOT NULL UNIQUE,
    view_count INT NOT NULL DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proposals_case ON proposals(case_id);
CREATE INDEX IF NOT EXISTS idx_proposals_token ON proposals(shareable_token);

-- 8. ADVISOR NOTES TABLE
CREATE TABLE IF NOT EXISTS advisor_notes (
    id TEXT PRIMARY KEY DEFAULT ('note_' || gen_random_uuid()),
    case_id TEXT NOT NULL REFERENCES trip_cases(id) ON DELETE CASCADE,
    advisor_id TEXT NOT NULL REFERENCES advisors(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    is_client_visible BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_case ON advisor_notes(case_id);

-- 9. CASE EVENTS / AUDIT TIMELINE TABLE
CREATE TABLE IF NOT EXISTS case_events (
    id TEXT PRIMARY KEY DEFAULT ('evt_' || gen_random_uuid()),
    case_id TEXT NOT NULL REFERENCES trip_cases(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_case ON case_events(case_id);

-- 10. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE agencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE advisors ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE advisor_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_events ENABLE ROW LEVEL SECURITY;

-- Agency Isolation Helper: Matches app user agency_id claim in JWT
-- (auth.jwt() ->> 'agency_id')

CREATE POLICY agency_isolation_advisors ON advisors
    FOR ALL USING (agency_id = current_setting('request.jwt.claim.agency_id', true) OR current_setting('request.jwt.claim.role', true) = 'super_admin');

CREATE POLICY agency_isolation_clients ON clients
    FOR ALL USING (agency_id = current_setting('request.jwt.claim.agency_id', true) OR current_setting('request.jwt.claim.role', true) = 'super_admin');

CREATE POLICY agency_isolation_cases ON trip_cases
    FOR ALL USING (agency_id = current_setting('request.jwt.claim.agency_id', true) OR current_setting('request.jwt.claim.role', true) = 'super_admin');

CREATE POLICY agency_isolation_proposals ON proposals
    FOR ALL USING (agency_id = current_setting('request.jwt.claim.agency_id', true) OR current_setting('request.jwt.claim.role', true) = 'super_admin');
