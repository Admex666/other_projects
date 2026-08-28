---
id: customer
type: entity
name: Customer
status: active
description: Unique participant / hiker registered in VitaSteps.
source:
  type: database
  ref: supabase.public.runners
code:
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/portal.html
related:
  - "[[run]]"
  - "[[order]]"
  - "[[referral-program|Referral Program]]"
used_by:
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[proof-verification|Proof Verification]]"
---

# Customer (Runner / Nevező)

A **Customer** represents an individual participant in the VitaSteps ecosystem. A customer is identified by their unique email address and can participate in multiple challenges over time.

## Data Model (Supabase `runners` table)
* `id`: UUID (Primary Key)
* `email`: String (Unique, case-insensitive lowercase)
* `name`: String (Participant full name)
* `phone`: String (E.164 formatted contact phone)
* `referral_code`: String (Unique 6-character referral code generated upon first registration)
* `referred_by`: String (Referral code of the customer who invited them, if any)
* `is_test`: Boolean (Excludes internal test purchases from rankings and analytics)
* `created_at`: Timestamp

## Relationships
* Has many [[run]] instances (one per challenge entry).
* Has many [[order]] instances (payment checkout sessions).
* Can earn referral credits via [[referral-program|Referral Program]].
