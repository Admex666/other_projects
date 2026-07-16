## 🚀 Nagy-Kevély csillagai Campaign Start

### 👥 Audiences & Ads Manager (Manual)
*   **[x]** Upload `docs/predikaloszek_emails.csv` as a Custom Audience in Meta Business Manager.
*   **[x]** Generate a 1% and 2% Lookalike (LAL) audience for Hungary.
*   **[x]** Configure Prospecting campaigns to exclude the purchaser custom list and success page visitors.
*   **[x]** Setup Retargeting ad sets targeting page visitors from the last 30 days (excluding buyers).
*   **[ ]** Verify Stripe live environment for the `VSBARAT10` coupon code.

### 🌐 Frontend Page Enhancements (AI)
*   **[x]** Promote free Kalandkönyv (PDF Guidebook) on `nagykevely/index.html` (add mockups and descriptions).
*   **[x]** Add community total distance stat (1,230 km completed) to `nagykevely/index.html`.
*   **[x]** Add countdown timer (ticking to Sept 6/13) and limited stock counter (100 medals max) JS logic to `nagykevely/index.html`.
*   **[x]** Update map filters to show the 4 new route options (Family 6km, Classic 10km, Half Marathon 15km, Ultra 25km).
*   **[x]** Fix mobile layout responsiveness (prevent horizontal overflow, iPhone 12 Pro compatibility).
*   **[x]** Reposition medal image on mobile to be shown before pricing inside the Hero section.
*   **[x]** Útvonalak POI-jainak (érdekességek, látnivalók) kigyűjtése és részletes információk összegyűjtése az egyes pontokról.

---

## 📧 Prédikálószék – Post-Campaign Follow-Up
*   **[x]** Identify non-finisher participants with no shipping data from Sheets (15 fő).
*   **[x]** Build ping email system (`send_emails.py` ping mode + `email_ping_template.html`).
*   **[x]** Send 15 ping emails to non-finishers (2026-07-13). `ping0713` column auto-updated.
*   **[ ]** Monitor replies and Tally form submissions (NpRz5W) for new completion proofs.
*   **[ ]** Once proofs are received, manually update `teljesítve dátum` in Sheets and trigger fulfillment (`send_emails.py teljesites`).

---

## 🔧 Maintenance, Documentation & Testing
*   **[ ]** Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper on local server (port 3001).
*   **[ ]** Elkészíteni a folyamat-dokumentációt (melyik script/végpont mit csinál, honnan olvas, hova ír) a `/memory/ARCHITECTURE.md` fájlban vagy egy külön `docs/folyamat.md`-ben.


---

## 💳 Payment Pipeline – Kövi feladatok
*   **[x]** Átnézni és tesztelni a **Számlázz.hu** e-számla generálást (`process-payment.js` → Számlázz.hu API hívás) — valóban megérkezik-e a számla emailben.
*   **[ ]** Átnézni és tesztelni a **welcome email** küldést (`process-payment.js` → nodemailer SMTP) — megérkezik-e a köszöntő email a vásárlónak.
*   **[ ]** End-to-end teszt: `checkout.html?campaign=pilis&test=true` → Stripe sandbox → `siker.html` → `process-payment` → Sheets + Supabase + számla + email.
*   **[x]** Supabase: lefuttatni `ALTER TABLE runners ADD COLUMN IF NOT EXISTS stripe_session_id text;`
*   **[x]** Deploy Vercel-re (`vercel --prod`) az összes mai változással.
