---
id: vercel
type: system
name: Vercel
status: active
description: Serverless backend API execution environment and frontend static web hosting.
code:
  - landing_predikalo1/api/
  - landing_predikalo1/package.json
related:
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[proof-verification|Proof Verification]]"
  - "[[supabase]]"
---

# System: Vercel Serverless Hosting

Vercel provides edge hosting and serverless Node.js backend execution for the VitaSteps web platform.

## Serverless API Functions (`landing_predikalo1/api/`)
> [!NOTE]
> **Vercel Hobby Plan Limit:** Maximum 12 Serverless Functions allowed per deployment. Keep total endpoints in `api/` <= 12.

* `checkout.js`: Generates Stripe Checkout sessions.
* `process-payment.js`: Validates Stripe payments, registers users in Supabase, issues invoices, and dispatches welcome emails.
* `stripe-webhook.js`: Fallback Stripe webhook handler.
* `capture-lead.js`: Captures email leads and triggers lead-magnet guidebook delivery.
* `submit-proof.js`: Uploads verification photos/GPX files to Supabase Storage.
* `submit-feedback.js`: Records user feedback and ratings in Supabase.
* `check-limit.js`: Checks real-time challenge slot availability and capacity.
* `check-referral-discount.js`: Calculates progressive and referral discounts.
* `leaderboard.js`: Serves public finisher leaderboard rankings.
* `admin-data.js`: Authenticated backend endpoint fetching admin lists, runs, and marketing targets.
* `admin-approve.js`: Handles run verification, manual approval, rejection, and manual shipping marks.
* `create-foxpost-parcels.js`: Communicates directly with Foxpost API for automated parcel dispatch.
