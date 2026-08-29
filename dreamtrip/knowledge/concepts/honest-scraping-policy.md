---
id: honest-scraping-policy
type: concept
name: Honest Scraping Policy
status: active

description: A platform működési elve, miszerint hiányzó API adatok vagy hálózati hiba esetén tilos szintetikus vagy fiktív repülőjegyeket és szállásokat generálni a felhasználónak.

source:
  type: decision
  ref: "[[ADR-004-honest-scraping-mode]]"

code:
  - app/scrapers/accommodation_scraper.py
  - app/scrapers/scraper.py

related:
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"

used_by:
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
---

# Concept: Honest Scraping Policy

Az Optivoya professzionális B2B utazási tanácsadói eszköz. Amennyiben egy külső aggregátor (pl. Kiwi vagy Cozycozy) nem ad vissza valós találatot egy adott szűrésre:

* **Tilos** a felhasználónak hardkódolt, fiktív 12.000 Ft-os járatokat vagy nem létező szállodákat mutatni.
* **Tilos** mesterséges heurisztikus szorzókat használni a célállomás szintű kalkulációban: a szállásárak a desztinációs döntési modellben is valós, Cozycozy-ból scrapelt és gyorsítótárazott piaci mediánárakból (`app.services.accommodation_market_service`) származnak.
* **Kötelező** egyértelmű, őszinte állapotjelzést adni (pl. „Nem találtunk közvetlen járatot a megadott dátumra, kérjük bővítsd az időablakot”).
* A hibakezelésnek meg kell őriznie a felhasználó által beállított szűrőket, hogy 1 kattintással módosíthassa azokat.
