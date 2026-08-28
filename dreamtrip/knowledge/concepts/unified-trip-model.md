---
id: unified-trip-model
type: concept
name: Unified Trip Model Architecture
status: active

description: Az Optivoya központi tervezési mintája, amely egyetlen perzisztens állapotobjektum köré szervezi a célállomás-ajánlást, a repülőjegy-keresést, a szállásfoglalást és a költségkalkulációt.

source:
  type: decision
  ref: "[[ADR-001-unified-trip-architecture]]"

code:
  - app/models/models.py
  - static/js/trip_cart.js
  - app/main.py

related:
  - "[[trip]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"

used_by:
  - "[[trip-cart-engine]]"
  - "[[fastapi-backend]]"
---

# Concept: Unified Trip Model Architecture

A **Unified Trip Model** az Optivoya gerince. Megakadályozza az adatok szétesését és felesleges újbóli bekérését.

```text
TRIP
├── trip_id
├── INPUT (origin, adults, children, dates, budget)
├── DESTINATION (selected, score, climate, numbeo)
├── FLIGHT (search_params, shortlist[], selected_flight)
├── ACCOMMODATION (search_params, shortlist[], selected_accommodation)
└── BUDGET (itemized Numbeo math breakdown)
```

## Alapelvek

1. **Egyirányú, zárolt adatfolyam (Downstream Locking)**:
   * A kiválasztott járat (`out_date`, `in_date`, `exact_stay_nights`) automatikusan és visszavonhatatlanul zárolja a szálláskereső `checkin`, `checkout` és `nights` mezőit.
2. **Kettős perzisztencia**:
   * Kliensoldalon a böngésző `localStorage` tárolja az állapotot (`optivoya_trip_workspace`), így oldalfrissítés vagy modulváltás esetén azonnal elérhető.
   * Szerveroldalon a `/api/trip/sync` végponton keresztül szinkronizálódik a backend session-be.
3. **Egyértelmű Lépésenkénti CTA-k**:
   * Minden modul végén pontosan egy elsődleges cselekvési gomb irányítja a felhasználót a következő fázisba.
