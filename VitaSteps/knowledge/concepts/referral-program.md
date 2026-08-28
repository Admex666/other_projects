---
id: referral-program
type: concept
name: Referral Program
status: active
description: Organic customer acquisition through bilateral reward codes.
code:
  - landing_predikalo1/portal.html
  - landing_predikalo1/checkout.html
  - landing_predikalo1/api/process-payment.js
related:
  - "[[customer]]"
  - "[[dynamic-pricing|Dynamic Pricing]]"
  - "[[cac]]"
---

# Concept: Referral Program (Ajánlói Rendszer)

Every registered runner receives a unique 6-character referral code (e.g. `ADAM66`) accessible in their [[customer]] portal.

## Mechanics
* **Invited Friend:** Gets an immediate **1 000 HUF discount** when entering the code during [[checkout-pipeline|Checkout Pipeline]].
* **Referring Runner:** Earns a **1 000 HUF credit** / payout reward per successful completion.
* **Tracking:** Recorded in Supabase `runners.referred_by` and validated dynamically via Stripe checkout session metadata.
