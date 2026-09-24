---
id: run
type: entity
name: Run
status: active
description: A specific challenge entry instance linked to a runner and a limited serial medal number.
source:
  type: database
  ref: supabase.public.runs
code:
  - landing_predikalo1/api/process-payment.js
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/portal.html
  - landing_predikalo1/admin.html
related:
  - "[[customer]]"
  - "[[order]]"
  - "[[campaign-predikaloszek|Campaign Predikaloszek]]"
  - "[[campaign-nagykevely|Campaign Nagy-Kevely]]"
  - "[[medal]]"
used_by:
  - "[[proof-verification|Proof Verification]]"
  - "[[order-fulfillment|Order Fulfillment]]"
---

# Run (Challenge Entry / Teljesítés)

A **Run** represents a single paid participation in a specific VitaSteps challenge. It is assigned a strictly limited, unique serial number (e.g. `#006/100` or `#006/100-PK`). The serial number belongs to the **run entry** — the physical medals themselves are **not** individually numbered.

## Lifecycle States
1. **Registered / Pending (`!proof_submitted && !completed`):** The runner has purchased entry and received their welcome pack and GPX/guidebook.
2. **Proof Submitted (`proof_submitted = true && !completed`):** The runner completed the route and uploaded their GPX track or photos via [[proof-verification|Proof Verification]].
3. **Approved / Completed (`completed = true`):** The verification was approved in [[admin-panel|Admin Panel]]. Diploma is generated and congratulatory email is sent.
4. **To Ship / Feladandó (`completed = true && shipments.shipped = false`):** Approved but not yet dispatched. Appears in the admin logistics "Feladandó" tab.
5. **Shipped / Már feladva (`shipments.shipped = true && !shipments.received_at`):** The physical medal has been packaged and dispatched via [[foxpost]]. Appears in the "Már feladva" tab.
6. **Received / Megérkezett (`shipments.received_at IS NOT NULL`):** The parcel has been collected from the Foxpost locker. Tracked automatically by `daily_tracking.py`. Appears in the "Megérkezett" tab.

## Data Model (Supabase `runs` table)
* `id`: UUID (Primary Key)
* `runner_id`: UUID (Foreign Key $\rightarrow$ `runners.id`)
* `order_id`: UUID (Foreign Key $\rightarrow$ `orders.id`)
* `campaign`: String (`predikaloszek`, `pilis`)
* `serial_number`: String (e.g. `#001/100`, `#012/100-PK`)
* `serial_rank`: Integer (Sequential order rank within the campaign)
* `name`: String (Name on the diploma)
* `proof_submitted`: Boolean
* `proof_submitted_at`: Timestamp
* `proof_urls`: Array of Strings (Supabase Storage URLs of GPX and photo proofs)
* `completed`: Boolean
* `completion_date`: String (`YYYY.MM.DD`)
* `diploma_url`: String (Direct URL to the generated online diploma)
* `received_date`: Timestamp (Set by `daily_tracking.py` when Foxpost confirms locker pickup)
* `ship_together_with`: String (Optional email of partner for combined shipping)
