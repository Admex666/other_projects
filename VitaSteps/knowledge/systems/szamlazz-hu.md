---
id: szamlazz-hu
type: system
name: Szamlazz.hu
status: active
description: Automated electronic invoicing system compliant with Hungarian NAV regulations.
source:
  type: api
  endpoint: https://www.szamlazz.hu/szamla/
code:
  - landing_predikalo1/api/process-payment.js
related:
  - "[[order]]"
  - "[[checkout-pipeline|Checkout Pipeline]]"
---

# System: Számlázz.hu E-Invoicing

Számlázz.hu automatically issues NAV-compliant electronic PDF invoices for every paid order.

## Integration Workflow
* Executed inside `api/process-payment.js` via the Számlázz.hu Agent XML API.
* **Line Items:**
  - Challenge entry (e.g. `Prédikálószék Vertical Nevezési díj`, `Nagy-Kevély csillagai Nevezési díj`).
  - Home delivery fee (if selected).
  - Referral discount credit (if applied).
* **Delivery:** Invoice PDF is stored on Számlázz.hu and emailed directly to the buyer's billing email.
* **Database Tracking:** The generated `invoice_number` is saved in `orders.invoice_number`.
