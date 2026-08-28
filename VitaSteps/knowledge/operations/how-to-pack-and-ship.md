---
id: how-to-pack-and-ship
type: operation
name: How to Pack and Ship Medals
status: active
description: Operational runbook for packaging medals using the admin packing guide and Foxpost bulk API.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/create-foxpost-parcels.js
related:
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[foxpost]]"
  - "[[ADR-004-consolidated-shipping|ADR-004]]"
---

# Operation: How to Pack and Ship Medals

Follow this procedure when preparing a physical shipping batch:

## Step 1: Open Admin Logistics Panel
1. Open `admin.html` in your browser and enter the admin password (`vitasteps2026admin`).
2. Click the **🦊 Logisztika (Foxpost)** tab.

## Step 2: Review Packing Guide
1. Click to expand **📦 Csomagolási és Kiszállítási Segédlet** at the top.
2. For each package listed:
   - Check the exact campaign and medal serial numbers needed (e.g. `1x 🏔️ Prédikálószék (#006/100) + 1x 🌌 Nagy-Kevély (#006/100-PK)`).
   - Place the corresponding physical numbered medals into the padded envelope or box.

## Step 3: Dispatch via Foxpost API
1. In the logistics table below, select the checkboxes for the packages you have prepared.
2. Click the **🦊 Foxpost API Feladás** button.
3. Confirm the dialog prompt. The system will create the parcels in Foxpost, retrieve barcodes, update tracking codes in Supabase, and mark the items as `Feladva` (Shipped).
4. Print the generated Foxpost labels and drop the packages at your local Foxpost locker.
