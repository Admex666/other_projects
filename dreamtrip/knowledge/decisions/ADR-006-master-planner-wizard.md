---
id: ADR-006
type: decision
name: "ADR-006: Master Travel Planner Unified Wizard"
status: active
date: 2026-08-28

supersedes: null

related:
  - "[[unified-trip-model]]"
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
---

# Decision

Létrehoztunk egyetlen összefogó **Master Travel Planner (`/planner`)** folyamatot, amely az elején bekéri az összes felhasználói preferenciát, és a lépések között automatikusan végzi a járat- és szálláskeresést manuális űrlapkitöltések nélkül, miközben minden fázisban biztosítja a szűrők menet közbeni finomhangolását.

# Context

A felhasználónak korábban külön-külön kellett elindítania a 3 modult. Az új Master Planner 1 közös intake űrlappal indít, és fokozatosan fűzi össze a desztinációt, a járatot és a szállást egyetlen kész B2B ajánlattá.

# Consequences

* 50%-kal gyorsabb utazástervezési folyamat.
* Zéró redundáns adatbevitel.
* Inline módosítási lehetőség minden fázisban.
