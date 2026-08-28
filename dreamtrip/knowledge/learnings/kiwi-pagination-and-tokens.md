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
* A nagyméretű lekérdezéseknél (több tucat járatkombináció) a kurzorral történő lapozás stabilabb, mint a túl tág dátumablak egyszerre történő lekérése.
* A deep link generálásánál a `kiwi.com/booking?token=...` formátum biztosítja a helyes ár átadását a foglalási oldalnak.
