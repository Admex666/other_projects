---
id: trip
type: entity
name: Trip (UnifiedTrip)
status: active

description: A központi utazási aggregátum, amely a felhasználói igényeket, a választott célállomást, a repülőjáratot, a szállást, a shortlist opciókat és a tételes költségkalkulációt tartalmazza.

source:
  type: code
  ref: app.models.models.UnifiedTrip

code:
  - app/models/models.py
  - static/js/trip_cart.js

related:
  - "[[unified-trip-model]]"
  - "[[destination]]"
  - "[[flight]]"
  - "[[accommodation]]"
  - "[[proposal-generation]]"

used_by:
  - "[[trip-cart-engine]]"
  - "[[fastapi-backend]]"
---

# Entity: Trip

A `UnifiedTrip` az Optivoya platform elsődleges állapothordozója. Egyetlen koherens objektumban reprezentálja az utazási döntési folyamat minden fázisát.

## Szerkezeti Felépítés

1. **`trip_id`**: Egyedi munkamenet/ajánlat azonosító (`trip_uuid`).
2. **`input`**: Utazási alapigények (indulási reptér, felnőttek/gyermekek száma, időszak, költségkeret).
3. **`destination`**: A kiválasztott célállomás és annak Numbeo/klíma metaadatai.
4. **`flight`**: Járatkeresési paraméterek, `shortlist` és a kiválasztott `selected_flight`.
5. **`accommodation`**: Szálláskeresési paraméterek, `shortlist` és a kiválasztott `selected_accommodation`.
6. **`budget`**: Tételes matematikai Numbeo költségbontás.

## Kapcsolatok és Életciklus

* A **Destination Matcher** inicializálja az úti célt és az időszakot.
* A **Flight Intelligence** rögzíti a konkrét retúr járatot, amiből automatikusan lezárul a check-in, check-out és éjszakaszám.
* Az **Accommodation Intelligence** a járat dátumaira szűkítve rögzíti a szállást.
* A **Proposal Generation** a teljes objektumból készít B2B ügyfélajánlatot.
