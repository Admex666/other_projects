---
id: event-intelligence-engine
type: system
name: Event Intelligence Engine
status: planned

description: Az Optivoya időfüggő esemény-intelligencia alrendszere, amely több külső zenei, színházi, kulturális és városi naptárból gyűjt, deduplikál, hitelesít és rangsorol dátumspecifikus eseményeket, integrálva az AHP élménypillérbe és a napi útitervbe.

source:
  type: code
  ref: app.services.events

code:
  - app/services/events/connectors/base.py
  - app/services/events/connectors/bandsintown_connector.py
  - app/services/events/connectors/songkick_connector.py
  - app/services/events/connectors/eventbrite_connector.py
  - app/services/events/event_service.py
  - app/services/events/event_deduplication.py
  - app/services/events/event_verification.py
  - app/services/events/event_ranking.py

related:
  - "[[ADR-011-event-intelligence-engine]]"
  - "[[ADR-009-experience-activity-intelligence-engine]]"
  - "[[ADR-004-honest-scraping-mode]]"
  - "[[experience-intelligence-engine]]"
  - "[[event]]"
  - "[[ahp-weighting]]"
  - "[[destination-matching]]"
  - "[[itinerary-optimization]]"
  - "[[supabase-database]]"

used_by:
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"
  - "[[advisor-workspace-blueprint-v2]]"
  - "[[itinerary-optimization]]"
---

# ⚙️ System: Event Intelligence Engine

Az **Event Intelligence Engine** az Optivoya azon kulcsfontosságú alrendszere, amely biztosítja, hogy az utazási döntések és útiterv-javaslatok ne csupán statikus látványosságokon, hanem **az adott utazási időpontban ténylegesen megrendezett, hiteles koncerteken, bulikon, fesztiválokon és kulturális vagy gasztronómiai eseményeken** alapuljanak.

A rendszer szoros szimbiózisban működik az Evergreen `[[experience-intelligence-engine]]`-nel (ADR-009), kiegészítve azt az idő dimenziójával.

---

## 🏛️ Rendszerarchitektúra & Folyamat (Pipeline)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. CONNECTORS & DISCOVERY LAYER                                        │
│    Bandsintown API | Songkick | Eventbrite | Helyi Városi Naptárak    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Raw Payloads
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. INGESTION, PROVENANCE & RAW STORE                                   │
│    Zero-Loss nyers JSON perzisztencia (public.event_sources)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Unprocessed Events
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. EVENT RESOLUTION, DEDUPLICATION & DATE VERIFICATION                 │
│    Idő- és térbeli klaszterezés (Δt ≤ 2h, Δd ≤ 300m) + Cím-illesztés   │
│    Státuszkezelés: verified / partially_verified / unverified          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Canonical Events
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. ENRICHMENT & LOGISTICS FEASIBILITY                                  │
│    Jegyárak, idősávok, helyszínkapcsolat, éjszakai hazajutás szűrő    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Enriched Events
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. DESTINATION SCORING & ITINERARY INTEGRATION                         │
│    AHP Level 2 Élmény-pillér szintézis + Napi útitervbe illesztés     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Fő Komponensek

1. **Connectors (`app/services/events/connectors/`):**
   - Külső eseményforrások aszinkron kezelői, amelyek szabványos Pydantic modellekké alakítják a forrásspecifikus API válaszokat.
   - Szigorúan betartják az `[[ADR-004-honest-scraping-mode]]` elveit: hiba esetén nincs fiktív mock adat generálás.
2. **Deduplication Engine (`event_deduplication.py`):**
   - Felismeri, ha ugyanazt a koncertet vagy bulit több különböző platform (pl. Bandsintown és Eventbrite) is listázza.
   - Időbeli fedés ($\le 2$ óra különbség a kezdésben), helyszín-koordináták ($\le 300\text{ m}$) és előadói/címszöveg Jaccard hasonlóság ($\ge 0.75$) alapján egyesíti az adatokat egyetlen `[[event]]` rekordba, megőrizve az összes forráslinket.
3. **Verification & Provenance Engine (`event_verification.py`):**
   - Kiszámítja a `confidence_score` értékét (0.00 – 1.00) a források száma és hitelessége alapján.
   - Elvégzi a dátum- és évszám-ellenőrzést, kiszűrve a korábbi évekből elavult eseményeket.
4. **Logistics & Feasibility Checker:**
   - Elemzi az esemény befejezési időpontját (`ends_at`), a helyszín és a szálláshely közötti távolságot, valamint az éjszakai tömegközlekedési vagy taxilehetőségeket.
5. **Destination & Itinerary Integrator:**
   - Előállítja az AHP Level 2 élménypontszámhoz szükséges esemény-súlyozott komponenst ($S_{\text{event}}$).
   - Támogatja a Master Travel Plannert és az Advisor Workspace-t az időpont-specifikus ajánlatok összeállításában.
