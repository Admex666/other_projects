---
id: cac
type: metric
name: Customer Acquisition Cost (CAC)
status: active
description: Blended and campaign-specific advertising cost incurred per paid medal purchase.
source:
  type: derived
  ref: landing_predikalo1/scripts/fetch_meta_daily.py
depends_on:
  - "[[meta-ads|Meta Ads]]"
  - "[[order]]"
used_by:
  - "[[unit-economics|Unit Economics]]"
  - "[[break-even]]"
---

# Metric: Customer Acquisition Cost (CAC / CPA)

CAC (or Cost Per Acquisition / CPA) measures the total advertising spend required to acquire one paid challenge registration.

## Calculation Formula
$$\text{CAC} = \frac{\text{Meta Ad Spend (Gross with 27\% VAT)}}{\text{Total Attributed Orders}}$$

## Threshold Guidelines (Configured in `marketing_targets`)
* **Target CAC:** $< \text{3 000 HUF}$ (Scale budget by +20–30% every few days).
* **Warning CAC:** $3 000 – 4 500 \text{ HUF}$ (Keep daily budget flat).
* **Critical CAC:** $> \text{4 500 HUF}$ (Pause weak ad sets, test new creative visuals).
