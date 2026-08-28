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
  - app/services/planner_service.py
  - app/main.py
  - app/scrapers/accommodation_scraper.py
  - templates/planner/planner_wizard.html
  - static/js/planner_wizard.js
  - static/js/ahp_wizard.js
  - static/js/components.js

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
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
   (Kiwi GraphQL retúr járatok + PROMETHEE II preferenciafüggvényes rangsorolás)
         ↓ (✈️ Kiválasztás -> Automatikus szálláskeresés indul, járatdátumok zárolva)
3. Lépés: Szállás kiválasztása
   (Cozycozy élő szállásaggregáció a pontos éjszakaszámra + kategória/típus/reggeli/felszereltség szűrés)
         ↓ (🏨 Kiválasztás -> Összesített terv)
4. Lépés: Összesített Terv & B2B Ajánlat
   (Tételes Numbeo matematikai költségbontás + 1-kattintásos PDF / Nyomtatás)
```

---

## 🛠️ Architektúra és Főbb Komponensek

### 1. Központi Kiwi Autocomplete & Saját Léptetők
* **Helyszínkereső:** A rendszer a központi `window.initLocationAutocomplete` komponenst használja (`/api/locations/autocomplete`), biztosítva a szabad szöveges város- és repülőtér-kiegészítést IATA kódokkal, ország- és repülőtér-alcímkékkel.
* **Egyedi léptetők (`+` és `−` stepperek):** A natív böngésző inputok helyett a platform egységes stílusú `stepper-circle-btn` és `stepper-control-box` komponensei kezelik a felnőttek, gyermekek, kinttartózkodási napok és max. menetidő kiválasztását.

### 2. Dátumkezelési Módok és Flatpickr Integráció
1. **Rugalmas Hónap (`month`):** Tetszőleges hónap kiválasztása és 1-től akár 30+ napos tartózkodási időtartam, kétirányúan szinkronizált csúszkával és léptetővel.
2. **Időintervallum (`interval`):** Odaút időablak (`out_from`–`out_to`), visszaút időablak (`in_to`) és Min-Max kinttartózkodási napok (`min_stay`, `max_stay`).
3. **Pontos Dátumok (`exact`):** A Flight Intelligence-ben bevált `window.initAdvisorDatePicker` Flatpickr naptárkomponens és gyorsválasztó pilulák (`2 hét múlva`, `1 hónap múlva`, `Hosszú hétvége`, `2 hetes nyaralás`).

### 3. Modális Prioritásvarázslók és Progressive Disclosure (Zárolási Rendszer)
* **Desztináció prioritások:** Repülőjegy ár, Napi költségek, Klíma és Közbiztonság páros összehasonlítása az `AHPWizard` modálban.
* **Progressive Disclosure:** A 4. pont (Repülési szűrők) és az 5. pont (Szállás szűrők) addig zárolva (`opacity: 0.45; pointer-events: none`) maradnak, amíg a felhasználó ki nem tölti a prioritási kérdőívet.
* **Preset-mentes döntéshozatal:** A repülési szempontoknál nincsenek mesterséges preset sablonok, így a döntési súlyok valódi felhasználói válaszokból származnak.
* **Szállás prioritások:** Ár / Éjszaka, Vendégértékelés & Csillagok, Központi Elhelyezkedés, és Felszereltség & Reggeli páros összehasonlítása.
* **Felhasználóbarát felület:** Szakzsargon (AHP, sajátvektor, CR) kivezetve; a vissza nyíl biztonságosan bezárja a modált (`this.onBack()`).

### 4. Napszaki és Szállás Intelligencia Szűrés
* **Feltételes indulási napszak:** Checkbox-szal aktiválható konkrét indulási óra (00:00–23:00) vizuális napszak-jelvénnyel.
* **Max. menetidő:** Saját `+`/`−` léptetővel állítható (0 = Korlátlan, 1–36 óra) és gyorsgombokkal (`≤ 4ó`, `≤ 6ó`, `≤ 10ó`, `Korlátlan`).
* **Cozycozy élő szállásaggregáció:** A backend `get_all_stays` és `parse_accommodation_results` függvényeket alkalmazza zárolt éjszakaszámra és automatikus fallback kezeléssel.
