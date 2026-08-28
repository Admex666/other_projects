---
id: ADR-004
type: decision
name: ADR-004 Consolidated Shipping & Itemized Packing Guide
status: accepted
date: 2026-08-28
replaces: null
related:
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[foxpost]]"
  - "[[unit-economics|Unit Economics]]"
---

# Decision: Consolidated Shipping & Itemized Packing Guide

## Context
Many runners participate in pairs/groups or purchase entries for multiple consecutive challenges (e.g. Prédikálószék and Nagy-Kevély) before shipping. Creating separate parcels incurs redundant Foxpost shipping fees (~1 250 HUF each) and multiple locker pickups for the customer.

## Decision
1. In `admin.html` and `api/create-foxpost-parcels.js`, automatically consolidate all unfulfilled runs for the same recipient (matching email, destination locker, or `ship_together_with`) into a single Foxpost parcel.
2. Render an itemized **Csomagolási és Kiszállítási Segédlet** (Packing Guide) in `admin.html` clearly specifying the exact count and serial numbers of each campaign's medals needed per parcel.

## Consequences
* Saves ~1 250 HUF per merged medal, boosting net profit contribution to $> 70\%$.
* Prevents human packing errors through visual badge breakdowns.
