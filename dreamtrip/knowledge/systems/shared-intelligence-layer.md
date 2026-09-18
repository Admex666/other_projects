---
id: shared-intelligence-layer
type: system
name: Shared Intelligence Layer
status: active

description: Az Optivoya leválasztott, újrafelhasználható közös intelligencia és döntési motor rétege (Shared Intelligence Layer). Kiszolgálja mind a B2C Master Plannert, mind a B2B Advisor Workspace-t.

source:
  type: code
  ref: app.services

code:
  - app/services/ahp_engine.py
  - app/services/promethee_engine.py
  - app/services/destination_matching_service.py
  - app/services/flight_intelligence_service.py
  - app/services/accommodation_intelligence_service.py
  - app/services/experience_intelligence_service.py
  - app/services/trip_scoring_service.py
  - app/services/itinerary_optimization_service.py
  - app/services/proposal_renderer.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[master-planner-blueprint]]"
  - "[[fastapi-backend]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[advisor-workspace-blueprint]]"
  - "[[master-planner-blueprint]]"
---

# Shared Intelligence Layer (Közös Intelligencia Réteg)

A **Shared Intelligence Layer** biztosítja, hogy az Optivoya döntési motorjai (AHP, PROMETHEE, Kiwi járatkereső, Cozycozy szálláskaparó, Open-Meteo klímamodell, Numbeo költségmodell, útiterv optimalizáló és ajánlatrenderelő) **önálló, tiszta Python szervizként működjenek**, leválasztva mind a B2C, mind a B2B felületekről.

```text
       ┌────────────────────────┐       ┌────────────────────────┐
       │   B2C Master Planner   │       │  B2B Advisor Workspace │
       │       (/planner)       │       │       (/advisor)       │
       └───────────┬────────────┘       └───────────┬────────────┘
                   │                                │
                   └───────────────┬────────────────┘
                                   │
                 ┌─────────────────▼─────────────────┐
                 │     SHARED INTELLIGENCE LAYER     │
                 ├───────────────────────────────────┤
                 │ • AHPEngine                       │
                 │ • PrometheeEngine                 │
                 │ • DestinationMatchingService      │
                 │ • FlightIntelligenceService       │
                 │ • AccommodationIntelligenceService│
                 │ • ExperienceIntelligenceService   │
                 │ • TripScoreService                │
                 │ • ItineraryOptimizationService    │
                 │ • ProposalRenderer                │
                 └───────────────────────────────────┘
```

## Önálló Szolgáltatások (Engine Extraction)

1. **`AHPEngine`** (`app/services/ahp_engine.py`):
   - Saaty-féle páros összehasonlító mátrixok, geometriai átlagos súlyszámítás és Konzisztencia Arány (CR) ellenőrzés.
2. **`PrometheeEngine`** (`app/services/promethee_engine.py`):
   - Többkritériumos PROMETHEE II rangsorolás, Type 1-6 preferenciafüggvények, nettó kiáramlási áram ($\Phi_{\text{net}}$) és relevancia százalék.
3. **`DestinationMatchingService`** (`app/services/destination_matching_service.py`):
   - Célállomás jelöltek többkritériumos szűrése, klíma- és költségilleszkedés, AHP súlyozás.
4. **`FlightIntelligenceService`** (`app/services/flight_intelligence_service.py`):
   - Kiwi API keresés, átszállások/menetidő szűrése és PROMETHEE II outranking.
5. **`AccommodationIntelligenceService`** (`app/services/accommodation_intelligence_service.py`):
   - Cozycozy kaparó, csillag/értékelés szűrők és szállásrangsorolás.
6. **`ExperienceIntelligenceService`** (`app/services/experience_intelligence_service.py`):
   - POI-k kinyerése, városi vibe profilok és személyre szabott aktivitások.
7. **`TripScoreService`** (`app/services/trip_scoring_service.py`):
   - 4-pilléres kompozit TripScore (0-100), hasznos nyaralási idő (daylight vacation hours) és Shannon-entrópia alapú diverzitási mutató.
8. **`ItineraryOptimizationService`** (`app/services/itinerary_optimization_service.py`):
   - Napi útiterv generálás és logisztikai ütemezés.
9. **`ProposalRenderer`** (`app/services/proposal_renderer.py`):
   - B2C `SingleTripProposal` és B2B `MultiOptionProposal` nyomtatható HTML generálás.
