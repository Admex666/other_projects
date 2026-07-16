# 📜 Changelog

All notable changes to the VitaSteps challenge platform project are documented here.

---

## [1.5.0] - 2026-07-16
### Added
*   **Adatbázis Normalizáció & Több Kihívás Támogatása:**
    *   Felbontottuk a sémát `runners` (név, egyedi email) és `runs` (kihívás regisztrációk, egyedi sorszám, a teljesítő nevével) táblákra.
    *   Módosítottuk a `process-payment.js`, `stripe-webhook.js`, `submit-feedback.js` és `daily_tracking.py` állományokat a két-táblás logikának megfelelően.
    *   A portálon (`portal.html`) bevezettünk egy legördülő választómenüt, amellyel a több kihívásra regisztrált felhasználók azonnal válthatnak a túráik között. A teljes felület (státusz, oklevél link, Kalandkönyv és Ajánlói fülek) dinamikusan frissül.
    *   Javítottuk a portál oklevél gombjának útvonalát `/predikalo/oklevel.html` értékre.

## [1.4.3] - 2026-07-16
### Added
*   **Dynamic Portal Tabs & Pending Challenge Card (`portal.html`):**
    *   Refactored the dashboard tab logic to dynamically show/hide tabs based on the runner's campaign and completion status.
    *   *Visszajelzés* and *Ajánlói Program* tabs are hidden for runners who have not completed their challenge.
    *   *Kalandkönyv* tab is only shown for Nagy-Kevély (Pilis) challengers.
    *   If only one tab is visible, the tab bar is hidden and that tab is activated automatically (e.g. non-completed Nagy-Kevély runners see the Guidebook card directly).
    *   If zero tabs are visible (non-completed Prédikálószék runners), the tab bar is hidden and a new `#pending-challenge-card` is displayed with instructions and a pre-filled Tally submission button (`https://tally.so/r/NpRz5W?email=...&name=...`).
*   **Payment Pipeline Hardening & Invoice Name Simplification:**
    *   **Golyóálló Kampány Kulcskereső:** Implemented a case-insensitive search loop over the entire Stripe metadata keys to match and extract campaign values regardless of character encoding anomalies (e.g. cyrillic "a" key error) or spelling variations.
    *   **Safe Számlázz.hu Key parsing:** Guarded `szamlaKey` extraction in `process-payment.js` and `stripe-webhook.js` against undefined values to prevent TypeError crashes in production when credentials are not set on Vercel.
    *   **Simplified Invoice Name:** Updated product name on Számlázz.hu invoices to be simply `${campaignName} érem` (e.g. "A Nagy-Kevély csillagai érem") instead of including the participant name and distance.

## [1.4.2] - 2026-07-15
### Added
*   **Webhook-Free Payment Pipeline (`api/process-payment.js`):**
    *   Created new `api/process-payment.js` endpoint as a full replacement for Stripe webhook-based post-payment processing (Stripe free plan does not support webhook registration via Dashboard).
    *   `siker.html` now reads the `?session_id=cs_xxx` parameter (passed by Stripe via `{CHECKOUT_SESSION_ID}` placeholder in `success_url`) and calls `/api/process-payment` in a fire-and-forget fetch on page load.
    *   `process-payment.js` retrieves and verifies the Stripe session (`payment_status === 'paid'`), then runs the full pipeline: Google Sheets (`tally_raw` + `stripe_raw2`), Supabase, Számlázz.hu invoice, and welcome email.
    *   **Idempotency:** Stores `stripe_session_id` in Supabase `runners` table; skips reprocessing if the session was already handled. Requires `ALTER TABLE runners ADD COLUMN IF NOT EXISTS stripe_session_id text;` in Supabase.
    *   **Test/live auto-detection:** Uses `cs_test_` prefix on session_id to select correct Stripe key and Számlázz.hu key.
*   **Test Mode Improvements:**
    *   `checkout.js`: Added hard guard — if `?test=true` is requested but `STRIPE_TEST_KEY` env var is missing, returns 500 error instead of silently falling back to live key.
    *   `stripe-webhook.js`: Updated signature verification to select `STRIPE_TEST_WEBHOOK_SECRET` for test events and `STRIPE_WEBHOOK_SECRET` for live events, detected via `"livemode":false` in raw body peek.
    *   `is_test` column added to Supabase `runners` table. Test transactions marked `is_test=true`; excluded from serial number max-calculation to preserve live sequence continuity.
*   **Google Sheets Cleanup:** Removed `tally_szallitas` writes from both `stripe-webhook.js` and `process-payment.js`. Shipping data (including `parcelId` at column I) is fully captured in `stripe_raw2`.

## [1.4.1] - 2026-07-15
### Added
*   **Guidebook Map Size and Loading Optimizations:**
    *   **Map Size Expansion:** Increased Leaflet map container height to 340px on screen and optimized to 230px height in print layout for perfect legibility.
    *   **6-Page Booklet Layout:** Deleted the dedicated Quiz (Page 5) and Bingo (Page 6) pages to tighten the content, reducing the total layout to a clean 6-page booklet. Updated all page footers (1/6 to 6/6) and layout constraints.
    *   **Print Page Sizing Fixes:** Added `@page` size rules, print-only padding overrides, and scale-down rules for elements in `@media print` to guarantee the booklet fits exactly on A5 paper without generating extra blank pages.
    *   **POI Coordinates & Dynamic Limits:** Corrected coordinates of several landmarks using official OpenStreetMap (OSM) nodes. Allowed showing all relevant POIs per route but capped at a maximum of 5 in order to prevent page overflow. Updated Sicambria (Monalovac) to its correct eastern location (`47.625800, 19.019200`).
    *   **Dropdown Order Swap:** Swapped the select menu options to match chronological file ordering: Option 3 is now Extra (25 km), Option 4 is Felmaraton (15 km).
    *   **Text & Info Cleanup:** Removed the "időtartam" (duration) and "nehézség" (difficulty) stats. Dynamically converted all "Tudtad-e?" instances to "Tudtad?" for a cleaner and more concise look.
    *   **Test Transactions Separation:** Updated the webhook (`api/stripe-webhook.js`) to automatically detect Stripe test mode transactions (`livemode === false`) and sync them to production database with `is_test = true`. Excluded test runs from the maximum serial number calculation queries to preserve the integrity and continuity of official buyer rank sequences.
    *   **Bugfix:** Fixed a null pointer exception caused by referencing the removed `route-timeline` DOM container inside `renderRoute`.

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
    *   **8-Page Premium Booklet Layout:** Upgraded the guidebook to a complete 8-page format (ideal for double-sided A4 printing folded in half). Added a dynamic POI reader on Page 4 and a dedicated Trivia & Quiz on Page 5.
    *   **Dynamic Route Mapping:** Integrated Leaflet.js inside Page 3, fetching and parsing GPX files client-side to render tracks, zoom bounds, and place custom numbered markers for each POI (1, 2, 3) in geographic order. Applied smart grayscale CSS filters for ink-saving printer-friendly BW theme.
    *   **Dynamic Canvas Elevation Profile:** Programmed a custom HTML5 Canvas drawing system that computes cumulative distance and elevations from the loaded GPX to render elevation profiles, complete with gridlines, axis labels, and vertical dashed pointer markers showing the exact location and altitude of each POI.
    *   **POI & Heritage Integration:** Integrated rich geological, historical, and cultural stories sorted in strict geographic sequence along each track with explicit distance markings (Teve-szikla, Egri vár, Levendulamező, Nagy-Kevély, Kevély-nyereg, Ezüst-hegy, Mackó-barlang, Oszoly, Sicambria/Monalovac, Kő-hegy).
    *   **Interactive Controls & Selector:** Added a live route selector dropdown to the top customization card, allowing runners to dynamically switch tracks and instantly preview guidebooks.
    *   **Prefilled Portal Tab:** Added a dedicated "Kalandkönyv" tab in `portal.html` visible exclusively to Nagy-Kevély challengers (`PK` serial code prefix). Prefills the runner's name, offers route selections, B&W or color themes, and launches print setups.
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
