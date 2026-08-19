-- ============================================================
-- VITASTEPS SUPABASE DATABASE SCHEMA (SECURED WITH RLS)
-- ============================================================

-- 1. Enable RLS on ALL public tables
ALTER TABLE public.runners ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meta_daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.marketing_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipments ENABLE ROW LEVEL SECURITY;

-- 2. Drop any legacy insecure or open policies
DROP POLICY IF EXISTS "Allow all actions for service role on runners" ON public.runners;
DROP POLICY IF EXISTS "Allow all actions for service role on runs" ON public.runs;
DROP POLICY IF EXISTS "Allow all actions for service role on orders" ON public.orders;
DROP POLICY IF EXISTS "Allow all actions for service role on shipments" ON public.shipments;
DROP POLICY IF EXISTS "Allow all actions for service role on feedbacks" ON public.feedbacks;
DROP POLICY IF EXISTS "Users can view their own profile" ON public.runners;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.runners;
DROP POLICY IF EXISTS "Users can view their own runs" ON public.runs;
DROP POLICY IF EXISTS "Users can view runs they referred" ON public.runs;
DROP POLICY IF EXISTS "Users can view their own orders" ON public.orders;
DROP POLICY IF EXISTS "Users can view their own shipments" ON public.shipments;
DROP POLICY IF EXISTS "Users can insert their own feedback" ON public.feedbacks;
DROP POLICY IF EXISTS "Users can view their own feedback" ON public.feedbacks;

-- 3. Define Clean, Secure Policies for Authenticated Portal Users (auth.jwt())

-- RUNNERS: Authenticated users can only view and update their own profile
CREATE POLICY "Users can view their own profile" ON public.runners
  FOR SELECT TO authenticated
  USING ((auth.jwt() ->> 'email') = email);

CREATE POLICY "Users can update their own profile" ON public.runners
  FOR UPDATE TO authenticated
  USING ((auth.jwt() ->> 'email') = email);

-- RUNS: Authenticated users can only view their own runs or runs they referred
CREATE POLICY "Users can view their own runs" ON public.runs
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.runners
      WHERE public.runners.id = public.runs.runner_id
      AND (auth.jwt() ->> 'email') = public.runners.email
    )
  );

CREATE POLICY "Users can view runs they referred" ON public.runs
  FOR SELECT TO authenticated
  USING (
    referred_by = (auth.jwt() ->> 'email')
  );

-- SHIPMENTS: Authenticated users can view shipments linked to their own runs
CREATE POLICY "Users can view their own shipments" ON public.shipments
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.runs
      JOIN public.runners ON public.runners.id = public.runs.runner_id
      WHERE public.runs.id = public.shipments.run_id
      AND (auth.jwt() ->> 'email') = public.runners.email
    )
  );

-- FEEDBACKS: Authenticated users can insert and view their own feedbacks
CREATE POLICY "Users can insert their own feedback" ON public.feedbacks
  FOR INSERT TO authenticated
  WITH CHECK ((auth.jwt() ->> 'email') = runner_email);

CREATE POLICY "Users can view their own feedback" ON public.feedbacks
  FOR SELECT TO authenticated
  USING ((auth.jwt() ->> 'email') = runner_email);

-- 4. ORDERS, META_DAILY_METRICS, MARKETING_TARGETS:
-- These tables have RLS enabled with NO public/anon policies.
-- They are strictly accessible only by the backend via SUPABASE_SERVICE_ROLE_KEY.
