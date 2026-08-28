---
id: order-fulfillment
type: process
name: Order Fulfillment
status: active
description: Package consolidation, packing guide generation, and Foxpost locker dispatch.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/create-foxpost-parcels.js
  - landing_predikalo1/scripts/daily_tracking.py
related:
  - "[[foxpost]]"
  - "[[run]]"
  - "[[ADR-004-consolidated-shipping|ADR-004]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# Process: Order Fulfillment (Csomagolás és Postázás)

```text
Approved Runs (completed = true, shipped = false)
       │
       ▼
Admin Panel: 🦊 Logisztika (Foxpost)
       │
       ├─► 📦 Csomagolási és Kiszállítási Segédlet:
       │     - Groups multi-medal runs by recipient email / locker / ship_together_with
       │     - Displays exact itemized breakdown (e.g. 1x Prédikálószék [#006], 1x Nagy-Kevély [#006-PK])
       │     - Physical packing of envelopes/boxes
       │
       ▼
api/create-foxpost-parcels.js (Bulk API upload)
       ├─► 1. Merges grouped runs into 1 single Foxpost parcel
       ├─► 2. Receives Foxpost barcode & tracking code (CLFOX...)
       ├─► 3. Updates Supabase shipments (tracking_code, shipped=true)
       └─► 4. Prints combined shipping labels
       │
       ▼
scripts/daily_tracking.py (GitHub Actions Daily Cron)
       ├─► Polls Foxpost parcel lifecycle (in transit -> delivered)
       └─► Sends post-delivery follow-up / review request emails
```
