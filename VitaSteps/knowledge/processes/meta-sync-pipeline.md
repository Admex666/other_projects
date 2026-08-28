---
id: meta-sync-pipeline
type: process
name: Meta Sync Pipeline
status: active
description: Automated daily extraction of Meta Ads insights, purchases, CPA, and ROAS into database & CSV.
source:
  type: api
  system: Meta
  endpoint: /v19.0/act_<ID>/insights
code:
  - landing_predikalo1/scripts/fetch_meta_daily.py
  - .github/workflows/daily_meta_sync.yml
  - landing_predikalo1/meta_kreativ_napi_riport.csv
related:
  - "[[meta-ads|Meta Ads]]"
  - "[[cac]]"
  - "[[roas]]"
  - "[[unit-economics|Unit Economics]]"
---

# Process: Meta Sync Pipeline

```text
GitHub Actions Workflow (.github/workflows/daily_meta_sync.yml)
       │ (Runs daily at 04:00 UTC)
       ▼
scripts/fetch_meta_daily.py
       ├─► 1. Fetches daily spend, impressions, link clicks from Meta Marketing API
       ├─► 2. Correlates ad UTMs with Supabase orders (live purchase counts & revenue)
       ├─► 3. Calculates real daily CPA, CPM, CTR, and ROAS
       ├─► 4. Upserts metrics into Supabase table: meta_daily_metrics
       └─► 5. Exports updated meta_kreativ_napi_riport.csv
```
