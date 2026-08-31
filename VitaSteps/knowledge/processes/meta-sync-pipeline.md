---
id: meta-sync-pipeline
type: process
name: Meta Sync Pipeline
status: active
description: Automated daily extraction of Meta Ads ad-level insights, order attribution, CPA, and ROAS into database & CSV.
source:
  type: api
  system: Meta
  endpoint: /v20.0/act_<ID>/insights
code:
  - landing_predikalo1/scripts/fetch_meta_daily.py
  - .github/workflows/daily_meta_sync.yml
  - landing_predikalo1/meta_kreativ_napi_riport.csv
related:
  - "[[meta-ads|Meta Ads]]"
  - "[[cac]]"
  - "[[roas]]"
  - "[[unit-economics|Unit Economics]]"
  - "[[ADR-006-multicampaign-unit-economics|ADR-006 Multi-Campaign Unit Economics]]"
---

# Process: Meta Sync Pipeline

The Meta Sync Pipeline extracts ad-level marketing performance, attributes Stripe orders, and syncs data to Supabase and the creative reporting CSV.

```text
GitHub Actions Workflow / Manual Run
       │ (Runs daily or via CLI --backfill=N)
       ▼
scripts/fetch_meta_daily.py
       ├─► 1. Fetches ad-level spend, impressions, CTR, link clicks from Meta API (level=ad)
       ├─► 2. Correlates ad UTM tags & campaign names with Supabase paid orders (no duplicate attribution)
       ├─► 3. Calculates unit economics: CPA, ROAS, Contribution Margin, and Cashflow
       ├─► 4. Upserts metrics into Supabase table: meta_daily_metrics
       ├─► 5. Automatically updates / appends rows into: meta_kreativ_napi_riport.csv
       └─► 6. Sends structured Pushbullet notification with status & P&L summary
```

## Key CLI Operations
* **Standard Daily Run (Yesterday):** `python scripts/fetch_meta_daily.py`
* **Specific Date Sync:** `python scripts/fetch_meta_daily.py --date=2026-08-30`
* **Multi-Day Backfill:** `python scripts/fetch_meta_daily.py --backfill=7`

## Data Safety Rules
* **No Revenue Duplication:** Each Stripe order is attributed to at most one Ad per day based on `utm_content` $\rightarrow$ `utm_campaign` $\rightarrow$ highest-spend Ad fallback.
* **Dual Persistence:** Always writes to both Supabase and `meta_kreativ_napi_riport.csv` so the admin dashboard (`admin.html`) has access to full creative names.
