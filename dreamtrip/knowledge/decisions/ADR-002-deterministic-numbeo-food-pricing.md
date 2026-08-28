---
id: ADR-002
type: decision
name: "ADR-002: Deterministic Numbeo Food & Transit Pricing"
status: active
date: 2026-08-22

supersedes: null

related:
  - "[[numbeo-cost-model]]"
  - "[[daily-food-cost]]"
  - "[[daily-transit-cost]]"
  - "[[numbeo-database]]"
---

# Decision

A kosárban és a B2B ajánlatban szereplő étkezési és közlekedési költségeket szigorúan a hivatalos Numbeo Cost of Living adatbázis tételeiből és matematikai képletekből számoljuk ki, becslések és hardkódolt konstansok helyett.

# Context

A felhasználói visszajelzés kifejezetten megkövetelte: *„De az ételek a numbeo service alapján legyenek odaírva, NE becsülve legyenek!”*

# Consequences

* Minden városnál auditálható, tételes képlet jelenik meg: $(1.5 \times \text{olcsó} + 0.5 \times \text{középkategória} + 2 \times \text{kávé}) \times \text{napok} \times \text{fő}$.
* A helyi tömegközlekedés $2 \times \text{jegyár} \times \text{napok} \times \text{fő}$ képlettel számolódik.
