---
id: fastapi-backend
type: system
name: FastAPI Backend Service
status: active

description: A platform központi Python webes kiszolgálója, amely moduláris APIRouter struktúrában biztosítja a REST végpontokat, az aszinkron adatgyűjtést és a Jinja2 template renderelést.

source:
  type: code
  ref: app.main

code:
  - app/main.py
  - app/routers/planner.py
  - app/routers/flights.py
  - app/routers/stays.py
  - app/routers/destinations.py
  - app/routers/trip.py
  - app/routers/auth.py

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[master-planner-wizard]]"
  - "[[ADR-007-fastapi-router-modularization]]"

used_by:
  - "[[trip-cart-engine]]"
---

# ⚙️ System: FastAPI Backend Service

A FastAPI alapú szerver felelős az API végpontok és a felhasználói felületek kiszolgálásáért a `[[ARCHITECTURE_RULES]]` szabályrendszernek megfelelően:

## 🧱 Moduláris Felépítés (`app/routers/` & `app/core/`)
* **Központi Belépési Pont (`app/main.py`)**: Tiszta alkalmazás-összeszerelő, életciklus (lifespan) kezelő és statikus fájl mountoló réteg.
* **Master Planner Router (`app/routers/planner.py`)**: `/planner` weboldal, `/api/planner/init-destinations`, `/api/planner/search-flights`, `/api/planner/search-stays`, `/api/trip/sync`.
* **Flights Router (`app/routers/flights.py`)**: Kiwi GraphQL járatkeresés, szűrés és AHP döntéstámogatás.
* **Stays Router (`app/routers/stays.py`)**: Cozycozy szállásaggregáció és előnézeti felületek.
* **Destinations Router (`app/routers/destinations.py`)**: Célállomás értékelés és éghajlati illesztés.
* **Trip & POI Router (`app/routers/trip.py`)**: V2 Útiterv-optimalizálás és POI keresés.
* **Auth & Core (`app/routers/auth.py`, `app/core/`)**: Session-kezelés és konfiguráció.
