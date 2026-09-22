---
id: WORK-003-advisor-workspace-v1
type: work_item
name: Optivoya Advisor Workspace v1 Implementation Checklist
status: in_progress

description: Az Optivoya B2B Advisor Workspace v1 fázisonkénti feladatlistája, hard/soft feltételrendszere, shared intelligence rétege, providencia modellje, hibatűrése, perzisztenciája és átvételi kritériumai (Acceptance Criteria).

created_at: 2026-09-17
updated_at: 2026-09-17

related:
  - "[[advisor-workspace-blueprint]]"
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
  - [x] `TripOption`, `OptionComponent` (Teljes utazási opciók és elemeik).
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
  - [x] Aszinkron kutatási státusz végpontok (`job_id` polling / SSE).
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
  - [x] **3-módú Költségvetési Modell:**
    - [x] *Mode A:* Teljes összköltségkeret (pl. 300 000 Ft).
    - [x] *Mode B:* Komponens keretek (max. járat, max. szállás, max. program, max. transzfer).
    - [x] *Mode C:* Keresési hatókör (Search Scope kijelölés: pl. csak járat + hotel).
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
- [x] **Hibatűrés & Provider Hibakezelés (Resilience Layer):**
  - [x] Kiwi timeout kezelése, Cozycozy részleges eredmények feldolgozása, Open-Meteo fallback.
  - [x] Rate limit kezelés és lejárt gyorsítótár (Stale Cache) fallback transzparens jelöléssel.
  - [x] Egy provider kiesése nem blokkolja a többi komponens megjelenítését.
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
  - [x] Felesleges és halmozott glassmorphism (túlzott háttérelmosás) megszüntetése, tiszta Material 3 felületi rétegződés alkalmazása.
  - [x] 0% Emoji gombokon, badge-eken és navigációs tabokon $\rightarrow$ tiszta Material Symbols Outlined ikonok (`calendar_today`, `flight`, `hotel`, `local_activity`).
  - [x] 0% elcsépelt marketing buzzword (*Unlock, Elevate, Supercharge*), helyettük konkrét mérnöki adatok.
- [x] **3-Szintű Tipográfiai Hierarchia (`DESIGN_SYSTEM.md`):**
  - [x] `--font-display`: `'Plus Jakarta Sans', sans-serif` (főcímek, szekciófejlécek).
  - [x] `--font-body`: `'Inter', -apple-system, sans-serif` (folyószöveg, űrlapcímkék, gombok).
  - [x] `--font-mono`: `'JetBrains Mono', monospace` (árak, időpontok, időtartamok, PROMETHEE értékek, kódok).
- [x] **UX Alapelvek & Döntéstámogató Ergonómia (`UX_PRINCIPLES.md`, `UX_PATTERNS.md`):**
  - [x] *Plain Language Invariant:* Nincsenek tudományos rövidítések és akadémikus zsargon a UI felületén.
  - [x] *4 Valódi Állapot minden modulban:* Empty State (segítőkész indító kártya), Loading State (progresszív státusz), Error State (emberi magyarázat és helyreállítás), Success State (tiszta adatok).
  - [x] *Domináns Primary CTA:* Minden nézeten pontosan egy kiemelt fő akció gomb.
- [x] **Quality Gates & DoD Bekötés (`QUALITY_GATES.md`, `DEFINITION_OF_DONE.md`):**
  - [x] Funkcionalitási, UX/Dizájn, Architektúra és Knowledge validációs kapuk érvényesítése minden módosítás előtt.

### 🎯 Phase 4.5 Acceptance Criteria
1. [x] Az Advisor Workspace felülete (`/advisor`) azonnal felismerhetően az Optivoya kanonikus zöld stílusát, hivatalos logóját (`/static/logo.png`) és 3-szintű tipográfiáját használja.
2. [x] A felület mentes minden AI-slop tünettől (nincs kék-lila neon gradient, nincs emoji-spam a gombokon, nincs akadémikus zsargon).
3. [x] A `python scripts/knowledge/validate.py` 100%-os zöld eredménnyel fut le.

---

## 📌 Phase 5: Multi-Option Generation & Archetypes
> **Cél:** 3 valós trade-offokkal rendelkező, teljes értékű utazási opció előállítása.

- [x] **`MultiOptionEngine` Implementálása (`app/services/multi_option_engine.py`):**
  - [x] Teljes utazási kombinációk előállítása a kutatási poolból.
  - [x] Érvénytelen (hard constraintet sértő) kombinációk kizárása.
  - [x] **3 Alapértelmezett Archetípus Kijelölése:**
    - [x] **Option A — BEST OVERALL:** Legmagasabb kiegyensúlyozott pontszám.
    - [x] **Option B — BEST VALUE:** Alacsonyabb összköltség, kiemelkedő ár-érték arány.
    - [x] **Option C — BEST EXPERIENCE:** Legerősebb élmény- és programilleszkedés.
- [x] **Diverzitási Szabályok (Diversity Constraints):**
  - [x] A 3 opciónak érdemben különböznie kell (különböző város VAGY szignifikáns árkülönbség VAGY eltérő járattípus/szálláskategória).
- [x] **Option Kártyák Renderelése (`advisor_options.js`):**
  - [x] Teljes ár és egy főre jutó költség.
  - [x] Repülő és szállás összefoglaló, időtartam, megbízhatósági státusz (*Verified / Estimated / Needs review*).
  - [x] Strukturált illeszkedési indoklás (*Why it fits*) és kompromisszumok (*Trade-offs*).

### 🎯 Phase 5 Acceptance Criteria
1. [x] A generált 3 opció ugyanabból a hiteles adatpoolból származik, minden hard constraintet tiszteletben tart.
2. [x] A 3 opció között mérhető és világosan kommunikált kompromisszumok (trade-offok) vannak.

---

## 📌 Phase 6: Relative Comparison, "Why This Option?" & Advisor Overrides
> **Cél:** Egymás melletti összehasonlítás, relatív különbségek és az advisor manuális döntési szabadsága (Whitebox).

- [x] **Side-by-Side Összehasonlító Mátrix (`/advisor/cases/:id/compare`, `advisor_option_compare.js`):**
  - [x] Desktop egymás melletti táblázat: Ár, Járattípus, Menetidő, Szállás csillag/értékelés, Strand, Gasztro, Kultúra.
  - [x] **Relatív Összehasonlító Logika:** Nem csak abszolút számok, hanem relatív különbségek (pl. *"Kréta 46 000 Ft-tal olcsóbb, de Mallorca repülőútja 4 órával kényelmesebb"*).
- [x] **Adatvezérelt "Why This Option?" Generátor:**
  - [x] Scoring delta és constraint kielégítés alapján előállított indoklás (LLM hallucinációk nélkül).
- [x] **"Find Better" Célzott Finomhangolási Modál (`find_better_modal.js`):**
  - [x] Célzott keresés: Alacsonyabb ár, kényelmesebb járat, jobb hotel, több program.
- [x] **Advisor Override & Whitebox Ergonomics:**
  - [x] Ajánlások kézi szerkesztése.
  - [x] Jelöltek kitűzése (Pin), törlése, vagy manuális hozzáadása.
  - [x] Sorrend kézi felülírása indoklás rögzítésével (`override_reason`).

### 🎯 Phase 6 Acceptance Criteria
1. [x] Az összehasonlító felület világosan megmutatja a 3 opció egymáshoz viszonyított előnyeit és hátrányait.
2. [x] Az advisor manuálisan módosíthatja vagy kicserélheti az opciók bármely elemét, a rendszer nem viselkedik zárt black-boxként.

---

## 📌 Phase 7: Constraint Relaxation, Verification & Risk Engine
> **Cél:** Zsákutcák megszüntetése (No dead-ends) és kockázati figyelmeztetések.

- [x] **`ConstraintRelaxationService` Implementálása (`app/services/constraint_relaxation_service.py`):**
  - [x] 0 találat esetén pontos ok-okozati diagnózis (mely feltételek ütköznek).
  - [x] 1-kattintásos enyhítési javaslatok számszerűsített új találati számmal (pl. *"+1 átszállás engedélyezése $\rightarrow$ 12 új opció"*, *"+40 000 Ft keret $\rightarrow$ 7 új opció"*).
  - [x] A megkötéseket a rendszer csak tanácsadói jóváhagyással módosítja.
- [x] **`VerificationService` & Provenance Ellenőrzés (`app/services/verification_service.py`):**
  - [x] Ár, menetrend, szoba elérhetőség hitelesítési státuszai (`VERIFIED`, `ESTIMATED`, `NEEDS_REVIEW`).
- [x] **`TripRiskService` & Figyelmeztető Motor (`app/services/trip_risk_service.py`):**
  - [x] Kockázatok azonosítása: <60 perces átszállás, éjszakai érkezés, rejtett üdülőhelyi díj (resort fee), hiányzó reptéri transzfer, nyitvatartási ütközés.
  - [x] Prioritási szintek: `Critical`, `Warning`, `Info`.

### 🎯 Phase 7 Acceptance Criteria
1. [x] Nincs olyan szűrési kombináció, ami zsákutcába (üres hibaüzenetbe) fut: a rendszer mindig konkrét feloldási javaslatokat kínál.
2. [x] Minden releváns utazási kockázat (pl. szűk átszállási idő) figyelmeztető kártyaként jelenik meg.

---

## 📌 Phase 8: Shortlist & Multi-Option Proposal
> **Cél:** Multi-Option ügyfélajánlat generálás, szerkesztés, verziókezelés és nyomtatás/PDF export.

- [x] **Shortlist Kezelés (`/advisor/cases/:id/shortlist`, `advisor_shortlist.js`):**
  - [x] Kiválasztott 1–3 opció véglegesítése az ajánlathoz.
  - [x] Belső tanácsadói jegyzetek hozzáadása (`advisor_notes` — ügyfél előtt rejtve).
- [x] **Multi-Option Ügyfélajánlat Generátor (`/advisor/cases/:id/proposal`, `advisor_proposal.js`):**
  - [x] 1–3 opciót tartalmazó egységes ügyféldokumentum renderelése.
  - [x] **Beépített Ajánlatszerkesztő:**
    - [x] Cím, személyes bevezető szöveg szerkesztése.
    - [x] Opciók sorrendje és ki/be kapcsolása (járat, hotel, programok, árak, foglalási linkek).
    - [x] Tanácsadói ajánlás és konklúzió hozzáadása.
  - [x] **Verziókezelés:** Proposal v1, v2, v3 tárolása, előzmények megőrzése.
  - [x] **Nyomtatási & PDF Export:** A4 méretre optimalizált stíluslapok (`@media print`), ügynökségi branding és logó.

### 🎯 Phase 8 Acceptance Criteria
1. [x] Az ajánlat 1, 2 vagy 3 opciót is hibátlanul prezentál összehasonlító vagy szekvenciális nézetben.
2. [x] A generált PDF/nyomtatási kép tördelése professzionális, minden ár és komponens forrás-hitelesített.

---

## 📌 Phase 9: Client Feedback, Timeline & Re-Optimization
> **Cél:** Ügyféli visszajelzések kezelése és zökkenőmentes újragenerálás.

- [x] **Ügyfél Visszajelzés Rögzítése:**
  - [x] Gyors visszajelzési pontok (pl. *"Mallorca tetszik, de olcsóbb hotel kell"*).
- [x] **Re-Optimization Workflow:**
  - [x] Módosított megkötésekkel történő újratervezés az ügyfél-eset újrakezdése nélkül.
  - [x] Automatikus Proposal v2 létrehozás a v1 megőrzésével.
- [x] **Eset Idővonal & Audit Napló (`advisor_timeline.js`):**
  - [x] Időbélyeges eseménynapló (Brief rögzítve $\rightarrow$ Kutatás $\rightarrow$ 3 opció $\rightarrow$ Ajánlat v1 $\rightarrow$ Visszajelzés $\rightarrow$ Ajánlat v2).

### 🎯 Phase 9 Acceptance Criteria
1. [x] Az ügyfél visszajelzése után 1 kattintással újragenerálható a csomag anélkül, hogy elölről kellene kezdeni a folyamatot.
2. [x] Az idővonal pontosan naplózza a tervezési folyamat minden lépését és a megtakarított kutatási időt.

---

## 📌 Phase 10: Hardening, Playwright E2E Tesztek & Minőségkapuk
> **Cél:** 20 automatizált E2E teszt, reszponzivitási audit és 100%-os tudásgráf-integritás.

- [x] **20 Átfogó Playwright E2E Teszt (`tests/e2e/test_advisor_workspace_e2e.py`):**
  - [x] `test_advisor_dashboard_load`
  - [x] `test_client_create_and_profile`
  - [x] `test_trip_case_create`
  - [x] `test_brief_completion_with_hard_soft_constraints`
  - [x] `test_budget_modes_total_and_component`
  - [x] `test_search_scope_component_only`
  - [x] `test_research_execution_and_progress`
  - [x] `test_multi_option_generation_3_archetypes`
  - [x] `test_option_diversity_verification`
  - [x] `test_side_by_side_comparison_matrix`
  - [x] `test_relative_comparison_why_this_option`
  - [x] `test_find_better_modal_workflow`
  - [x] `test_constraint_relaxation_on_zero_results`
  - [x] `test_provider_failure_resilience_and_stale_cache`
  - [x] `test_risk_engine_warnings_display`
  - [x] `test_shortlist_management`
  - [x] `test_multi_option_proposal_generation_and_export`
  - [x] `test_client_feedback_and_proposal_v2_reoptimization`
  - [x] `test_unauthorized_case_access_isolation`
  - [x] `test_b2c_master_planner_zero_regression`
- [x] **UI Reszponzivitás, DOM Pixel Audit & Billentyűzet UX:**
  - [x] 0 horizontális túlcsordulás desktopon (1280px+) és mobilon (<768px).
  - [x] Gyorsbillentyűk ellenőrzése.
- [x] **Knowledge Graph Validáció:**
  - [x] `python scripts/knowledge/validate.py` sikeres futása (181 node, 740 wikilink, 0 error).

### 🎯 Phase 10 Acceptance Criteria
1. [x] Mind a 20 Advisor E2E teszt és az összes meglévő B2C teszt hibátlanul átmegy (100% Pass Rate: 74/74 teszt zöld).
2. [x] A teljes tudástár és a forráskód kapcsolatai 100%-ban érvényesek.
