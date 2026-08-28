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

related:
  - "[[accommodation]]"
  - "[[accommodation-search-workflow]]"
  - "[[honest-scraping-policy]]"

used_by:
  - "[[fastapi-backend]]"
---

# System: Cozycozy Accommodation Aggregator

A szálláskereső motor:

* **Real-time lekérdezés**: Városnév, check-in, check-out, felnőttek száma és valutabeállítás alapján.
* **Tisztítás és normalizálás**: Csillagbesorolás, vendégértékelés (0–10), képek és foglalási deeplinkek kinyerése.
* **Transzparens hibakezelés**: Memória- vagy hálózati probléma esetén explicit hibaüzenetet küld.
