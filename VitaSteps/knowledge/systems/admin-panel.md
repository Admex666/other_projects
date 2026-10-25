---
id: admin-panel
type: system
name: Admin Panel
status: active
description: Central administrative Single Page Application for proof verification, packing guides, Foxpost automated dispatch, and marketing break-even tracking.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/lib/admin/approve.js
  - landing_predikalo1/lib/admin/foxpost.js
  - landing_predikalo1/lib/admin/leads-email.js
  - landing_predikalo1/lib/admin/finance.js
  - landing_predikalo1/lib/admin/ai-assistant.js
  - landing_predikalo1/js/admin-ai.js
related:
  - "[[proof-verification|Proof Verification]]"
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[break-even|Break-Even]]"
  - "[[unit-economics|Unit Economics]]"
  - "[[how-to-manual-approve|How to Manual Approve]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# System: Admin Panel (`admin.html`)

The VitaSteps Admin Dashboard is a password-protected Single Page Application (`admin.html`) connecting directly to serverless Vercel endpoints and Supabase.

## Core Operational Views

### 1. ⏳ Várakozó (Egységes Várakozó és Jóváhagyó Lista)
* **Központi lista:** Minden várakozó résztvevő egy helyen kezelhető (mind a Prédikálószék, mind a Nagy-Kevély futók).
* **Al-szűrők:**
  - `⏳ Összes várakozó`: Minden még nem teljesített regisztráció.
  - `📥 Beküldött igazolások`: Portálon képet vagy GPX-et feltöltött, elbírálásra váró futók.
  - `🏃 Még nem igazolt`: Nevezett, de még nem igazolt résztvevők.
* **Kihívás szerinti gyorsszűrő:** `Összes`, `🏔️ Prédikálószék`, `🌌 Nagy-Kevély`.
* **Közvetlen `✅ Manuális Jóváhagyás`:** Egykattintásos jóváhagyás külső (e-mail, közösségi média) igazolásokhoz.

### 2. ✅ Jóváhagyott (Approved)
* Sikeresen hitelesített és oklevéllel ellátott teljesítők archívuma.

### 3. 🦊 Logisztika (Foxpost)
* **Háromfázisú státuszkezelés:**
  - `📦 Feladandó`: Jóváhagyott, de még nem feladott csomagok (`completed=true`, `shipped=false`).
  - `📬 Már feladva`: Foxpost-on keresztül feladott, úton lévő csomagok (`shipped=true`, `received_at=NULL`).
  - `✅ Megérkezett`: Foxpost automatán átvett csomagok (`received_at IS NOT NULL`), a `daily_tracking.py` alapján frissítve.
* **Csomagolási és Kiszállítási Segédlet:** Kártyás nézet, amely kampányonként részletezi a borítékba teendő érmek sorszámait és darabszámát (több kampányos összevonás támogatása azonos címzettnél).
* **1-Kattintásos Foxpost API Feladás:** Csomagok automatikus létrehozása, vonalkódok generálása és követési kód szinkronizáció.

### 4. 💬 Visszajelzések (Feedbacks & Reviews)
* **Visszajelzési KPI Kártyák:**
  - Összes kitöltés száma és fotófeltöltések aránya.
  - Átlagos érem minőség értékelés (5.0 skála).
  - Átlagos csomagolás & szállítási elégedettség (5.0 skála).
  - Átlagos NPS pontszám & Promóter arány (9–10 pontot adók %).
  - Újra részt venne arány (%).
* **Következő tájegység igények összegzése:** Felhasználói szavazatok és igények összesítése jövőbeli kihívások tervezéséhez (pl. Börzsöny, Mátra, Balaton-felvidék, Bükk).
* **Részletes Véleménykártyák:** Futó adatok, csillagos értékelések, NPS jelvény, „Mi tetszett legjobban” idézetek, „Mit tenne jobbá” észrevételek, és kattintásra nagyítható beküldött élmény/éremfotók.
* **Szűrés:** Kampányonként (`Mindkét kihívás`, `Nagy-Kevély`, `Prédikálószék`), 5-csillagos, szöveges vagy fotós értékelésekre.

### 5. 📊 Marketing & Break-Even Dashboard
* **Megtérülés (Break-Even):** 193 000 Ft fix költség (163k érem + 30k könyvelés) törlesztésének követése a termékenkénti nettó fedezetből.
* **Tételes Változó Költségek (CM):** Bruttó bevétel − Meta(+ÁFA) − Foxpost (1 250 Ft) − Stripe (1,5%+50Ft) − Számlázz.hu (35 Ft) − Csomagolás (120 Ft).
* **Lojalitási Kohorsz Analízis:** Új vs. visszatérő vásárlók aránya kihívásonként.

### 6. 💳 Pénzügy & Cashflow Modul (3 Al-fül)
A pénzügyi modul 3 önálló, mélyreható al-nézetre van bontva:

* **📊 P&L & Kampány Audit (1. al-fül):**
  - **Árbevétel bontás:** Érmek eladása, szállítási felárak, többérmes kosarak (1, 2, 3+ érem eloszlás), kedvezmények és referral levonások.
  - **Közvetlen költségek (COGS & Fulfillment):** Érem gyártási bekerülési ár (Capex amortizáció), csomagolás (150 Ft), Foxpost szállítás (1 140 Ft / 2 400 Ft), Stripe fizetési jutalék (1.5% + 85 Ft), Számlázz.hu e-számla díj (40 Ft).
  - **Marketing költség:** Meta Ads nettó költés és a fizetendő 27% import ÁFA.
  - **Hozzájárulási eredmény (Contribution Margin):** Bruttó és nettó fedezet/profit forintban és százalékban kampányonként (`Nagy-Kevély`, `Prédikálószék`, `Mindkettő`).
  - **Készletkimutatás & Értékelés:** Eladott és raktáron maradt darabszámok, bekerülési érték és potenciális árbevétel érménként.

* **📈 Cashflow & Mérleg Kimutatás (2. al-fül):**
  - **Élő Pénzügyi Mérlegkimutatás (Nyugta kártya):**
    - `Revolut Pro egyenleg` + `Stripe elérhető egyenleg` = **Jelenlegi likvid tőke**.
    - `Stripe jóváírás alatt álló` = **Likvid tőke hamarosan**.
    - `Prédikálószék Készlet` (db × beszerzési egységár) + `Nagy-Kevély Készlet` (db × beszerzési egységár) = **📦 Készletek összesen** (raktárkészlet fizikai értéke).
    - **👑 Mérlegfőösszeg** = Likvid tőke + Készletek összesen.
  - **Idővonal & Vizuális Grafikon:** Dupla görbén mutatja a halmozott likvid cashflow-t és a teljes mérleg vagyont, dinamikus Alibaba gyártási Capex felismeréssel és Stripe-Revolut belső átutalás szűréssel.

* **🧾 Nyers Tranzakciók (3. al-fül):**
  - Egységesített főkönyv (Revolut Pro banki kivonatok + Stripe kifizetések és vevői tranzakciók).
  - Időszak (`Összes`, `30 nap`, `7 nap`, havi bontás), számla (`Revolut`, `Stripe`) és kategória szerinti szűrés, szabadszavas tranzakció-keresővel.


### 7. 🤖 AI Asszisztens (Gemini 3.8 Pro & Flash)
A VitaSteps Admin AI Asszisztens (`lib/admin/ai-assistant.js`, `js/admin-ai.js`) közvetlen, több-lépéses **Gemini Function Calling** kapcsolaton keresztül valós idejű elemzési és lekérdezési hozzáférést biztosít a teljes ökoszisztémához (önálló **🤖 AI Asszisztens** fülön és bármely más fülről megnyitható jobb alsó lebegő **Slide-Over Drawer** ablakban):

* **6 Integrált Tool (Függvényhívás):**
  1. `get_database_overview`: Valós idejű készlet-, nevezés-, igazolás-, Foxpost csomagolási-, visszajelzés- (NPS) és lead-összefoglaló kampányonként (`Nagy-Kevély` vs. `Prédikálószék`).
  2. `query_supabase_table`: Rugalmas, csak-olvasható lekérdezés bármelyik [[supabase|Supabase]] táblán (`runners`, `runs`, `orders`, `shipments`, `feedbacks`, `leads`, `meta_daily_metrics`, `analytics_sessions`, `analytics_visitors`, `analytics_events`).
  3. `get_financial_and_cashflow_data`: Élő [[stripe|Stripe]] egyenleg, kifizetések, [[revolut|Revolut Pro]] számlatörténet kategória-bontással, raktárkészlet-értékelés és kampány-szintű P&L.
  4. `get_marketing_and_creatives_data`: [[meta-ads|Meta Ads]] kreatívok (`meta_kreativ_napi_riport.csv` és `meta_daily_metrics`) CPA, ROAS, CTR és napi költés elemzése.
  5. `read_knowledge_graph`: A teljes `knowledge/` tudásgráf és `config/campaigns.json` beolvasása és keresése.
  6. `search_and_read_emails`: Élő IMAP kapcsolat a `vitasteps.team@gmail.com` (és opcionális másodlagos) Gmail postafiókhoz beérkezett ügyféllevelek, [[foxpost|Foxpost]] és [[szamlazz-hu|Számlázz.hu]] értesítések keresésére és olvasására.
