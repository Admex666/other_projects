---
id: accommodation-nightly-rate
type: metric
name: Accommodation Nightly Rate
status: active

description: A szállás éjszakánkénti és a teljes tartózkodásra vonatkozó szobaára forintban.

source:
  type: api
  system: Cozycozy

code:
  - app/models/models.py
  - static/js/trip_cart.js

depends_on:
  - "[[accommodation]]"

used_by:
  - "[[unified-trip-model]]"
  - "[[proposal-generation]]"
---

# Metric: Accommodation Nightly Rate

* **Mértékegység**: HUF (Ft).
* **Képlet**:
  $$\text{price\_per\_night\_huf} = \frac{\text{price\_total\_huf}}{\text{nights}}$$
