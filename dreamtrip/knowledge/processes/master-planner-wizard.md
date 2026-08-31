---
id: master-planner-wizard
type: process
name: Master Travel Planner Wizard
status: active

description: Egyetlen integrált, 4-lépéses utazástervezési folyamat, amely közös intake űrlappal, Kiwi helyszín-autocomplettel, Flatpickr naptárkezeléssel, modális szempontprioritási kérdőívvel (desztináció és szállás) és Cozycozy szállásaggregációval működik.

source:
  type: code
  ref: app.services.planner_service

code:
  - app/api/v2/planner.py
  - app/services/planner_service.py
  - app/main.py
  - app/scrapers/accommodation_scraper.py
  - templates/planner/planner_wizard.html
  - static/js/planner/planner_state.js
  - static/js/planner/planner_intake.js
  - static/js/planner/planner_destinations.js
  - static/js/planner/planner_flights.js
  - static/js/planner/planner_stays.js
  - static/js/planner/planner_summary.js
  - static/js/planner_wizard.js
  - static/js/decision_dna/dna_math.js
  - static/js/decision_dna/dna_dest_step.js
  - static/js/decision_dna/dna_flight_step.js
  - static/js/decision_dna/dna_stay_step.js
  - static/js/decision_dna/dna_summary_step.js
  - static/js/decision_dna_wizard.js
  - static/js/components.js


related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[guided-progressive-decision-flow]]"
  - "[[cozycozy-scraper]]"

used_by:
  - "[[fastapi-backend]]"

---

# Process: Master Travel Planner Wizard

A **Master Travel Planner** a platform legmagasabb szintű folyamata, amely összeköti a teljes utazástervezést egyetlen gördülékeny folyamatban:

```text
0. Lépés: Unified Intake & Személyre Szabott Prioritások
   (Kiwi élő autocomplete, 3 Dátummód + Flatpickr naptár, Desztináció és Szállás prioritásmodálok, Teljes szűrőkészlet)
         ↓
1. Lépés: Célállomás kiválasztása
   (Sajátvektor-súlyozott Open-Meteo klíma + Kiwi járatárak + Numbeo költség/biztonság pontozás)
         ↓ (🏆 Kiválasztás -> Automatikus járatkeresés indul a háttérben)
2. Lépés: Járat kiválasztása
   (Kiwi GraphQL retúr járatok dinamikus skálázással [napi 5 járat, 30–150 db] + PROMETHEE II rangsorolás)
         ↓ (✈️ Kiválasztás -> Automatikus szálláskeresés indul, járatdátumok zárolva)
3. Lépés: Szállás kiválasztása
   (Cozycozy élő szállásaggregáció a pontos éjszakaszámra + kategória/típus/reggeli/felszereltség szűrés)
         ↓ (🏨 Kiválasztás -> Összesített terv)
4. Lépés: Összesített Terv
   (Tételes Numbeo matematikai költségbontás + 1-kattintásos PDF / Nyomtatás)
```

---

## 🛠️ Architektúra és Főbb Komponensek

### 1. Központi Kiwi Autocomplete & Saját Léptetők
* **Helyszínkereső:** A rendszer a központi `window.initLocationAutocomplete` komponenst használja (`/api/locations/autocomplete`), biztosítva a szabad szöveges város- és repülőtér-kiegészítést IATA kódokkal, ország- és repülőtér-alcímkékkel.
* **Egyedi léptetők (`+` és `−` stepperek):** A natív böngésző inputok helyett a platform egységes stílusú `stepper-circle-btn` és `stepper-control-box` komponensei kezelik a felnőttek, gyermekek, kinttartózkodási napok és max. menetidő kiválasztását.

### 2. Dátumkezelési Módok és Flatpickr Integráció
1. **Pontos Dátumok (`exact` — Alapértelmezett):** A bevált `window.initAdvisorDatePicker` Flatpickr naptárkomponens és gyorsválasztó pilulák (`Jövő hét`, `3 hét múlva`, `Hosszú hétvége`). Pontos dátumok esetén a tartózkodási időtartam fix, így az AHP és PROMETHEE súlya automatikusan $w_{stay} = 0.0$.
2. **Időintervallum & Tartózkodási Keret (`interval`):** Odaút időablak (`out_from`–`out_to`), visszaút időablak (`in_to`) és Min-Max kinttartózkodási napok (`min_stay`, `max_stay`). Ekkor a tartózkodási időtartam illeszkedése ($g_4$) aktívan beleszámít a PROMETHEE II outranking flow-ba.

### 3. Modális Prioritásvarázslók és Progressive Disclosure (Zárolási Rendszer)
* **3-Pilléres Desztináció prioritások:** A redundáns pénz-pénz összevetések kivezetésével 3 független pillér (Teljes Utazási Költség, Klíma, Közbiztonság) páros összehasonlítása mindössze 3 gyors kérdésben az `AHPWizard` modálban.
* **Progressive Disclosure:** A 4. pont (Repülési szűrők) és az 5. pont (Szállás szűrők) addig zárolva (`opacity: 0.45; pointer-events: none`) maradnak, amíg a felhasználó ki nem tölti a prioritási kérdőívet.
* **Preset-mentes döntéshozatal:** A repülési szempontoknál nincsenek mesterséges preset sablonok, így a döntési súlyok valódi felhasználói válaszokból származnak.
* **Szállás prioritások:** Ár / Éjszaka, Vendégértékelés & Csillagok, Központi Elhelyezkedés, és Felszereltség & Reggeli páros összehasonlítása.
* **Felhasználóbarát felület:** Szakzsargon (AHP, sajátvektor, CR) kivezetve; a vissza nyíl biztonságosan bezárja a modált (`this.onBack()`).

### 4. 5-Dimenziós PROMETHEE II Járatrangsoroló és Kétirányú Gyorsítótár
* **PROMETHEE II 5-dimenziós kiértékelés:** $g_1$ Teljes ár, $g_2$ Menetidő, $g_3$ Átszállások, $g_4$ Tartózkodási illeszkedés (intervallum módban), $g_5$ Napszak-illeszkedés V-alakú lineáris preferenciafüggvénnyel és nettó outranking flow ($\Phi_{net}$) relevanciával.
* **Kétirányú Intelligens Gyorsítótár (Frontend Session Storage & Backend Memory Cache):**
  * Kliensoldalon a `sessionStorage` kulcsok alapján az azonos feltételekkel már lekérdezett járatok és szállások **0 ms alatt, azonnal, loader nélkül** jelennek meg visszalépés vagy oldalfrissítés esetén.
  * Szerveroldalon a `_FLIGHTS_CACHE` in-memory dict 30 perces TTL-lel tehermentesíti a Kiwi és Cozycozy scrapereket.
* **Szálláskártyák fotókkal és közvetlen `Megtekintés ↗` linkkel:** Élő Cozycozy képek, szolgáltatói badgek, valamint új lapon megnyitható külső előnézeti link a foglalás előtti ellenőrzéshez.

