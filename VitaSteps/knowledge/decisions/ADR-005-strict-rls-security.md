---
id: ADR-005
type: decision
name: ADR-005 Supabase Row-Level Security (RLS) Hardening
status: accepted
date: 2026-08-19
replaces: null
related:
  - "[[supabase]]"
  - "[[vercel]]"
---

# Decision: Supabase Row-Level Security (RLS) Hardening

## Context
Early prototypes used broad `using (true)` policies in Supabase, allowing client-side readers with the public anon key to read customer tables.

## Decision
1. Enable strict RLS across all tables (`runners`, `runs`, `orders`, `feedbacks`, `meta_daily_metrics`, `marketing_targets`, `shipments`).
2. Lock client queries strictly to authenticated JWT user emails (`auth.jwt() ->> 'email' = email`).
3. Route all administrative and aggregated dashboard operations through secure Vercel serverless endpoints (`/api/admin-data`, `/api/admin-approve`) authenticated with `ADMIN_SECRET` using `service_role` privileges.

## Consequences
* Complete GDPR and privacy compliance for customer personal data.
* Admin secrets remain strictly server-side and invisible to browser inspection.
