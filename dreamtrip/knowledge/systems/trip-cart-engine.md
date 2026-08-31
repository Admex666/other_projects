---
id: trip-cart-engine
type: system
name: TripCart & Workspace Engine (Frontend)
status: active

description: Kliensoldali állapotkezelő JavaScript motor, amely a perzisztens lebegő sávot, a slide-over fiókot, a Numbeo költségkalkulációt és a B2B exportot vezérli.

source:
  type: code
  ref: static/js/trip_cart.js

code:
  - static/js/trip/trip_store.js
  - static/js/trip/trip_calculator.js
  - static/js/trip/trip_report.js
  - static/js/trip/trip_drawer.js
  - static/js/trip_cart.js
  - static/css/trip_cart.css
  - templates/base.html

related:
  - "[[unified-trip-model]]"
  - "[[proposal-generation]]"
  - "[[numbeo-cost-model]]"

used_by:
  - "[[fastapi-backend]]"
---

# System: TripCart & Workspace Engine (Frontend)

A `TripEngine` (elérhető a `window.TripCart` globális változón) biztosítja az azonnali és folyamatos felhasználói visszajelzést:

* **Lebegő Sáv (Floating Bar)**: Minden oldalon mutatja az aktív célállomást, járatot, szállást, az összköltséget és a következő lépés CTA gombot.
* **Oldalsó Fiók (Slide-over Drawer)**: Lépésjelzővel (Stepper), kártyás összefoglalóval és tételes Numbeo kalkulációval.
* **1-kattintásos Ajánlat Export**: Nyomtatható és PDF-be menthető professzionális ajánlat generálása.
* **Backend szinkronizáció**: Automatikus `POST /api/trip/sync` mentés minden módosításkor.
