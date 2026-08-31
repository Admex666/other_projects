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
  - "[[ADR-006-multicampaign-unit-economics|ADR-006 Multi-Campaign Unit Economics]]"
---

# Operation: How to Run Daily Sync & Marketing Reports

Daily tracking is automated via GitHub Actions, but can also be executed on demand from your terminal:

## 1. Syncing Meta Marketing Insights & Updating CSV
Run in PowerShell (from repository root or `landing_predikalo1/`):
```powershell
# Sync yesterday's metrics
python landing_predikalo1/scripts/fetch_meta_daily.py

# Backfill the last 7 days after launching new campaigns or creatives
python landing_predikalo1/scripts/fetch_meta_daily.py --backfill=7

# Sync a specific date
python landing_predikalo1/scripts/fetch_meta_daily.py --date=2026-08-30
```
* **Output:** Fetches latest ad-level spend from Meta Marketing API, matches with Supabase orders, updates table `meta_daily_metrics`, automatically updates `meta_kreativ_napi_riport.csv`, and sends a Pushbullet summary notification.

## 2. Syncing Foxpost Package Statuses & Sending Reviews
```powershell
python landing_predikalo1/scripts/daily_tracking.py
```
* **Output:** Queries Foxpost API for parcel status updates (`arrived_in_locker`, `delivered`), updates Supabase `shipments`, and emails review requests to recipients of delivered packages.
