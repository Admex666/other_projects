---
id: unified-trip-score
type: metric
name: Unified TripScore
status: active

description: 0 és 100 közötti harmonizált minőségi mérőszám, amely a célállomás, repülés, szállás és élmények 4-pilléres összhangját, élménydiverzitását és logisztikai súrlódásait számszerűsíti.

source:
  type: code
  ref: app.services.trip_scoring_service

code:
  - app/services/trip_scoring_service.py
  - static/js/planner/planner_summary.js
  - static/js/trip/trip_report.js

depends_on:
  - "[[unified-trip-model]]"
  - "[[ahp-weighting]]"
  - "[[effective-vacation-time]]"

used_by:
  - "[[master-planner-wizard]]"
  - "[[proposal-generation]]"
---

# Metric: Unified TripScore

A **Unified TripScore** az Optivoya központi minőségi indexe, amely egyetlen 0–100 közötti pontszámban foglalja össze az utazási csomag koherenciáját:

* **Skála**: 0–100 pont.
* **Minőségi kategóriák**:
  - `88 - 100 pont`: *Kiemelkedő Összhang & Prémium Illeszkedés*
  - `78 - 87 pont`: *Kiváló Összhang & Kiegyensúlyozott Csomag*
  - `< 78 pont`: *Jó Ár-Érték Arányú Utazási Terv*
* **Összetevők (4 Pillér egyensúly)**:
  1. Desztináció és klíma pontszám (25%)
  2. Járat kényelem, menetrend és hasznos nyaralási idő (25%)
  3. Szállás minőségértékelés és lokáció (25%)
  4. Élmény- és programdiverzitás (25%)
* **Élménydiverzitás (Shannon Entrópia)**:
  $$H = -\sum p_i \ln(p_i)$$
  Bünteti a monofókuszú, unalmas utazást és jutalmazza a többdimenziós (kultúra + gasztronómia + természet/strand) egyensúlyt.
* **Súrlódási levonások (Friction Penalties)**:
  - Kényelmetlen átszállások (-3..-7 pont).
  - Éjszakai érkezés vagy hajnali indulás (-2..-5 pont).
  - Rossz sétálhatóság és túlzott utazási logisztika (-2..-4 pont).
