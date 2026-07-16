# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync & Payment Pipeline:** The Vercel Node.js webhook (`api/stripe-webhook.js`) still exists as fallback, but the **primary post-payment pipeline is now `api/process-payment.js`** (webhook-free, triggered from `siker.html` via `session_id` URL param). This was necessary because Stripe's free plan does not support webhook endpoint registration. The pipeline covers: Google Sheets (`tally_raw` + `stripe_raw2`), Supabase runner registration, Számlázz.hu e-invoice, and welcome email. Test/live mode is auto-detected from `cs_test_` session_id prefix. Idempotency is enforced via `stripe_session_id` column in Supabase. Checked and validated: added a robust fallback key-matching system for Stripe session metadata (fixing character encoding/cyrillic issues) and protected Számlázz.hu credentials lookup. Simplified Számlázz.hu invoice term names.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed. `is_test` column in `runners` table excludes test buys from serial rank calculations. `tally_szallitas` writes removed — shipping data (incl. `parcelId`) is in `stripe_raw2` column I.
*   **Daily Foxpost Cron:** GitHub Actions run `scripts/daily_tracking.py` daily to fetch package updates and email follow-ups. Path mapping is correct.
*   **Meta Ads Campaign Configuration:**
    *   Prospecting Ad Set (LAL 1% exclusion of buyers) is active/ready.
    *   Retargeting Ad Set (VitaSteps Webhelylátogatók 30 nap + FB/IG Engagers 90 nap, buyer exclusions) configured.
    *   Ads setup configured at a starting budget of **2 000 HUF / day** (as of July 16, 2026).
    *   **3-Phase Sell-Out Strategy:** Starting with 2 000 HUF/day for validation, scaling by 20-30% every few days if CPA < 3 000 HUF, keeping budget flat and updating creatives if CPA > 4 500 HUF. High-converting copywriting and visuals (V4/V5) are prepared. See detailed strategy at [nagy_kevely_csillagai.md](file:///e:/Data/other_projects/VitaSteps/campaigns/nagy_kevely_csillagai.md#L70-L100).
*   **Nagy-Kevély Landing Page Megújítás (UPDATED 2026-07-13):**
    *   Beillesztettük a közösségi kilométer-statisztikát (1 230 km completed) és a Kalandkönyv (PDF) promóciós szekciót.
    *   A visszaszámlálót a kihívás végére (**szeptember 13. 23:59**) állítottuk be.
    *   A gombok felett kiemeltük az akciós árat (**13.990 Ft helyett 7.990 Ft**).
    *   A hívó gombok feliratát átírtuk a konverziós szempontból erősebb **„Megszerzem az érmemet! 🏅”** (és mobilon/nav sávban **„Kérem az érmet 🏅”**) szövegre.
    *   A gombok alá elhelyeztük az `✓ Ingyenes szállítás` és `✓ Ajándék kalandkönyv` meggyőző előny-címkéket.
    *   A térképes útvonal-szűrőket kiterjesztettük a 4 új távra (6km, 10km, 15km, 25km).
    *   **Hero kép cseréje (FIXED):** A korábbi nem betöltődő éremképet lecseréltük az éles termék kreatívra (`nagy_kevely_creative_v4.png`), 12px border-radius-szal.
    *   **Mobil Sticky CTA és Kicsúszás Fixek (FIXED):** Globális CSS szabályokkal megszüntettük a vízszintes kicsúszást.
    *   **Nagy-Kevély Kalandkönyv Generátor (COMPLETED 2026-07-15):** Elkészült a `nagykevely/kalandkonyv.html` 6 oldalas túranapló és kalandkönyv füzet generátor. Leaflet térkép (340px), HTML5 Canvas szintmetszet, max 5 POI/oldal, A5 nyomtatás.
    *   **Személyes Portál Dinamikus Tabok és Kalandkönyv (UPDATED 2026-07-16):** A `portal.html` oldalon létrehoztunk egy új „Kalandkönyv” fület PK sorszámú nevezőknek. Továbbfejlesztettük a tab-kezelést: a nem teljesített túrázóknak a nem releváns tabok (Visszajelzés, Ajánlói Program) rejtve maradnak. Ha egyetlen tab aktív, a tab-sáv nem jelenik meg, hanem az adott kártya közvetlenül látható. Ha nincs elérhető tab (teljesítetlen Prédikálószék), egy egyedi Tally-s teljesítés-igazoló kártya jelenik meg dinamikusan kitöltött adatokkal.
    *   **Adatbázis Normalizáció & Több Kihívás Támogatása (COMPLETED 2026-07-16):**
        *   Felbontottuk a sémát `runners` (név, egyedi email) és `runs` (kihívás regisztrációk, egyedi sorszám) táblákra.
        *   Módosítottuk a `process-payment.js`, `stripe-webhook.js`, `submit-feedback.js` és `daily_tracking.py` állományokat az új sémának megfelelően.
        *   A portálon (`portal.html`) bevezettünk egy legördülő választómenüt, amellyel a több kihívásra regisztrált felhasználók azonnal válthatnak a túráik között. A teljes felület (státusz, oklevél link, Kalandkönyv és Ajánlói fülek) dinamikusan frissül.
        *   Javítottuk a portál oklevél gombjának útvonalát `/predikalo/oklevel.html` értékre.
        *   **Beépített Teljesítés Igazoló és Admin Dashboard:** Létrehoztunk egy fájlfeltöltő tabot a portálon (GPX és fotó feltöltésével), egy hozzá tartozó adminisztrátori ellenőrző felületet (`admin.html` és `api/admin-approve.js`), valamint automatikus gratulációs e-mail küldést és dinamikus oklevél-sablon javítást (`oklevel.html` paraméter-dekódolás és tábla lekérdezés).
*   **Prédikálószék Ping Email System (COMPLETED 2026-07-13):**
    *   `scripts/send_emails.py` updated with `ping` mode as default.
    *   15 emails sent to non-finisher Prédikálószék participants; `ping0713` column auto-updated in Sheets.

---

## 🎯 Current Focus
*   **Payment Pipeline Tesztelése:**
    *   Számlázz.hu és welcome email működésének end-to-end ellenőrzése `?test=true` módban.
    *   Vercel deploy (`vercel --prod`) az összes mai változással.
*   **Nagy-Kevély csillagai Campaign Pre-launch:**
    *   Secure checkout: `?test=true` teszt mód működik, live védelem aktív.
    *   Verify Stripe live environment for the `VSBARAT10` coupon code.
    *   Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper.

---

## 🛑 Known Blockers / Issues
*   `DRY_RUN = True` is currently set in `scripts/send_emails.py` — must be manually changed to `False` before any live email send.
*   Nagy-Kevély campaign pre-launch: Checkout is blocked globally on live Vercel domains to avoid premature signups. Must be removed when launching.
*   Stripe `VSBARAT10` referral coupon code: live environment testing still pending.
