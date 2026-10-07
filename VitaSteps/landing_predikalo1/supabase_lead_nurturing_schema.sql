-- ============================================================================
-- VITASTEPS LEAD NURTURING ENGINE V1 (SQL SCHEMA & MIGRATION)
-- ============================================================================
-- Futtasd le ezt a scriptet a Supabase SQL Editorban.
-- Biztonságosan kiegészíti a 'leads' táblát az automatikus sequence mezőkkel,
-- és lezártként jelöli a 2026. október 1. előtt keletkezett régi (legacy) leadeket.
-- ============================================================================

-- 1. Új mezők hozzáadása a meglévő 'leads' táblához
ALTER TABLE public.leads
    ADD COLUMN IF NOT EXISTS sequence TEXT DEFAULT 'lead_nurture_v1',
    ADD COLUMN IF NOT EXISTS sequence_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_sequence_step INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_sequence_sent_at TIMESTAMPTZ;

-- 2. Régi leadek lezárása (2026-10-01 előttiek):
-- Őket a sequence végére (10. lépés) állítjuk, hogy a GitHub Action véletlenül se küldjön nekik új emaileket!
UPDATE public.leads
SET sequence = 'lead_nurture_v1',
    last_sequence_step = 10,
    sequence_started_at = COALESCE(sequence_started_at, created_at),
    last_sequence_sent_at = COALESCE(last_sequence_sent_at, created_at)
WHERE created_at < '2026-10-01T00:00:00Z'
  AND (last_sequence_step IS NULL OR last_sequence_step = 0);

-- 3. Új leadek (2026-10-01 utániak) alapállapotának inicializálása (ha még üres)
UPDATE public.leads
SET sequence = COALESCE(sequence, 'lead_nurture_v1'),
    sequence_started_at = COALESCE(sequence_started_at, created_at),
    last_sequence_step = COALESCE(last_sequence_step, 0),
    last_sequence_sent_at = COALESCE(last_sequence_sent_at, created_at)
WHERE created_at >= '2026-10-01T00:00:00Z'
  AND sequence_started_at IS NULL;

-- 4. Index létrehozása a gyors lekérdezésekhez a napi automatizmusban
CREATE INDEX IF NOT EXISTS idx_leads_nurture_lookup
    ON public.leads (converted, unsubscribed, last_sequence_step, created_at);
