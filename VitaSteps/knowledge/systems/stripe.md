---
id: stripe
type: system
name: Stripe
status: active
description: Payment gateway handling credit card, Apple Pay, and Google Pay transactions.
code:
  - landing_predikalo1/api/checkout.js
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/checkout.html
related:
  - "[[order]]"
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[dynamic-pricing|Dynamic Pricing]]"
  - "[[ADR-002-webhook-free-payment|ADR-002]]"
---

# System: Stripe Payments

Stripe handles all direct payment processing on VitaSteps.

## Implementation Details
* **Checkout Session Creation (`api/create-checkout-session.js`):** Builds session with dynamic line items (Entry fee $\times$ quantity + optional home delivery fee - referral discount).
* **Metadata Payload:** Packs participant names, emails, delivery locker ID, and billing details directly into Stripe session metadata.
* **Fulfillment:** Due to free-tier webhook limitations, the post-payment pipeline is triggered client-side from `siker.html` upon successful redirect via `api/process-payment.js`.
* **Fee Structure:** Standard Stripe EU processing fee: **1.5% + 50 HUF** per transaction.
