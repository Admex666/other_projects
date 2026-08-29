---
id: cozycozy-scraper
type: system
name: Cozycozy Accommodation Aggregator
status: active

description: Szállásaggregátor modul, amely a Cozycozy platformon keresztül szálláskínálatot gyűjt.

source:
  type: code
  ref: app.scrapers.accommodation_scraper

code:
  - app/scrapers/accommodation_scraper.py
  - app/services/accommodation_market_service.py
  - data/cozycozy_market_cache.json

related:
  - "[[accommodation]]"
  - "[[accommodation-search-workflow]]"
  - "[[honest-scraping-policy]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
---

# System: Cozycozy Accommodation Aggregator

A szálláskereső motor:

* **Real-time lekérdezés**: Városnév, check-in, check-out, felnőttek száma és valutabeállítás alapján.
* **Piaci gyorsítótár és Desztinációs integráció**: A `data/cozycozy_market_cache.json` és `app.services.accommodation_market_service` segítségével a célállomások döntési modellje valós, scrapelt éjszakánkénti piaci mediánárakkal számol heurisztikus becslések helyett.
* **Tisztítás és normalizálás**: Csillagbesorolás, vendégértékelés (0–10), képek és foglalási deeplinkek kinyerése.
* **Transzparens hibakezelés**: Memória- vagy hálózati probléma esetén explicit hibaüzenetet küld az [[honest-scraping-policy]] szerint.
