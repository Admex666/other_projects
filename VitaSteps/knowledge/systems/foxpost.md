---
id: foxpost
type: system
name: Foxpost
status: active
description: Automated parcel locker logistics network, batch API dispatch, and lifecycle tracking.
source:
  type: api
  endpoint: https://webapi.foxpost.hu/api
code:
  - landing_predikalo1/api/create-foxpost-parcels.js
  - landing_predikalo1/scripts/daily_tracking.py
  - landing_predikalo1/admin.html
related:
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[ADR-004-consolidated-shipping|ADR-004 Consolidated Shipping]]"
  - "[[ADR-008-foxpost-batch-resilience|ADR-008 Foxpost Batch Resilience]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# System: Foxpost Logistics

Foxpost is the primary shipping provider for physical medal fulfillment in Hungary.

## Key Integration Points
1. **Locker Selection Widget:** Embedded in `checkout.html` for picking the nearest automated parcel locker (`parcel_id`, `parcel_name`).
2. **Direct Bulk API Parcel Creation (`api/create-foxpost-parcels.js`):**
   * Pre-validates Hungarian mobile phone numbers and locker IDs before dispatch.
   * Isolates validation errors to prevent single-order malformations from rejecting entire batches.
   * Returns generated `CLFOX...` barcodes and assigns them to Supabase `shipments.tracking_code`.
3. **Daily Lifecycle Cron (`scripts/daily_tracking.py`):** Runs daily to sync parcel state transitions:
   * `created` $\rightarrow$ `in_transit` $\rightarrow$ `arrived_in_locker` $\rightarrow$ `delivered` $\rightarrow$ triggers review feedback email.
4. **Unit Shipping Cost:** Base locker shipping fee is **1 141 HUF + VAT = ~1 250 HUF / parcel**.
