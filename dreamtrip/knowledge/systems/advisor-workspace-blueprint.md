---
id: advisor-workspace-blueprint
type: system
name: Optivoya Advisor Workspace Blueprint & Architecture Specification
status: active

description: Az Optivoya B2B Travel Advisor Workspace v1 teljes, részletes műszaki specifikációja (Master Architecture Blueprint). Matematikai képletekkel, döntési modellekkel, adatstruktúrákkal, a 9 kutatási munkafolyamattal, a 3 archetípus szintézisével, a relatív összehasonlító motorral, a feltétel-enyhítési diagnosztikával, az audit idővonallal, a biztonsági/többügynökséges izolációval és az API szerződésekkel.

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
  - templates/hub.html

related:
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
  - "[[ADR-010-dual-auth-and-app-switcher]]"
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

# 🏛️ Optivoya B2B Advisor Workspace — Master Architecture Blueprint (v1.0)

Ez a dokumentum az **Optivoya B2B Travel Advisor Workspace** teljes, implementációs szintű műszaki tervrajza. Célja, hogy egy mérnök vagy AI ágens a nulláról, külső kontextus nélkül is képes legyen a teljes rendszert maradéktalanul reprodukálni és üzemeltetni.

---

## 1. Termékstratégia & Rendszerarchitektúra

### 1.1 Cél és Szerepkör
Az Optivoya B2B Advisor Workspace egy **Desktop-First döntéstámogató és ajánlatkészítő munkaállomás** független utazási tanácsadók, concierge irodák és boutique utazási ügynökségek számára.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       OPTIVOYA ARCHITEKTÚRA RÉTEGEK                    │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Post-Login Hub (`/hub`) → [Master Planner] | [Advisor Workspace]     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Presentation Layer:                                                 │
│    - B2C Master Planner UI (`/planner`)                                │
│    - B2B Advisor Workspace Desktop Shell (`/advisor`)                  │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Shared Intelligence & Decision Layer (Közös Motorok):              │
│    - `DestinationMatchingService` & `ExperienceIntelligenceService`    │
│    - `FlightIntelligenceService` (Kiwi.com GraphQL)                    │
│    - `AccommodationIntelligenceService` (Cozycozy Scraper)             │
│    - `TripScoreService` (Harmonizált 4-pilléres kompozit index)        │
│    - `AHPEngine` & `PrometheeEngine` (MCDM rangsoroló motorok)         │
│    - `ItineraryOptimizationService` & `ProposalRenderer`               │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Advisor Core Orchestration Layer (`app/services/`):                 │
│    - `AdvisorOrchestrationService` (9 specializált kutatási stratégia) │
│    - `PreferenceResolver` (4 rétegű prioritási hierarchia)             │
│    - `MultiOptionEngine` (3 döntési archetípus szintézise)             │
│    - `RelativeComparisonService` (Relatív trade-off mátrix)            │
│    - `ConstraintRelaxationService` (0-találat feloldási motor)         │
│    - `VerificationService` & `TripRiskService` (Provenance & Kockázat) │
│    - `ProposalService` & `TimelineReoptimizationService`               │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Data & Persistence Layer:                                           │
│    - Supabase Cloud PostgreSQL (`beta_users`, `trip_cases`, `clients`) │
│    - Helyi SQLite fallback (`data/analytics.db`)                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Adatmodellek & Entitások (`app/models/advisor_models.py`)

### 2.1 Multi-Tenant Szervezeti Modell
* `Agency`: Ügynökségi entitás (`id`, `name`, `slug`, `branding`, `is_active`).
* `AgencyBranding`: Ügynökségi arculati beállítások (`company_name`, `primary_color`, `accent_color`, `logo_url`, `contact_email`, `footer_text`).
* `Advisor`: Utazási tanácsadó profilja (`id`, `agency_id`, `name`, `email`, `role`, `default_origin`, `default_currency`).

### 2.2 Ügyfélprofil & Tartós Preferenciák
* `Client`: Ügyfél rekord (`id`, `agency_id`, `advisor_id`, `name`, `email`, `phone`, `passport_country`, `tags`, `preferences`, `notes`).
* `ClientPreferences`: Tartós utazási profil (`preferred_origins`, `preferred_airlines`, `avoid_airlines`, `hotel_min_stars`, `hotel_min_rating`, `direct_flights_only`, `interests`, `travel_style`).

### 2.3 TripCase & Döntési Aggregátum
* `TripCase`: Központi döntési aggregátum (`id`, `agency_id`, `advisor_id`, `client_id`, `title`, `status`, `scope`, `budget_mode`, `budget_constraint`, `origin`, `destination_focus`, `adults`, `children`, `duration_days`, `out_date`, `in_date`, `preferences`, `shortlist_ids`, `selected_option_ids`).

---

## 3. Preferencia-feloldási Hierarchia (`PreferenceResolver`)

A rendszer a preferenciákat szigorúan **4 prioritási szinten** oldja fel:

$$\text{Advisor Overrides} \succ \text{Case Brief} \succ \text{Client Profile} \succ \text{System Defaults}$$

### 3.1 Feltétel Kategóriák
1. **Hard Constraints (Szigorú Megkötések — Pass/Fail):**
   * $\text{Price} \le \text{TotalBudget}$ (Hard ceiling, szigorúan betartva).
   * $\text{Stops} = 0$, ha $\text{direct\_flights\_only} = \text{True}$.
   * $\text{HotelStars} \ge \text{min\_hotel\_stars}$.
   * $\text{HotelRating} \ge \text{min\_hotel\_rating}$.
2. **Soft Preferences (Súlyozott Döntési Preferenciák — 0–100 skálán):**
   * AHP 4-Pillér Súlyok: $w_{\text{dest}} + w_{\text{flight}} + w_{\text{stay}} + w_{\text{exp}} = 100$.
   * Vibe preferenciák: kultúra, gasztronómia, tengerpart, természet, éjszakai élet.
3. **Avoid Rules (Büntetett vagy Tiltott Elemek):**
   * Hajnali indulás ($\le 06:00$) vagy késő éjszakai érkezés ($\ge 23:30$).
   * Tiltott légitársaságok vagy célállomások.
4. **Nice-to-Have (Pozitív Bónusz Pontok):**
   * Reggeli az árban ($+5$), medence ($+3$), ingyenes lemondás ($+5$).

---

## 4. A 9 Tanácsadói Kutatási Stratégia (`[[advisor-research-pipeline]]`)

Az [`AdvisorOrchestrationService`](file:///e:/Data/other_projects/dreamtrip/app/services/advisor_orchestration_service.py) 9 dedikált munkafolyamatot valósít meg:
1. `DESTINATION_DISCOVERY`: 45+ európai város párhuzamos rangsorolása.
2. `KNOWN_DESTINATION`: Konkrét városra fókuszált mély járat- és szálláskutatás.
3. `FLIGHT_FIRST`: Járatmenetrend és kedvező viteldíjak priorizálása.
4. `STAY_FIRST`: Prémium 4-5★ szállodák elérhetősége által vezérelt csomagépítés.
5. `FULL_TRIP_OPTIMIZATION`: Egyidejű, többcélú Pareto-optimalizálás.
6. `COMPONENT_ONLY`: Csak járat vagy csak szállás keresése.
7. `MIXED_SCOPE`: 2–4 konkrét célállomás egymás melletti versenyeztetése.
8. `RE_OPTIMIZATION`: 1-kattintásos újrahangolás megváltozott feltételekkel.
9. `FIND_BETTER`: Célzott komponens-csere a globális kontextus megőrzésével.

---

## 5. A 3 Döntési Archetípus Szintézise (`[[advisor-option-generation]]`)

A motor objektív, standardizált $[0, 100]$ skálájú profilok alapján állítja elő a csomagokat:

```text
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│  🏆 OPTION A: BEST OVERALL   │   💡 OPTION B: BEST VALUE    │ 🌟 OPTION C: BEST EXPERIENCE │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Kiegyensúlyozott menetrend,  │ Optimális költségvetés,      │ 4-5★ prémium szállás,        │
│ optimális ár-érték és a      │ okos járatválasztás a szilárd│ gazdag programkínálat és     │
│ legmagasabb TripScore index. │ minőségi alapok mellett.     │ maximális élmény/vibe fit.   │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

### 5.1 Objektív Pontszámítási Képletek

#### Option A: `BEST_OVERALL`
$$\text{Score}_{\text{Overall}} = \text{TripScore} \in [0, 100]$$

#### Option B: `BEST_VALUE`
$$\text{Score}_{\text{Value}} = \min\left(100.0, \frac{\text{TripScore}}{\max\left(\frac{\text{Price}}{\text{Budget}_{\text{ref}}}, 0.3\right)} \times 0.8\right)$$

#### Option C: `BEST_EXPERIENCE`
$$\text{Score}_{\text{Exp}} = 0.35 \cdot S_{\text{stay}} + 0.25 \cdot S_{\text{act}} + 0.25 \cdot S_{\text{vibe}} + 0.15 \cdot S_{\text{flight}}$$
Ahol:
- $S_{\text{stay}} = \left(\frac{\text{Stars}}{5.0} \times 50\right) + \left(\frac{\text{Rating}}{10.0} \times 50\right)$
- $S_{\text{act}} = \min\left(\frac{N_{\text{activities}}}{4.0}, 1.0\right) \times 100$
- $S_{\text{vibe}} = \text{VibeMatchScore} \in [0, 100]$
- $S_{\text{flight}} = 100.0 \text{ (közvetlen)}, 75.0 \text{ (1 átszállás)}, 50.0 \text{ (2+ átszállás)}$

### 5.2 A 3-Option Szabály (Quality Invariant)
```text
Cél: 3 opció | Előnyben részesített: 3 | Elfogadható: 2 | Minimum: 1
```
*Tilos gyenge minőségű hotelt vagy kényelmetlen járatot mesterségesen beilleszteni kizárólag azért, hogy meglegyen a 3 kártya.*

---

## 6. Relatív Összehasonlító Motor (`RelativeComparisonService`)

Az `Option A` (Best Overall) képezi a viszonyítási bázist ($P_{\text{base}}$):
- $\Delta \text{Price}_{\text{nominal}} = \text{Price}_i - P_{\text{base}}$
- $\Delta \text{Price}_{\%} = \frac{\text{Price}_i - P_{\text{base}}}{P_{\text{base}}} \cdot 100\%$
- $\Delta \text{FlightDuration} = T_i^{\text{flight}} - T_{\text{base}}^{\text{flight}}$
- Értelmezhető, adat-alapú trade-off mondatok előállítása generatív sablonok nélkül.

---

## 7. Feltétel-enyhítési Motor (`ConstraintRelaxationService`)

0 találat (Dead-End) esetén a motor strukturált diagnózist és 1-kattintásos javaslatokat ad:
- Keretbővítés (+15%, +30%)
- Átszállás engedélyezése (+1 stop)
- Szálláskategória mérséklése (5★ $\to$ 4★)
- Dátumrugalmasság ($\pm 2$ nap)

*Semmilyen megkötés nem lazul csendben vagy automatikusan!*

---

## 8. Kockázatelemző & Figyelmeztető Motor (`TripRiskService`)

Valós idejű logisztikai kockázatok detektálása:
- `TIGHT_TRANSFER`: Átszállási idő $< 90$ perc.
- `EARLY_DEPARTURE`: Indulás $< 06:00$.
- `LATE_ARRIVAL`: Érkezés a szállásra $> 23:30$.
- `LOW_RATING_RISK`: Hotel pontszám $< 7.2$.

---

## 9. Ügyfélajánlat (Proposal) Verziókezelés (`[[advisor-proposal-versioning]]`)

- **Immutábilis pillanatfelvétel (Snapshot)**: Az elküldött ajánlat adatai zárolódnak.
- **Elágaztatott verziótörténet**: $v1 \to v2 \to v3$ indoklással.
- **A4 Print/PDF Export**: Teljes körű nyomtatási stíluslap ([proposal_print.html](file:///e:/Data/other_projects/dreamtrip/templates/advisor/proposal_print.html)).

---

## 10. Kriptográfiai Ajánlat-Megosztás & Biztonság (`[[advisor-security-and-multitenancy]]`)

- **Token**: 256 bites véletlenszerű URL-safe token (`ProposalShare`).
- **Időkorlát & Visszavonhatóság**: Opcionális lejárati dátum és 1-kattintásos azonnali tiltás (`/revoke-share`).
- **Ügyfél-biztonságos nézet**: Belső tanácsadói jegyzetek (`advisor_notes`) és technikai pontszámok szigorú eltávolítása.

---

## 11. REST API Végpontok (`[[advisor-api-contract]]`)

A teljes végpontkatalógus a [advisor-api-contract.md](file:///e:/Data/other_projects/dreamtrip/knowledge/systems/advisor-api-contract.md) dokumentumban található.

---

## 12. Asztali Felület & UX Specifikáció (`[[advisor-workspace-ux-specification]]`)

A részletes interakciós és asztali munkaállomás-szerződés a [advisor-workspace-ux-specification.md](file:///e:/Data/other_projects/dreamtrip/knowledge/systems/advisor-workspace-ux-specification.md) dokumentumban található.

---

## 13. Költségvetési Korlát Modell (`[[advisor-budget-and-constraints]]`)

- Teljes utazási keret vs. komponens keretek (járat, hotel, programok, transzfer).
- Per-fő és csoportos bázis automatikus skálázása.
- Hard (szigorú) vs. Target (rugalmas) keménységi állapot.

---

## 14. Aszinkron Kutatási Életciklus (`[[advisor-research-run-lifecycle]]`)

- Állapotgép: `QUEUED` $\to$ `RUNNING` $\to$ `PARTIAL` / `COMPLETED` / `FAILED` / `CANCELLED`.
- Részleges forráskiesés esetén (pl. Kiwi timeout) a folyamat nem omlik össze, hanem `PARTIAL` státusszal zárul.

---

## 15. Adat-eredet & Mélylinkelés (`[[advisor-provenance-and-verification]]`)

- `ProviderProvenance` modell: forrástípus (`api`, `aggregator`, `manual`), ellenőrzés ideje, TTL, mélylinkek és verifikációs státusz (`VERIFIED`, `ESTIMATED`, `STALE`, `NEEDS_REVIEW`, `UNAVAILABLE`).

---

## 16. Többügynökséges Izoláció (`[[advisor-security-and-multitenancy]]`)

- Ügynökségi (`agency_id`) határok védelme szerveroldali hitelesítéssel és Supabase RLS házirendekkel.

---

## 17. Minőségbiztosítás & Governance Invariánsok

1. **Anti-AI-Slop Szabályzat (`[[ANTI_AI_SLOP_POLICY]]`):** Belső algoritmusnevek (PROMETHEE, AHP) nem szerepelnek a felületen.
2. **Dizájnrendszer (`[[DESIGN_SYSTEM]]`):** Zöld fenyő paletta, 3-szintű tipográfia.
3. **Minőségi Kapuk (`[[QUALITY_GATES]]` & `[[DEFINITION_OF_DONE]]`):** 100%-os zöld tesztlefedettség és érvényes tudásgráf.
