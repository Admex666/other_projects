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
   (Kiwi élő autocomplete, 3 Dátummód + Flatpickr naptár, 4-Pilléres Decision DNA páros összehasonlítás [Költség, Klíma, Biztonság, Élmények], Élményfókusz szituáció)
         ↓
1. Lépés: Célállomás kiválasztása
   (4-pilléres pontozás + Élmény & Aktivitás profil badge-ek: látnivalószám, sétálhatósági %, esőbiztos helyszínek, kiemelt nevezetességek)
         ↓ (🏆 Kiválasztás -> Automatikus járatkeresés indul a háttérben)
2. Lépés: Járat kiválasztása
   (Kiwi GraphQL retúr járatok dinamikus skálázással [napi 5 járat, 30–150 db] + PROMETHEE II rangsorolás)
         ↓ (✈️ Kiválasztás -> Automatikus szálláskeresés indul, járatdátumok zárolva)
3. Lépés: Szállás kiválasztása
   (Cozycozy élő szállásaggregáció a pontos éjszakaszámra + kategória/típus/reggeli/felszereltség szűrés)
         ↓ (🏨 Kiválasztás -> Összesített terv)
4. Lépés: Összesített Terv & Napi Élménynaptár
   (Tételes Numbeo matematikai költségbontás + Interaktív Napi Programtervező délelőtt/ebéd/délután/este idősávokkal, sétaútvonalakkal és stílusválasztóval + 1-kattintásos PDF)
```

---

## 🛠️ Architektúra és Főbb Komponensek

### 1. Központi Kiwi Autocomplete & Saját Léptetők
* **Helyszínkereső:** A rendszer a központi `window.initLocationAutocomplete` komponenst használja (`/api/locations/autocomplete`), biztosítva a szabad szöveges város- és repülőtér-kiegészítést IATA kódokkal, ország- és repülőtér-alcímkékkel.
* **Egyedi léptetők (`+` és `−` stepperek):** A natív böngésző inputok helyett a platform egységes stílusú `stepper-circle-btn` és `stepper-control-box` komponensei kezelik a felnőttek, gyermekek, kinttartózkodási napok és max. menetidő kiválasztását.

### 2. Dátumkezelési Módok és Flatpickr Integráció
1. **Pontos Dátumok (`exact` — Alapértelmezett):** A bevált `window.initAdvisorDatePicker` Flatpickr naptárkomponens és gyorsválasztó pilulák (`Jövő hét`, `3 hét múlva`, `Hosszú hétvége`).
2. **Időintervallum & Tartózkodási Keret (`interval`):** Odaút időablak (`out_from`–`out_to`), visszaút időablak (`in_to`) és Min-Max kinttartózkodási napok (`min_stay`, `max_stay`). Ekkor a tartózkodási időtartam illeszkedése ($g_4$) aktívan beleszámít a PROMETHEE II outranking flow-ba.

### 3. 4-Pilléres Decision DNA & Páros Összehasonlítás
* **4-Pilléres Desztináció prioritások:** 4 független pillér (Teljes Utazási Költség, Klíma, Közbiztonság, Élmények & Látnivalók) 4x4-es Saaty AHP mátrixa 6 páros összehasonlító csúszkával:
  1. `total_cost_vs_weather`
  2. `total_cost_vs_safety`
  3. `total_cost_vs_experience`
  4. `weather_vs_safety`
  5. `weather_vs_experience`
  6. `safety_vs_experience`
* **Döntési szituációk & Élményfókusz:** 4 életszerű választási helyzet, beleértve a programstílus preferenciát (*Kulturális nevezetességek* vs. *Helyi gasztronómia & séta*).
* **Szállás prioritások:** Ár / Éjszaka, Vendégértékelés & Csillagok, Központi Elhelyezkedés, és Felszereltség & Reggeli páros összehasonlítása.

### 4. Élmény- és Aktivitás Profil a Desztináció Kártyákon
* A desztináció illeszkedési pontszáma tartalmazza az élménygazdagság részpontszámát (`s_experience`).
* A kártyákon megjelenik a részletes élmény badge: összesített látnivalószám (`266+ látnivaló`), gyalogos bejárhatósági sűrűség (`100% sétálható`), és esőbiztos helyszínek száma.
* Kiemelt nevezetességek preview a kártyán.

### 5. Interaktív Napi Programtervező (Step 4 Itinerary Engine)
* Az összegző lépésben az utazás pontos napjaira és éjszakaszámára betöltődik az `[[experience-intelligence-engine]]` által generált napi élménynaptár.
* **Idősávos (Time Slot) felépítés:**
  - Délelőtt (09:30 - 12:30): Kiemelt kulturális/történelmi nevezetesség.
  - Ebédszünet (12:30 - 14:00): Helyi gasztronómiai ajánlás.
  - Délután (14:00 - 18:00): Sétálható szomszédos látványosság, pontos séta-távolság kijelzéssel (`🚶 350 m séta (~4 perc)`).
  - Naplemente & Este (18:30 - 22:00): Tengerparti sétány panoráma vagy esti hangulat.
* **Stílusválasztó:** Az utazó a felületről 1 kattintással újrakalibrálhatja az útiterv hangulatát (*Kultúra*, *Gasztronómia*, *Romantikus*, *Kötetlen felfedező*).


