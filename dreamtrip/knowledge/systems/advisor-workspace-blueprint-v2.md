---
id: advisor-workspace-blueprint-v2
type: system
name: Optivoya Advisor Workspace v2 — Teljes Logikai Modell & Architektúra Specifikáció
status: active

description: Az Optivoya B2B Travel Advisor Workspace v2 teljes, input-intelligence-döntés-output logikai modellje és rendszerspecifikációja. 5 fázisú UX folyamat (Understand, Define, Research, Decide, Deliver), központi ResearchState absztrakció, Intent Confirmation, Candidate Pool, Score Decomposition, dinamikus AHP/PROMETHEE kritérium-aktiválás, Geo/Map és Experience Intelligence, Advisor szerkesztési és zárolási réteg, valamint kétirányú ügyfél visszacsatolási hurok.

source:
  type: code
  ref: app.services.advisor_orchestration_service

code:
  - app/models/advisor_models.py
  - app/repositories/advisor_repository.py
  - app/routers/advisor_api.py
  - app/services/advisor_orchestration_service.py
  - app/services/preference_resolver.py
  - app/services/multi_option_engine.py
  - app/services/relative_comparison_service.py
  - app/services/constraint_relaxation_service.py
  - app/services/verification_service.py
  - app/services/trip_risk_service.py
  - app/services/proposal_service.py
  - app/services/timeline_reoptimization_service.py
  - app/services/trip_scoring_service.py
  - templates/advisor/advisor_workspace.html

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[WORK-004-advisor-workspace-v2]]"
  - "[[trip-case]]"
  - "[[master-planner-blueprint]]"
  - "[[app-hub-and-workspace-switcher]]"
  - "[[fastapi-backend]]"
  - "[[supabase-database]]"
  - "[[proposal-generation]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[numbeo-cost-model]]"
  - "[[honest-scraping-policy]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[advisor-workspace-ux-specification]]"
  - "[[advisor-research-pipeline]]"
  - "[[advisor-budget-and-constraints]]"
  - "[[advisor-option-generation]]"
  - "[[advisor-provenance-and-verification]]"
  - "[[advisor-security-and-multitenancy]]"
  - "[[advisor-research-run-lifecycle]]"
  - "[[advisor-api-contract]]"
  - "[[advisor-proposal-versioning]]"

used_by:
  - "[[fastapi-backend]]"
---

# Optivoya Advisor Workspace v2 — Teljes Logikai Modell

## 0. A rendszer alapelve

Az Advisor ne úgy működjön, hogy:

> „Válassz egyet a 9 research strategy közül.”

Hanem:

> **Az advisor megadja a problémát és a rendelkezésre álló információkat → a rendszer rekonstruálja a kutatási célt → visszaigazoltatja → meghatározza, milyen adatokat kell még kérni → csak a releváns kritériumokat aktiválja → kiválasztja a szükséges kutatási műveleteket → összegyűjti és ellenőrzi az adatokat → optimalizál → magyarázza az eredményt → az advisor szerkesztheti → ebből lesz az ügyfélnek küldhető ajánlat.**

---

# 1. A teljes rendszer nagy képe

```text
                    ┌─────────────────────┐
                    │   ADVISOR / USER    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  1. CASE CONTEXT    │
                    │ Mi áll rendelkezésre?│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 2. INTENT ENGINE     │
                    │ Mit akar valójában?  │
                    └──────────┬──────────┘
                               │
                         confirmation
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 3. REQUIREMENT      │
                    │ DISCOVERY           │
                    │ Mi fontos? Mi fix?  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 4. PREFERENCE MODEL │
                    │ AHP / PROMETHEE II   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ 5. RESEARCH PLAN    │
                    │ Mit kell megkeresni?│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         DESTINATION         FLIGHT            STAY
         INTELLIGENCE      INTELLIGENCE     INTELLIGENCE
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 6. GEO / MAP        │
                    │ INTELLIGENCE        │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 7. EXPERIENCE       │
                    │ INTELLIGENCE        │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 8. NORMALIZATION +  │
                    │ VERIFICATION        │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 9. CANDIDATE POOL   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 10. CONSTRAINT      │
                    │ ENGINE              │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 11. OPTIMIZATION    │
                    │ AHP / PROMETHEE /   │
                    │ itinerary / Pareto │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 12. OPTION SYNTHESIS│
                    │ Overall / Value /   │
                    │ Experience          │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 13. EXPLAINABILITY  │
                    │ Miért ezt?          │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 14. MAP + ITINERARY │
                    │ + BACKUPS           │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ 15. ADVISOR EDIT    │
                    │ PIN / REMOVE /      │
                    │ REPLACE / REFINE    │
                    └──────────┬──────────┘
                               │
                         re-optimization
                               │
                               └──────────────┐
                                              ▼
                                  ┌─────────────────────┐
                                  │ 16. SHORTLIST       │
                                  └──────────┬──────────┘
                                             ▼
                                  ┌─────────────────────┐
                                  │ 17. PROPOSAL        │
                                  └──────────┬──────────┘
                                             ▼
                                  ┌─────────────────────┐
                                  │ 18. CLIENT OUTPUT   │
                                  └─────────────────────┘
```

---

# 2. MINDEN INPUT

Az inputokat 6 nagy csoportba érdemes osztani.

## A. Advisor által megadott input

### Case létrehozásakor

* ügyfél
* ügyfélcsoport
* utazók száma
* felnőttek
* gyerekek
* életkorok
* indulási hely
* lehetséges indulási helyek
* úti cél
* lehetséges úti célok
* utazás típusa
* indulási dátum
* visszaérkezési dátum
* dátumtartomány
* hónap
* időtartam
* flexibilitás
* budget
* budget currency
* budget per person / group
* budget hard / target
* budget relaxation allowed
* flight budget
* accommodation budget
* activity budget
* local transport budget

### Már meglévő elemek

* meglévő repülő
* meglévő szállás
* meglévő program
* meglévő itinerary
* meglévő ajánlat
* meglévő foglalás
* meglévő ügyfélterv

És mindegyiknél:

```text
KEEP
REPLACE
IMPROVE
UNKNOWN
```

---

# 3. „Mi van / mi nincs?” mátrix

Ez az új Advisor egyik legfontosabb része.

Például:

| Input       | Van? | Biztos? | Rendszer teendő      |
| ----------- | ---- | ------- | -------------------- |
| Ügyfél      | ✓    | ✓       | profil betöltése     |
| Destination | ✓    | ✓       | destination research |
| Flight      | ✗    | —       | flight search        |
| Stay        | ✗    | —       | accommodation search |
| Budget      | ✓    | ✓       | hard constraint      |
| Dates       | ✓    | ✓       | exact search         |
| Beach       | ✓    | ✓       | hard/soft criterion  |
| Activities  | ✗    | —       | experience discovery |

Ebből épül fel a **Research State**.

---

# 4. B. Ügyféladatok

A Client Profile külön adatforrás.

### Tartós adatok

* név
* korcsoport
* lakóhely
* origin
* currency
* korábbi utak
* korábbi választások
* preferált légitársaságok
* kerülendő légitársaságok
* hotel preference
* hotel category
* hotel rating
* room preference
* direct-flight preference
* travel style
* interests
* mobility constraints
* dietary preferences
* family characteristics

De nagyon fontos:

> **A Client Profile nem automatikusan írhatja felül az adott utazás briefjét.**

Hierarchia:

```text
Advisor Override
      ↓
Current Case
      ↓
Client Profile
      ↓
System Default
```

---

# 5. C. Utazó preferenciáinak felderítése

Ez nem egy fix 50 kérdéses form.

A rendszer először megkérdezi:

> **„Mi fontos ezen az utazáson?”**

Például:

* ár
* repülés kényelme
* szállás
* lokáció
* tengerpart
* természet
* kultúra
* gasztronómia
* nightlife
* shopping
* programok
* nyugalom
* autentikusság
* prémium élmény
* családbarát működés
* romantika
* időhatékonyság

Csak a releváns kiválasztott dimenziókból épül tovább a preference model.

---

# 6. D. Kritériumok

Minden kritérium valamelyik kategóriába kerül:

### HARD

Pass/fail.

Például:

```text
Beach = required
Hotel >= 4★
Budget <= 800k
Direct flight = required
```

### SOFT

Optimalizálandó.

```text
Location importance = 25%
Price importance = 30%
Hotel quality = 20%
Experience = 25%
```

### AVOID

Kerülendő.

```text
departure < 06:00
2+ stops
tourist-heavy area
```

### NICE TO HAVE

Extra előny.

```text
breakfast included
pool
free cancellation
ocean view
```

---

# 7. E. AHP / PROMETHEE input

Itt használjuk a Master Plannerből már meglévő logikát.

De **dinamikusan generált kritériumkészlettel**.

Például ha az utazó ezt választja:

> Ár + Lokáció + Tengerpart + Hotelminőség

akkor:

```text
Price
Location
Beach
Hotel Quality
```

kerül be az AHP/PROMETHEE modellbe.

Nem:

```text
Flight
Weather
Nightlife
Shopping
Culture
Nature
...
```

ha ezek nem relevánsak.

Ez az egyik legfontosabb UX-invariáns.

---

# 8. F. Külső intelligence inputok

A rendszer nem csak user inputból dolgozik.

## Destination

* destination metadata
* country
* city
* coordinates
* timezone
* climate
* weather
* seasonality
* cost
* safety/risk
* attractions
* experiences
* neighborhoods
* airports
* transport
* opening hours
* events, ahol releváns

## Flight

* airports
* coordinates
* airlines
* departure
* arrival
* duration
* stops
* layover
* baggage
* price
* fare conditions
* deep link
* booking link
* checked_at
* freshness
* verification

## Accommodation

* hotel
* coordinates
* stars
* rating
* reviews
* price
* room
* board
* cancellation
* amenities
* neighborhood
* airport distance
* attractions distance
* transit accessibility
* booking link
* freshness
* verification

---

# 9. Geo / Map Intelligence

Ezt külön intelligence layerként kezelném.

**Input:**

* latitude
* longitude
* airport coordinates
* hotel coordinates
* attraction coordinates
* restaurant coordinates
* transit points

**Derived data:**

* airport → hotel distance
* hotel → attraction distance
* attraction → attraction distance
* travel time
* walking distance
* transit distance
* geographic clustering
* daily route efficiency
* neighborhood density
* itinerary friction

Így például a rendszer nem csak azt mondja:

> Hotel rating: 8.9

hanem:

> **Lokáció: 9.1/10**

mert:

```text
Airport transfer       8.7
Top attractions        9.6
Public transport       9.2
Daily route efficiency 9.0
Neighborhood fit       8.9
```

---

# 10. Experience Intelligence

Az aktivitásoknak is strukturált adatai vannak:

* category
* interests
* location
* duration
* price
* opening hours
* booking requirement
* seasonality
* rating
* popularity
* family suitability
* weather dependency
* indoor/outdoor
* estimated visit duration

Így lehet:

> „Ez az activity 94%-ban illeszkedik az ügyfél érdeklődéséhez.”

---

# 11. Research Intent Engine

Ez fordítja le az inputokat **kutatási feladatra**.

Példák:

```text
Known destination
+ no flight
+ fixed dates
= FLIGHT-FIRST
```

```text
Known destination
+ no stay
+ premium hotel required
= STAY-FIRST
```

```text
No destination
+ flexible dates
+ budget
+ beach important
= DESTINATION DISCOVERY
```

```text
Existing flight
+ existing stay
+ wants better total experience
= RE-OPTIMIZATION
```

```text
Existing option
+ "find better hotel"
= FIND BETTER / STAY
```

A fontos változás:

**ez belső orchestration, nem user-facing választási lista.**

---

# 12. Intent Confirmation

A rendszer visszajelez:

> **Jól értem a feladatot?**
>
> Japán utazást keresünk 2 fő részére,
> 7 napra, maximum 900 000 Ft-ból,
> ahol a tengerpart és a jó lokáció fontos.
>
> A meglévő repülő és szállás még nincs kiválasztva.
>
> **Ez alapján teljes utazás-optimalizálást végzünk.**

Buttons:

**Igen, indulhat**
**Módosítom**

Ez megakadályozza a rossz research futtatást.

---

# 13. Research Planner

Az Intentből létrejön egy **Research Plan**.

Például:

```text
1. Destination discovery
2. Flight candidate search
3. Accommodation candidate search
4. Geo analysis
5. Experience discovery
6. Itinerary generation
7. Candidate scoring
8. Option synthesis
9. Verification
```

Nem minden case futtatja mindet.

---

# 14. Candidate Pool

A rendszer először **nem 3 ajánlatot gyárt**.

Hanem létrehoz egy nagyobb candidate poolt.

Például:

```text
42 destinations
↓
18 viable
↓
11 hard constraints pass
↓
7 high-quality candidates
↓
candidate enrichment
↓
3–5 complete trip concepts
```

Flightnál:

```text
150 flight results
↓
32 constraint-compatible
↓
14 high quality
↓
6 serious candidates
```

Hotel:

```text
300 hotels
↓
48 constraint-compatible
↓
16 preference-compatible
↓
8 serious candidates
```

---

# 15. Hard Constraint Engine

Első szűrés:

```text
Budget
Dates
Passengers
Destination
Flight stops
Hotel category
Required criteria
Availability
```

**Hard constraintet nem lehet score-alapú kompenzációval megkerülni.**

---

# 16. Preference / Optimization Engine

A megmaradt jelöltekre:

* AHP
* PROMETHEE II
* TripScore
* value analysis
* experience fit
* geo efficiency
* itinerary quality
* risk
* freshness

---

# 17. Score decomposition

Nem csak:

> **8.7/10**

hanem:

```text
OVERALL SCORE: 8.7

Price             9.5 × 40%
Location          6.1 × 25%
Hotel quality     9.2 × 20%
Experience        8.8 × 15%
────────────────────────
Final             8.7
```

És:

> **Mi húzza felfelé?**
> Ár + hotel

> **Mi húzza lefelé?**
> Lokáció

Ezután az advisor pontosan érti, **miért került előre egy opció**.

---

# 18. Option Synthesis

A rendszer célja:

### Option A

**Best Overall**

### Option B

**Best Value**

### Option C

**Best Experience**

De csak akkor, ha tényleg léteznek jó alternatívák.

```text
Target: 3
Acceptable: 2
Minimum: 1
```

---

# 19. Relative Comparison

Minden opció egymáshoz képest is értelmezhető.

Például:

|            |          A |        B |       C |
| ---------- | ---------: | -------: | ------: |
| Ár         |       820k | **690k** |    960k |
| Flight     | **Direct** |   1 stop |  Direct |
| Hotel      |        8.8 |      8.1 | **9.5** |
| Location   |        9.1 |      7.4 | **9.4** |
| Experience |        8.5 |      8.0 | **9.7** |

És:

> B 130 000 Ft-tal olcsóbb A-nál, de gyengébb lokációjú.

---

# 20. Geo + Itinerary Engine

A kiválasztott optionből itinerary készül.

### Input

* hotel
* flights
* activities
* opening hours
* travel times
* preferences
* weather
* duration
* meal windows
* arrival/departure
* geographic clustering

### Output

```text
Day 1
Arrival
→ Airport
→ Hotel
→ Nearby dinner

Day 2
Area A
→ Attraction 1
→ Lunch
→ Attraction 2
→ Dinner
```

A rendszer figyeli:

* nyitvatartást
* travel time-ot
* túlzsúfolt napokat
* felesleges visszautazást
* érkezési/indulási időket
* időjárásfüggő programokat.

---

# 21. Backup / Alternative Engine

Minden fontos programhoz lehet:

**Primary**

> Senso-ji

**Backup 1**

> Meiji Shrine

**Backup 2**

> teamLab

**Backup 3**

> Tokyo Skytree

És a backupok rankingje is az ügyfélprofilból jön.

Nem random „10 Things to Do”.

---

# 22. Opening Hours / Live Verification

Az activity intelligencehez:

* opening hours
* closed days
* booking requirement
* ticket availability, ahol elérhető
* weather suitability
* last entry
* estimated duration

Ez alapján például:

> ⚠️ **Keddre nem ajánlott**
> Az attraction kedden zárva van.

vagy:

> 🔄 **Backup aktiválható**
> Esős idő esetén ezt a beltéri programot javasoljuk.

---

# 23. Advisor Editing Layer

Ez kritikus.

A rendszer ajánl, **de az advisor a végső döntéshozó**.

Műveletek:

* Pin
* Remove
* Replace
* Add manually
* Change hotel
* Change flight
* Change activity
* Change day
* Reorder
* Lock element
* Unlock element
* Find better
* Re-optimize
* Compare

Ha valamit módosít:

```text
Advisor change
      ↓
Impact analysis
      ↓
Affected components
      ↓
Re-optimization
```

Például:

> „A hotel cseréje +42 000 Ft, de a napi átlagos utazási idő 31 perccel csökken.”

---

# 24. Locking

Ez is fontos.

Az advisor mondhatja:

> 🔒 **Ezt a repülőt megtartjuk.**

Onnantól az optimizer nem cseréli le.

Ugyanez:

* flight locked
* hotel locked
* destination locked
* activity locked
* date locked
* budget locked

---

# 25. Re-optimization

Ha változik:

```text
Budget
↓
Recalculate

Flight
↓
Recalculate

Hotel
↓
Recalculate

Preference
↓
Recalculate

Date
↓
Research affected layer
```

Nem mindig kell mindent nulláról lefuttatni.

---

# 26. Constraint Relaxation

Ha nincs találat:

> **Nem találtunk megfelelő opciót.**

Majd megmutatjuk:

```text
Current:
800k
Direct flight
4★
Beach
Fixed dates
```

Lehetséges:

* +10% budget
* ±1 nap
* 1 stop engedélyezése
* 4★ → 3★
* másik airport
* másik destination

**De semmi nem történik automatikusan.**

Advisor választ.

---

# 27. Verification / Provenance

Minden lényeges adat mögött:

```text
Source
Provider
URL
Checked at
Freshness
Verification status
```

Például:

> Flight price
> ✓ Verified 8 min ago

> Hotel rating
> ✓ Verified

> Activity opening hours
> ⚠️ Last checked 2 days ago

---

# 28. Research Run

Minden kutatás egy külön:

```text
ResearchRun
```

amely tartalmazza:

* input snapshot
* resolved intent
* research plan
* providers
* started_at
* completed_at
* partial results
* errors
* candidates
* final output
* modifications

Így később vissza lehet nézni:

> **Miért ezt ajánlotta a rendszer tegnap?**

---

# 29. Shortlist

Az advisor végül:

```text
Candidate pool
      ↓
3 recommended options
      ↓
Advisor review
      ↓
2 shortlisted
      ↓
1 selected
```

A shortlist nem ugyanaz, mint az automatikus ranking.

---

# 30. Proposal

A kiválasztott optionből:

* itinerary
* flight
* hotel
* activities
* pricing
* images
* map
* explanation
* inclusions
* exclusions
* booking links

→ Proposal.

A proposal snapshot.

Utána:

```text
v1
↓
client feedback
↓
revision
↓
v2
```

---

# 31. Feedback loop

A rendszer itt nem ér véget.

Ügyfél:

> „Ez jó, de inkább jobb hotelt szeretnék.”

Ez visszamegy:

```text
Client feedback
↓
Requirement change
↓
Preference/constraint update
↓
Affected component detection
↓
Re-optimization
↓
New proposal
```

---

# 32. A teljes adatkapcsolat

A legfontosabb kapcsolatot így definiálnám:

```text
CLIENT PROFILE
      │
      ├──────────────┐
      ▼              │
CURRENT CASE         │
      │              │
      ├── dates      │
      ├── budget     │
      ├── travelers  │
      ├── existing   │
      └── availability
      │
      ▼
INTAKE
      │
      ▼
RESEARCH INTENT
      │
      ▼
REQUIREMENTS
      │
      ├── HARD
      ├── SOFT
      ├── AVOID
      └── NICE TO HAVE
      │
      ▼
ACTIVE CRITERIA
      │
      ▼
AHP / PROMETHEE
      │
      ▼
RESEARCH PLAN
      │
      ├──── Flight Intelligence
      ├──── Stay Intelligence
      ├──── Destination Intelligence
      ├──── Experience Intelligence
      ├──── Weather
      ├──── Cost
      ├──── Geo / Maps
      └──── Risk
              │
              ▼
        ENRICHED CANDIDATES
              │
              ▼
       HARD CONSTRAINT FILTER
              │
              ▼
        PREFERENCE RANKING
              │
              ▼
        OPTION SYNTHESIS
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
    OVERALL VALUE EXPERIENCE
       │      │      │
       └──────┼──────┘
              ▼
       EXPLAINABILITY
              │
              ▼
      MAP + ITINERARY
              │
       ┌──────┴──────┐
       ▼             ▼
    PRIMARY        BACKUPS
       │             │
       └──────┬──────┘
              ▼
       ADVISOR EDIT
              │
       ┌──────┴─────────┐
       ▼                ▼
    APPROVE          RE-OPTIMIZE
       │                │
       └───────┬────────┘
               ▼
           SHORTLIST
               ▼
           PROPOSAL
               ▼
          CLIENT
               │
          FEEDBACK
               │
               └────→ RESEARCH
```

---

# 33. A legfontosabb új absztrakció: Research State

Szerintem a jelenlegi rendszerből hiányzik egy ilyen központi fogalom.

Minden case-nek legyen egy folyamatosan frissülő:

## `ResearchState`

amiben a rendszer tudja:

```text
WHAT WE KNOW
WHAT WE DON'T KNOW
WHAT IS FIXED
WHAT IS FLEXIBLE
WHAT MATTERS
WHAT WE ARE SEARCHING
WHAT WE FOUND
WHAT IS VERIFIED
WHAT THE ADVISOR CHANGED
WHAT STILL NEEDS A DECISION
```

Ez sokkal fontosabb, mint a 9 külön workflow.

A 9 workflow **ennek a ResearchState-nek a különböző feldolgozási mintái**.

---

# 34. És ebből következik a legfontosabb UX-elv

Az Advisornak **soha nem kell az egész rendszert értenie.**

Nem ezt látja:

> AHP → PROMETHEE → MultiOptionEngine → ConstraintRelaxation → Geo Intelligence → Research Strategy 7...

Hanem:

> **Mit tudunk?**
> **Mit szeretne az ügyfél?**
> **Mi fontos neki?**
> **Mit találtunk?**
> **Miért ezt ajánljuk?**
> **Mit szeretnél megváltoztatni?**

A teljes komplexitás **a rendszer mögött marad**.

---

## 35. A teljes Advisor így 5 nagy fázisra egyszerűsíthető

A 9 strategy helyett UX-szinten én ezt használnám:

### ① UNDERSTAND

**Értsük meg a kérést.**

Input + ügyfél + meglévő dolgok + intent.

### ② DEFINE

**Határozzuk meg, mi számít.**

Hard constraints + releváns kritériumok + AHP/PROMETHEE.

### ③ RESEARCH

**Keressük meg és ellenőrizzük a lehetőségeket.**

Flight + stay + destination + experiences + maps + weather + cost.

### ④ DECIDE

**Mutassuk meg a legjobb lehetőségeket és hogy miért.**

3 options + comparison + explanation + map + itinerary + backups.

### ⑤ DELIVER

**Finomítsuk és készítsük el az ajánlatot.**

Advisor edits → shortlist → proposal → client → feedback → reoptimization.