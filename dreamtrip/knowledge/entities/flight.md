---
id: flight
type: entity
name: Flight (Flight Item)
status: active

description: Egy konkrét menetrend szerinti oda-vissza vagy egyirányú repülőjárat ajánlat, árakkal, időpontokkal és légitársasági adatokkal.

source:
  type: api
  system: Kiwi.com
  endpoint: /graphql

code:
  - app/models/models.py
  - app/scrapers/scraper.py

related:
  - "[[trip]]"
  - "[[flight-intelligence-workflow]]"
  - "[[flight-price]]"
  - "[[kiwi-scraper]]"

used_by:
  - "[[unified-trip-model]]"
  - "[[trip-cart-engine]]"
---

# Entity: Flight

A `TripFlightItem` egy kiválasztott vagy shortlistre helyezett repülőjáratot reprezentál.

## Főbb Attribútumok

* **`airline`**: Légitársaság(ok) neve (pl. Wizz Air, Ryanair, Lufthansa).
* **`price_total_huf`**: A teljes fizetendő összeg az összes utasra.
* **`price_per_person_huf`**: Egy főre eső retúr repülőjegy ára.
* **`out_date` & `in_date`**: Indulás és visszaérkezés naptári napja (YYYY-MM-DD).
* **`out_time` & `in_time`**: Felszállás pontos időpontja.
* **`out_airport` & `in_airport`**: IATA repülőtér kódok (pl. BUD, FCO).
* **`duration_h`**: Repülési idő órában.
* **`stops`**: Átszállások száma (0 = közvetlen járat).
* **`exact_stay_nights`**: A kint töltött éjszakák pontos száma (ez határozza meg a szálláskeresést).
* **`booking_url`**: Közvetlen foglalási hivatkozás.
