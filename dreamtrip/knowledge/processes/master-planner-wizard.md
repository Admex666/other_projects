---
id: master-planner-wizard
type: process
name: Master Travel Planner Wizard
status: active

description: Egyetlen integrált, 5-lépéses utazástervezési folyamat közös intake űrlappal, Kiwi helyszín-autocomplettel, 4-pilléres AHP és Level 2 koszinusz élményilleszkedéssel, járatértékeléssel hasznos nyaralási idővel, szállásaggregációval, személyre szabott programválasztóval, Unified TripScore-ral és B2B ajánlat exporttal.

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
  - static/js/trip/trip_report.js
  - static/js/trip/trip_store.js
  - static/js/trip_cart.js

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
  - "[[effective-vacation-time]]"
  - "[[unified-trip-score]]"

used_by:
  - "[[fastapi-backend]]"

---

# Process: Master Travel Planner Wizard

A **Master Travel Planner** a platform legmagasabb szintű folyamata, amely összeköti a teljes utazástervezést egyetlen gördülékeny, 5-lépéses folyamatban:

```text
0. Lépés: Unified Intake & Személyre Szabott Prioritások
   (Kiwi élő autocomplete, 3 Dátummód + Flatpickr naptár, 4-Pilléres Decision DNA [Költség, Klíma, Biztonság, Élmények], Élményfókusz csipek és Logisztikai keret)
         ↓
1. Lépés: Célállomás kiválasztása
   (4-pilléres AHP + Level 2 Vektoros Koszinusz Hasonlóság + Élmény & Vibe profil badge-ek: látnivalószám, sétálhatósági %, kiemelt nevezetességek)
         ↓ (🏆 Kiválasztás -> Automatikus járatkeresés indul a háttérben)
2. Lépés: Járat kiválasztása
   (Kiwi GraphQL retúr járatok + PROMETHEE II rangsorolás + Effective Vacation Time bónusz számítás)
         ↓ (✈️ Kiválasztás -> Automatikus szálláskeresés indul, járatdátumok zárolva)
3. Lépés: Szállás kiválasztása
   (Cozycozy élő szállásaggregáció a pontos éjszakaszámra + kategória/típus/reggeli/felszereltség szűrés)
         ↓ (🏨 Kiválasztás -> Programválasztó)
4. Lépés: Programok Kiválasztása („Ezeket ajánljuk nektek”)
   (Kanonikus élménykatalógus személyre szabott fit score-ral, kategóriaszűrőkkel, időtartammal és belépődíj-becsléssel)
         ↓ (🎭 Tovább az összesítéshez)
5. Lépés: Kész Terv, Unified TripScore & B2B Ajánlat Export
   (0-100 TripScore banner hasznos idővel, Napi Útiterv sétaidőkkel és tranzit javaslatokkal, tételes Numbeo költségvetés, 1-kattintásos PDF/Print)
```

---

## 🛠️ Architektúra és Főbb Komponensek

### 1. Központi Kiwi Autocomplete & Saját Léptetők
* **Helyszínkereső:** A rendszer a központi `window.initLocationAutocomplete` komponenst használja (`/api/locations/autocomplete`), biztosítva a szabad szöveges város- és repülőtér-kiegészítést IATA kódokkal, ország- és repülőtér-alcímkékkel.
* **Egyedi léptetők (`+` és `−` stepperek):** A natív böngésző inputok helyett a platform egységes stílusú `stepper-circle-btn` és `stepper-control-box` komponensei kezelik a felnőttek, gyermekek, kinttartózkodási napok és max. menetidő kiválasztását.

### 2. Intelligens Dátumkezelési Módok és Flatpickr Integráció
* **Valós futási időhöz (`today`) viszonyított dinamikus dátumok:** A naptár sosem inicializálódik merev, múltbeli konstansokkal. Az alapértelmezett indulás mindig pontosan 3 héttel (`today + 21 nap`) későbbre kerül, a tartózkodási időtartam pedig ehhez igazodik.
* **Múltbeli dátumok szigorú kizárása:** A Flatpickr inicializálása `minDate: "today"` szabályt alkalmaz. A kliensoldali gyorsválasztó pilulák (`Jövő hét`, `3 hét múlva`, `Hosszú hétvége`) és a szerveroldali intake validáció automatikusan felülírja az elavult dátumokat a jövőbeli alapértelmezésekkel.
* **Támogatott dátummódok:**
  1. **Pontos Dátumok (`exact` — Alapértelmezett):** Egybefüggő intervallum kijelölés Flatpickr naptárral.
  2. **Időintervallum & Tartózkodási Keret (`interval`):** Odaút időablak (`out_from`–`out_to`), visszaút időablak (`in_to`) és Min-Max kinttartózkodási napok (`min_stay`, `max_stay`). Ekkor a tartózkodási időtartam illeszkedése ($g_4$) aktívan beleszámít a PROMETHEE II outranking flow-ba.
  3. **Rugalmas Hónap (`month`):** Év és hónap szerinti keresés automatikus jövőbeli fókusszal.

### 3. 4-Pilléres Decision DNA & Páros Összehasonlítás
* **4-Pilléres Desztináció prioritások:** 4 független pillér (Teljes Utazási Költség, Klíma, Közbiztonság, Élmények & Látnivalók) 4x4-es Saaty AHP mátrixa 6 páros összehasonlító csúszkával:
  1. `total_cost_vs_weather`
  2. `total_cost_vs_safety`
  3. `total_cost_vs_experience`
  4. `weather_vs_safety`
  5. `weather_vs_experience`
  6. `safety_vs_experience`
* **Döntési szituációk & Élményfókusz:** Életszerű választási helyzetek és interaktív élményfókusz csipek (🍷 Gasztro, 🏛️ Kultúra, 🏺 Autentikusság, 🌿 Természet, 🌊 Strand, ⚡ Aktív élmény).
* **Szállás prioritások:** Ár / Éjszaka, Vendégértékelés & Csillagok, Központi Elhelyezkedés, és Felszereltség & Reggeli páros összehasonlítása.

### 4. Level 2 Vektoros Élményilleszkedés & Hasznos Nyaralási Idő
* **Level 2 Koszinusz Hasonlóság:** Az élménypillér pontozása a célállomás 12-dimenziós Vibe profilja és a felhasználó preferenciái közötti koszinusz hasonlóságot számítja, Bayesi simítással és adatfedettségi faktorral.
* **Effective Vacation Time:** A járatok értékelésekor az érkezési és indulási idősávok alapján számított hasznos nappali órák bónuszként jelennek meg (+16–22 óra).

### 5. Személyre Szabott Programválasztó (Step 4)
* A desztináció kanonikus élménykínálatából a rendszer az „Ezeket ajánljuk nektek” kiemeléssel mutatja be a leginkább illeszkedő látnivalókat `fit_score` és magyar nyelvű indoklás kíséretében.
* Kategóriaszűrés (Kultúra, Gasztro, Természet, Strand, Aktív) és élő belépődíj-becslés, amely azonnal beépül a költségvetésbe.

### 6. Napi Útiterv & Tranzit Ajánlások (Step 5)
* A napi útiterv generátor dinamikusan igazodik a logisztikai kerethez (`day_start`, `day_end`) és a maximális sétaidőhöz (`max_walking_minutes`).
* **Tranzit Javaslatok:** Amikor két látnivaló közötti távolság meghaladja a séta keretet, a rendszer automatikusan tranzit ajánlást generál.
* **Unified TripScore (0–100):** A 4 pillér harmóniáját, a Shannon entrópia élménydiverzitást és a logisztikai súrlódásokat összesítő minőségi mutató.
* **B2B Ügyfélajánlat Export:** Egykattintásos nyomtatható és PDF-be menthető professzionális dokumentum.


