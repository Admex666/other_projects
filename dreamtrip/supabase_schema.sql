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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security) with public access policy for service role / anon API
ALTER TABLE public.beta_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.telemetry_events ENABLE ROW LEVEL SECURITY;

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
