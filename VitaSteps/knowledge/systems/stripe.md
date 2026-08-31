---
id: stripe
type: system
name: Stripe
status: active
description: Payment gateway handling credit card, Apple Pay, Google Pay transactions, live balance retrieval, and payout tracking.
code:
  - landing_predikalo1/api/checkout.js
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/checkout.html
related:
  - "[[order]]"
  - "[[revolut]]"
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[dynamic-pricing|Dynamic Pricing]]"
  - "[[ADR-002-webhook-free-payment|ADR-002]]"
  - "[[ADR-007-revolut-stripe-cashflow-integration|ADR-007 Revolut & Stripe Cashflow]]"
---

# System: Stripe Payments

Stripe handles all direct payment processing, payout scheduling, and transaction ledger recording on VitaSteps.

## Implementation Details
* **Checkout Session Creation (`api/create-checkout-session.js`):** Builds session with dynamic line items (Entry fee $\times$ quantity + optional home delivery fee - referral discount).
* **Metadata Payload:** Packs participant names, emails, delivery locker ID, and billing details directly into Stripe session metadata.
* **Fulfillment:** The post-payment pipeline is triggered client-side from `siker.html` upon successful redirect via `api/process-payment.js`.
* **Fee Structure:** Standard Stripe EU card processing fee (approx. **1.5% + 50 HUF**).
* **Live Balance & Payout API (`api/admin-data.js`):**
  * Live available & pending balances in HUF via `stripe.balance.retrieve()`.
  * Detailed balance transaction ledger via `stripe.balanceTransactions.list()`.
  * Automated bank account payout logs via `stripe.payouts.list()`.
