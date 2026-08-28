---
id: flight-price
type: metric
name: Flight Price (Total & Per Person)
status: active

description: A kiválasztott retúr repülőjegy ára forintban kifejezve, mind a teljes utaslétszámra, mind egy főre vetítve.

source:
  type: api
  system: Kiwi.com

code:
  - app/models/models.py
  - static/js/trip_cart.js

depends_on:
  - "[[flight]]"

used_by:
  - "[[unified-trip-model]]"
  - "[[proposal-generation]]"
---

# Metric: Flight Price

* **Mértékegység**: HUF (Ft).
* **Számítás**: A Kiwi GraphQL scraper által visszaadott valós jegyár.
* **Per Person formula**:
  $$\text{price\_per\_person\_huf} = \frac{\text{price\_total\_huf}}{\text{adults} + \text{children}}$$
