---
id: fastapi-backend
type: system
name: FastAPI Backend Service
status: active

description: A platform központi Python webes kiszolgálója, amely a REST végpontokat, aszinkron adatgyűjtést és Jinja2 template renderelést biztosítja.

source:
  type: code
  ref: app.main

code:
  - app/main.py
  - app/api/v2/planner.py
  - main.py

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[master-planner-wizard]]"

used_by:
  - "[[trip-cart-engine]]"
---

# System: FastAPI Backend Service

A FastAPI alapú szerver felelős az API végpontok és a felhasználói felületek kiszolgálásáért:

* **Moduláris V2 API Router**: `app/api/v2/planner.py` (`/api/planner/init-destinations`, `/api/planner/search-flights`, `/api/planner/search-stays`, `/api/trip/sync`, `/api/trip/active`).
* **Aszinkron háttérfolyamatok**: Háttérszálon futó járat- és szállásaggregáció, polling alapú állapotlekérdezéssel (`/api/planner/destinations-status`).
* **Session és State kezelés**: Cookie-alapú munkamenetek és aktív utazási tervek nyilvántartása.

