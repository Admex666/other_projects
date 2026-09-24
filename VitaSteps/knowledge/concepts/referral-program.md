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
* **Invited Friend:** Gets an immediate **10% discount** when entering the code / referral link during [[checkout-pipeline|Checkout Pipeline]].
* **Referring Runner:** Earns progressive discounts towards their next challenge:
  - 👤 1 friend: **10%** discount
  - 👥 2 friends: **25%** discount
  - 🏔️ 3 friends: **45%** discount
  - 🎯 4 friends: **70%** discount
  - 🏆 5 friends: **100% FREE** medal & entry
* **Tracking:** Recorded in Supabase `runners.referred_by` and validated dynamically via Stripe checkout session metadata.
