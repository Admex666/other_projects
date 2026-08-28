---
id: how-to-launch-campaign
type: operation
name: How to Launch a New Campaign
status: active
description: Step-by-step checklist for launching a brand new VitaSteps challenge.
code:
  - landing_predikalo1/config/campaigns.json
related:
  - "[[unified-campaign-config|Unified Campaign Config]]"
  - "[[campaign-predikaloszek|Campaign Predikaloszek]]"
  - "[[campaign-nagykevely|Campaign Nagy-Kevely]]"
---

# Operation: How to Launch a New Campaign

To launch a new challenge on the VitaSteps platform:

## Step 1: Add Campaign Configuration
Add a new object to `landing_predikalo1/config/campaigns.json`:
```json
{
  "id": "new_challenge_id",
  "name": "Új Kihívás Neve",
  "price": 7990,
  "serialPrefix": "#",
  "serialSuffix": "-NEW",
  "maxParticipants": 100,
  "deliveryNotice": "2026. október 1. után",
  "diplomaPath": "/new_challenge/oklevel.html",
  "guidebookPath": "/new_challenge/kalandkonyv.html"
}
```

## Step 2: Create Challenge Directory & Assets
1. Create folder `landing_predikalo1/<challenge_id>/`.
2. Create `index.html` (copy from template and update copy/elevation data).
3. Create `oklevel.html` (diploma certificate template).
4. Add GPX tracks in `gpx/` and parse route data.

## Step 3: Configure Target Metrics in Supabase
Insert a row into `marketing_targets` table with `target_cpa`, `warning_cpa`, `critical_cpa`, and `target_roas`.
