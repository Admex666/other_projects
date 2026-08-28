---
id: flight-intelligence-workflow
type: process
name: Flight Intelligence Workflow
status: active

description: Valós idejű repülőjegy adatgyűjtés, AHP preferenciabeállítás, PROMETHEE II rangsorolás és átadás a szálláskeresőnek.

source:
  type: code
  ref: app.main

code:
  - app/main.py
  - app/scrapers/scraper.py
  - app/services/scoring_service.py
  - templates/flights/flight_intelligence.html
  - templates/flights/flight_results.html

related:
  - "[[flight]]"
  - "[[kiwi-scraper]]"
  - "[[promethee-ranking]]"
  - "[[accommodation-search-workflow]]"

used_by:
  - "[[unified-trip-model]]"
---

# Process: Flight Intelligence Workflow

A repülőjegy-keresési folyamat lépései:

```text
1. Járatkeresés indítása (Aszinkron háttérfolyamat)
   (Origin, Destination, Dátumablak, Kiwi GraphQL lekérdezés)
         ↓
2. AHP preferenciák és szűrők beállítása (/flight-intelligence-filter)
   (Ár vs. Menetidő vs. Átszállások súlyozása)
         ↓
3. PROMETHEE II rangsorolás és megjelenítés (/flight-results)
   (Kártyás és táblázatos nézet, relevancia % kalkuláció)
         ↓
4. Járat rögzítése a tervben (addFlightToCart)
   (Dátumok, éjszakák, árak rögzítése a UnifiedTrip objektumban)
         ↓
5. Elsődleges CTA megjelenítése:
   "→ Szállások keresése (2026. szept. 10–17. · 7 éj)"
```

A kiválasztott járat pontos dátumai közvetlenül átadódnak a szálláskeresőnek, így a felhasználónak nem kell újra megadnia az időpontokat.
