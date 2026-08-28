---
id: accommodation-search-workflow
type: process
name: Accommodation Search Workflow
status: active

description: Zárolt dátumú szálláskeresés, Cozycozy aggregáció, szűrés és a végleges szállás rögzítése a tervben.

source:
  type: code
  ref: app.main

code:
  - app/main.py
  - app/scrapers/accommodation_scraper.py
  - templates/accommodation/accommodation_intelligence.html
  - templates/accommodation/accommodation_results.html

related:
  - "[[accommodation]]"
  - "[[cozycozy-scraper]]"
  - "[[flight-intelligence-workflow]]"
  - "[[proposal-generation]]"

used_by:
  - "[[unified-trip-model]]"
---

# Process: Accommodation Search Workflow

A szálláskeresési folyamat automatikusan épít a kiválasztott repülőjáratra:

```text
1. Automatikus inicializálás zárolt adatokkal
   (Célváros, Check-in = out_date, Check-out = in_date, Nights, Adults)
         ↓
2. Cozycozy aggregáció és szűrés
   (Ártartomány, csillagok, vendégértékelés, térképes megjelenítés)
         ↓
3. PROMETHEE II rangsorolás
   (Ár-érték arány és komfort szerinti rendezés)
         ↓
4. Szállás rögzítése a tervben (addStayToCart)
         ↓
5. Elsődleges CTA:
   "→ Utazási terv megnyitása & Ajánlatkészítés"
```
