---
id: ADR-001
type: decision
name: "ADR-001: Unified Trip Architecture Consolidation"
status: active
date: 2026-08-23

supersedes: null

related:
  - "[[unified-trip-model]]"
  - "[[trip]]"
  - "[[trip-cart-engine]]"
---

# Decision

A platform adatmodelljét egyetlen központi `UnifiedTrip` objektum köré konszolidáltuk a korábbi különálló, fragmentált modulok és handoff foltozgatások helyett.

# Context

A felhasználó a Destination Matcher, Flight Intelligence és Accommodation Intelligence modulok közötti váltáskor elveszíthette a kontextust, és a szálláskeresőben manuálisan kellett újra beírnia a járat dátumait.

# Consequences

* A kiválasztott járat pontos oda- és visszaút napja automatikusan zárolja a szálláskereső check-in és check-out mezőit.
* A kosár fiók minden fázisban elérhető perzisztens `localStorage` állapotból és `/api/trip/sync` végponton keresztül.
* Egyértelművé vált a „Mi a következő lépés?” cselekvési útvonal.
