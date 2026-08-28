---
id: ADR-003
type: decision
name: "ADR-003: Multi-Criteria Ranking with AHP and PROMETHEE II"
status: active
date: 2026-08-10

supersedes: null

related:
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[flight-intelligence-workflow]]"
---

# Decision

A járatok és szállások rangsorolására az AHP (Analytic Hierarchy Process) páros preferenciamátrixot és a PROMETHEE II outranking módszert kombináljuk.

# Context

Az utazási döntések sokdimenziósak (ár vs. menetidő vs. kényelem vs. értékelés). Egy egyszerű súlyozott átlag (WSM) nem kezeli megfelelően a nem-lineáris preferenciákat és küszöbértékeket.

# Consequences

* A felhasználó intuitív módon súlyozhat páros összehasonlítással.
* A PROMETHEE II nettó dominanciaértéket ($\Phi_{net}$) és robusztus relatív relevancia százalékot számít.
