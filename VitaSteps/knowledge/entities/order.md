---
id: order
type: entity
name: Order
status: active
description: Payment transaction record originating from Stripe Checkout.
source:
  type: database
  ref: supabase.public.orders
code:
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/checkout.html
related:
  - "[[customer]]"
  - "[[run]]"
  - "[[stripe]]"
  - "[[szamlazz-hu|Szamlazz.hu]]"
used_by:
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[unit-economics|Unit Economics]]"
---

# Order (Rendelés)

An **Order** represents a successful monetary transaction. It captures the quantity of medals purchased, billing details for the e-invoice, and metadata for multi-runner registrations.

## Data Model (Supabase `orders` table)
* `id`: UUID (Primary Key)
* `runner_id`: UUID (Foreign Key $\rightarrow$ `runners.id`)
* `campaign`: String (`predikaloszek`, `pilis`)
* `stripe_session_id`: String (Unique Stripe Checkout Session ID; ensures idempotency)
* `amount`: Integer (Gross amount in HUF, e.g. 7990, 15980)
* `currency`: String (`huf`)
* `quantity`: Integer (Total medals purchased in this order)
* `billing_name`: String (Name for Számlázz.hu invoice)
* `billing_address`: String (Full billing address)
* `billing_tax_number`: String (Optional company tax number)
* `invoice_number`: String (Issued e-invoice number from [[szamlazz-hu|Szamlazz.hu]])
* `created_at`: Timestamp
