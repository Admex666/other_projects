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
* **Dinamikus Lekérdezési Limit & Párhuzamos Sávos Darabolás (Parallel Chunking)**: Az időablak méretétől függő dinamikus járatlekérdezés ($\text{limit} = \min(150, \max(30, \text{napok} \times 5))$). Mivel a Kiwi GraphQL szerveroldalon kérésenként fix 50 járatra korlátoz, a rendszer 50 feletti igény esetén az időablakot 2–3 egyenlő idősávra bontja és `ThreadPoolExecutor`-ral párhuzamosan kéri le. Így 30 napra 150 egyedi járatot és közel 3000 valós kombinációt ad vissza ~3 másodperc alatt.
* **Adattisztítás**: Menetidők, átszállási idők, légitársasági adatok és közvetlen foglalási linkek kinyerése.
