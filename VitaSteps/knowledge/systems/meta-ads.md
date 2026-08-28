---
id: meta-ads
type: system
name: Meta Ads
status: active
description: Facebook and Instagram advertising campaign management, creative sets, and insights API.
source:
  type: api
  system: Meta Marketing API v19.0
code:
  - landing_predikalo1/scripts/fetch_meta_daily.py
  - .github/workflows/daily_meta_sync.yml
  - landing_predikalo1/meta_kreativ_napi_riport.csv
related:
  - "[[meta-sync-pipeline|Meta Sync Pipeline]]"
  - "[[cac]]"
  - "[[roas]]"
  - "[[meta-ad-creatives|Meta Ad Creatives]]"
---

# System: Meta Ads (Facebook & Instagram)

Meta Ads is the primary paid acquisition channel for new VitaSteps runners.

## Campaign Structure
1. **Prospecting (Cold Audience):**
   - Lookalike (LAL 1%) based on verified challenge finishers, excluding existing buyers.
   - Broad interest targeting: Hiking, trail running, Pilis, outdoor sports in Hungary.
2. **Retargeting (Warm Audience):**
   - Website visitors (30 days) + Social Engagers (90 days), excluding converters.

## Daily Analytics Sync
* GitHub Actions executes `scripts/fetch_meta_daily.py` every night.
* Extracts ad-level spend, impressions, CTR, CPM, and maps UTM codes to real revenue in Supabase `orders`.
* Data is stored in Supabase table `meta_daily_metrics` and exported to `meta_kreativ_napi_riport.csv`.
