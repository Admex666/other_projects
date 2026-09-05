---
id: supabase
type: system
name: Supabase
status: active
description: Primary managed PostgreSQL relational database, authentication, and file storage backend.
source:
  type: database
  ref: https://ncsathcqpvlrygkphced.supabase.co
code:
  - landing_predikalo1/api/
  - landing_predikalo1/portal.html
  - landing_predikalo1/admin.html
related:
  - "[[customer]]"
  - "[[run]]"
  - "[[order]]"
  - "[[ADR-001-supabase-migration|ADR-001]]"
  - "[[ADR-005-strict-rls-security|ADR-005]]"
---

# System: Supabase (PostgreSQL & Storage)

Supabase serves as the persistent single source of truth for all VitaSteps operational and customer data.

## Relational Schema Architecture
* **`runners`:** User profiles (`id`, `email`, `name`, `phone`, `referral_code`, `referred_by`, `is_test`).
* **`orders`:** Financial transactions (`id`, `runner_id`, `stripe_session_id`, `amount`, `quantity`, `billing_name`, `billing_address`, `invoice_number`).
* **`runs`:** Challenge registrations (`id`, `runner_id`, `order_id`, `campaign`, `serial_number`, `serial_rank`, `proof_submitted`, `proof_urls`, `completed`, `completion_date`, `diploma_url`, `ship_together_with`).
* **`shipments`:** Logistics records (`id`, `run_id`, `method`, `parcel_id`, `parcel_name`, `home_address`, `phone`, `shipped`, `shipped_at`, `tracking_code`).
* **`feedbacks`:** Post-challenge ratings and reviews.
* **`leads`:** Captured prospective runners from gated landing page content (`id`, `email` $\rightarrow$ `runners.email`, `name`, `campaign`, `source`, `converted`, `converted_at`, `created_at`).
* **`meta_daily_metrics`:** Daily aggregated ad spend, revenue, and ROAS.
* **`marketing_targets`:** Target CAC, ROAS, and unit thresholds per campaign.

## Storage Buckets
* `proofs`: User GPX track uploads and summit selfie photos (restricted read/write).

## Security & Row-Level Security (RLS)
* Public anonymous access is locked down. Customer portal queries are scoped strictly to the authenticated user's email (`auth.jwt() ->> 'email' = email`).
* Admin operations use serverless Vercel endpoints authenticated via `ADMIN_SECRET` using the `service_role` key.
