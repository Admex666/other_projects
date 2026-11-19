---
name: skill-kiwi-pagination-and-tokens
description: >-
  Use this skill when handling learning: kiwi graphql pagination and token lifecycle or related operational workflows in domain 'dreamtrip'. Synthesized from canonical operational learning: kiwi-pagination-and-tokens.md.
---

# Learning: Kiwi GraphQL Pagination and Token Lifecycle

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `kiwi-pagination-and-tokens.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
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


## Canonical Source of Truth
- Primary Reference: [kiwi-pagination-and-tokens.md](./references/kiwi-pagination-and-tokens.md)
- Original Location: `E:\Data\other_projects\dreamtrip\knowledge\learnings\kiwi-pagination-and-tokens.md`
