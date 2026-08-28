---
id: checkout-pipeline
type: process
name: Checkout Pipeline
status: active
description: End-to-end post-payment registration, e-invoicing, and onboarding workflow.
code:
  - landing_predikalo1/checkout.html
  - landing_predikalo1/api/checkout.js
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/siker.html
related:
  - "[[stripe]]"
  - "[[supabase]]"
  - "[[szamlazz-hu|Szamlazz.hu]]"
  - "[[ADR-002-webhook-free-payment|ADR-002]]"
---

# Process: Checkout Pipeline

```text
User on checkout.html
       │ (Select quantity, locker, billing)
       ▼
api/create-checkout-session.js
       │ (Creates Stripe Session with metadata)
       ▼
Stripe Hosted Payment
       │ (Card / Apple Pay / Google Pay)
       ▼
siker.html?session_id=cs_...
       │ (Auto-invokes post-payment processor)
       ▼
api/process-payment.js
       ├─► 1. Verifies Stripe session & idempotency
       ├─► 2. Upserts runner in Supabase (runners table)
       ├─► 3. Creates order & assigns sequential serial rank
       ├─► 4. Issues NAV-compliant E-Invoice via Számlázz.hu
       ├─► 5. Sends Welcome Email (magic link + GPX pack)
       └─► 6. Returns success payload to siker.html
```

## Resilience & Idempotency
* If the user reloads `siker.html`, `process-payment.js` checks `orders.stripe_session_id`. If already processed, it returns existing record without duplicating runs or invoices.
