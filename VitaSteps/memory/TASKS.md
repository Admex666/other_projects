## 🚀 Nagy-Kevély csillagai Campaign Start

### 👥 Audiences & Ads Manager (Manual)
*   **[x]** Upload `docs/predikaloszek_emails.csv` as a Custom Audience in Meta Business Manager.
*   **[x]** Generate a 1% and 2% Lookalike (LAL) audience for Hungary.
*   **[x]** Configure Prospecting campaigns to exclude the purchaser custom list and success page visitors.
*   **[x]** Setup Retargeting ad sets targeting page visitors from the last 30 days (excluding buyers).

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

---

## 🔧 Maintenance, Documentation & Testing
*   **[ ]** Elkészíteni a folyamat-dokumentációt (melyik script/végpont mit csinál, honnan olvas, hova ír) a `/memory/ARCHITECTURE.md` fájlban vagy egy külön `docs/folyamat.md`-ben.


---

## 🚚 Logisztika és Csomagkezelés
*   **[x]** Foxpost tömeges export felület integrálása az `admin.html`-be (1 kattintásos letöltés SheetJS segítségével).
*   **[x]** Címadatok szétbontása (település, irányítószám, utca) házhozszállítás esetén a Foxpost XLSX sablonnak megfelelően.
*   **[x]** Kijelölt futások és szállítmányok feladottként való megjelölése az admin felületen (bulk `/api/admin-approve` hívás).

---

## 💳 Payment Pipeline – Kövi feladatok
*   **[x]** Átnézni és tesztelni a **Számlázz.hu** e-számla generálást (`process-payment.js` → Számlázz.hu API hívás) — valóban megérkezik-e a számla emailben.
*   **[x]** Átnézni és tesztelni a **welcome email** küldést (`process-payment.js` → nodemailer SMTP) — megérkezik-e a köszöntő email a vásárlónak.
*   **[x]** Normális supabase email megerősítés (most alap "confirm your email" van)
*   **[x]** Számla template javítás: bank, cím, megnevezés!!!
*   **[x]**  Portálon kezelni, ha több jelentkező van egy e-mail címről, teljesítés igazolása felületen szintén, lehetőleg egy képpel lehessen több embert is igazolni.
*   **[x]** "Sikeres nevezés" Welcome emailben legyen tájékoztató mindenről (GPX/szelfi feltöltés), portál elérhetősége és szerepe.
*   **[ ]** Referral kedvezmények beépítése, tesztelése
*   **[ ]** Normális kalandkönyv
*   **[x]** End-to-end teszt: `checkout.html?campaign=pilis&test=true` → Stripe sandbox → `siker.html` → `process-payment` → Sheets + Supabase + számla + email.
*   **[x]** Supabase: lefuttatni `ALTER TABLE runners ADD COLUMN IF NOT EXISTS stripe_session_id text;`
*   **[x]** Deploy Vercel-re (`vercel --prod`) az összes mai változással.

---

## 🗄️ Database Migration & Cleanup (Deferred)
*   **[ ]** Database Migration: Normalize payment and shipping data
    *   `[ ]` orders tábla létrehozása production előtt (a `supabase_schema.sql` alapján)
    *   `[ ]` shipments tábla létrehozása
    *   `[ ]` runners mezők bővítése (`phone`, `billing_name`, `billing_address`)
    *   `[ ]` meglévő `stripe_raw2` adatok importálása a Supabase orders/shipments táblákba (migrációs scripttel)
    *   `[ ]` runs kapcsolatok ellenőrzése és `order_id` / `campaign` értékek feltöltése a múltbeli futásokhoz
    *   `[ ]` feedbacks tisztítása: `runner_id` idegen kulcs beállítása a meglévő visszajelzésekre e-mail helyett
    *   `[ ]` régi Google Sheet adatforrás megszüntetése (amikor a Foxpost automatizációs szkripteket átállítottuk a shipments táblára)
    *   `[ ]` régi, elavult oszlopok törlése a `runs` táblából (`stripe_session_id`, `referred_by`)

