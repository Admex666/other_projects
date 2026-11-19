---
name: skill-numbeo-hungarian-city-mapping
description: >-
  Use this skill when handling learning: hungarian city name mapping for numbeo indices or related operational workflows in domain 'dreamtrip'. Synthesized from canonical operational learning: numbeo-hungarian-city-mapping.md.
---

# Learning: Hungarian City Name Mapping for Numbeo Indices

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `numbeo-hungarian-city-mapping.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
---
id: learning-numbeo-mapping
type: learning
name: Hungarian City Name Mapping for Numbeo Indices
status: active

description: A magyar ékezetes városnevek (Róma, Párizs, Bécs, Varsó) megbízható összekapcsolása a nemzetközi Numbeo és Kiwi városnevekkel.

source:
  type: code
  ref: app.services.numbeo_service

code:
  - app/services/numbeo_service.py

related:
  - "[[numbeo-database]]"
  - "[[destination]]"
---

# Learning: Hungarian City Name Mapping for Numbeo Indices

* A Numbeo adatbázis angol neveket használ (pl. `Rome`, `Paris`, `Vienna`, `Prague`), míg a magyar felhasználói felület magyar ékezetes neveket (`Róma`, `Párizs`, `Bécs`, `Prága`).
* **Megoldás**:
  Az `app/services/numbeo_service.py` és a `static/js/trip_cart.js` egy kétirányú alias szótárat használ (`CITY_ALIASES`), amely automatikusan feloldja mind a magyar, mind az angol, mind az IATA repülőtér kódokat a megfelelő Numbeo rekordhoz.


## Canonical Source of Truth
- Primary Reference: [numbeo-hungarian-city-mapping.md](./references/numbeo-hungarian-city-mapping.md)
- Original Location: `E:\Data\other_projects\dreamtrip\knowledge\learnings\numbeo-hungarian-city-mapping.md`
