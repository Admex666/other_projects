---
id: open-meteo-api
type: system
name: Open-Meteo Climate API
status: active

description: Nyílt meteorológiai adatforrás, amely havi átlaghőmérsékletet, csapadékos napok számát és napsütéses órákat biztosít a célállomásokhoz.

source:
  type: api
  system: Open-Meteo
  endpoint: https://archive-api.open-meteo.com/v1/archive

code:
  - app/services/destination_scoring_service.py
  - scripts/enrich_destinations.py

related:
  - "[[destination]]"
  - "[[destination-matching]]"

used_by:
  - "[[fastapi-backend]]"
---

# System: Open-Meteo Climate API

Az éghajlati adatok meghatározására szolgál a Destination Matcherben:

* Hőmérsékleti optimum vizsgálata a felhasználó preferenciája szerint (pl. „Kellemes meleg 22–27 °C”).
* Csapadék-kockázat számítása (esős napok havi valószínűsége).
* Időjárási pontszám kalkulációja determinisztikus büntetőfüggvényekkel.
