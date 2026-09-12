---
id: destination-matching
type: process
name: Destination Matching Process
status: active

description: A felhasználó utazási preferenciáinak (költségkeret, éghajlat, biztonság és élményfókusz) felmérése és optimális úti célok 4-pilléres rangsorolása.

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
  - "[[experience-vector-and-vibe-profiling]]"

used_by:
  - "[[unified-trip-model]]"
  - "[[master-planner-wizard]]"
---

# Process: Destination Matching Process

A **Destination Matcher** folyamat fázisai:

```text
1. Felhasználói preferenciák megadása (Level 1 + Level 2)
   (Indulás, Utasok, Hónap, Időtartam, Költségkeret, Hőmérséklet, Biztonság, Élményfókusz csipek)
         ↓
2. Többszempontú 4-pilléres pontozás és szűrés (AHP + Vektoros hasonlóság)
   - Pillér 1: Kiwi járatár + Numbeo megélhetés (Teljes Utazási Költség)
   - Pillér 2: Open-Meteo éghajlati illeszkedés (Hőmérséklet & Napsütés)
   - Pillér 3: Numbeo Közbiztonsági Index
   - Pillér 4: Level 2 Élményilleszkedés (Vibe Profil koszinusz hasonlóság a preferenciákkal)
         ↓
3. Célállomás kiválasztása
   (🏆 Kiválasztás → 1-kattintásos handoff a Flight Intelligence-be)
```

## Adatátadás a következő lépésnek
A kiválasztott célállomás adatai (`name`, `city`, `country`, `duration`, `adults`, `origin`, `score`, `experience_vector`, `numbeo_breakdown`) közvetlenül bekerülnek a `window.TripCart`-ba, és átadódnak a következő tervezési lépéseknek.
