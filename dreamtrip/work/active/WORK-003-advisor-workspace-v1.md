---
id: WORK-003-advisor-workspace-v1
type: work_item
name: Optivoya Advisor Workspace v1 Implementation Checklist
status: in_progress

description: Az Optivoya B2B Advisor Workspace v1 fázisonkénti feladatlistája, hard/soft feltételrendszere, shared intelligence rétege, providencia modellje, hibatűrése, perzisztenciája és átvételi kritériumai (Acceptance Criteria).

created_at: 2026-09-17
updated_at: 2026-09-24

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[advisor-workspace-ux-specification]]"
  - "[[advisor-budget-and-constraints]]"
  - "[[advisor-option-generation]]"
  - "[[advisor-research-pipeline]]"
  - "[[advisor-provenance-and-verification]]"
  - "[[advisor-security-and-multitenancy]]"
  - "[[advisor-research-run-lifecycle]]"
  - "[[advisor-api-contract]]"
  - "[[advisor-proposal-versioning]]"
  - "[[trip-case]]"
  - "[[master-planner-blueprint]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[PRODUCT_PRINCIPLES]]"
---

# WORK-003: Optivoya Advisor Workspace v1 Checklist

Ez a dokumentum tartalmazza az **Optivoya Advisor Workspace v1** teljes, 10 fázisból álló implementációs feladatlistáját és átvételi kritériumait. A fejlesztés során a feladatokat folyamatosan pipáljuk.

---

## 📌 Phase 0: Architecture Extraction & Shared Intelligence Layer
> **Cél:** A meglévő B2C Planner és az új Advisor Workspace közös, leválasztott `Shared Intelligence Layer`-t használjon (nem B2C hack).

- [x] **Engine Extraction & Szolgáltatás Leválasztás:**
  - [x] `DestinationMatchingService` leválasztása önálló, újrafelhasználható szolgáltatássá (`app/services/destination_matching_service.py`).
  - [x] `FlightIntelligenceService` leválasztása önálló szolgáltatássá (`app/services/flight_intelligence_service.py`).
  - [x] `AccommodationIntelligenceService` leválasztása (`app/services/accommodation_intelligence_service.py`).
  - [x] `ExperienceIntelligenceService` leválasztása (`app/services/experience_intelligence_service.py`).
  - [x] `TripScoreService` leválasztása (`app/services/trip_scoring_service.py`).
  - [x] `AHPEngine` általános, moduláris döntési mátrix szervizzé alakítása (`app/services/ahp_engine.py`).
  - [x] `PrometheeEngine` általános, többkritériumos rangsoroló motorrá alakítása (`app/services/promethee_engine.py`).
  - [x] `ItineraryOptimizationService` önálló útiterv- és sétaútvonal generálóvá alakítása (`app/services/itinerary_optimization_service.py`).
  - [x] `ProposalRenderer` közös ajánlat- és PDF/nyomtatás generálóvá tétele (`app/services/proposal_renderer.py`).
- [x] **B2C Regresszióvédelem:**
  - [x] Meglévő `/planner` API szerződések érintetlenségének biztosítása.
  - [x] Egységtesztek zöld futása a leválasztott motorokon (`tests/test_shared_intelligence_services.py`).

### 🎯 Phase 0 Acceptance Criteria
1. A B2C Master Planner 100%-ban regressziómentesen működik a leválasztott `Shared Intelligence Layer`-en keresztül.
2. Minden motor (AHP, PROMETHEE, Kiwi, Cozycozy, Open-Meteo, Numbeo, OSM, Itinerary, Proposal) tiszta Python szervizként importálható az Advisor Orchestrator számára.


---

## 📌 Phase 1: Database, Security & Provenance Data Models
> **Cél:** Robusztus PostgreSQL/Supabase séma, multi-tenancy védelem és teljes adat-eredet (Provenance) nyilvántartás.

- [x] **Pydantic Adatmodellek & Sémák (`app/models/advisor_models.py`):**
  - [x] `Agency`, `Advisor` (Multi-tenant szervezeti hierarchia).
  - [x] `Client`, `ClientPreferences` (Ügyfélprofil tartós preferenciákkal).
  - [x] `TripCase`, `TripCasePreferences` (Központi ügy aggregátum).
  - [x] `BudgetConstraint` (Hard/Target hardness, Per-person/Group basis, Component-level limits: flight, stay, activities, transport).
  - [x] `ResearchRun` & `ResearchRunStatus` (`QUEUED`, `RUNNING`, `PARTIAL`, `COMPLETED`, `FAILED`, `CANCELLED`).
  - [x] `ResearchCandidate` (Provenance-kötött jelöltek szűrt listája).
  - [x] `ProviderProvenance` (provider, source_type, source_url, deep_link, booking_url, checked_at, freshness_ttl, verification_status).
  - [x] `AdvisorOverride` / `AdvisorOverrideEntry` (Audited actor_id, timestamp, field, previous_value, new_value, reason).
  - [x] `ProposalShare` (Kriptográfiailag biztonságos token_hash, opcionális expiry, revocable flag, access auditing).
  - [x] `TripOption`, `OptionComponent`, `OptionSet` (Teljes utazási opciók és elemeik).
  - [x] `Shortlist`, `AdvisorNote`, `CaseEvent` (Audit timeline napló).
  - [x] `Proposal`, `ProposalVersion` (Ajánlatok és verziótörténet).
- [x] **Hard vs. Soft Constraint Modell (`ResolvedTripPreferences`):**
  - [x] `hard_constraints` (Kötelező megkötések: pl. szigorúan max. összköltség, csak közvetlen járat, min. 4★).
  - [x] `soft_preferences` (Súlyozott preferenciák: pl. jobb legyen a gasztro, mint a strand).
  - [x] `avoid_rules` (Kifejezetten kerülendő elemek: pl. hajnali járat, bizonyos légitársaság).
  - [x] `nice_to_have` (Előny, de nem kizáró ok: pl. medence, tengerre néző kilátás).
  - [x] `advisor_overrides` (Tanácsadói kézi felülírások és rögzítések).
- [x] **Research Scope Modell:**
  - [x] `scope`: `['destination', 'flight', 'stay', 'activities', 'full_trip']` vagy tetszőleges kombináció (pl. csak járat + hotel).
- [x] **Provenance & Provider Adatmodell (`ProviderProvenance`):**
  - [x] `source`, `source_url`, `provider` (Kiwi, Cozycozy, Open-Meteo, Numbeo, OSM).
  - [x] `checked_at`, `expires_at` / `freshness_ttl`.
  - [x] `verification_status` (`VERIFIED`, `ESTIMATED`, `STALE`, `UNAVAILABLE`).
  - [x] `raw_reference`, `is_estimated`.
- [x] **Biztonság & Multi-Tenancy (Server-side & RLS):**
  - [x] PostgreSQL migráció (`scripts/migrations/003_advisor_workspace.sql`).
  - [x] Row Level Security (RLS): Agency izoláció, tanácsadói tagság ellenőrzés.
  - [x] Szigorú szerveroldali jogosultságvizsgálat: Kliens, Case, Proposal azonosítók nem hamisíthatók a frontendről.

### 🎯 Phase 1 Acceptance Criteria
1. Minden külső adat rendelkezik forrás- és frissességi metaadattal (Provenance).
2. Egy advisor kizárólag a saját ügynökségéhez tartozó klienseket és ügyeket tudja lekérni/módosítani (RLS és szerveroldali Auth tesztekkel igazolva).
3. A preferenciamodell élesen megkülönbözteti a hard megkötéseket a soft preferenciáktól.


---

## 📌 Phase 2: Advisor Shell, Dashboard & API Contracts
> **Cél:** Információ-sűrű B2B felület, állapotkezelés és szigorú REST API szerződések.

- [x] **REST API Szerződés & Végpontok (`app/routers/advisor_api.py`):**
  - [x] Szabványos kérés/válasz sémák, hibakontraktus, validáció, lapozás és szűrés.
  - [x] Idempotens végpontok (`Idempotency-Key` támogatás).
  - [x] Aszinkron kutatási státusz és leállítási végpontok (`GET /cases/{case_id}/research/{run_id}`, `POST .../cancel`).
  - [x] Kriptográfiai megosztási végpontok (`POST /proposals/{id}/share`, `POST .../revoke-share`, `GET /public/proposals/{token}`).
- [x] **Frontend Alaprendszer (`templates/advisor/`, `static/js/advisor/`):**
  - [x] `advisor_workspace.html` (Desktop-first, 1280px+ optimalizált, bal oldali navigáció, kontextus panel).
  - [x] `advisor_state.js` (Reaktív állapot: currentAdvisor, currentClient, currentCase, draftState, options, shortlist).
  - [x] `advisor_api.js` (Typed API kliens hiba- és idempotencia-kezeléssel).
  - [x] `advisor_navigation.js` (Gyorsbillentyűk: `N` = Új ügy, `C` = Ügyfelek, `R` = Kutatás, `P` = Ajánlat).
- [x] **Dashboard Képernyő (`/advisor`, `advisor_dashboard.js`):**
  - [x] Aktív ügyek (Active Cases) kártyák státuszjelzőkkel (Brief, Research, Shortlist, Proposal, Revision, Closed).
  - [x] Legutóbbi ügyfelek és ajánlatok listája.
  - [x] KPI sáv: Active Cases, Proposals Created, Research Time Saved.

### 🎯 Phase 2 Acceptance Criteria
1. [x] A dashboard <300ms alatt betöltődik, az aktív ügyek állapota azonnal látható.
2. [x] Az API szerződés teljes mértékben típusbiztos és Pydantic sémákkal validált.

---

## 📌 Phase 3: Client Management & Deep Trip Brief
> **Cél:** Ügyfélprofilok tartós preferenciákkal, 3-módú költségvetés és hierarchikus preferencia-feloldás.

- [x] **Ügyfélkezelés (`/advisor/clients`, `/advisor/clients/:client_id`):**
  - [x] Ügyféllista kereséssel, szűréssel, új ügyfél modállal (`advisor_clients.js`).
  - [x] Ügyfél adatlap tartós utazási stílussal és járat/szállás alapbeállításokkal (`advisor_clients.js`).
- [x] **Új Utazási Ügy & Brief Képernyő (`/advisor/cases/new`, `advisor_brief.js`):**
  - [x] Ügyfél kiválasztása vagy azonnali létrehozása.
  - [x] Alapadatok: Indulás, Utasok (felnőtt/gyerek), Cél fókusz, Dátumok, Időtartam ablak.
  - [x] **3-módú Költségvetési Modell & Hardness:**
    - [x] *Mode A:* Teljes összköltségkeret (pl. 300 000 Ft).
    - [x] *Mode B:* Komponens keretek (max. járat, max. szállás, max. program, max. transzfer).
    - [x] *Mode C:* Keresési hatókör (Search Scope kijelölés: pl. csak járat + hotel).
    - [x] *Hardness:* `hard` (zéró túllépés megengedett) vs `target` (explicit tanácsadói jóváhagyással lazítható max %-ig).
  - [x] **Hard/Soft Megkötések & Avoid Szabályok Bevitele.**
- [x] **`PreferenceResolver` Szolgáltatás (`app/services/preference_resolver.py`):**
  - [x] Szigorú prioritási sorrend: `Advisor Overrides > Case Brief > Client Profile > System Defaults`.
- [x] **Draft Mentés & Autosave:**
  - [x] Automatikus és explicit piszkozat-mentés a brief szerkesztése közben.

### 🎯 Phase 3 Acceptance Criteria
1. [x] A Brief felület egyetlen átlátható képernyőn rögzíti az összes igényt.
2. [x] A PreferenceResolver determinisztikusan állítja elő a feloldott preferenciamodellt a prioritási szintek szerint.

---

## 📌 Phase 4: Research Orchestration & 9 Workflow Engine
> **Cél:** Rugalmas, nem lineáris kutatási munkaterület 9 különböző tanácsadói munkafolyamat támogatásával és hibatűréssel.

- [x] **9 Tanácsadói Kutatási Stratégia Implementálása (`AdvisorOrchestrationService`):**
  - [x] 1. *Destination Discovery* (45+ célállomás szűrése és rangsorolása $\rightarrow$ járatok $\rightarrow$ szállások).
  - [x] 2. *Known Destination Research* (Konkrét célpont mély kutatása).
  - [x] 3. *Flight-First Strategy* (Legjobb repülőjegyek keresése $\rightarrow$ kapcsolódó opciók).
  - [x] 4. *Stay-First Strategy* (Prémium szállás keresése $\rightarrow$ logisztika).
  - [x] 5. *Full-Trip Optimization* (Teljes csomag egyidejű matematikai optimalizálása).
  - [x] 6. *Component-Only Research* (Kizárólag repülő VAGY kizárólag szállás keresése megadott keretre).
  - [x] 7. *Mixed-Scope Research* (Több város párhuzamos összehasonlítása csak repülő+hotelre).
  - [x] 8. *Re-Optimization Workflow* (Meglévő eset újraszámolása módosított feltétellel).
  - [x] 9. *Find Better Workflow* (Egy kiválasztott opció célzott finomhangolása).
- [x] **Aszinkron Életciklus & Hibatűrés (ResearchRun Lifecycle):**
  - [x] `QUEUED` $\rightarrow$ `RUNNING` $\rightarrow$ `PARTIAL` / `COMPLETED` / `FAILED` / `CANCELLED` állapotgép.
  - [x] Kiwi timeout kezelése, Cozycozy részleges eredmények feldolgozása, Open-Meteo fallback.
  - [x] Rate limit kezelés és lejárt gyorsítótár (Stale Cache) fallback transzparens jelöléssel.
  - [x] Egy provider kiesése nem blokkolja a többi komponens megjelenítését (`PARTIAL` run status).
- [x] **Kutatási Felület & Progresszív Betöltés (`/advisor/cases/:id/research`, `advisor_research.js`):**
  - [x] Mindig látható kontextus sáv (Ügyfél, Keret, Dátumok, Fő megkötések).
  - [x] Folyamatjelző kártya lépésenkénti vizualizációval (Destinations ✓, Flights ✓, Hotels ●, Scoring ○).
  - [x] Részleges eredmények azonnali megjelenítése (Progressive rendering).
- [x] **Idempotencia & Munkamenet Folytatás:**
  - [x] Megszakadt kutatás folytatása (`resume interrupted research`).
  - [x] Ügy duplikálása, archiválása és visszaállítása.

### 🎯 Phase 4 Acceptance Criteria
1. [x] Bármelyik külső API kiesése vagy lassúsága esetén a rendszer nem omlik össze, hanem részleges/becsült jelöléssel visszaadja az elérhető adatokat.
2. [x] Mind a 9 kutatási stratégia végrehajtható és idempotens módon mentődik az adatbázisba.

---

## 📌 Phase 4.5: Governance, Design System & Anti-AI-Slop Alignment
> **Cél:** Az Advisor Workspace felületének teljes körű becsatornázása az Optivoya kanonikus fenyőzöld dizájnrendszerébe, a logó megjelenítése, valamint a `governance/` (design, quality, ux) előírásainak és az Anti-AI-Slop szabályzatnak való 100%-os megfeleltetés.

- [x] **Kanonikus Fenyőzöld & Chartreuse Design Rendszer (`DESIGN_SYSTEM.md`, `theme.css`):**
  - [x] Klisés kék/cián sötét téma (`#0284c7`, `#0f172a`, `#38bdf8`) teljes lecserélése a brand színeire:
    - `--primary: #003710` (Mély fenyőzöld)
    - `--primary-container: #1c4e24`
    - `--secondary: #406900`
    - `--secondary-container: #a7f540` (Friss Chartreuse akcentus)
    - `--surface: #ffffff`, `--surface-container-low: #f2f4f2`, `--surface-container: #eceeec`
  - [x] Hivatalos Optivoya logó (`/static/logo.png`) elhelyezése a bal felső sidebar sávban.
- [x] **Anti-AI-Slop Irányelvek Érvényesítése (`ANTI_AI_SLOP_POLICY.md`):**
  - [x] 0% AI lila-kék/neon gradient, 0% fluoreszkáló glow fényudvar.
  - [x] Felesleges és halmozott glassmorphism megszüntetése, tiszta Material 3 felületi rétegződés alkalmazása.
  - [x] 0% Emoji gombokon, badge-eken és navigációs tabokon $\rightarrow$ tiszta Material Symbols Outlined ikonok (`calendar_today`, `flight`, `hotel`, `local_activity`).
  - [x] 0% elcsépelt marketing buzzword (*Unlock, Elevate, Supercharge*), helyettük konkrét mérnöki adatok.
- [x] **3-Szintű Tipográfiai Hierarchia (`DESIGN_SYSTEM.md`):**
  - [x] `--font-display`: `'Plus Jakarta Sans', sans-serif` (főcímek, szekciófejlécek).
  - [x] `--font-body`: `'Inter', -apple-system, sans-serif` (folyószöveg, űrlapcímkék, gombok).
  - [x] `--font-mono`: `'JetBrains Mono', monospace` (árak, időpontok, időtartamok, kódok).
- [x] **UX Alapelvek & Döntéstámogató Ergonómia (`UX_PRINCIPLES.md`, `UX_PATTERNS.md`):**
  - [x] *Plain Language Invariant:* Nincsenek tudományos rövidítések és akadémikus zsargon a UI felületén.
  - [x] *4 Valódi Állapot minden modulban:* Empty State, Loading State, Error State, Success State.
  - [x] *Domináns Primary CTA:* Minden nézeten pontosan egy kiemelt fő akció gomb.
- [x] **Quality Gates & DoD Bekötés (`QUALITY_GATES.md`, `DEFINITION_OF_DONE.md`):**
  - [x] Funkcionalitási, UX/Dizájn, Architektúra és Knowledge validációs kapuk érvényesítése minden módosítás előtt.

### 🎯 Phase 4.5 Acceptance Criteria
1. [x] Az Advisor Workspace felülete (`/advisor`) azonnal felismerhetően az Optivoya kanonikus zöld stílusát, hivatalos logóját (`/static/logo.png`) és 3-szintű tipográfiáját használja.
2. [x] A felület mentes minden AI-slop tünettől.
3. [x] A `python scripts/knowledge/validate.py` 100%-os zöld eredménnyel fut le.

---

## 📌 Phase 5: Multi-Option Generation & Archetypes
> **Cél:** 3 valós trade-offokkal rendelkező, teljes értékű utazási opció előállítása normalizált célfüggvényekkel és magic numberök nélkül.

- [x] **`MultiOptionEngine` Implementálása (`app/services/multi_option_engine.py`):**
  - [x] Teljes utazási kombinációk előállítása a kutatási poolból.
  - [x] Érvénytelen (hard constraintet sértő) kombinációk kizárása.
  - [x] **3 Normalizált Célprofil (Objective Profiles):**
    - [x] **Option A — BEST OVERALL:** Legmagasabb TripScore kiegyensúlyozott súlyokkal.
    - [x] **Option B — BEST VALUE:** Normalizált Value Efficiency ($0..100$) mutató alapján.
    - [x] **Option C — BEST EXPERIENCE:** Normalizált Experience Score ($0..100$) szállás, programok és vibe súlyozásával.
  - [x] **3-Opciós Szabály (3-Option Rule):**
    - [x] Target: 3, Preferred: 3, Acceptable: 2, Minimum: 1.
    - [x] Tilos gyenge/nem illeszkedő hotelt vagy járatot mesterségesen behelyettesíteni csak a 3 kártya kedvéért.
  - [x] **Diverzitási Szabályok (Diversity Constraints):**
    - [x] Valódi kompromisszumok létrehozása anélkül, hogy a diverzitás kedvéért lerondanánk a minőséget.
- [x] **Option Kártyák Renderelése (`advisor_options.js`):**
  - [x] Teljes ár és egy főre jutó költség.
  - [x] Repülő és szállás összefoglaló, időtartam, megbízhatósági státusz (*Verified / Estimated / Needs review*).
  - [x] Strukturált illeszkedési indoklás (*Why it fits*) és kompromisszumok (*Trade-offs*).

### 🎯 Phase 5 Acceptance Criteria
1. [x] A generált opciók ugyanabból a hiteles adatpoolból származnak, minden hard constraintet tiszteletben tartanak.
2. [x] A célfüggvények mentesek az önkényes magic numberöktől, normalizáltak ($0..100$).
3. [x] 2 valódi opció esetén a rendszer nem gyárt mesterséges harmadik rossz opciót.

---

## 📌 Phase 6: Relative Comparison, "Why This Option?" & Advisor Overrides
> **Cél:** Egymás melletti összehasonlítás, relatív különbségek és az advisor manuális döntési szabadsága (Whitebox).

- [x] **Side-by-Side Összehasonlító Mátrix (`/advisor/cases/:id/compare`, `advisor_option_compare.js`):**
  - [x] Desktop egymás melletti táblázat: Ár, Járattípus, Menetidő, Szállás csillag/értékelés, Strand, Gasztro, Kultúra.
  - [x] **Relatív Összehasonlító Logika:** Abszolút értékek, relatív különbségek és százalékos delaták ahol értelmezhető.
- [x] **Adatvezérelt "Why This Option?" Generátor:**
  - [x] Scoring delta és constraint kielégítés alapján előállított indoklás (LLM hallucinációk nélkül).
- [x] **"Find Better" Célzott Finomhangolási Modál (`find_better_modal.js`):**
  - [x] Célzott keresés az alapadatok és hard megkötések megőrzése mellett (Lower price, Better flight, Better hotel, Better experience).
- [x] **Advisor Override & Whitebox Ergonomics:**
  - [x] Jelöltek kitűzése (Pin), törlése, vagy manuális hozzáadása.
  - [x] Auditált felülbírálás `AdvisorOverrideEntry` rögzítéssel (`actor_id`, `timestamp`, `field`, `previous_value`, `new_value`, `reason`).

### 🎯 Phase 6 Acceptance Criteria
1. [x] Az összehasonlító felület világosan megmutatja az opciók egymáshoz viszonyított relatív előnyeit és hátrányait.
2. [x] Az advisor manuálisan módosíthatja vagy kicserélheti az opciók bármely elemét; minden felülbírálás auditált.

---

## 📌 Phase 7: Constraint Relaxation, Verification & Risk Engine
> **Cél:** Zsákutcák megszüntetése (No dead-ends), explicit jóváhagyás és kockázati figyelmeztetések.

- [x] **`ConstraintRelaxationService` Implementálása (`app/services/constraint_relaxation_service.py`):**
  - [x] 0 találat esetén pontos ok-okozati diagnózis (mely feltételek ütköznek).
  - [x] 1-kattintásos enyhítési javaslatok számszerűsített új találati számmal.
  - [x] **Hard Constraint Védelem:** A rendszer soha nem lazít automatikusan/csendben hard megkötést; kizárólag explicit advisor jóváhagyással léptethető életbe.
- [x] **`VerificationService` & Provenance Ellenőrzés (`app/services/verification_service.py`):**
  - [x] Ár, menetrend, szoba elérhetőség hitelesítési státuszai (`VERIFIED`, `ESTIMATED`, `NEEDS_REVIEW`).
  - [x] Deep linkek, forrás URL-ek és frissességi időbélyegek megjelenítése.
- [x] **`TripRiskService` & Figyelmeztető Motor (`app/services/trip_risk_service.py`):**
  - [x] Kockázatok azonosítása: <60 perces átszállás, éjszakai érkezés, rejtett üdülőhelyi díj, hiányzó reptéri transzfer, nyitvatartási ütközés.
  - [x] Prioritási szintek: `Critical`, `Warning`, `Info`.

### 🎯 Phase 7 Acceptance Criteria
1. [x] Nincs olyan szűrési kombináció, ami zsákutcába fut: a rendszer mindig konkrét feloldási javaslatokat kínál.
2. [x] Hard constraint soha nem lazul automatikusan.

---

## 📌 Phase 8: Shortlist & Multi-Option Proposal
> **Cél:** Multi-Option ügyfélajánlat generálás, szerkesztés, verziókezelés, biztonságos megosztás és nyomtatás/PDF export.

- [x] **Shortlist Kezelés (`/advisor/cases/:id/shortlist`, `advisor_shortlist.js`):**
  - [x] Kiválasztott 1–3 opció véglegesítése az ajánlathoz.
  - [x] Belső tanácsadói jegyzetek hozzáadása (`advisor_notes` — ügyfél előtt szigorúan rejtve).
- [x] **Multi-Option Ügyfélajánlat Generátor (`/advisor/cases/:id/proposal`, `advisor_proposal.js`):**
  - [x] 1–3 opciót tartalmazó egységes ügyféldokumentum renderelése.
  - [x] **Beépített Ajánlatszerkesztő:** Cím, bevezető, opciók ki/be kapcsolása, konklúzió.
  - [x] **Immutable Proposal Snapshot:** Rögzített állapot a generálás pillanatában.
  - [x] **Verziókezelés:** Proposal v1, v2, v3 tárolása, előzmények megőrzése.
  - [x] **Kriptográfiai Megosztás (`ProposalShare`):** URL-safe token, kliens-biztonságos adatszűrés (belső jegyzetek és árrés nélkül), visszavonási lehetőség (`revoke`).
  - [x] **Nyomtatási & PDF Export:** A4 méretre optimalizált stíluslapok (`@media print`), ügynökségi branding és logó.

### 🎯 Phase 8 Acceptance Criteria
1. [x] Az ajánlat 1, 2 vagy 3 opciót is hibátlanul prezentál összehasonlító vagy szekvenciális nézetben.
2. [x] A publikus megosztási link nem enged hozzáférést a teljes Case-hez vagy belső tanácsadói jegyzetekhez.

---

## 📌 Phase 9: Client Feedback, Timeline & Re-Optimization
> **Cél:** Ügyféli visszajelzések kezelése és zökkenőmentes újragenerálás.

- [x] **Ügyfél Visszajelzés Rögzítése:** Gyors visszajelzési pontok rögzítése.
- [x] **Re-Optimization Workflow:** Módosított megkötésekkel történő újratervezés Proposal v2 létrehozásával.
- [x] **Eset Idővonal & Audit Napló (`advisor_timeline.js`):** Időbélyeges eseménynapló.

### 🎯 Phase 9 Acceptance Criteria
1. [x] Az ügyfél visszajelzése után 1 kattintással újragenerálható a csomag.
2. [x] Az idővonal pontosan naplózza a tervezési folyamat minden lépését.

---

## 📌 Phase 10: Hardening, Egység-, Integrációs & E2E Tesztek
> **Cél:** Átfogó tesztelési lefedettség a megerősített architektúrán és 100%-os tudásgráf-integritás.

- [x] **Hardening Unit & Integration Tesztek (`tests/test_advisor_workspace_hardening.py`):**
  - [x] `test_budget_constraint_semantics_hard_vs_target`
  - [x] `test_advisor_override_audit_trail`
  - [x] `test_multi_option_engine_objective_profiles_and_diversity`
  - [x] `test_multi_option_engine_3_option_rule_never_pads_fake_options`
  - [x] `test_provider_provenance_structure_and_freshness`
  - [x] `test_async_research_run_lifecycle_and_cancel`
  - [x] `test_proposal_share_token_security_and_revocation`
  - [x] `test_public_proposal_view_sanitization`
  - [x] `test_api_contract_validation_and_idempotency`
  - [x] `test_b2c_master_planner_regression_protection`
- [x] **Playwright E2E Tesztek (`tests/e2e/test_advisor_workspace_e2e.py`):**
  - [x] 20 automatizált végpontok közötti teszt a teljes tanácsadói folyamatra.
- [x] **Knowledge Graph Validáció:**
  - [x] `python scripts/knowledge/validate.py` sikeres futása.

### 🎯 Phase 10 Acceptance Criteria
1. [x] Az összes hardening teszt, B2C regressziós teszt és E2E teszt hibátlanul lefut.
2. [x] A teljes tudástár és a forráskód kapcsolatai 100%-ban érvényesek.
