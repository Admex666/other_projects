---
id: cozycozy-scraper
type: system
name: Cozycozy Accommodation Aggregator
status: active

description: Szállásaggregátor és intelligens piaci benchmark modul, amely a Cozycozy platformon keresztül valós szálláskínálatot gyűjt és transzparens piaci benchmarkot biztosít.

source:
  type: code
  ref: app.scrapers.accommodation_scraper

code:
  - app/scrapers/accommodation_scraper.py
  - app/services/accommodation_market_service.py
  - data/cozycozy_market_cache.json
  - app/routers/planner.py

related:
  - "[[accommodation]]"
  - "[[accommodation-search-workflow]]"
  - "[[honest-scraping-policy]]"
  - "[[ADR-004-honest-scraping-mode]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
---

# 🏨 System: Cozycozy Accommodation Aggregator & Market Benchmark

A szálláskereső és költségbecslő alrendszer két összekapcsolt szinten működik az `[[honest-scraping-policy]]` szerint:

## 1. Valós Idejű Live Scraping
* **Dinamikus Lekérdezés**: Város, pontos be- és kijelentkezési dátumok, szoba- és vendégszám alapján.
* **Tisztítás és normalizálás**: Csillagbesorolás, vendégértékelések (0–10), képek és foglalási deeplinkek kinyerése.

## 2. Intelligens Piaci Benchmark Fallback (`accommodation_market_service.py`)
* **Garantált Válaszidő**: 5 másodperces szigorú timeout a külső live scraping hívásokra.
* **Valós Piaci Medián**: Ha a live scraper időtúllépést szenved vagy üres eredményt ad, a rendszer a `data/cozycozy_market_cache.json` alapján összeállított, valós városi mediánárakon alapuló benchmark szálláscsomagot ad át (`badge: Piaci Benchmark (Cozycozy)`).
* **Zéró Felhasználói Elakadás**: A tervezési folyamat sosem akad el üres fehér képernyővel vagy végtelen töltéssel.
