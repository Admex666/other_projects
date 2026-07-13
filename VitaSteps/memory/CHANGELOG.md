# 📜 Changelog

All notable changes to the VitaSteps challenge platform project are documented here.

---

## [1.4.0] - 2026-07-13
### Added
*   **Prédikálószék Ping Email System** – built a re-engagement script to contact participants who haven't completed the challenge and haven't been pinged yet:
    *   **Logic:** Targets rows in the `Nevezések` sheet where `széria` = Prédikálószék, `teljesítve dátum` is EMPTY, and `ping0713` column is EMPTY.
    *   **Write-back:** After each successful send, the script immediately writes `Igen` to the `ping0713` column to prevent duplicate sends.
    *   **Default mode:** Running `send_emails.py` without arguments now defaults to `ping` mode (previously defaulted to `teljesites`).
*   **Dual CTA Email Template** – rewrote `email_ping_template.html`:
    *   Explains clearly that the June 30 deadline has passed and we haven't received proof of completion.
    *   Lists 3 options (completed / will complete / cancelling).
    *   Two action buttons: ✅ **Teljesítés igazolása** → `tally.so/r/NpRz5W?name=...&email=...` (prefilled) and 📦 **Szállítási cím megadása** → `predikalo/szallitas.html?name=...&email=...` (prefilled).
    *   The igazolás (verification) button is positioned **outside** the `STEP_SHIPPING_START/END` conditional block, so it always renders even when `has_address=True`.
*   **`make_completion_link()` function** – generates prefilled `tally.so/r/NpRz5W` links with name + email query params.
*   **`{{COMPLETION_LINK}}` template variable** – injected into HTML via `get_html_email()`.

### Fixed
*   **Broken `/szallitas.html` link** – changed to `/predikalo/szallitas.html` (the correct page containing the Foxpost Tally embed, form ID `RGj5aQ`).
*   **`ping0713` column default index collision** – changed `find_col("ping0713", 20)` default from `20` to `99`; `col(99)` always returns `""` (row is shorter), ensuring new participants are never wrongly skipped.
*   **Script ran in wrong mode** – added `PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)` to correctly load `.env` and HTML templates from the project root (not the `/scripts` subfolder).
*   **Igazolás button disappeared when `has_address=True`** – moved the completion button above the `STEP_SHIPPING_START` comment so it is never replaced by the "already registered" block.

### Sent
*   **15 ping emails sent** (2026-07-13) to non-finisher Prédikálószék participants with no prior ping. Google Sheets `ping0713` column updated automatically.

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
