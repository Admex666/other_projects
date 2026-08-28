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
    *   **Nagy-Kevély Kalandkönyv Generátor (UPDATED 2026-08-25):** A `nagykevely/kalandkonyv.html` 6 oldalas kalandkönyv nyomtatási és térképnézete tökéletesítve. Fix 280px Leaflet konténer, geográfiai kiterjesztés (`currentBounds.pad(0.18)`), automatikus tört zoom (`zoomSnap: 0.1`) és az utolsó lap utáni üres oldal megszüntetése (`page-break-after: avoid` az utolsó oldalon). Beágyazva a `/portal.html` közvetlen link.
    *   **Napi Meta Kreatív Riport Export (UPDATED 2026-08-25):** Legenerálva a `meta_kreativ_napi_riport.csv` (140 sor, 2026-07-26 – 2026-08-25), egyedi rendelés-hozzárendeléssel és pontos CPA/ROAS számítással.
    *   **Személyes Portál Dinamikus Tabok és Kalandkönyv (UPDATED 2026-07-16):** A `portal.html` oldalon létrehoztunk egy új „Kalandkönyv” fület PK sorszámú nevezőknek. Továbbfejlesztettük a tab-kezelést: a nem teljesített túrázóknak a nem releváns tabok (Visszajelzés, Ajánlói Program) rejtve maradnak. Ha egyetlen tab aktív, a tab-sáv nem jelenik meg, hanem az adott kártya közvetlenül látható. Ha nincs elérhető tab (teljesítetlen Prédikálószék), egy egyedi Tally-s teljesítés-igazoló kártya jelenik meg dinamikusan kitöltött adatokkal.
    *   **Adatbázis Normalizáció & Több Kihívás Támogatása (COMPLETED 2026-07-16):**
        *   Felbontottuk a sémát `runners` (név, egyedi email) és `runs` (kihívás regisztrációk, egyedi sorszám) táblákra.
        *   Módosítottuk a `process-payment.js`, `stripe-webhook.js`, `submit-feedback.js` és `daily_tracking.py` állományokat az új sémának megfelelően.
        *   A portálon (`portal.html`) bevezettünk egy legördülő választómenüt, amellyel a több kihívásra regisztrált felhasználók azonnal válthatnak a túráik között. A teljes felület (státusz, oklevél link, Kalandkönyv és Ajánlói fülek) dinamikusan frissül.
        *   Javítottuk a portál oklevél gombjának útvonalát `/predikalo/oklevel.html` értékre.
        *   **Beépített Teljesítés Igazoló és Admin Dashboard (COMPLETED 2026-07-16):** Létrehoztunk egy fájlfeltöltő tabot a portálon (GPX és fotó feltöltésével), egy hozzá tartozó adminisztrátori ellenőrző felületet (`admin.html` és `api/admin-approve.js`), valamint automatikus gratulációs e-mail küldést és dinamikus oklevél-sablon javítást (`oklevel.html` paraméter-dekódolás és tábla lekérdezés).
        *   **Google Sheets Teljes Leválasztás és Supabase Migráció (COMPLETED 2026-07-21, UPDATED 2026-07-26):** Teljesen megszüntettük a Google Sheets függőséget a fizetési, limit-ellenőrzési és visszajelzési folyamatokban. Biztonságos migrációval átmentettük az összes korábbi Prédikálószék résztvevőt a Google Sheets-ből a Supabase-be (`runners`, `orders`, `runs`, `shipments`) a Foxpost csomagszámokkal együtt. Az adatbázist megtisztítottuk a hibás tesztsoroktól (0 db null-campaign run maradt).
        *   **Foxpost API Közvetlen Feladás & Követés (COMPLETED 2026-07-21, UPDATED 2026-07-26):** Kialakítottunk egy teljesen automatizált Foxpost csomagfeladást közvetlenül az admin felületről. A háttérben futó követő script (`daily_tracking.py`) folyamatosan frissíti a státuszokat.
        *   **Közös Szállítás & Csomagolási Segédlet Részletezés (UPDATED 2026-08-28):**
            *   *Admin panel:* A Csomagolási és Kiszállítási Segédlet kártyái mostantól pontosan, színes jelvényekkel és sorszámokkal részletezik, hogy **melyik kampányból hány darab érmet** kell ugyanabba a borítékba/csomagba tenni (pl. `1x 🏔️ Prédikálószék (#006/100) + 1x 🌌 Nagy-Kevély (#006/100-PK)`).
            *   *Több kampányos összevonás:* Azonos email/címzett esetén a rendszer egy csomagba rendezi az összes feladatlan érmet, spórolva a szállítási díjjal.
            *   *Foxpost végpont:* Az összevont csomagokhoz egyetlen közös címkét generál a Foxpost API-nál.
        *   **Egységes Várakozó Lista & Manuális Jóváhagyás (`admin.html`) (UPDATED 2026-08-28):**
            *   *Külön Prédikálószék fül megszüntetve:* Az összes várakozó (beküldött igazolások ÉS még nem igazolt nevezők) egyetlen, átlátható felületre került a `⏳ Várakozó` fül alá.
            *   *Al-szűrők & Kampány jelvények:* Gyorsszűrők (`⏳ Összes várakozó`, `📥 Beküldött igazolások`, `🏃 Még nem igazolt`) és kampány szerinti szűrés (`🏔️ Prédikálószék`, `🌌 Nagy-Kevély`). Minden kártyán és a táblázatban is jól látható a kihívás neve és színe.
            *   *Azonnali Manuális Jóváhagyás:* Bármelyik nevezőnél közvetlenül a kártyáról elérhető a `✅ Manuális Jóváhagyás` gomb (pl. ha a futó e-mailben/Facebookon küldte az igazolást), ami azonnal kiküldi a gratulációs e-mailt és aktiválja az oklevelet.
        *   **Google Sheets Szállítási Adat Migráció & Tisztítás (COMPLETED 2026-08-06):**
            *   A Google Sheets `Nevezések` munkalapjáról hiánytalanul átmigráltuk a `ship_together_with` (együtt küldve) partnereket és a feladási állapotokat a Supabase `runs` és `shipments` táblákba.
            *   A Prédikálószék mind az 58 jóváhagyott éremjének feladási állapota frissült (0 feladatlan maradt).
        *   **Microsoft Clarity Heatmap & Session Recording (COMPLETED 2026-08-04):**
            *   Beépítve a Clarity tracking script (`xx85zg2g25`) az `index.html`, `nagykevely/index.html`, `predikalo/index.html`, `checkout.html` és `siker.html` oldalakra a felhasználói hőtérképek és videófelvételek rögzítéséhez.
        *   **Supabase Row-Level Security (RLS) & Adatbiztonsági Megoldás (COMPLETED 2026-08-19):**
            *   Megszüntettük a nyitott adatbázis-hozzáféréseket: RLS engedélyezése az összes publikus táblán (`runners`, `runs`, `feedbacks`, `orders`, `meta_daily_metrics`, `marketing_targets`, `shipments`).
            *   Töröltük a korábbi hibás `using (true)` szabályokat, és szigorú, csak a bejelentkezett felhasználók saját adataira (`auth.jwt() ->> 'email' = email`) korlátozott RLS szabályokat hoztunk létre.
            *   Az `admin.html` adatlekéréseit leválasztottuk a publikus anon kulcsról, és a jelszóval védett `/api/admin-data` szerveroldali végponton keresztül biztosítottuk a biztonságos betöltést.
        *   **Kombinált Ajánlói Kedvezmény Számítás & Levonási Rendszer (`checkout.html` & `api/checkout.js`) (COMPLETED 2026-08-12):**
            *   Módosítottuk az ajánlói kedvezmény kerekítését: a rendszer a még fel nem használt meglévő ajánlásokat (`unusedReferrals = totalReferrals - pastRedeemed`) összegzi a jelenlegi rendelésben vásárolt extra érmek számával (`qty - 1`). Az így kapott effektív ajánlásszám alapján határozza meg a kedvezmény szintjét (1: 10%, 2: 25%, 3: 45%, 4: 70%, 5+: 100%).
            *   **Visszaélés-védelem:** A sikeres vásárláskor a felhasznált ajánlási kreditek elmentődnek a `orders.referrals_redeemed` mezőbe, így a vásárló a jövőbeli rendeléseinél **nem tudja újra felhasználni a már levásárolt kedvezményt / ingyen érmet**.
            *   A kedvezmény **kizárólag a vásárló 1. (saját) érmére érvényesül**, a többi `(qty - 1)` érem teljes áron (`7 990 Ft`) marad.
        *   **Hirdetés (Ad) Szintű Meta Szinkron & Kreatív Követés (`fetch_meta_daily.py`) (COMPLETED 2026-08-13):**
            *   Átállítottuk a Meta szinkronizációt Ad (hirdetés) szintre: a szkript mostantól hirdetésenként menti a mutatókat (`ad_id`, `ad_name`, `adset_id`, `adset_name`).
            *   Hiánytalanul átkötöttük az UTM követő láncot (`utm_campaign`, `utm_term`, `utm_content` / `{{ad.name}}`) a landing oldalakon (`index.html`), a `checkout.html`-en és az `api/checkout.js` Stripe metadata-ban, így a Supabase `orders.utm_content` mezőjében és a webhookban hiánytalanul rögzül a konverziót hozó konkrét kreatív neve.
        *   **Szigorú Checkout Formátumvizsgálat (`checkout.html`) (COMPLETED 2026-08-06):**
            *   Szigorú kliensoldali formátumkényszereket építettünk be: nevező neve (min. 2 szó, pl. Vezetéknév + Keresztnév, de engedélyezi a 3 vagy több szavas neveket is pl. két keresztnév vagy titulus esetén), e-mail cím RegEx szűrés, magyar telefonszám formátum (`+36` / `06` + min. 9-11 számjegy), és számlázási/szállítási cím ellenőrzés (4 jegyű irányítószám + utca/házszám). Hibás mezők piros kiemelést kapnak, a nézet automatikusan a legfelső hibás mezőre ugrik és arra fókuszál.
        *   **Logisztikai Teszt Felhasználó Elrejtés (COMPLETED 2026-08-06):**

            *   Tesztek elrejtése toggle switch a Logisztika fülön, ami kiszűri a teszt sorszámos/emailes tételeket a csomagolási listából és a táblázatból.
        *   **Csoportos Nevezések & Tömeges Igazolás a Portálon (COMPLETED 2026-07-24):** A portál fejlécében a kiválasztott résztvevő neve jelenik meg, a többes nevezés dropdownja kiírja a résztvevők neveit, és a teljesítés igazolásakor egyetlen kattintással az összes kijelölt résztvevő teljesítése igazolható (tömeges GPX/fotó feltöltés).
        *   **Külső HTML Email Sablonok (COMPLETED 2026-07-24):** Külön HTML fájlokba szerveztük ki az összes tranzakciós e-mail sablont (a Supabase Auth megerősítő és Magic Link leveleit, valamint a sikeres nevezés welcome levelét: `email_welcome_template.html`). Ezzel megszüntettük az inline szövegeket, könnyen szerkeszthetővé és egységessé téve a kommunikációt.
        *   **Progresszív Ajánlói Kedvezmények a Kosár Szétbontásával (COMPLETED 2026-07-26):** Lecseréltük a Stripe kuponokat egy sokkal biztonságosabb, backend-szintű árszámításra. Ha a felhasználó rendelkezik ajánlásokkal (1-től 5+ barátig), a rendszer a kosár első érmének árát sávosan csökkenti (10%, 25%, 45%, 70%, 100% kedvezmény), míg az esetleges további érmeket teljes áron tartja. Így kizárt a kuponokkal való visszaélés és a teljes kosár ingyenessé tétele.
        *   **Automatikus Ajánlói Link Továbbítás (COMPLETED 2026-07-26):** Scriptet helyeztünk el a Nagy-Kevély marketing oldalon, ami a megosztott ajánlói linkekből (`?ref=...`) automatikusan továbbviszi az ajánló e-mail címét a checkout oldalra. A portálon generált ajánlói link mostantól a fő marketing oldalra irányítja a barátokat a közvetlen checkout helyett.
        *   **Ajánlói Hírlevél és Promóciós Sablon (COMPLETED 2026-07-26):** Külön HTML-be szerveztük ki az előző teljesítőknek kiküldhető hírlevél sablont (`email_promo_referral_template.html`), mely közvetlenül tartalmazza a dinamikus ajánlói linket és a progresszív mérföldköveket.
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
