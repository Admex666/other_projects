## 🚀 Nagy-Kevély csillagai Campaign Start

### 👥 Audiences & Ads Manager (Manual)
*   **[x]** Upload `docs/predikaloszek_emails.csv` as a Custom Audience in Meta Business Manager.
*   **[x]** Generate a 1% and 2% Lookalike (LAL) audience for Hungary.
*   **[ ]** Configure Prospecting campaigns to exclude the purchaser custom list and success page visitors.
*   **[ ]** Setup Retargeting ad sets targeting page visitors from the last 30 days (excluding buyers).
*   **[ ]** Verify Stripe live environment for the `VSBARAT10` coupon code.

### 🌐 Frontend Page Enhancements (AI)
*   **[ ]** Promote free Kalandkönyv (PDF Guidebook) on `nagykevely/index.html` (add mockups and descriptions).
*   **[ ]** Add community total distance stat (1,230 km completed) to `nagykevely/index.html`.
*   **[ ]** Add countdown timer (ticking to Sept 6/13) and limited stock counter (100 medals max) JS logic to `nagykevely/index.html`.
*   **[ ]** Update map filters to show the 4 new route options (Family 6km, Classic 10km, Half Marathon 15km, Ultra 25km).

---

## 📧 Prédikálószék – Post-Campaign Follow-Up
*   **[x]** Identify non-finisher participants with no shipping data from Sheets (15 fő).
*   **[x]** Build ping email system (`send_emails.py` ping mode + `email_ping_template.html`).
*   **[x]** Send 15 ping emails to non-finishers (2026-07-13). `ping0713` column auto-updated.
*   **[ ]** Monitor replies and Tally form submissions (NpRz5W) for new completion proofs.
*   **[ ]** Once proofs are received, manually update `teljesítve dátum` in Sheets and trigger fulfillment (`send_emails.py teljesites`).

---

## 🔧 Maintenance & Testing
*   **[ ]** Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper on local server (port 3001).
