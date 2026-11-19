---
id: learning-kiwi-tokens
type: learning
name: Kiwi GraphQL Pagination and Token Lifecycle
status: active

description: A Kiwi.com GraphQL API válaszaiban található search tokenek és kurzoralapú lapozás működése.

source:
  type: code
  ref: app.scrapers.scraper

code:
  - app/scrapers/scraper.py

related:
  - "[[kiwi-scraper]]"
  - "[[flight-intelligence-workflow]]"
---

# Learning: Kiwi GraphQL Pagination and Token Lifecycle

* A Kiwi GraphQL keresések session tokent adnak vissza, amely 10–15 percig érvényes.
* **Szerveroldali 50-es korlát:** A Kiwi GraphQL végpontja (`onewayItineraries`) egyetlen lekérdezésre legfeljebb 50 járatot ad vissza. Ha a kívánt limit ennél nagyobb (pl. 100–150 járat 30 napra), a rendszert nem szabad egyetlen tág kérésre hagyni.
* **Párhuzamos Sávosítás (Parallel Chunking):** A dátumtartományt 2–3 idősávra bontva (`ThreadPoolExecutor`) egyidejűleg kérjük le, így 150 egyedi járatot kapunk minimális válaszidővel (~3 mp).
* A deep link generálásánál a `kiwi.com/booking?token=...` formátum biztosítja a helyes ár átadását a foglalási oldalnak.
