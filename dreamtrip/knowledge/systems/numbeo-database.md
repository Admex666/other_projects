---
id: numbeo-database
type: system
name: Numbeo Living Cost & Safety Database
status: active

description: A célvárosok hivatalos Numbeo megélhetési árait, éttermi költségeit, jegyárait és biztonsági mutatóit tartalmazó helyi JSON adatbázis és szinkronizáló pipeline.

source:
  type: file
  ref: data/live_numbeo_indices.json

code:
  - app/services/numbeo_service.py
  - static/js/trip_cart.js
  - scripts/refresh_numbeo_data.py

related:
  - "[[numbeo-cost-model]]"
  - "[[safety-index]]"
  - "[[daily-food-cost]]"

used_by:
  - "[[destination-matching]]"
  - "[[trip-cart-engine]]"
---

# System: Numbeo Living Cost & Safety Database

A Numbeo adatbázis biztosítja a megbízható költségbecslést:

* **Helyi gyorsítótár**: `data/live_numbeo_indices.json`
* **Kulcsok városonként**: `meal_inexpensive`, `meal_midrange`, `coffee`, `transport_ticket`, `safety_index`.
* **Frontend beágyazás**: A `trip_cart.js` azonnali offline/kliensoldali rendereléshez tartalmazza a szinkronizált indexeket.
