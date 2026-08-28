---
id: master-planner-wizard
type: process
name: Master Travel Planner Wizard
status: active

description: Egyetlen integrált, 4-lépéses utazástervezési folyamat, amely közös kezdő intake űrlappal, automatikus háttér-aggregációval és menet közbeni szűrőmódosítással működik.

source:
  type: code
  ref: app.services.planner_service

code:
  - app/services/planner_service.py
  - app/main.py
  - templates/planner/planner_wizard.html
  - static/js/planner_wizard.js

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"

used_by:
  - "[[fastapi-backend]]"
---

# Process: Master Travel Planner Wizard

A **Master Travel Planner** a platform legmagasabb szintű folyamata:

```text
0. Lépés: Unified Intake Form
   (Indulási reptér, utasok, hónap, időtartam, éghajlat, repülési és szállás preferenciák)
         ↓
1. Lépés: Célállomás kiválasztása
   (Open-Meteo klíma + Kiwi járatárak + Numbeo költség/biztonság pontozás)
         ↓ (🏆 Kiválasztás -> Automatikus járatkeresés indul)
2. Lépés: Járat kiválasztása
   (Kiwi GraphQL retúr járatok + PROMETHEE II relevancia rangsorolás)
         ↓ (✈️ Kiválasztás -> Automatikus szálláskeresés indul, dátumok zárolva)
3. Lépés: Szállás kiválasztása
   (Cozycozy szállásaggregáció a pontos éjszakaszámra + értékelési szűrés)
         ↓ (🏨 Kiválasztás -> Összesített terv)
4. Lépés: Összesített Terv & B2B Ajánlat
   (Tételes Numbeo matematikai költségbontás + 1-kattintásos PDF / Nyomtatás)
```

## Menet közbeni finomhangolás
Minden fázisban elérhető az inline lenyitható `⚙️ Szűrők és preferenciák módosítása` doboz, így a felhasználó visszalépés nélkül módosíthatja pl. az átszállás-toleranciát vagy a szállás csillagszámát.
