---
id: roas
type: metric
name: Return on Ad Spend (ROAS)
status: active
description: Revenue generated per unit of advertising spend.
source:
  type: derived
  ref: landing_predikalo1/scripts/fetch_meta_daily.py
depends_on:
  - "[[meta-ads|Meta Ads]]"
  - "[[order]]"
used_by:
  - "[[unit-economics|Unit Economics]]"
---

# Metric: Return on Ad Spend (ROAS)

ROAS measures the marketing multiplier of paid advertising spend on revenue.

## Calculation Formula
$$\text{ROAS} = \frac{\text{Total Attributed Revenue (HUF)}}{\text{Meta Ad Spend (Net HUF)}}$$

## Target Benchmarks
* **Target ROAS:** $\ge 3.0\times$
* **Historical Performance:** Between May and August 2026, VitaSteps achieved an aggregate ROAS of **$> 10.0\times$** due to strong viral word-of-mouth and high customer retention.
