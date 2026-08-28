---
id: unified-campaign-config
type: concept
name: Unified Campaign Config
status: active
description: Centralized JSON configuration driving checkout, pricing, emails, and landing pages.
source:
  type: config
  ref: landing_predikalo1/config/campaigns.json
code:
  - landing_predikalo1/config/campaigns.json
  - landing_predikalo1/checkout.html
  - landing_predikalo1/siker.html
  - landing_predikalo1/portal.html
related:
  - "[[campaign-predikaloszek|Campaign Predikaloszek]]"
  - "[[campaign-nagykevely|Campaign Nagy-Kevely]]"
  - "[[ADR-003-unified-campaign-config|ADR-003]]"
---

# Concept: Unified Campaign Config

All marketing campaigns, checkout workflows, prices, email templates, and diploma URLs are controlled by a single canonical configuration file: `config/campaigns.json`.

## Configuration Schema
Each campaign entry specifies:
* `id`: Unique campaign identifier (`predikaloszek`, `pilis`).
* `name`: Display name.
* `price`: Base entry price in HUF (e.g. 7990).
* `serialPrefix` & `serialSuffix`: Suffix format (e.g. `-PK`).
* `maxParticipants`: Inventory cap (e.g. 100).
* `deliveryNotice`: Dynamic shipment dispatch date string in congratulatory emails.
* `diplomaPath`: Relative path to the diploma HTML file.
* `guidebookPath`: Optional URL for downloadable PDF/online guidebook.

## Benefits
* Zero code duplication between landing pages.
* Adding a new challenge requires only adding a new JSON block.
