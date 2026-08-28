---
id: ADR-002
type: decision
name: ADR-002 Client-Triggered Post-Payment Processing
status: accepted
date: 2026-07-16
replaces: null
related:
  - "[[stripe]]"
  - "[[checkout-pipeline|Checkout Pipeline]]"
---

# Decision: Client-Triggered Post-Payment Processing

## Context
Standard Stripe integrations rely on Stripe Webhooks. However, on the free Stripe plan, registering public webhook endpoints has operational constraints and local dev complexity.

## Decision
Implement a secure, idempotent post-payment pipeline in `api/process-payment.js` triggered from `siker.html` upon user redirect with the `session_id` query parameter.

## Consequences
* Highly reliable: Works out-of-the-box in local development, Vercel preview environments, and production without webhook setup.
* Idempotency is strictly enforced by checking `orders.stripe_session_id` in Supabase prior to creating runs or generating invoices.
