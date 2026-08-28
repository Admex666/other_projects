---
id: poi
type: entity
name: Point of Interest (POI)
status: active

description: Látványosság, múzeum, étterem vagy tevékenység konkrét földrajzi koordinátákkal, nyitvatartási idővel és látogatási időtartammal.

source:
  type: api
  system: Google Places API / Local Cache
  ref: data/poi_cache.json

code:
  - app/services/maps_service.py
  - app/services/itinerary_service.py

related:
  - "[[destination]]"
  - "[[itinerary-optimization]]"
  - "[[google-places-service]]"

used_by:
  - "[[trip]]"
---

# Entity: Point of Interest (POI)

A POI entitások alkotják a napi útiterv és élménytervező komponenseit.

## Főbb Attribútumok

* **`name`**: Látványosság neve (pl. Colosseum, Louvre Múzeum).
* **`category`**: Kategória (pl. `sightseeing`, `museum`, `restaurant`, `park`).
* **`lat` & `lng`**: Földrajzi koordináták.
* **`rating`**: Google Places értékelési pontszám.
* **`duration_minutes`**: Ajánlott látogatási időtartam.
* **`opening_hours`**: Nyitvatartási idősávok.
