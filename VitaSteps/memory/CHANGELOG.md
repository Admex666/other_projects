# 📜 Changelog

All notable changes to the VitaSteps challenge platform project are documented here.

---

## [1.4.0] - 2026-07-13
### Added
*   **Nagy-Kevély Landing Page CTA Optimization:**
    *   **Price Positioning:** Positioned the discounted price (7.990 Ft) highlighted above all call-to-action buttons.
    *   **CTA Button Copy:** Updated all main action buttons with the chosen high-converting text: *"Megszerzem az érmemet! 🏅"* (nav bar layout uses *"Kérem az érmet 🏅"* for space).
    *   **Benefit Tags:** Positioned clear checklist tags (*"✓ Ingyenes szállítás • ✓ Ajándék kalandkönyv"*) directly below all CTA buttons.
    *   **Hero Image Replacement:** Replaced the broken or missing medal image with the official product creative banner (`nagy_kevely_creative_v4.png`), adjusting styles with 12px border radius.
    *   **Mobile Sticky CTA Fix:** Implemented width, padding, flexbox, and box-sizing overrides to prevent the mobile sticky button container from overflowing horizontally.
    *   **Branding Uniformity:** Replaced all leftover 'Pilis' text references with 'Nagy-Kevély' or 'Kevély' (e.g., stats bar, serial badges, mockups).
    *   **Direct Checkout Links:** Changed all navigation, hero, and mobile sticky buttons to link directly to `/checkout.html?c=pilis` instead of scrolling down to the local anchor.
*   **Personalized Adventure Guidebook (Kalandkönyv):**
    *   **Dynamic Generator Page:** Created `nagykevely/kalandkonyv.html` providing dynamically built, customizable, printable A5/A4 adventure guidebooks and hiking logs.
    *   **8-Page Premium Booklet Layout:** Upgraded the guidebook to a complete 8-page format (ideal for double-sided A4 printing folded in half). Added a dynamic POI reader spanning Pages 4 & 5.
    *   **POI & Heritage Integration:** Integrated rich geological, historical, and cultural stories sourced from local research, featuring the Teve-szikla (geology and Egri Csillagok scene), Egri vár replica, Kevélyhegyi Levendulamező, Mackó-barlang (ice age fauna and Neanderthal archaeology), the csobánkai Sicambria (Monalovac) hun capital theories, and Kő-hegy history (Czibulka menedékház, Petőfi's 1845 visit, Napóleon kalapja rock).
    *   **Prefilled Portal Tab:** Added a dedicated "Kalandkönyv" tab in `portal.html` visible exclusively to Nagy-Kevély challengers (`PK` serial code prefix). Prefills the runner's name, offers route selections (Family 6km, Classic 10km, Half Marathon 15km, Long 25km), B&W or color themes, and launches print setups.
    *   **Dynamic GPX QR-Codes:** Generates real-time QR codes linked to official GPX track files (`01csaladi.gpx`, `02klasszik.gpx`, `04felmaraton.gpx`, `03extra.gpx`) using a lightweight public redirect API.
    *   **Interactive Activities:** Included custom trail timelines, weather logs, journal sections, and a nature scavenger Hunt bingo grid, and a history/trivia section.
*   **Tiered Referral Discount System:**
    *   **Automated Discounting:** Refactored `api/checkout.js` to look up the runner's email in Supabase and calculate past successful referrals. Applies 10% (1 referral) up to 50% (5+ referrals) discount automatically.
    *   **Programmatic Stripe Sync:** If the computed discount coupon (e.g., `VS_AJANLO_20`) does not exist on the merchant's Stripe account, the backend creates it automatically on the fly to prevent transaction failures.
    *   **Fallback Friend Promo:** Maintains the `VSBARAT10` 10% discount for referred friends if they are buying for the first time.
*   **Checkout Pre-Launch Safety Blocking:**
    *   **Client-Side Gate:** Added conditional script checks in `checkout.html` blocking the order form for the live `pilis` campaign on non-localhost/non-test URLs, showing a customized "Coming Soon" screen.
    *   **Backend Validation:** Refactored `api/checkout.js` to reject any public checkout requests targeting `pilis` on live deployments, returning HTTP 403 Forbidden to prevent unauthorized card transactions. Local development and explicit test triggers (`?test=true`) remain bypassable.
*   **Meta Ads Campaign Configuration** – configured the Ads Manager setup for the Nagy-Kevély campaign:
    *   **Prospecting Ad Set:** Targets 1% LAL from previous buyers, excluding actual buyers.
    *   **Retargeting Ad Set:** Targets 30-day website visitors and 90-day FB/IG social media engagers, excluding previous buyers.
    *   **Budgeting:** Configured with an initial starting budget of **1 600 HUF / day**.
    *   **Copywriting:** Added optimized, high-converting primary texts, headlines, and descriptions focusing on premium 3D metal medals, FOMO, and natural achievement.
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
*   **Mobile View Layout Overflow (iPhone 12 Pro)** – Fixed global horizontal overflow by adding `html { overflow-x: hidden; }` and strict `max-width` rules, ensuring no elements slide or overflow to the right on 390px screens.
*   **Mobile Medal Image Placement** – Swapped the visual order on mobile viewports so the physical medal illustration renders *before* the pricing structure and CTA buttons (above the fold/actions flow).

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
