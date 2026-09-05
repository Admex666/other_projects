-- ==========================================================
-- 1. LEADS TÁBLA BŐVÍTÉSE ÉS ÖSSZEKÖTÉSE A RUNNERS TÁBLÁVAL
-- ==========================================================

-- Konverziós státusz és időpont hozzáadása a leads táblához
ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS converted boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS converted_at timestamp with time zone;

-- Foreign Key kapcsolat létrehozása az email mező alapján:
-- Ez lehetővé teszi a közvetlen JOIN lekérdezéseket (pl. leads -> runners -> runs/orders)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_leads_runners_email'
    ) THEN
        ALTER TABLE public.leads 
        ADD CONSTRAINT fk_leads_runners_email 
        FOREIGN KEY (email) REFERENCES public.runners(email) 
        ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;
END $$;

-- Index a gyors szűrésekhez
CREATE INDEX IF NOT EXISTS idx_leads_email ON public.leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_converted ON public.leads(converted);

-- ==========================================================
-- 2. KÉNYELMI NÉZET (VIEW): LEADS ÉS KONVERZIÓK ÁTTEKINTÉSE
-- ==========================================================
CREATE OR REPLACE VIEW public.leads_conversion_overview AS
SELECT 
    l.id AS lead_id,
    l.email,
    l.name AS lead_name,
    l.campaign,
    l.source,
    l.created_at AS registered_at,
    COALESCE(l.converted, (r.id IS NOT NULL AND count(runs.id) > 0)) AS has_converted,
    l.converted_at,
    count(runs.id) AS total_runs_purchased,
    min(runs.created_at) AS first_purchase_at
FROM public.leads l
LEFT JOIN public.runners r ON LOWER(l.email) = LOWER(r.email)
LEFT JOIN public.runs runs ON r.id = runs.runner_id
GROUP BY l.id, l.email, l.name, l.campaign, l.source, l.created_at, l.converted, l.converted_at, r.id;
