---
id: destination
type: entity
name: Destination
status: active

description: Célváros vagy turisztikai régió, amelyhez éghajlati adatok, repülőjegy árak, Numbeo megélhetési és biztonsági mutatók tartoznak.

source:
  type: file
  ref: data/destinations.json

code:
  - app/services/destination_scoring_service.py
  - app/services/numbeo_service.py

related:
  - "[[trip]]"
  - "[[destination-matching]]"
  - "[[numbeo-database]]"
  - "[[safety-index]]"

used_by:
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
---

# Entity: Destination

A célállomás entitás képviseli az utazó által felkeresendő várost vagy régiót.

## Főbb Attribútumok

* **`name` / `city`**: A célállomás neve (pl. Róma, Barcelona, Párizs).
* **`country`**: Az ország neve.
* **`region`**: Turisztikai régió besorolás (pl. `europe_south`, `europe_west`).
* **`coordinates`**: Szélességi és hosszúsági fokok térképes megjelenítéshez.
* **`climate`**: Havi átlagos hőmérséklet, esős napok, napsütéses órák.
* **`flight_price_huf`**: Becsült / aktuális repülőjegy ár Budapestről.
* **`daily_cost_eur`**: Napi becsült költség (Numbeo alapon).
* **`safety_index`**: Biztonsági index (0–100).
* **`numbeo_breakdown`**: Étkezési és közlekedési tételes indexek.
