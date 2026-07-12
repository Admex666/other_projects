# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync:** The Vercel Node.js webhook (`api/stripe-webhook.js`) handles payment checkout completion, logs rows in Google Sheets, registers profiles in Supabase with custom serial numbering, generates Számlázz.hu AAM e-invoices, and sends welcome emails.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed, stopping exponential rank calculations in Supabase. Supabase test runner records are cleared.
*   **Daily Foxpost Cron:** GitHub Actions run `scripts/daily_tracking.py` daily to fetch package updates and email follow-ups. Path mapping has been corrected.
*   **Meta Ads Preparation Complete:** The email list has been exported, custom audience uploaded, LAL 1% and 2% generated, and the split-test setup (ABO 2500 HUF split) documented. Both final creative variants (`nagy_kevely_creative_v4.png` and `nagy_kevely_hiker_creative_v5.png`) have been created and saved in the project assets.

---

## 🎯 Current Focus
*   **Nagy-Kevély csillagai Campaign Pre-launch:**
    *   Implement frontend updates on the Nagy-Kevély landing page (`nagykevely/index.html`):
        1.  Incorporate the free downloadable PDF Guidebook (Kalandkönyv) promotion.
        2.  Insert community total mileage stats (1,230 km completed) to build social proof.
        3.  Implement JavaScript countdown timer (ticking to Sept 6/13) and limited stock counter (100 medals max).
        4.  Update the Leaflet map filtering to display the 4 new routes (6km, 10km, 15km, 25km).

---

## 🛑 Known Blockers / Issues
*   None. (All core webhook, invoice generation, database syncing, and automation pipelines are verified and running locally on port 3001).
