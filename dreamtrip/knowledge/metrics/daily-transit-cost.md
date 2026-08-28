---
id: daily-transit-cost
type: metric
name: Daily Local Transit Cost
status: active

description: A célvárosban egy főre eső napi helyi közlekedési (metró, busz, villamos) költség.

source:
  type: derived
  ref: app.services.numbeo_service.get_city_numbeo_data

code:
  - app/services/numbeo_service.py
  - static/js/trip_cart.js

depends_on:
  - "[[numbeo-database]]"
  - "[[numbeo-cost-model]]"

used_by:
  - "[[proposal-generation]]"
  - "[[unified-trip-model]]"
---

# Metric: Daily Local Transit Cost

## Képlet
$$\text{Transit}_{\text{daily\_eur}} = 2.0 \times \text{transport\_ticket}$$
$$\text{Transit}_{\text{daily\_huf}} = \text{Transit}_{\text{daily\_eur}} \times \text{EUR\_HUF\_RATE}$$

* **Példa Róma**: $2.0 \times 1.50€ = 3.00€ \approx 1.185\text{ Ft / nap / fő}$.
