---
id: ADR-006-multicampaign-unit-economics
type: decision
name: ADR-006 Multi-Campaign Unit Economics and Ad-Level Attribution
status: active
description: Architectural separation of challenge batch fixed costs and reliable ad-level creative metric synchronization.
date: 2026-08-31
deciders:
  - Adam
  - Antigravity AI
related:
  - "[[unit-economics|Unit Economics]]"
  - "[[break-even|Break-Even]]"
  - "[[meta-sync-pipeline|Meta Sync Pipeline]]"
  - "[[meta-ads|Meta Ads]]"
  - "[[admin-panel|Admin Panel]]"
---

# ADR-006: Multi-Campaign Unit Economics & Ad-Level Attribution

## Context
When introducing subsequent collectible challenges (e.g., *Nagy-Kevély csillagai* alongside *Prédikálószék Vertical*):
1. **Batch Capex Isolation:** Each medal series has an independent manufacturing run (100 medals @ 163 000 Ft + 30 000 Ft accounting = 193 000 Ft fixed cost). Merging all historical revenues into a single global 193 000 Ft break-even calculation created a false 100% payback status for newly launched campaigns.
2. **Creative Performance Attribution:** Supabase `meta_daily_metrics` table schema constraints previously caused ad-level records to fallback to campaign aggregates with null `ad_name` / `adset_name`.
3. **Revenue Discrepancy:** Summing solely ad-attributed revenue from Meta Marketing API underrepresented total enterprise revenue collected via Stripe (`orders` table).

## Decisions

1. **Campaign-Specific P&L & Break-Even Filtering:**
   * In `admin.html`, the Marketing dashboard provides a top-level **Campaign Selector** (`🌌 Nagy-Kevély`, `🏔️ Prédikálószék`, `♾️ Összesített`).
   * **Nagy-Kevély View:** Calculates P&L and break-even against **193 000 Ft** fixed costs using only Nagy-Kevély orders & Meta ad spend.
   * **Prédikálószék View:** Evaluates against its own **193 000 Ft** fixed costs (68 medals sold, 100% break-even achieved).
   * **Összesített View:** Combines all orders (84 orders / 88 medals) and evaluates against **386 000 Ft** ($2 \times 193\,000\text{ Ft}$) combined fixed costs.

2. **Automated Creative-Level CSV Pipeline:**
   * `scripts/fetch_meta_daily.py` automatically updates `meta_kreativ_napi_riport.csv` upon every daily cron run or backfill execution.
   * `/api/admin-data` reads the rich creative dataset to render the granular creative table (CPA, ROAS, link clicks, CTR, CPM, CPC, net margin) with exact creative and adset names.

3. **Stripe Order Revenue as Enterprise Source of Truth:**
   * `/api/admin-data` includes `amount_total` from paid real orders.
   * Macro KPI cards utilize actual Stripe cash inflow, avoiding under-reporting from Meta ad tracking dropouts or organic/direct entries.

## Consequences
* Accurate, uncorrupted break-even progress tracking for active batches.
* Complete visibility into creative-level marketing ROAS and CPA.
* Zero data loss from API latency or schema constraint mismatches.
