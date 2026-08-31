---
id: order-fulfillment
type: process
name: Order Fulfillment
status: active
description: Package consolidation, packing guide generation, Foxpost batch validation, and dispatch.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/create-foxpost-parcels.js
  - landing_predikalo1/scripts/daily_tracking.py
related:
  - "[[foxpost]]"
  - "[[run]]"
  - "[[ADR-004-consolidated-shipping|ADR-004 Consolidated Shipping]]"
  - "[[ADR-008-foxpost-batch-resilience|ADR-008 Foxpost Batch Resilience]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# Process: Order Fulfillment (Csomagolás és Postázás)

```text
Approved Runs (completed = true, shipments.shipped = false)
       │
       ▼
Admin Panel: 🦊 Logisztika (Foxpost)
       │
       ├─► 📦 Csomagolási és Kiszállítási Segédlet:
       │     - Groups multi-medal runs by recipient email / locker / ship_together_with
       │     - Displays exact itemized breakdown (e.g. 1x Prédikálószék [#006], 1x Nagy-Kevély [#006-PK])
       │     - Visual warning (⚠️) & inline editor (✏️) for missing phone numbers or lockers
       │
       ▼
api/create-foxpost-parcels.js (Batch API upload with Error Isolation)
       ├─► 1. Pre-validates phone numbers & locker codes (isolates any invalid entry)
       ├─► 2. Merges grouped runs into 1 single Foxpost parcel
       ├─► 3. Receives Foxpost barcode & tracking code (CLFOX...)
       ├─► 4. Updates Supabase shipments table (tracking_code, shipped=true, shipped_at=now)
       └─► 5. Prints combined shipping labels
       │
       ▼
scripts/daily_tracking.py (GitHub Actions Daily Cron)
       ├─► Polls Foxpost parcel lifecycle (in transit -> delivered)
       └─► Updates shipments.received=true & sends post-delivery review request emails
```
