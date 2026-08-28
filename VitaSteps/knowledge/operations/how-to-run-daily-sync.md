---
id: how-to-run-daily-sync
type: operation
name: How to Run Daily Sync & Marketing Reports
status: active
description: Manual and automated execution of Meta Ads, Foxpost tracking, and financial sync scripts.
code:
  - landing_predikalo1/scripts/fetch_meta_daily.py
  - landing_predikalo1/scripts/daily_tracking.py
  - .github/workflows/daily_meta_sync.yml
related:
  - "[[meta-sync-pipeline|Meta Sync Pipeline]]"
  - "[[foxpost]]"
---

# Operation: How to Run Daily Sync & Marketing Reports

Daily tracking is automated via GitHub Actions, but can also be executed on demand from your terminal:

## 1. Syncing Meta Marketing Insights & Exporting CSV
Run in PowerShell:
```powershell
python landing_predikalo1/scripts/fetch_meta_daily.py
```
* **Output:** Fetches latest spend from Meta Marketing API, calculates exact CPA/ROAS against Supabase orders, updates table `meta_daily_metrics`, and rewrites `meta_kreativ_napi_riport.csv`.

## 2. Syncing Foxpost Package Statuses & Sending Reviews
```powershell
python landing_predikalo1/scripts/daily_tracking.py
```
* **Output:** Queries Foxpost API for parcel status updates (`arrived_in_locker`, `delivered`), updates Supabase `shipments`, and emails review requests to recipients of delivered packages.
