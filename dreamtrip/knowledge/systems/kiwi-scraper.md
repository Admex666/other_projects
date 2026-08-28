---
id: kiwi-scraper
type: system
name: Kiwi.com Scraper & GraphQL Aggregator
status: active

description: A Kiwi.com publikus GraphQL és REST végpontjait használó élő repülőjegy aggregátor modul.

source:
  type: api
  system: Kiwi.com
  endpoint: https://api.skypicker.com / https://graphql.kiwi.com

code:
  - app/scrapers/scraper.py

related:
  - "[[flight]]"
  - "[[flight-intelligence-workflow]]"
  - "[[honest-scraping-policy]]"

used_by:
  - "[[fastapi-backend]]"
---

# System: Kiwi.com Scraper & GraphQL Aggregator

A Kiwi modul élő járatadatokat gyűjt:

* **Locations API**: Repülőterek és IATA kódok dinamikus feloldása gépeléskor.
* **GraphQL Return Search**: Oda-vissza járatkombinációk keresése rugalmas dátumtartományban.
* **Adattisztítás**: Menetidők, átszállási idők, légitársasági adatok és közvetlen foglalási linkek kinyerése.
