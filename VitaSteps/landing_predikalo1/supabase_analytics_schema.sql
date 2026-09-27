-- ============================================================================
-- VITASTEPS ANALYTICS & ATTRIBUTION ENGINE (SQL SCHEMA)
-- ============================================================================
-- Futtasd le ezt a scriptet a Supabase SQL Editorban (vagy Migrations-ben).
-- Létrehozza a látogatói, session és esemény-szintű funnel mérési táblákat.
-- ============================================================================

-- 1. ANALYTICS VISITORS (Multi-touch attribution & Visitor Identity)
CREATE TABLE IF NOT EXISTS public.analytics_visitors (
    visitor_id TEXT PRIMARY KEY,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_sessions INT DEFAULT 1,
    total_orders INT DEFAULT 0,
    total_revenue NUMERIC DEFAULT 0,
    
    -- First Touch Attribution (Honnan jött legelőször?)
    first_touch_source TEXT,
    first_touch_medium TEXT,
    first_touch_campaign_id TEXT,
    first_touch_campaign_name TEXT,
    first_touch_adset_id TEXT,
    first_touch_adset_name TEXT,
    first_touch_ad_id TEXT,
    first_touch_ad_name TEXT,
    first_touch_content TEXT,
    first_touch_fbclid TEXT,
    first_touch_landing_page TEXT,
    
    -- Last Touch Attribution (Honnan jött a legutóbb?)
    last_touch_source TEXT,
    last_touch_medium TEXT,
    last_touch_campaign_id TEXT,
    last_touch_campaign_name TEXT,
    last_touch_adset_id TEXT,
    last_touch_adset_name TEXT,
    last_touch_ad_id TEXT,
    last_touch_ad_name TEXT,
    last_touch_content TEXT,
    last_touch_fbclid TEXT,
    last_touch_landing_page TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. ANALYTICS SESSIONS (Session-level behavioral tracking & Raw metrics)
CREATE TABLE IF NOT EXISTS public.analytics_sessions (
    session_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL REFERENCES public.analytics_visitors(visitor_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Meta IDs (Primary) & Names (Metadata)
    meta_campaign_id TEXT,
    meta_campaign_name TEXT,
    meta_adset_id TEXT,
    meta_adset_name TEXT,
    meta_ad_id TEXT,
    meta_ad_name TEXT,
    
    -- UTM & Web parameters
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,
    fbclid TEXT,
    landing_page TEXT,
    referrer TEXT,
    device_type TEXT,
    browser TEXT,
    
    -- Raw Behavioral Metrics (Nyers viselkedési adatok)
    time_on_page INT DEFAULT 0,          -- Oldalon töltött idő másodpercben
    max_scroll_depth INT DEFAULT 0,       -- Max görgetési mélység százalékban (0-100)
    offer_viewed BOOLEAN DEFAULT FALSE,   -- Látta-e az ár/csomagajánlatot
    cta_clicked BOOLEAN DEFAULT FALSE,    -- Kattintott-e CTA gombra
    checkout_started BOOLEAN DEFAULT FALSE,
    checkout_completed BOOLEAN DEFAULT FALSE,
    purchase_completed BOOLEAN DEFAULT FALSE,
    
    -- Conversion linkage
    order_id TEXT,
    revenue NUMERIC DEFAULT 0,
    lead_email TEXT
);

-- 3. ANALYTICS EVENTS (Granular Step-by-Step Funnel Events)
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    event_name TEXT NOT NULL,             -- 'landing_session', 'engaged', 'offer_view', 'cta_click', 'checkout_start', 'purchase'
    event_data JSONB DEFAULT '{}'::jsonb, -- { scroll_depth, time_spent, button_id, button_text, price, order_id }
    meta_campaign_id TEXT,
    meta_adset_id TEXT,
    meta_ad_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. PERFORMANCE INDEXES (Villámgyors lekérdezésekhez)
CREATE INDEX IF NOT EXISTS idx_sessions_ad_id ON public.analytics_sessions(meta_ad_id);
CREATE INDEX IF NOT EXISTS idx_sessions_campaign_id ON public.analytics_sessions(meta_campaign_id);
CREATE INDEX IF NOT EXISTS idx_sessions_visitor_id ON public.analytics_sessions(visitor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON public.analytics_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_events_session_id ON public.analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_name ON public.analytics_events(event_name);
CREATE INDEX IF NOT EXISTS idx_events_ad_id ON public.analytics_events(meta_ad_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON public.analytics_events(created_at);
