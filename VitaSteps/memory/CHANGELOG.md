# 📜 Changelog

All notable changes to the VitaSteps challenge platform project are documented here.

---

## [1.3.0] - 2026-07-12
### Added
*   Created official `/memory` canonical directory layout conforming to the global AI Operating Protocol.
*   Generated and refined two Meta Ads creative banners under `campaigns/assets/creatives/`:
    *   `nagy_kevely_creative_v4.png`: Product-focused rendering of the physical 3D zinc-alloy medal on limestone rocks, spotlighted under warm sunlight.
    *   `nagy_kevely_hiker_creative_v5.png`: Social proof/aspirational portrait of a female hiker holding the 3D medal with its custom mustard-yellow lanyard (including white text print).
*   Documented Ad Set split-testing methodology and step-by-step setup guides for Meta Ads Manager.

---

## [1.2.0] - 2026-07-11
### Added
*   Extracted 61 unique buyer email addresses from Google Sheets into a clean CSV file: `docs/predikaloszek_emails.csv` to create a Custom Audience and Lookalike (LAL) audience for Meta Ads.

### Changed
*   Fixed path mapping in `.github/workflows/daily_tracking.yml` to point to `scripts/daily_tracking.py` instead of the old root path, fixing CI/CD execution errors.

---

## [1.1.0] - 2026-07-10
### Added
*   Dynamic JSON configuration file: `config/campaigns.json` storing prices, limits, prefixes, and distances for both `pilis` (Nagy-Kevély) and `predikaloszek` campaigns.
*   Unified `/checkout.html` page replacing campaign-specific files (`predikalo/checkout-widget.html`, `nagykevely/checkout-widget.html`). Loads params via query strings (`?c=pilis` / `?c=predikaloszek`) and fetches configurations dynamically.
*   Unified `/siker.html` success page with campaign-specific details, guidebook PDF links, and dynamic Facebook Pixel Purchase events.

### Fixed
*   **Rank Sorszám Bug:** Replaced the numeric-only regex extractor (`replace(/[^0-9]/g, '')`) with `#(\d+)\/` inside the Stripe webhook. Fixes rank serial index multiplication and exponential growth errors inside Supabase.
*   Cleared test database rows in Supabase to restore proper `#001` sequential numbering.

### Changed
*   Cleaned and reorganized workspace directory structure:
    *   Moved Python scripts to `/scripts`.
    *   Moved marketing reports and cheat sheets to `/docs`.
    *   Organized assets under `/assets/predikalo` and `/assets/nagykevely`.
    *   Removed duplicates in campaign subdirectories.
