---
id: order-fulfillment
type: process
name: Order Fulfillment
status: active
description: Package consolidation, packing guide generation, Foxpost batch validation, and dispatch.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/js/admin-logistics.js
  - landing_predikalo1/css/admin.css
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

The admin logistics dashboard (`admin.html` → 🦊 Logisztika) uses a **three-stage status flow**:

```text
┌─────────────────────────────────────────────────────────────┐
│  1️⃣  Feladandó (To Ship)                                    │
│  completed = true  AND  shipments.shipped = false           │
│  → Approved runs waiting for packaging & Foxpost dispatch   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  📦 Csomagolási és Kiszállítási Segédlet                    │
│  - Groups multi-medal runs by recipient email / locker /    │
│    ship_together_with                                       │
│  - Displays itemized breakdown per package                  │
│  - Visual warning (⚠️) & inline editor (✏️) for missing     │
│    phone numbers or lockers                                 │
│                                                             │
│  🦊 Foxpost API Feladás (api/create-foxpost-parcels.js)     │
│  ├─ 1. Pre-validates phone numbers & locker codes           │
│  ├─ 2. Merges grouped runs into 1 Foxpost parcel            │
│  ├─ 3. Receives CLFOX... barcode & tracking code            │
│  └─ 4. Updates shipments (tracking_code, shipped=true,      │
│         shipped_at=now)                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2️⃣  Már feladva (Shipped / In Transit)                     │
│  shipments.shipped = true  AND  shipments.received_at = NULL│
│  → Parcels en route or waiting in Foxpost locker            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  scripts/daily_tracking.py (GitHub Actions Daily Cron)      │
│  ├─ Polls Foxpost parcel lifecycle (RECEIVE / HDRECEIVE)    │
│  └─ Updates shipments.received_at & runs.received_date      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3️⃣  Megérkezett (Received / Delivered)                     │
│  shipments.received_at IS NOT NULL                          │
│  → Parcel collected from locker by recipient                │
└─────────────────────────────────────────────────────────────┘
```

## Implementation
* **Frontend:** `js/admin-logistics.js` — toolbar buttons filter `allRuns` client-side using `isRunShipped()` and `isRunReceived()` helpers.
* **CSS badges:** `.badge-shipped` (blue), `.badge-received` (green) in `css/admin.css`.
* **Code files:** see frontmatter `code:` references.

