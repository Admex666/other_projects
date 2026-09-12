-- ====================================================================
-- OPTIVOYA B2B BETA — SUPABASE POSTGRESQL SCHEMA
-- Execute this SQL in your Supabase SQL Editor (1 click)
-- ====================================================================

-- 1. Beta Users Table
CREATE TABLE IF NOT EXISTS public.beta_users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    company_name TEXT,
    email TEXT,
    role TEXT DEFAULT 'advisor',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- 2. User Sessions Table
CREATE TABLE IF NOT EXISTS public.user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_event_at TIMESTAMPTZ DEFAULT NOW(),
    device_info TEXT,
    ip_address TEXT,
    searches_count INTEGER DEFAULT 0
);

-- 3. Telemetry & Analytics Events Table
CREATE TABLE IF NOT EXISTS public.telemetry_events (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    session_id TEXT,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- search_started, search_completed, item_selected, proposal_exported, error
    module TEXT NOT NULL,     -- destination_matcher, flight_intelligence, accommodation_intelligence, master_planner, proposal
    search_params JSONB DEFAULT '{}'::jsonb,
    duration_ms DOUBLE PRECISION,
    results_count INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    meta_data JSONB DEFAULT '{}'::jsonb,
    environment TEXT DEFAULT 'production', -- production vs test
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security) with public access policy for service role / anon API
ALTER TABLE public.beta_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telemetry_events ENABLE ROW LEVEL SECURITY;

-- Migration for existing databases:
-- ALTER TABLE public.telemetry_events ADD COLUMN IF NOT EXISTS environment TEXT DEFAULT 'production';

-- Allow full access to backend with API key
CREATE POLICY "Allow all operations for service and anon keys" ON public.beta_users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for service and anon keys" ON public.user_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for service and anon keys" ON public.telemetry_events FOR ALL USING (true) WITH CHECK (true);

-- Starter users
INSERT INTO public.beta_users (username, password_hash, full_name, company_name, email, role, is_active)
VALUES 
('admin', 'optivoya2026', 'Adminisztrátor', 'Optivoya HQ', 'admin@optivoya.com', 'admin', true),
('bean', 'bean', 'Founder', 'Optivoya HQ', 'adam@optivoya.com', 'advisor', true)
ON CONFLICT (username) DO NOTHING;


-- ====================================================================
-- 4. EXPERIENCE & ACTIVITY INTELLIGENCE ENGINE TABLES
-- ====================================================================

-- 4.1. Raw Source Records (Audit-proof Ingestion Store)
CREATE TABLE IF NOT EXISTS public.raw_source_records (
    id BIGSERIAL PRIMARY KEY,
    destination_id TEXT NOT NULL,
    source TEXT NOT NULL,          -- 'osm', 'wikidata', 'wikipedia', 'google_maps'
    source_id TEXT NOT NULL,       -- unique ID from external source (node/123, Q3519, slug)
    name_candidate TEXT NOT NULL,
    raw_payload JSONB NOT NULL,    -- unmodified complete payload from source
    license TEXT,                  -- 'ODbL', 'CC-0', 'CC-BY-SA 4.0', 'Proprietary'
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    parser_version TEXT DEFAULT 'v1.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_raw_source_dest_id UNIQUE (destination_id, source, source_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_sources_dest_source 
ON public.raw_source_records (destination_id, source);

CREATE INDEX IF NOT EXISTS idx_raw_sources_retrieved 
ON public.raw_source_records (retrieved_at DESC);


-- 4.2. Experience Entities (Canonical Resolved Places, Activities & Attractions)
CREATE TABLE IF NOT EXISTS public.experience_entities (
    id BIGSERIAL PRIMARY KEY,
    entity_id TEXT UNIQUE NOT NULL, -- e.g. 'exp_it_bari_basilica_san_nicola'
    destination_id TEXT NOT NULL,   -- 'IT_BARI'
    canonical_name TEXT NOT NULL,
    category TEXT NOT NULL,         -- 'culture_history', 'beach_coastal', 'nature_viewpoint', 'food_market', 'active_adventure', 'entertainment'
    subcategory TEXT,               -- 'church_cathedral', 'castle_fortress', 'museum', 'public_beach', 'boat_tour', 'promenade'
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    rating DOUBLE PRECISION,
    review_count INTEGER DEFAULT 0,
    price_level TEXT DEFAULT 'moderate', -- 'free', 'budget', 'moderate', 'premium'
    est_duration_hours DOUBLE PRECISION DEFAULT 1.5,
    best_time_of_day TEXT DEFAULT 'anytime', -- 'morning', 'afternoon', 'sunset', 'evening', 'anytime'
    confidence_score DOUBLE PRECISION DEFAULT 1.0,
    sources_present TEXT[] DEFAULT '{}',
    source_ids JSONB DEFAULT '{}'::jsonb,
    image_urls TEXT[] DEFAULT '{}',
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exp_entities_dest_cat 
ON public.experience_entities (destination_id, category);

CREATE INDEX IF NOT EXISTS idx_exp_entities_coords 
ON public.experience_entities (lat, lon);

CREATE INDEX IF NOT EXISTS idx_exp_entities_rating 
ON public.experience_entities (rating DESC NULLS LAST);


-- 4.3. Destination Experience Profiles (Pre-aggregated Rollups for Instant <5ms Matcher Lookup)
CREATE TABLE IF NOT EXISTS public.destination_experience_profiles (
    destination_id TEXT PRIMARY KEY,
    city_name TEXT NOT NULL,
    country TEXT NOT NULL,
    total_activities_count INTEGER DEFAULT 0,
    category_distribution JSONB DEFAULT '{}'::jsonb,
    top_experiences_summary JSONB DEFAULT '[]'::jsonb,
    vibe_scores JSONB DEFAULT '{}'::jsonb,
    confidence_level DOUBLE PRECISION DEFAULT 1.0,
    last_synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS & Policies for Experience Engine
ALTER TABLE public.raw_source_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.experience_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.destination_experience_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all operations for raw_source_records" ON public.raw_source_records;
CREATE POLICY "Allow all operations for raw_source_records" 
ON public.raw_source_records FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations for experience_entities" ON public.experience_entities;
CREATE POLICY "Allow all operations for experience_entities" 
ON public.experience_entities FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations for destination_experience_profiles" ON public.destination_experience_profiles;
CREATE POLICY "Allow all operations for destination_experience_profiles" 
ON public.destination_experience_profiles FOR ALL USING (true) WITH CHECK (true);

