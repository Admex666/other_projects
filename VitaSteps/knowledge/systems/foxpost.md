---
id: foxpost
type: system
name: Foxpost
status: active
description: Automated parcel locker logistics network and shipping API.
source:
  type: api
  endpoint: https://api.foxpost.hu/
code:
  - landing_predikalo1/api/create-foxpost-parcels.js
  - landing_predikalo1/scripts/daily_tracking.py
  - landing_predikalo1/admin.html
related:
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[ADR-004-consolidated-shipping|ADR-004]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# System: Foxpost Logistics

Foxpost is the primary shipping provider for physical medal fulfillment in Hungary.

## Key Integration Points
1. **Locker Selection Widget:** Embedded in `checkout.html` for picking the nearest automated parcel locker (`parcel_id`, `parcel_name`).
2. **Direct Bulk API Parcel Creation (`api/create-foxpost-parcels.js`):** Creates consolidated shipments directly from `admin.html`, returning barcode labels and tracking codes (`CLFOX...`).
3. **Daily Lifecycle Cron (`scripts/daily_tracking.py`):** Runs daily via GitHub Actions to sync parcel state transitions:
   - `created` $\rightarrow$ `in_transit` $\rightarrow$ `arrived_in_locker` $\rightarrow$ `delivered` $\rightarrow$ triggers review feedback email.
4. **Unit Shipping Cost:** Base locker shipping fee is **1 141 HUF + VAT = ~1 250 HUF / parcel**.
