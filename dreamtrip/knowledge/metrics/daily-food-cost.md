---
id: daily-food-cost
type: metric
name: Daily Food & Dining Cost
status: active

description: A célvárosban egy főre eső napi étkezési költségkeret, amely a Numbeo Cost of Living adatbázisán alapul.

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

# Metric: Daily Food & Dining Cost

## Képlet
$$\text{Food}_{\text{daily\_eur}} = 1.5 \times \text{meal\_inexpensive} + 0.5 \times \text{meal\_midrange} + 2.0 \times \text{coffee}$$
$$\text{Food}_{\text{daily\_huf}} = \text{Food}_{\text{daily\_eur}} \times \text{EUR\_HUF\_RATE}$$

* **Példa Róma**: $(1.5 \times 16.0€ + 0.5 \times 32.0€ + 2 \times 1.60€) = 43.20€ \approx 17.064\text{ Ft / nap / fő}$.
