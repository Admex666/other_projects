---
id: accommodation
type: entity
name: Accommodation (Stay Item)
status: active

description: Szálláshely (hotel, apartman, resort) konkrét árakkal, csillagbesorolással, vendégértékelésekkel és kényelmi szolgáltatásokkal.

source:
  type: api
  system: Cozycozy
  ref: app.scrapers.accommodation_scraper

code:
  - app/models/models.py
  - app/scrapers/accommodation_scraper.py

related:
  - "[[trip]]"
  - "[[accommodation-search-workflow]]"
  - "[[accommodation-nightly-rate]]"
  - "[[cozycozy-scraper]]"

used_by:
  - "[[unified-trip-model]]"
  - "[[trip-cart-engine]]"
---

# Entity: Accommodation

A `TripAccommodationItem` a kiválasztott vagy shortlistre mentett szálláshelyet jelöli.

## Főbb Attribútumok

* **`name`**: A szállás neve (pl. Hotel Colosseum).
* **`stars`**: Hivatalos besorolás (1–5 csillag).
* **`rating`**: Vendégértékelés (0–10 vagy 0–100 skálán).
* **`price_total_huf`**: Teljes szállásköltség a teljes tartózkodásra.
* **`price_per_night_huf`**: Egy éjszakára vetített szobaár.
* **`nights`**: Lefoglalt éjszakák száma (a kiválasztott járatból örökölve).
* **`address` / `city`**: Elhelyezkedés és cím.
* **`image_url`**: Fotó URL az ajánlathoz.
* **`deeplink`**: Közvetlen foglalási link.
