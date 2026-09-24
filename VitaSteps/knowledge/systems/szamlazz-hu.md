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
* Executed inside `api/process-payment.js` and `api/stripe-webhook.js` via the Számlázz.hu Agent XML API (`https://www.szamlazz.hu/szamla/`).
* **Line Items (Egységes Tételmegnevezések):**
  - Nagy-Kevély érem: `Nagy-Kevély csillagai érem`
  - Prédikálószék érem: `Prédikálószék érem`
  - Házhozszállítás: `Házhozszállítás (Magyar Posta)` (1 200 Ft)
  - Stripe dinamikus kedvezmények: A Stripe Checkout session pontos tételsorából (`stripeItems`) olvassa be a végső fizetett összeget, így az ajánlói és kupon kedvezmények cent / forint pontosan, AAM adókulccsal kerülnek a számlára.
* **Delivery:** Invoice PDF is stored on Számlázz.hu and emailed directly to the buyer's billing email.
* **Database Tracking:** The generated `invoice_number` is saved in `orders.invoice_number`.
