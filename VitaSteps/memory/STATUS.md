# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync:** The Vercel Node.js webhook (`api/stripe-webhook.js`) handles payment checkout completion, logs rows in Google Sheets, registers profiles in Supabase with custom serial numbering, generates Számlázz.hu AAM e-invoices, and sends welcome emails. It auto-detects Stripe test mode transactions (`livemode === false`) and marks them with `is_test: true` in Supabase, keeping them out of official serial calculation queries to prevent rank jumps.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed, stopping exponential rank calculations in Supabase.
*   **Daily Foxpost Cron:** GitHub Actions run `scripts/daily_tracking.py` daily to fetch package updates and email follow-ups. Path mapping is correct.
*   **Meta Ads Campaign Configuration:**
    *   Prospecting Ad Set (LAL 1% exclusion of buyers) is active/ready.
    *   Retargeting Ad Set (VitaSteps Webhelylátogatók 30 nap + FB/IG Engagers 90 nap, buyer exclusions) configured.
    *   Ads setup configured at a starting budget of **1 600 HUF / day**.
    *   High-converting, sales-oriented ad copywriting variations for V4 (product) and V5 (hiker) saved and prepared.
*   **Nagy-Kevély Landing Page Megújítás (UPDATED 2026-07-13):**
    *   Beillesztettük a közösségi kilométer-statisztikát (1 230 km completed) és a Kalandkönyv (PDF) promóciós szekciót.
    *   A visszaszámlálót a kihívás végére (**szeptember 13. 23:59**) állítottuk be.
    *   A gombok felett kiemeltük az akciós árat (**13.990 Ft helyett 7.990 Ft**).
    *   A hívó gombok feliratát átírtuk a konverziós szempontból erősebb **„Megszerzem az érmemet! 🏅”** (és mobilon/nav sávban **„Kérem az érmet 🏅”**) szövegre.
    *   A gombok alá elhelyeztük az `✓ Ingyenes szállítás` és `✓ Ajándék kalandkönyv` meggyőző előny-címkéket.
    *   A térképes útvonal-szűrőket kiterjesztettük a 4 új távra (6km, 10km, 15km, 25km).
    *   **Hero kép cseréje (FIXED):** A korábbi nem betöltődő éremképet lecseréltük az éles termék kreatívra (`nagy_kevely_creative_v4.png`), 12px border-radius-szal.
    *   **Mobil Sticky CTA és Kicsúszás Fixek (FIXED):** Globális CSS szabályokkal (`html, body { overflow-x: hidden; }` és `max-width` megkötések) megszüntettük a vízszintes kicsúszást (különös tekintettel az iPhone 12 Pro 390px szélességű kijelzőjére). A navigációs sávot és a sticky gombsávot reszponzívvá tettük.
    *   **Érem kép pozicionálása mobilon (FIXED):** Telefonos nézetben az érem képe az akciós árazás és a CTA gombok elé került beágyazásra a jobb vizuális elrendezés érdekében.
    *   **Nagy-Kevély Kalandkönyv Generátor (COMPLETED 2026-07-15):** Elkészült a `nagykevely/kalandkonyv.html` 6 oldalas túranapló és kalandkönyv füzet generátor. A fenti vezérlőpulton közvetlen útvonalválasztót helyeztünk el (az EXTRA a 3., a FÉLMARATON a 4. opció). A 3. oldalon integráltunk egy kiemelten részletes és nagy méretű (képernyőn 340px, nyomtatásban 230px magas) dinamikus Leaflet térképet (a turistautak jelzéseit mutató Waymarked Trails réteggel és számozott POI pinekkel) és egy HTML5 Canvas alapú szintmetszet-grafikont (amelyen a POI magasságok és távolságok is jelölve vannak). A látnivalókat összevontuk egyetlen helytakarékos lapra (4. oldal) szigorú földrajzi sorrendben, és a POI-k koordinátáit és távolságait OpenStreetMap (OSM) és geocaching adatok alapján hajszálpontosra frissítettük (különös tekintettel a Monalovác-tető helyes keleti elhelyezkedésére). A füzet tartalmát a legfontosabb **maximum 5 POI-ra korlátoztuk**, ami megelőzi a tartalom lecsúszását az A5 oldalakról. A felesleges Kvíz és Bingó lapokat töröltük, a füzet méretét 6 oldalra csökkentettük, és a nyomtatási stílusokat optimalizáltuk, így a 100%-os méretezés is tökéletesen és túlcsordulások nélkül ráfér az A5 lapokra. Az időtartam és a nehézség mezőket eltávolítottuk, a "Tudtad-e?" szövegeket pedig "Tudtad?" alakra frissítettük.
    *   **Személyes Portál Kalandkönyv Tab (COMPLETED 2026-07-13):** A `portal.html` oldalon létrehoztunk egy új "Kalandkönyv" fület, ami kizárólag a Nagy-Kevély kihívás nevezőinek (`PK` sorszám előtag) jelenik meg, lehetővé téve a névvel és távval előre kitöltött könyv színes vagy B&W exportálását.
*   **Prédikálószék Ping Email System (COMPLETED 2026-07-13):**
    *   `scripts/send_emails.py` updated with `ping` mode as default.
    *   `email_ping_template.html` rewritten with dual CTA: ✅ igazolás (NpRz5W) + 📦 szállítás (predikalo/szallitas.html).
    *   15 emails sent to non-finisher Prédikálószék participants; `ping0713` column auto-updated in Sheets.

---

## 🎯 Current Focus
*   **Nagy-Kevély csillagai Campaign Pre-launch:**
    *   Secure checkout: Added client-side (`checkout.html`) and backend-side (`api/checkout.js`) blocks to prevent public live registrations for the Pilis/Kevély campaign, while keeping local development (localhost) and explicitly bypassed tests (`?test=true`) open.
    *   Verify Stripe live environment for the `VSBARAT10` coupon code.
    *   Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper.

---

## 🛑 Known Blockers / Issues
*   `DRY_RUN = True` is currently set in `scripts/send_emails.py` — must be manually changed to `False` before any live email send.
*   Nagy-Kevély campaign pre-launch: Checkout is blocked globally on live Vercel domains to avoid premature signups. Must be removed when launching.
*   Stripe `VSBARAT10` referral coupon code: live environment testing still pending.
