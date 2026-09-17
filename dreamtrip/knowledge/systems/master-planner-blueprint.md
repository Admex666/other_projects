---
id: master-planner-blueprint
type: system
name: Master Planner Blueprint & System Architecture
status: active

description: Az Optivoya Master Travel Planner teljes, átfogó rendszerspecifikációja (Master Blueprint) potenciális co-founderek és mérnökök számára. Részletezi a piaci problémát, a termékvíziót, az 5-lépéses progresszív döntési folyamatot, az AHP és PROMETHEE II matematikai döntési motort, a valós idejű külső adatforrásokat, a kosár- és ajánlatkészítő motort, valamint a monetizációs modellt.

source:
  type: code
  ref: app.services.planner_service

code:
  - app/api/v2/planner.py
  - app/services/planner_service.py
  - app/services/trip_scoring_service.py
  - app/services/experience/trip_generator.py
  - templates/planner/planner_wizard.html
  - static/js/planner/planner_state.js
  - static/js/planner/planner_intake.js
  - static/js/planner/planner_destinations.js
  - static/js/planner/planner_flights.js
  - static/js/planner/planner_stays.js
  - static/js/planner/planner_activities.js
  - static/js/planner/planner_summary.js
  - static/js/planner_wizard.js
  - static/js/trip_cart.js

related:
  - "[[master-planner-wizard]]"
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"
  - "[[itinerary-optimization]]"
  - "[[experience-ingestion-pipeline]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[guided-progressive-decision-flow]]"
  - "[[numbeo-cost-model]]"
  - "[[honest-scraping-policy]]"
  - "[[progressive-async-prefetching]]"
  - "[[trip-cart-engine]]"
  - "[[fastapi-backend]]"
  - "[[supabase-database]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
  - "[[open-meteo-api]]"
  - "[[numbeo-database]]"
  - "[[effective-vacation-time]]"
  - "[[unified-trip-score]]"
  - "[[experience-intelligence-engine]]"

used_by:
  - "[[fastapi-backend]]"

---

# Optivoya — Master Planner System Blueprint & Architecture
> **Az intelligens utazási operációs rendszer (End-to-End Travel Intelligence & Decision Engine)**  
> *Készült: Alapítóknak, Befektetőknek és Vezető Rendszermérnököknek*

---

## 1. Vezetői Összefoglaló (Executive Summary & The "Why")

### A Piaci Probléma: A Széttöredezett Tervezés és az "Elemzési Bénultság"
Ma egy átlagos utazó **10–20+ órát** tölt egyetlen hétvégi vagy nyaralási út megszervezésével. Ennek során **15–25 böngészőfül** között ugrál:
* **Skyscanner / Google Flights:** Keresi az olcsó járatot, de nem tudja, az adott városban milyen lesz az időjárás vagy a helyi megélhetési költség.
* **Booking.com / Airbnb:** Keresi a szállást, de a járat pontos érkezési/indulási ideje még nincs szinkronban, a belvárosi távolság és a transzfer bizonytalan.
* **TripAdvisor / Blogok / Instagram:** Kétségbeesetten próbálja összeszedni, mit érdemes csinálni, elkerülve a turistacsapdákat.
* **Numbeo / AccuWeather:** Próbálja kisakkozni, mennyibe fog kerülni az ebéd és kell-e esernyőt vinni.

**Az eredmény:** *Analysis Paralysis* (döntési képtelenség), elszálló költségvetés, fárasztó járatátszállások, és az érzés, hogy a tervezés nem élmény, hanem stresszes munka.

### Az Optivoya Megoldása: Intelligens Döntéstámogató Rendszer (Nem Csak Kereső)
Az Optivoya nem egy hagyományos OTA (Online Travel Agency) és nem egy újabb egyszerű aggregátor.  
Az Optivoya egy **tudományos alapokon nyugvó, multi-kritériumos döntési motor (MCDA)**, amely:
1. **Rögzíti az utazó egyéni Döntési DNS-ét** (egyedi preferenciák, tolerancia-határok, aktív szempontok).
2. **Keresztoptimalizálja az összes pillért:** Desztináció + Repülőjegy + Szállás + Élmények.
3. **Egyetlen interaktív Utazási Kosárba és B2B Ajánlatba foglalja a teljes utat**, valós idejű árakkal és átlátható pontszámokkal.

---

## 2. Az 5-Lépéses Progresszív Döntési Folyamat (End-to-End Flow)

Az Optivoya a **[[guided-progressive-decision-flow]]** elvét követi: soha nem zúdít egyszerre kezelhetetlen adatmennyiséget a felhasználóra, hanem vezérelt, lineáris, mégis rugalmas lépéseken viszi végig:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 0: Unified Intake & Személyre Szabott Döntési DNS                          │
│ • Indulási város (Kiwi autocomplete) + Dátumválasztás (Fix / Intervallum / Hónap)│
│ • Utazási Prioritások (AHP súlyozás & PROMETHEE döntési küszöbök)                │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Célállomás Választás (Multi-Pillar Destination Matching)                 │
│ • 40+ európai város rangsorolása egyéni súlyok szerint                          │
│ • Költség (Numbeo) + Időjárás (Open-Meteo) + Biztonság + Élmény illeszkedés     │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Repülőjárat Optimalizáció (Flight Intelligence)                          │
│ • Kiwi.com GraphQL élő járatok a kiválasztott városba                           │
│ • Ár vs. Menetidő vs. Átszállás + "Hasznos Nyaralási Idő" (Effective Vacation)  │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Szálláslehetőségek (Accommodation Aggregation)                           │
│ • Cozycozy aggregált szálláskínálat a zárolt utazási dátumokra                  │
│ • Csillagok, vendégértékelés, ellátás, belvárosi távolság                       │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Élmények & Komplett Utazási Terv (Experiences & Proposal)                │
│ • Személyre szabott látnivalók, éttermek, programok                              │
│ • Lebegő Utazási Kosár (TripCart) + Részletes B2B Ajánlat / PDF Export           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Részletes Lépésről-Lépésre Funkcionális Specifikáció

### Step 0: Unified Intake & Döntési DNS (A Tervezés Alapja)
* **Kanonikus Indulási Hely:** Élő IATA és városkód autocomplete a [[kiwi-scraper]] modulon keresztül.
* **Rugalmas Dátumkezelés (3 Mód):**
  1. *Pontos dátum (Exact):* Fix napok Flatpickr naptárral.
  2. *Időintervallum (Window):* Pl. indulás szept. 1-15 között, vissza szept. 10-25 között, tartózkodás 4-7 nap.
  3. *Egész hónap (Month):* Pl. 2026. októberben egy 5 napos utazás.
* **Kötelező Döntési DNS (Decision DNA Modal):**
  * **Kétfázisú döntési folyamat:**
    1. *1. Fázis (Kiválasztás & Jóváhagyás):* A felhasználó először bejelöli, mely szempontok számítanak neki, és jóváhagyja azokat. A csúszkák ezelőtt nem jelennek meg.
    2. *2. Fázis (Súlyozás):* Csak a jóváhagyott szempontok kerülnek összehasonlításra. Bármikor módosítható a „✎ Szempontok módosítása” gombbal.
  * **Maximum 5 Összehasonlítás:** Kognitív túlterhelés elkerülésére legfeljebb 5 feszítő pár kerül a felhasználó elé, a többit a motor geometriai tranzitivitással számítja ki.
  * **Kiterjesztett 9-pontos Saaty-skála:** A csúszkán mindkét irányban +1 barázda (1, 3, 5, 7, 9 arányok; Extrém mértékben 9x és 1/9).
  * **Toleranciaküszöbök:** "Mennyi felárat ér meg 1 órával rövidebb repülőút?" (PROMETHEE küszöbök).
* **Egyetlen Fő CTA:** Nincs konfúzió: az űrlapon mindig szigorúan egyetlen fő CTA gomb található, amely dinamikusan vált a *„Saját szempontok beállítása (A kereséshez kötelező) →”* és a *„Célállomások Keresése & Tervezés Indítása →”* állapotok között.

### Step 1: Célállomás Rangsorolás (Destination Matching)
* **4-Pilléres Kiértékelés:**
  1. *Becsült Költség:* Napi étkezés + helyi transzfer a [[numbeo-database]] alapján + átlagos repülőjegy és szállásköltség.
  2. *Klíma & Időjárás:* [[open-meteo-api]] 10 éves historikus és előrejelzési adatai (hőmérséklet, csapadékos napok).
  3. *Biztonság:* Numbeo Safety Index normalizálva.
  4. *Élményprofil:* 8 élménykategória (Gasztronómia, Kultúra, Tengerpart, Természet, stb.) koszinusz-illeszkedése.
* **Intelligens Célállomás Kártyák:**
  * Személyre szabott egyezési pontszám (pl. 94% Match).
  * Dinamikus hőmérsékleti jelvény és várható időjárás.
  * Transzparens költségbecslés (nem csak a jegyár, hanem a teljes ott-tartózkodás költsége!).

### Step 2: Járat Intelligencia & Hasznos Nyaralási Idő (Flight Selection)
* **Élő Kiwi.com GraphQL Integráció:** Valós jegyárak és menetrendek.
* **Többdimenziós Értékelés:** Nem a legolcsóbb "fapados hajnali 5-ös" járat nyer automatikusan, ha miatta elveszik egy teljes nap.
* **[[effective-vacation-time]] Koncepció:**
  * Kiszámolja a célállomáson tölthető, ébren lévő, hasznos órákat.
  * Bünteti az extrém korai indulást (alváshiány) és a késő esti érkezést (elveszett nap).
* **Preferált Utazási Napok és Indulási Idősávok:** Péntek délutáni indulás és vasárnap esti visszajövetel előnyben részesítése.

### Step 3: Szállás Aggregáció (Stays Matching)
* **Élő Cozycozy Adatfolyam:** Nem korlátozódik egyetlen szolgáltatóra; hotelek, apartmanok és vendégházak valós árai.
* **Dátumzárolt Keresés:** A Step 2-ben kiválasztott konkrét repülőjárat érkezési és indulási dátumaira szűkítve.
* **Minőségi Küszöbök:** Minimális csillagszám, 7.5+ vagy 8.5+ vendégértékelés, reggeli opció, belvárosi elhelyezkedés.

### Step 4: Élmények, Utazási Kosár & Ajánlat Export
* **[[experience-intelligence-engine]]:**
  * Több forrásból (OpenStreetMap, Wikidata, Google Places) gyűjtött POI-k.
  * Személyre szabott programcsomagok és időzített napi útiterv (`[[itinerary-optimization]]`).
* **Lebegő Utazási Kosár ([[trip-cart-engine]]):**
  * Képernyő alján (mobilon) vagy jobb oldalán dokkolva (desktopon).
  * Folyamatosan mutatja a kalkulált összköltséget, a személyenkénti árat és a járat/szállás státuszát.
* **B2B Ügyfélajánlat Készítő ([[proposal-generation]]):**
  * Egyetlen kattintással generálható, elegáns, nyomtatható vagy PDF-be menthető utazási dosszié.
  * Tartalmazza a napi bontású programot, a tételes költségeket és a foglalási linkeket.

---

## 4. A Matematikai és Algoritmikus Motor (Under the Hood)

Az Optivoya versenyelőnye a mély tudományos megalapozottság, amelyet a versenytársak nem használnak:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 1. AHP (Analytic Hierarchy Process) — Saaty Geometriai Átlag                      │
│ Bemenet: Páros preferenciák a felhasználó által kiválasztott szempontok között   │
│ Logika: Súlyvektor w_i = (∏ a_ij)^(1/n) / ∑ w_k                                   │
│ Eredmény: Dinamikus, konzisztens súlyok (összegük pontosan 100%)                  │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 2. PROMETHEE II — Outranking Preferencia Függvények                              │
│ Bemenet: Valós alternatívák (járatok, hotelek), q (közömbösségi), p (előny) küszöb│
│ Logika: D_j(a,b) = f_j(a) - f_j(b) → P_j(a,b) V-alakú/U-alakú preferencia        │
│ Eredmény: Pozitív (Phi+) és Negatív (Phi-) áramlások → Nettó preferenciarangsor  │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 3. Unified TripScore™ — Globális Kompozit Mutató (0–100)                         │
│ Súlyozott összegzés: TripScore = w_d·DestScore + w_f·FlightScore + w_s·StayScore │
│ Transzparens magyarázat a felhasználó felé (X% ár-érték, Y% kényelem)             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

* **Zero Arbitrary Weights:** Nincsenek beégetett, "hasraütésszerű" konstansok. A felhasználó döntési mátrixa vezérli a rendszert.
* **Kétfázisú Szempont-Jóváhagyás:** A felhasználó először kiválasztja és jóváhagyja az aktív szempontokat; a páros csúszkák csak a jóváhagyás után jelennek meg. Egyetlen szempont esetén a szempont automatikusan 100%-os súlyt kap.
* **Maximum 5 Összehasonlítás & Tranzitivitás:** A felületen legfeljebb 5 feszítő páros csúszka jelenik meg; ha 4 szempont esetén 6 pár lenne, a kimaradó párt a motor a geometriai tranzitivitás ($M_{ik} \cdot M_{kj}$) segítségével azonnal és pontosan kiszámítja.
* **Kiterjesztett 9-Pontos Saaty-Skála:** A csúszkán mindkét irányban +1 barázda található (1, 3, 5, 7, 9 arányok), lefedve a teljes klasszikus Saaty-tartományt a finomhangoláshoz.
* **[[honest-scraping-policy]]:** Nincsenek kitalált dummy járatok vagy generált kamu árak. Ha egy partner API nem ad találatot, a rendszer transzparensen kezeli és alternatívát kínál.

---

## 5. Rendszerarchitektúra és Adatfolyam

```text
[ KLIENS (Browser / Mobile PWA) ]
  • Vanilla CSS Design System (Sötét/Világos luxus téma, üveghatás, mikróanimációk)
  • Vanilla JS Modulok (PlannerState, WizardFacade, TripCart, DecisionDNAWizard)
  • Offline-first LocalStorage szinkronizáció (Döntési DNS & Kosár állapot)
                                ▲
                                │ REST / JSON (FastAPI V2 Endpoints)
                                ▼
[ BACKEND (Python FastAPI — app/) ]
  • PlannerService & TripScoringService
  • Aszinkron I/O (httpx, asyncio)
  • Többszintű gyorsítótárazás (In-memory + Redis kész)
                                ▲
                                │ Külső Integrációk & Tárolás
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ KANONIKUS KÜLSŐ ÉS BELSŐ FORRÁSOK                                                │
│ ├── Kiwi.com GraphQL API ────────► Élő járatmenetrendek és jegyárak              │
│ ├── Cozycozy Scraper ────────────► Élő szállásárak (hotelek, apartmanok)         │
│ ├── Open-Meteo API ──────────────► Historikus és előrejelzett éghajlati adatok  │
│ ├── Numbeo Database (JSON) ──────► 40+ európai város megélhetési indexe          │
│ ├── OSM / Wikidata / Google ─────► Többforrásos POI és látványosság adatbázis    │
│ └── Supabase Cloud (Postgres) ───► Felhasználói profilok, béta adatok, telemetria│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Üzleti Modell és Monetizáció (Hogyan Termel Pénzt?)

Az Optivoya három rétegű bevételi pillérre épül:

1. **Metasearch & Affiliate Jutalékok (B2C Alapmodell):**
   * Minden járatfoglalás (Kiwi, Skyscanner átkattintás) után **1.5% – 3%** jutalék.
   * Minden szállásfoglalás (Booking.com, Expedia, Cozycozy) után **4% – 8%** jutalék.
   * Élmény- és belépőjegy foglalások (GetYourGuide, Viator) után **8% – 12%** jutalék.
   * *A hagyományos OTA-khoz képest a konverzió sokkal magasabb*, mert az utazó nem külön-külön keresgél, hanem egy komplett, harmonizált csomagot kap.

2. **Optivoya Pro / B2B SaaS Előfizetés (Utazási Irodáknak és Tanácsadóknak):**
   * Független utazásszervezőknek és butik-irodáknak havi előfizetés (pl. 49–149 €/hó).
   * Saját logóval ellátott (white-label) PDF ajánlatok készítése ügyfeleknek 60 másodperc alatt.
   * Egyedi jutalék-felárazás (markup) beépítése a generált ajánlatokba.

3. **Prémium Concierge & AI Asszisztens:**
   * Dinamikus újratervezés késés vagy járattörlés esetén.
   * Személyre szabott digitális idegenvezető a teljes utazás alatt.

---

## 7. Miért Most és Miért az Optivoya? (A Védvonal / Moat)

| Hagyományos Szereplők (Google, Booking) | Mesterséges Intelligencia Csetbotok (ChatGPT) | **Optivoya** |
| :--- | :--- | :--- |
| Csak egyetlen szegmensre fókuszálnak (csak járat VAGY csak hotel). | Gyakran hallucinálnak árakat és nem létező járatokat. | **Komplett E2E integráció:** Desztináció + Járat + Hotel + Program. |
| Nincs személyes döntési matematika (csak rendezés: legolcsóbb / leggyorsabb). | Nem képesek közvetlen foglalási kosarat kezelni. | **Valós idejű élő árak** és foglalható járat/szállás adatok. |
| A felhasználóra hárítják az összekötés és döntés 100%-át. | Nincs optimalizált időzítés és menetrend-összehangolás. | **AHP + PROMETHEE II:** Tudományosan megalapozott egyéni döntési modell. |

---

## 8. Mérföldkövek és Jelenlegi Állapot (Current Status)

* **Funkcionális Készültség:** 
  * A teljes 5-lépéses folyamat működik.
  * Valós Kiwi járatkeresés és Cozycozy szállásintegráció él.
  * Numbeo és Open-Meteo adatbázisok beépítve.
  * Dinamikus AHP szempont-előszűrés és emberközpontú döntési felület kész.
  * Lebegő TripCart kosár és ajánlatkészítő üzemképes.
* **Teszteltség és Megbízhatóság:**
  * 100%-ban validált tudásgráf (`scripts/knowledge/validate.py`).
  * Hibamentes, szigorú JavaScript kódkészlet.
  * **Teljeskörű Playwright E2E Tesztcsomag (`tests/e2e/`):** Automatikus böngésző-interakciós tesztek, amelyek lefedik a teljes 5-lépéses Golden Flow-t, a szűrőket, a modálokat és a reszponzív nézeteket.
* **Következő Lépés a Co-founderrel:**
  * Béta felhasználói tesztelés és konverziós tölcsér mérés.
  * Affiliate partnerek éles szerződéseinek véglegesítése.
  * Mobil PWA és B2B értékesítési csatornák elindítása.

---

## 9. Automatizált E2E Tesztelési Architektúra (Playwright Test Suite)

A Master Planner és a B2B landing stabilitását egy szisztematikus, headless Chromium alapú Playwright E2E tesztcsomag garantálja (`tests/e2e/`):

### Főbb Tesztcsoportok:
1. **Master Planner Golden Flow (`test_master_planner_e2e.py`):**
   * `test_planner_page_load_and_elements`: Oldalbetöltés és 0 fatális konzolhiba ellenőrzése.
   * `test_step0_intake_controls_and_presets`: Gyorsválasztó pilulák, felnőtt/gyermek számlálók, naptári módváltás (Exact vs. Interval), stílus-chipek.
   * `test_decision_dna_modal_workflow`: Kétfázisú döntési DNS modál megnyitása, szempontok kijelölése és AHP/PROMETHEE súlyok mentése.
   * `test_full_golden_flow_dummy_mode`: A teljes 5-lépéses útvonal (Célállomás választás $\to$ Járat kiválasztás $\to$ Szállás benchmark $\to$ Élmények $\to$ Kész Terv & Lebegő Kosár) szimulálása.
   * `test_stepper_back_and_forward_navigation`: Lépések közötti közvetlen ugrás és állapotmegőrzés.
   * `test_mobile_viewport_no_horizontal_overflow`: 375px mobil nézet (iPhone SE) túlcsordulás-mentességének validálása.
2. **B2B Landing & Kalkulátor (`test_b2b_landing_e2e.py`):**
   * Értékajánlat és Anti-ChatGPT blokk megléte.
   * ROI Kalkulátor csúszkák és 1-kattintásos profil-presetek dinamikus számítása.
   * Béta Hozzáférési Kapu (Access Gate) modál megnyitása és űrlapellenőrzése.
   * Mobil layout és gombelrendezés ellenőrzése.

### Futtatási Parancs:
```powershell
python -m pytest tests/e2e/ -v
```
