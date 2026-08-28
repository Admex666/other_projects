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
  - main.py

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"

used_by:
  - "[[trip-cart-engine]]"
---

# System: FastAPI Backend Service

A FastAPI alapú szerver felelős az API végpontok és a felhasználói felületek kiszolgálásáért:

* **V1 & V2 API végpontok**: `/api/v2/flights/search`, `/api/v2/accommodations/search`, `/api/trip/sync`.
* **Aszinkron háttérfolyamatok**: Háttérszálon futó járat- és szállásaggregáció, polling alapú állapotlekérdezéssel (`/search-status`, `/api/accommodation-status`).
* **Session és State kezelés**: Cookie-alapú munkamenetek és aktív utazási tervek nyilvántartása.
