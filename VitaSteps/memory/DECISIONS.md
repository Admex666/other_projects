# 🧠 Architectural & Business Decisions

## 1. Unified, Configuration-Driven Checkout & Success Templates (2026-07-10)
*   **Context:** Originally, each campaign had duplicate widget and success pages (`predikalo/checkout-widget.html`, `nagykevely/checkout-widget.html`). Bugfixes and new features (like multi-medal purchases or pricing updates) had to be manually edited in every folder.
*   **Decision:** We unified checkout and success flows into a single `/checkout.html` and `/siker.html` in the root folder. These templates read campaign parameters from query strings (e.g. `?c=pilis`) and dynamically fetch details (prices, limits, routes) from a single config file: `config/campaigns.json`.
*   **Impact:** Zero code duplication for checkout logic. Launching a new campaign (e.g., Börzsöny) only requires adding a config entry and placing its map GPX files.

---

## 2. Directory Reorganization & Asset Isolation (2026-07-10)
*   **Context:** The root directory was cluttered with local Python crons, markdown reports, and campaign assets.
*   **Decision:** 
    *   Moved all Python scripts to the `/scripts` directory.
    *   Moved all marketing cheat-sheets and closing reports to the `/docs` directory.
    *   Organized GPX/image assets under `/assets/predikalo` and `/assets/nagykevely` directories.
*   **Impact:** Cleaner repository structure. Improved codebase navigation for developers and AI agents.

---

## 3. Multiple File Upload Support on Finisher Portal (2026-07-10)
*   **Context:** Prédikálószék Vertical feedback indicated that users found it restrictive to upload only one proof document (either photo or GPX).
*   **Decision:** Refactored the portal frontend and backend integration to allow multiple file uploads simultaneously (GPX + Photos) saved under Supabase Storage.
*   **Impact:** Enhanced user experience (UX) and easier manual verification for administrators.

---

## 4. Standard Purchase Event Optimization (2026-07-11)
*   **Context:** Previous campaigns used URL-based custom conversions in Meta Ads Manager.
*   **Decision:** Standardized the Facebook Pixel Purchase event triggering inside the unified `siker.html`. It dynamically fires:
    `fbq('track', 'Purchase', { value: config.price, currency: 'HUF', content_name: config.productName })`
*   **Impact:** Meta Pixel automatically tracks correct transaction values and maps conversions to specific campaigns without manual custom conversion adjustments in Meta.

---

## 5. Tiered Referral Discount System (2026-07-14)
*   **Context:** We wanted to reward loyal participants who actively refer friends to VitaSteps, incentivizing them to sign up for subsequent challenges at a lower price point.
*   **Decision:** Implemented a backend check in `api/checkout.js` matching the purchaser's email against the `referred_by` column in Supabase `runners`. A tiered discount is computed (1 referral = 10% off, 2 = 20% off, up to 5+ = 50% off). The code programmatically creates the corresponding discount coupon in Stripe if it does not yet exist.
*   **Impact:** Fully automated loyalty program without requiring manual coupon generation on Stripe or promo code inputs from the customer. Users are dynamically recognized and rewarded upon checkout.
