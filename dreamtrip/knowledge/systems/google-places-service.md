---
id: google-places-service
type: system
name: Google Places Service
status: active

description: A Google Places API-ra épülő szolgáltatás, amely helyi látványosságokat, értékeléseket és nyitvatartási adatokat kérdez le helyi gyorsítótárazással.

source:
  type: api
  system: Google Places API
  storage: data/poi_cache.json

code:
  - app/services/maps_service.py

related:
  - "[[poi]]"
  - "[[itinerary-optimization]]"

used_by:
  - "[[fastapi-backend]]"
---

# System: Google Places Service

A Places integráció feladata:

* POI-k lekérése a kiválasztott célállomáshoz.
* 7 napos helyi JSON cache (`data/poi_cache.json`) a gyors működésért és API költségoptimalizálásért.
* Mock fallback támogatás tesztkörnyezetben.
