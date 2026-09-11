-- ====================================================================
-- OPTIVOYA EXPERIENCE & ACTIVITY INTELLIGENCE ENGINE
-- Supabase PostgreSQL Migration / Schema
-- Execute this SQL in your Supabase SQL Editor (1 click)
-- ====================================================================

-- 1. Raw Source Records (Audit-proof Ingestion Store)
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


-- 2. Experience Entities (Canonical Resolved Places, Activities & Attractions)
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


-- 3. Destination Experience Profiles (Pre-aggregated Rollups for Instant <5ms Matcher Lookup)
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


-- 4. Enable Row Level Security (RLS) & Policies
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
