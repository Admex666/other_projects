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
---

# WORK-003: Optivoya Advisor Workspace v1 Checklist

Ez a dokumentum tartalmazza az **Optivoya Advisor Workspace v1** teljes, 10 fázisból álló implementációs feladatlistáját és átvételi kritériumait. A fejlesztés során a feladatokat folyamatosan pipáljuk.

---

## 📌 Phase 0: Architecture Extraction & Shared Intelligence Layer
> **Cél:** A meglévő B2C Planner és az új Advisor Workspace közös, leválasztott `Shared Intelligence Layer`-t használjon (nem B2C hack).

- [ ] **Engine Extraction & Szolgáltatás Leválasztás:**
  - [ ] `DestinationMatchingService` leválasztása önálló, újrafelhasználható szolgáltatássá.
  - [ ] `FlightIntelligenceService` leválasztása önálló szolgáltatássá (Kiwi API kliens, ár/idősáv/átszállás analízis).
  - [ ] `AccommodationIntelligenceService` leválasztása (Cozycozy kliens, rating/ár/lokáció analízis).
  - [ ] `ExperienceIntelligenceService` leválasztása (POI-k, élménygráf, vibe profilok).
  - [ ] `TripScoreService` leválasztása (4-pilléres kompozit scoring és hasznos nyaralási idő kalkuláció).
  - [ ] `AHPEngine` általános, moduláris döntési mátrix szervizzé alakítása.
  - [ ] `PrometheeEngine` általános, többkritériumos rangsoroló motorrá alakítása.
  - [ ] `ItineraryOptimizationService` önálló útiterv- és sétaútvonal generálóvá alakítása.
  - [ ] `ProposalRenderer` közös ajánlat- és PDF/nyomtatás generálóvá tétele (`SingleTripProposal` + `MultiOptionProposal`).
- [ ] **B2C Regresszióvédelem:**
  - [ ] Meglévő `/planner` API szerződések érintetlenségének biztosítása.
  - [ ] Meglévő 17 E2E teszt zöld futása a leválasztott motorokon.

### 🎯 Phase 0 Acceptance Criteria
1. A B2C Master Planner 100%-ban regressziómentesen működik a leválasztott `Shared Intelligence Layer`-en keresztül.
2. Minden motor (AHP, PROMETHEE, Kiwi, Cozycozy, Open-Meteo, Numbeo, OSM, Itinerary, Proposal) tiszta Python szervizként importálható az Advisor Orchestrator számára.

---

## 📌 Phase 1: Database, Security & Provenance Data Models
> **Cél:** Robusztus PostgreSQL/Supabase séma, multi-tenancy védelem és teljes adat-eredet (Provenance) nyilvántartás.

- [ ] **Pydantic Adatmodellek & Sémák (`app/models/advisor_models.py`):**
  - [ ] `Agency`, `Advisor` (Multi-tenant szervezeti hierarchia).
  - [ ] `Client`, `ClientPreferences` (Ügyfélprofil tartós preferenciákkal).
  - [ ] `TripCase`, `TripCasePreferences` (Központi ügy aggregátum).
  - [ ] `TripOption`, `OptionComponent` (Teljes utazási opciók és elemeik).
  - [ ] `Shortlist`, `AdvisorNote`, `CaseEvent` (Audit timeline napló).
  - [ ] `Proposal`, `ProposalVersion` (Ajánlatok és verziótörténet).
- [ ] **Hard vs. Soft Constraint Modell (`ResolvedTripPreferences`):**
  - [ ] `hard_constraints` (Kötelező megkötések: pl. szigorúan max. €1200, csak közvetlen járat, min. 4★).
  - [ ] `soft_preferences` (Súlyozott preferenciák: pl. jobb legyen a gasztro, mint a strand).
  - [ ] `avoid_rules` (Kifejezetten kerülendő elemek: pl. hajnali járat, bizonyos légitársaság).
  - [ ] `nice_to_have` (Előny, de nem kizáró ok: pl. medence, tengerre néző kilátás).
  - [ ] `advisor_overrides` (Tanácsadói kézi felülírások és rögzítések).
- [ ] **Research Scope Modell:**
  - [ ] `scope`: `['destination', 'flight', 'stay', 'activities', 'full_trip']` vagy tetszőleges kombináció (pl. csak járat + hotel).
- [ ] **Provenance & Provider Adatmodell (`ProviderProvenance`):**
  - [ ] `source`, `source_url`, `provider` (Kiwi, Cozycozy, Open-Meteo, Numbeo, OSM).
  - [ ] `checked_at`, `expires_at` / `freshness_ttl`.
  - [ ] `verification_status` (`VERIFIED`, `ESTIMATED`, `STALE`, `UNAVAILABLE`).
  - [ ] `raw_reference`, `is_estimated`.
- [ ] **Biztonság & Multi-Tenancy (Server-side & RLS):**
  - [ ] PostgreSQL migráció (`scripts/migrations/003_advisor_workspace.sql`).
  - [ ] Row Level Security (RLS): Agency izoláció, tanácsadói tagság ellenőrzés.
  - [ ] Szigorú szerveroldali jogosultságvizsgálat: Kliens, Case, Proposal azonosítók nem hamisíthatók a frontendről.

### 🎯 Phase 1 Acceptance Criteria
1. Minden külső adat rendelkezik forrás- és frissességi metaadattal (Provenance).
2. Egy advisor kizárólag a saját ügynökségéhez tartozó klienseket és ügyeket tudja lekérni/módosítani (RLS és szerveroldali Auth tesztekkel igazolva).
3. A preferenciamodell élesen megkülönbözteti a hard megkötéseket a soft preferenciáktól.

---

## 📌 Phase 2: Advisor Shell, Dashboard & API Contracts
> **Cél:** Információ-sűrű B2B felület, állapotkezelés és szigorú REST API szerződések.

- [ ] **REST API Szerződés & Végpontok (`app/routers/advisor_api.py`):**
  - [ ] Szabványos kérés/válasz sémák, hibakontraktus, validáció, lapozás és szűrés.
  - [ ] Idempotens végpontok (`Idempotency-Key` támogatás).
  - [ ] Aszinkron kutatási státusz végpontok (`job_id` polling / SSE).
- [ ] **Frontend Alaprendszer (`templates/advisor/`, `static/js/advisor/`):**
  - [ ] `advisor_workspace.html` (Desktop-first, 1280px+ optimalizált, bal oldali navigáció, kontextus panel).
  - [ ] `advisor_state.js` (Reaktív állapot: currentAdvisor, currentClient, currentCase, draftState, options, shortlist).
  - [ ] `advisor_api.js` (Typed API kliens hiba- és idempotencia-kezeléssel).
  - [ ] `advisor_navigation.js` (Gyorsbillentyűk: `N` = Új ügy, `C` = Ügyfelek, `R` = Kutatás, `P` = Ajánlat).
- [ ] **Dashboard Képernyő (`/advisor`, `advisor_dashboard.js`):**
  - [ ] Aktív ügyek (Active Cases) kártyák státuszjelzőkkel (Brief, Research, Shortlist, Proposal, Revision, Closed).
  - [ ] Legutóbbi ügyfelek és ajánlatok listája.
  - [ ] KPI sáv: Active Cases, Proposals Created, Research Time Saved.

### 🎯 Phase 2 Acceptance Criteria
1. A dashboard <300ms alatt betöltődik, az aktív ügyek állapota azonnal látható.
2. Az API szerződés teljes mértékben típusbiztos és Pydantic sémákkal validált.

---

## 📌 Phase 3: Client Management & Deep Trip Brief
> **Cél:** Ügyfélprofilok tartós preferenciákkal, 3-módú költségvetés és hierarchikus preferencia-feloldás.

- [ ] **Ügyfélkezelés (`/advisor/clients`, `/advisor/clients/:client_id`):**
  - [ ] Ügyféllista kereséssel, szűréssel, új ügyfél modállal (`advisor_clients.js`).
  - [ ] Ügyfél adatlap tartós utazási stílussal és járat/szállás alapbeállításokkal (`advisor_client_profile.js`).
- [ ] **Új Utazási Ügy & Brief Képernyő (`/advisor/cases/new`, `advisor_brief.js`):**
  - [ ] Ügyfél kiválasztása vagy azonnali létrehozása.
  - [ ] Alapadatok: Indulás, Utasok (felnőtt/gyerek), Cél fókusz, Dátumok, Időtartam ablak.
  - [ ] **3-módú Költségvetési Modell:**
    - [ ] *Mode A:* Teljes összköltségkeret (pl. 300 000 Ft).
    - [ ] *Mode B:* Komponens keretek (max. járat, max. szállás, max. program, max. transzfer).
    - [ ] *Mode C:* Keresési hatókör (Search Scope kijelölés: pl. csak járat + hotel).
  - [ ] **Hard/Soft Megkötések & Avoid Szabályok Bevitele.**
- [ ] **`PreferenceResolver` Szolgáltatás (`app/services/preference_resolver.py`):**
  - [ ] Szigorú prioritási sorrend: `Case Override > Client Profile > Advisor Default > System Default`.
- [ ] **Draft Mentés & Autosave:**
  - [ ] Automatikus piszkozat-mentés a brief szerkesztése közben.

### 🎯 Phase 3 Acceptance Criteria
1. A Brief felület egyetlen átlátható képernyőn rögzíti az összes igényt.
2. A PreferenceResolver determinisztikusan állítja elő a feloldott preferenciamodellt a prioritási szintek szerint.

---

## 📌 Phase 4: Research Orchestration & 9 Workflow Engine
> **Cél:** Rugalmas, nem lineáris kutatási munkaterület 9 különböző tanácsadói munkafolyamat támogatásával és hibatűréssel.

- [ ] **9 Tanácsadói Kutatási Stratégia Implementálása (`AdvisorOrchestrationService`):**
  - [ ] 1. *Destination Discovery* (45+ célállomás szűrése és rangsorolása $\rightarrow$ járatok $\rightarrow$ szállások).
  - [ ] 2. *Known Destination Research* (Konkrét célpont mély kutatása).
  - [ ] 3. *Flight-First Strategy* (Legjobb repülőjegyek keresése $\rightarrow$ kapcsolódó opciók).
  - [ ] 4. *Stay-First Strategy* (Prémium szállás keresése $\rightarrow$ logisztika).
  - [ ] 5. *Full-Trip Optimization* (Teljes csomag egyidejű matematikai optimalizálása).
  - [ ] 6. *Component-Only Research* (Kizárólag repülő VAGY kizárólag szállás keresése megadott keretre).
  - [ ] 7. *Mixed-Scope Research* (Több város párhuzamos összehasonlítása csak repülő+hotelre).
  - [ ] 8. *Re-Optimization Workflow* (Meglévő eset újraszámolása módosított feltétellel).
  - [ ] 9. *Find Better Workflow* (Egy kiválasztott opció célzott finomhangolása).
- [ ] **Hibatűrés & Provider Hibakezelés (Resilience Layer):**
  - [ ] Kiwi timeout kezelése, Cozycozy részleges eredmények feldolgozása, Open-Meteo fallback.
  - [ ] Rate limit kezelés és lejárt gyorsítótár (Stale Cache) fallback transzparens jelöléssel.
  - [ ] Egy provider kiesése nem blokkolja a többi komponens megjelenítését.
- [ ] **Kutatási Felület & Progresszív Betöltés (`/advisor/cases/:id/research`, `advisor_research.js`):**
  - [ ] Mindig látható kontextus sáv (Ügyfél, Keret, Dátumok, Fő megkötések).
  - [ ] Folyamatjelző kártya lépésenkénti vizualizációval (Destinations ✓, Flights ✓, Hotels ●, Scoring ○).
  - [ ] Részleges eredmények azonnali megjelenítése (Progressive rendering).
- [ ] **Idempotencia & Munkamenet Folytatás:**
  - [ ] Megszakadt kutatás folytatása (`resume interrupted research`).
  - [ ] Ügy duplikálása, archiválása és visszaállítása.

### 🎯 Phase 4 Acceptance Criteria
1. Bármelyik külső API kiesése vagy lassúsága esetén a rendszer nem omlik össze, hanem részleges/becsült jelöléssel visszaadja az elérhető adatokat.
2. Mind a 9 kutatási stratégia végrehajtható és idempotens módon mentődik az adatbázisba.

---

## 📌 Phase 5: Multi-Option Generation & Archetypes
> **Cél:** 3 valós trade-offokkal rendelkező, teljes értékű utazási opció előállítása.

- [ ] **`MultiOptionEngine` Implementálása (`app/services/multi_option_engine.py`):**
  - [ ] Teljes utazási kombinációk előállítása a kutatási poolból.
  - [ ] Érvénytelen (hard constraintet sértő) kombinációk kizárása.
  - [ ] **3 Alapértelmezett Archetípus Kijelölése:**
    - [ ] **Option A — BEST OVERALL:** Legmagasabb kiegyensúlyozott pontszám.
    - [ ] **Option B — BEST VALUE:** Alacsonyabb összköltség, kiemelkedő ár-érték arány.
    - [ ] **Option C — BEST EXPERIENCE:** Legerősebb élmény- és programilleszkedés.
- [ ] **Diverzitási Szabályok (Diversity Constraints):**
  - [ ] A 3 opciónak érdemben különböznie kell (különböző város VAGY szignifikáns árkülönbség VAGY eltérő járattípus/szálláskategória).
- [ ] **Option Kártyák Renderelése (`advisor_options.js`):**
  - [ ] Teljes ár és egy főre jutó költség.
  - [ ] Repülő és szállás összefoglaló, időtartam, megbízhatósági státusz (*Verified / Estimated / Needs review*).
  - [ ] Strukturált illeszkedési indoklás (*Why it fits*) és kompromisszumok (*Trade-offs*).

### 🎯 Phase 5 Acceptance Criteria
1. A generált 3 opció ugyanabból a hiteles adatpoolból származik, minden hard constraintet tiszteletben tart.
2. A 3 opció között mérhető és világosan kommunikált kompromisszumok (trade-offok) vannak.

---

## 📌 Phase 6: Relative Comparison, "Why This Option?" & Advisor Overrides
> **Cél:** Egymás melletti összehasonlítás, relatív különbségek és az advisor manuális döntési szabadsága (Whitebox).

- [ ] **Side-by-Side Összehasonlító Mátrix (`/advisor/cases/:id/compare`, `advisor_option_compare.js`):**
  - [ ] Desktop egymás melletti táblázat: Ár, Járattípus, Menetidő, Szállás csillag/értékelés, Strand, Gasztro, Kultúra.
  - [ ] **Relatív Összehasonlító Logika:** Nem csak abszolút számok, hanem relatív különbségek (pl. *"Kréta 46 000 Ft-tal olcsóbb, de Mallorca repülőútja 4 órával kényelmesebb"*).
- [ ] **Adatvezérelt "Why This Option?" Generátor:**
  - [ ] Scoring delta és constraint kielégítés alapján előállított indoklás (LLM hallucinációk nélkül).
- [ ] **"Find Better" Célzott Finomhangolási Modál (`find_better_modal.js`):**
  - [ ] Célzott keresés: Alacsonyabb ár, kényelmesebb járat, jobb hotel, több program.
- [ ] **Advisor Override & Whitebox Ergonomics:**
  - [ ] Ajánlások kézi szerkesztése.
  - [ ] Jelöltek kitűzése (Pin), törlése, vagy manuális hozzáadása.
  - [ ] Sorrend kézi felülírása indoklás rögzítésével (`override_reason`).

### 🎯 Phase 6 Acceptance Criteria
1. Az összehasonlító felület világosan megmutatja a 3 opció egymáshoz viszonyított előnyeit és hátrányait.
2. Az advisor manuálisan módosíthatja vagy kicserélheti az opciók bármely elemét, a rendszer nem viselkedik zárt black-boxként.

---

## 📌 Phase 7: Constraint Relaxation, Verification & Risk Engine
> **Cél:** Zsákutcák megszüntetése (No dead-ends) és kockázati figyelmeztetések.

- [ ] **`ConstraintRelaxationService` Implementálása (`app/services/constraint_relaxation_service.py`):**
  - [ ] 0 találat esetén pontos ok-okozati diagnózis (mely feltételek ütköznek).
  - [ ] 1-kattintásos enyhítési javaslatok számszerűsített új találati számmal (pl. *"+1 átszállás engedélyezése $\rightarrow$ 12 új opció"*, *"+40 000 Ft keret $\rightarrow$ 7 új opció"*).
  - [ ] A megkötéseket a rendszer csak tanácsadói jóváhagyással módosítja.
- [ ] **`VerificationService` & Provenance Ellenőrzés (`app/services/verification_service.py`):**
  - [ ] Ár, menetrend, szoba elérhetőség hitelesítési státuszai (`VERIFIED`, `ESTIMATED`, `NEEDS_REVIEW`).
- [ ] **`TripRiskService` & Figyelmeztető Motor (`app/services/trip_risk_service.py`):**
  - [ ] Kockázatok azonosítása: <60 perces átszállás, éjszakai érkezés, rejtett üdülőhelyi díj (resort fee), hiányzó reptéri transzfer, nyitvatartási ütközés.
  - [ ] Prioritási szintek: `Critical`, `Warning`, `Info`.

### 🎯 Phase 7 Acceptance Criteria
1. Nincs olyan szűrési kombináció, ami zsákutcába (üres hibaüzenetbe) fut: a rendszer mindig konkrét feloldási javaslatokat kínál.
2. Minden releváns utazási kockázat (pl. szűk átszállási idő) figyelmeztető kártyaként jelenik meg.

---

## 📌 Phase 8: Shortlist & Multi-Option Proposal
> **Cél:** Multi-Option ügyfélajánlat generálás, szerkesztés, verziókezelés és nyomtatás/PDF export.

- [ ] **Shortlist Kezelés (`/advisor/cases/:id/shortlist`, `advisor_shortlist.js`):**
  - [ ] Kiválasztott 1–3 opció véglegesítése az ajánlathoz.
  - [ ] Belső tanácsadói jegyzetek hozzáadása (`advisor_notes` — ügyfél előtt rejtve).
- [ ] **Multi-Option Ügyfélajánlat Generátor (`/advisor/cases/:id/proposal`, `advisor_proposal.js`):**
  - [ ] 1–3 opciót tartalmazó egységes ügyféldokumentum renderelése.
  - [ ] **Beépített Ajánlatszerkesztő:**
    - [ ] Cím, személyes bevezető szöveg szerkesztése.
    - [ ] Opciók sorrendje és ki/be kapcsolása (járat, hotel, programok, árak, foglalási linkek).
    - [ ] Tanácsadói ajánlás és konklúzió hozzáadása.
  - [ ] **Verziókezelés:** Proposal v1, v2, v3 tárolása, előzmények megőrzése.
  - [ ] **Nyomtatási & PDF Export:** A4 méretre optimalizált stíluslapok (`@media print`), ügynökségi branding és logó.

### 🎯 Phase 8 Acceptance Criteria
1. Az ajánlat 1, 2 vagy 3 opciót is hibátlanul prezentál összehasonlító vagy szekvenciális nézetben.
2. A generált PDF/nyomtatási kép tördelése professzionális, minden ár és komponens forrás-hitelesített.

---

## 📌 Phase 9: Client Feedback, Timeline & Re-Optimization
> **Cél:** Ügyféli visszajelzések kezelése és zökkenőmentes újragenerálás.

- [ ] **Ügyfél Visszajelzés Rögzítése:**
  - [ ] Gyors visszajelzési pontok (pl. *"Mallorca tetszik, de olcsóbb hotel kell"*).
- [ ] **Re-Optimization Workflow:**
  - [ ] Módosított megkötésekkel történő újratervezés az ügyfél-eset újrakezdése nélkül.
  - [ ] Automatikus Proposal v2 létrehozás a v1 megőrzésével.
- [ ] **Eset Idővonal & Audit Napló (`advisor_timeline.js`):**
  - [ ] Időbélyeges eseménynapló (Brief rögzítve $\rightarrow$ Kutatás $\rightarrow$ 3 opció $\rightarrow$ Ajánlat v1 $\rightarrow$ Visszajelzés $\rightarrow$ Ajánlat v2).

### 🎯 Phase 9 Acceptance Criteria
1. Az ügyfél visszajelzése után 1 kattintással újragenerálható a csomag anélkül, hogy elölről kellene kezdeni a folyamatot.
2. Az idővonal pontosan naplózza a tervezési folyamat minden lépését és a megtakarított kutatási időt.

---

## 📌 Phase 10: Hardening, Playwright E2E Tesztek & Minőségkapuk
> **Cél:** 20 automatizált E2E teszt, reszponzivitási audit és 100%-os tudásgráf-integritás.

- [ ] **20 Átfogó Playwright E2E Teszt (`tests/e2e/advisor/test_advisor_workspace_e2e.py`):**
  - [ ] `test_advisor_dashboard_load`
  - [ ] `test_client_create_and_profile`
  - [ ] `test_trip_case_create`
  - [ ] `test_brief_completion_with_hard_soft_constraints`
  - [ ] `test_budget_modes_total_and_component`
  - [ ] `test_search_scope_component_only`
  - [ ] `test_research_execution_and_progress`
  - [ ] `test_multi_option_generation_3_archetypes`
  - [ ] `test_option_diversity_verification`
  - [ ] `test_side_by_side_comparison_matrix`
  - [ ] `test_relative_comparison_why_this_option`
  - [ ] `test_find_better_modal_workflow`
  - [ ] `test_constraint_relaxation_on_zero_results`
  - [ ] `test_provider_failure_resilience_and_stale_cache`
  - [ ] `test_risk_engine_warnings_display`
  - [ ] `test_shortlist_management`
  - [ ] `test_multi_option_proposal_generation_and_export`
  - [ ] `test_client_feedback_and_proposal_v2_reoptimization`
  - [ ] `test_unauthorized_case_access_isolation`
  - [ ] `test_b2c_master_planner_zero_regression`
- [ ] **UI Reszponzivitás, DOM Pixel Audit & Billentyűzet UX:**
  - [ ] 0 horizontális túlcsordulás desktopon (1280px+) és mobilon (<768px).
  - [ ] Gyorsbillentyűk ellenőrzése.
- [ ] **Knowledge Graph Validáció:**
  - [ ] `python scripts/knowledge/validate.py` sikeres futása.

### 🎯 Phase 10 Acceptance Criteria
1. Mind a 20 Advisor E2E teszt és az összes meglévő B2C teszt hibátlanul átmegy (100% Pass Rate).
2. A teljes tudástár és a forráskód kapcsolatai 100%-ban érvényesek.
