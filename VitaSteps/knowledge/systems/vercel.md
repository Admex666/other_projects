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
* `create-checkout-session.js`: Generates Stripe Checkout sessions.
* `process-payment.js`: Validates Stripe payments, registers users in Supabase, issues invoices, and dispatches welcome emails.
* `submit-proof.js`: Uploads verification photos/GPX files to Supabase Storage.
* `admin-data.js`: Authenticated backend endpoint fetching admin lists, runs, and marketing targets.
* `admin-approve.js`: Handles run verification, manual approval, rejection, and manual shipping marks.
* `create-foxpost-parcels.js`: Communicates directly with Foxpost API for automated parcel dispatch.
