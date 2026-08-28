---
id: destination-matching
type: process
name: Destination Matching Process
status: active

description: A felhasználó utazási preferenciáinak (időjárás, repülőjegy árak, biztonság, megélhetési költségek) felmérése és optimális úti célok rangsorolása.

source:
  type: code
  ref: app.services.destination_scoring_service

code:
  - app/services/destination_scoring_service.py
  - templates/destination/destination_matcher.html
  - templates/destination/destination_results.html

related:
  - "[[destination]]"
  - "[[ahp-weighting]]"
  - "[[numbeo-database]]"
  - "[[flight-intelligence-workflow]]"

used_by:
  - "[[unified-trip-model]]"
---

# Process: Destination Matching Process

A **Destination Matcher** folyamat 2 fő fázisból áll:

```text
1. Felhasználói preferenciák megadása
   (Indulás, Utasok, Hónap, Időtartam, Költségkeret, Hőmérséklet, Biztonság)
         ↓
2. Többszempontú pontozás és szűrés (AHP)
   (Open-Meteo éghajlat + Kiwi járatár + Numbeo megélhetés & biztonság)
         ↓
3. Célállomás kiválasztása
   (🏆 Kiválasztás → 1-kattintásos handoff a Flight Intelligence-be)
```

## Adatátadás a következő lépésnek
A kiválasztott célállomás adatai (`name`, `city`, `country`, `duration`, `adults`, `origin`, `numbeo_breakdown`) közvetlenül bekerülnek a `window.TripCart`-ba, és URL paraméterként átadódnak a `/flight-intelligence` felületnek.
