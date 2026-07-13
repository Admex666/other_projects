# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync:** The Vercel Node.js webhook (`api/stripe-webhook.js`) handles payment checkout completion, logs rows in Google Sheets, registers profiles in Supabase with custom serial numbering, generates Számlázz.hu AAM e-invoices, and sends welcome emails.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed, stopping exponential rank calculations in Supabase.
*   **Daily Foxpost Cron:** GitHub Actions run `scripts/daily_tracking.py` daily to fetch package updates and email follow-ups. Path mapping is correct.
*   **Meta Ads Preparation Complete:** Email list exported, custom audience uploaded, LAL 1% and 2% generated, split-test setup (ABO 2500 HUF) documented. Both creative variants saved in `campaigns/assets/creatives/`.
*   **Prédikálószék Ping Email System (COMPLETED 2026-07-13):**
    *   `scripts/send_emails.py` updated with `ping` mode as default.
    *   `email_ping_template.html` rewritten with dual CTA: ✅ igazolás (NpRz5W) + 📦 szállítás (predikalo/szallitas.html).
    *   Both links are prefilled with participant name + email.
    *   Igazolás button always visible (outside conditional block).
    *   15 emails sent to non-finisher Prédikálószék participants; `ping0713` column auto-updated in Sheets.

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
*   `DRY_RUN = True` is currently set in `scripts/send_emails.py` — must be manually changed to `False` before any live email send.
*   Stripe `VSBARAT10` referral coupon code: live environment testing still pending.
