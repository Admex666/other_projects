---
id: ADR-004
type: decision
name: "ADR-004: Honest Scraping and Transparent Failure Policy"
status: active
date: 2026-08-14

supersedes: null

related:
  - "[[honest-scraping-policy]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
---

# Decision

Megszüntettük a mesterséges mock/fallback járat- és szállásgenerálást a scraper modulokban. Hibák vagy sikertelen keresések esetén a rendszer valós állapotüzenetet ad át.

# Context

A korábbi scraper verziók hiba esetén fiktív járatokat vagy kamu szállásokat generáltak, ami megtévesztő volt a B2B tesztelés során.

# Consequences

* Az aggregátorok valós adatot adnak, vagy tiszta, informatív hibaüzenetet küldenek.
* A felhasználó pontosan látja, ha az adott városra/időszakra nincs közvetlen járat vagy elérhető szállás.
