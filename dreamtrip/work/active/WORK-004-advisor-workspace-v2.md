---
id: WORK-004-advisor-workspace-v2
type: work_item
name: Optivoya Advisor Workspace v2 Implementation Roadmap & Checklist
status: in_progress

description: Az Optivoya B2B Travel Advisor Workspace v2 teljes, 11 fázisú implementációs feladatlistája, hard/soft feltételrendszere, ResearchState állapota, Intent megerősítője, Candidate Pool modellje, Geo/Map és Experience intelligenciája, szerkesztési/zárolási rétege, 5 fázisú UX folyamata és átvételi kritériumai (Acceptance Criteria).

created_at: 2026-09-26
updated_at: 2026-09-26

related:
  - "[[advisor-workspace-blueprint-v2]]"
  - "[[advisor-workspace-blueprint]]"
  - "[[WORK-003-advisor-workspace-v1]]"
  - "[[trip-case]]"
  - "[[master-planner-blueprint]]"
  - "[[shared-intelligence-layer]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[guided-progressive-decision-flow]]"
  - "[[numbeo-cost-model]]"
  - "[[honest-scraping-policy]]"
  - "[[effective-vacation-time]]"
  - "[[unified-trip-score]]"
  - "[[experience-intelligence-engine]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[PRODUCT_PRINCIPLES]]"
---

# WORK-004: Optivoya Advisor Workspace v2 Roadmap & Checklist

Ez a dokumentum az **Optivoya Advisor Workspace v2** teljes, 11 fázisból álló implementációs feladatlistáját és átvételi kritériumait tartalmazza a **[[advisor-workspace-blueprint-v2]]** kanonikus logikai modell alapján.

> **Alapelv:** Az Advisor ne kézi workflow-választó legyen (pl. „Válassz 9 stratégia közül”), hanem egy intelligens **Input $\to$ Intelligence $\to$ Döntés $\to$ Output** rendszer, amely rekonstruálja a célt, visszaigazoltatja, csak a releváns kritériumokat aktiválja, candidate poolt épít, szintetizál, magyaráz és támogatja a tanácsadói felülbírálást.  
> **Kompatibilitás:** Az Advisor Workspace v1 nem kerül törlésre; adminisztrátorként továbbra is elérhető marad, de a v2 képezi az új, alapértelmezett munkaállomást.

---

## 📌 Phase 0: Central ResearchState & Dual-Version Architecture
> **Cél:** A központi `ResearchState` állapotmodell bevezetése és a v1/v2 kettős futtatókörnyezet kialakítása.

- [x] **Központi `ResearchState` Adatmodell (`app/models/advisor_models.py`):**
  - [x] `what_we_know`: Validált és rendelkezésre álló tények (utasok, meglévő jegy/hotel, célpont).
  - [x] `what_we_dont_know`: Hiányzó, de a kutatáshoz szükséges mezők.
  - [x] `what_is_fixed`: Szigorú, zárolt elemek (`is_locked: True`).
  - [x] `what_is_flexible`: Rugalmas paraméterek (dátumablak, büdzsé tolerancia).
  - [x] `what_matters`: Aktív, kiválasztott döntési dimenziók és AHP súlyok.
  - [x] `what_we_are_searching`: Aktív kutatási folyamatok és API taskok.
  - [x] `what_we_found`: Candidate pool (nyers és szűrt alternatívák).
  - [x] `what_is_verified`: Provenance és frissességi időbélyegek.
  - [x] `what_advisor_changed`: Kézi tanácsadói módosítások és felülbírálások naplója.
  - [x] `what_still_needs_decision`: Megválaszolatlan kérdések és döntési pontok.
- [x] **„Mi van / Mi nincs?” Mátrix Elemző:**
  - [x] Determinisztikus hiányelemző, amely a Case Context alapján összeállítja a teendők listáját.
- [x] **Dual-Version Routing & Admin Toggle:**
  - [x] Alapértelmezett `/advisor` útvonal $\to$ Advisor Workspace v2.
  - [x] Admin hozzáférési útvonal `/advisor/v1` $\to$ Eredeti v1 felület megőrzése és elérhetősége.

### 🎯 Phase 0 Acceptance Criteria
1. A `ResearchState` entitás minden Case-hez perzisztensen és egyértelműen leírja a tervezés aktuális állapotát.
2. A v1 és v2 munkaállomások párhuzamosan elérhetők anélkül, hogy egymás adatait vagy függőségeit sértenék.

#### 💡 Phase 0 Tapasztalatok & Implementációs Tanulságok (Key Learnings & Fixes)
- **Modell-sorrend & Pydantic v2 Invariánsok:** A `ResearchState`, `ExistingComponent` és `ComponentIntentAction` modelleket a `TripCase` definíciója elé kellett pozicionálni az `app/models/advisor_models.py`-ban a tiszta típusreferencia és forward-ref elkerülése végett.
- **Költségkeret-modell Kanonikus Struktúra:** A `BudgetConstraint` a hierarchikus `total.amount`, `total.hardness` (`BudgetHardness`), és `total.basis` (`BudgetBasis`) mezőkkel dolgozik. A `ResearchStateService` ennek megfelelően egységesen kezeli mind az új objektummodellt, mind a legacy `total_budget_huf` mezőt.
- **Több-bérlős (Multi-Tenant) Repository Szignatúrák:** A `ClientRepository.save_client` és `TripCaseRepository.save_case` metódusok fel lettek készítve az opcionális `agency_id` paraméter fogadására a teszt- és bérlő-specifikus perzisztencia egységesítéséhez.
- **Determinisztikus Fázis-átmenet:** A szándék megerősítése (`/intent/confirm`) azonnal és megbízhatóan átlépteti az állapotot `UNDERSTAND` $	o$ `DEFINE` fázisba, és rögzíti a jóváhagyást a `what_still_needs_decision.intent_confirmed` mezőben.
- **Kettős HTML Shell Routing:** A `main.py` routingja transzparensen szétválasztja az új alapértelmezett `/advisor` (v2) és a legacy `/advisor/v1` felületeket, biztosítva a 100%-os visszamenőleges kompatibilitást.
- **Tesztfedettség:** A `tests/test_research_state_and_v2_phase0.py` 6/6 teszttel validálja az állapotmodellt, mátrixot, intent-felismerést és REST API-t; a teljes advisor tesztcsomag 32/32 sikeres teszttel fut.

---

## 📌 Phase 1: Research Intent Engine & Intent Confirmation Layer
> **Cél:** A kérés automatikus cél-rekonstrukciója és kötelező megerősítése a felesleges API futtatások elkerülésére.

- [x] **Research Intent Resolver (`app/services/research_state_service.py`):**
  - [x] Input adatokból a cél automatikus meghatározása mind a 7 archetípusra: `KNOWN_DESTINATION_FULL`, `DESTINATION_DISCOVERY`, `FLIGHT_FIRST`, `STAY_FIRST`, `RE_OPTIMIZE`, `FIND_BETTER_COMPONENT`, `MIXED_SCOPE_COMPETITION`.
  - [x] Meglévő komponensek szándékának kezelése: `KEEP`, `REPLACE`, `IMPROVE`, `UNKNOWN` és valós idejű szándék-újraszámítás (`update_component_intent`).
- [x] **Intent Confirmation Kártya & Dialógus (UI & API):**
  - [x] Emberi nyelven megfogalmazott összefoglaló: „Jól értem a feladatot? [X] utazást keresünk [N] főre, maximum [B] büdzsékeretből...”
  - [x] Visszaigazoló gombok: `[Igen, indulhat a kutatás]` és `[Feltételek módosítása]`.
  - [x] REST API végpontok: `GET /api/advisor/cases/{case_id}/intent/plan`, `POST /api/advisor/cases/{case_id}/intent/confirm`, `POST /api/advisor/cases/{case_id}/components/intent`.
  - [x] Frontend komponens (`static/js/advisor/advisor_intent_v2.js`) és banner integráció a Brief nézetben.
- [x] **Dinamikus Research Plan Generálás:**
  - [x] Az Intentből automatikusan felépülő műveleti sorrend (`ResearchPlan`, `ResearchPlanStep`), szolgáltatók hozzárendelése (Kiwi, Cozycozy, Open-Meteo, Numbeo, OSM, Decision Engine) és másodperc-alapú futásidő-becslés.

### 🎯 Phase 1 Acceptance Criteria
1. Nincs vak API-futtatás: a rendszer a brief és a meglévő elemek alapján összeállítja a kutatási szándékot, és jóváhagyatja a tanácsadóval.

#### 💡 Phase 1 Tapasztalatok & Implementációs Tanulságok (Key Learnings & Fixes)
- **7-Archetípusos Cél-rekonstrukció:** A rendszer a felhasználói inputokból és meglévő elemekből 100%-os determinizmussal ismeri fel a célállomás-felfedezést (`DESTINATION_DISCOVERY`), járatközpontú utat (`FLIGHT_FIRST`), szállásfókuszt (`STAY_FIRST`), meglévő elemek újraoptimalizálását (`RE_OPTIMIZATION`) és a komponens-cserét (`FIND_BETTER_COMPONENT`).
- **Valós idejű Szándék-átbillenés (Intent Flipping):** Ha a tanácsadó egy meglévő szállás elemhez `IMPROVE` vagy `REPLACE` státuszt rendel, a szándék azonnal átbillen `FIND_BETTER_COMPONENT` módba, és a pipeline lépései automatikusan a Pareto-domináns alternatívák keresésére (`market_sweep`, `pareto_filtering`) módosulnak.
- **Konzisztens Becsült Futásidő & Pipeline Átláthatóság:** A `ResearchPlan` minden lépéshez pontos szolgáltatót (Kiwi, Cozycozy, Places, PROMETHEE Engine) és várható időtartamot rendel, így a tanácsadó már az indítás előtt látja, hogy pontosan milyen adatokból épül fel a javaslat.
- **Tesztfedettség:** A `tests/test_research_intent_engine_phase1.py` 4/4 teszttel validálja az archetípusokat, a dinamikus tervet, a komponens-mutációkat és a REST API-kat; a kombinált tesztcsomag (Phase 0 + Phase 1) 10/10 zöld.

---

## 📌 Phase 2: Dynamic Requirement Discovery & Preference Model
> **Cél:** Kétfázisú igényfelmérés és dinamikus AHP/PROMETHEE kritérium-aktiválás kognitív túlterhelés nélkül.

- [ ] **Kétfázisú Preferencia Felderítés („Mi fontos ezen az utazáson?”):**
  - [ ] 1. Fázis: Releváns dimenziók kiválasztása (Ár, Repülés kényelme, Lokáció, Tengerpart, Gasztro, Nyugalom, Család stb.).
  - [ ] 2. Fázis: Csak a kiválasztott dimenziók közötti páros AHP súlyozás (max. 5 feszítő pár).
- [ ] **4-Szintű Kritérium Kategorizálás:**
  - [ ] `HARD`: Pass/Fail szűrők (pl. Büdzsé $\le 800\text{k}$, csak közvetlen járat, min. 4★).
  - [ ] `SOFT`: Optimalizálandó szempontok (pl. Lokáció 25%, Ár 30%, Hotel 20%, Élmény 25%).
  - [ ] `AVOID`: Kerülendő feltételek (pl. indulás $< 06:00$, 2+ átszállás, túlzsúfolt negyed).
  - [ ] `NICE_TO_HAVE`: Bónusz tényezők (reggeli az árban, ingyenes lemondás, medence).
- [ ] **Dinamikus Kritérium-generálás az AHP/PROMETHEE motorokhoz:**
  - [ ] Nem releváns szempontok (pl. Éjszakai élet egy csendes családi útnál) teljes kihagyása a döntési mátrixból.

### 🎯 Phase 2 Acceptance Criteria
1. A döntési motor kizárólag azokat a dimenziókat súlyozza, amelyeket a tanácsadó/ügyfél fontosnak jelölt meg.

---

## 📌 Phase 3: Multi-Intelligence Data Gathering & Candidate Pool
> **Cél:** Széles jelöltbázis (Candidate Pool) felépítése és többforrásos intelligencia-dúsítás.

- [ ] **Candidate Pool Építő Folyamat (`CandidatePool`):**
  - [ ] Desztinációk: 40+ város $\to$ 15 életképes $\to$ 7 kiemelt jelölt.
  - [ ] Járatok: 150 járatkombináció $\to$ 30 szabályos $\to$ 6 komoly alternatíva.
  - [ ] Szállások: 300 hotel $\to$ 40 releváns $\to$ 8 prémium jelölt.
- [ ] **Geo / Map Intelligence Réteg:**
  - [ ] Koordináta-alapú távolságok és utazási idők (Reptér $\to$ Hotel, Hotel $\to$ Látványosságok, Tranzit pontok).
  - [ ] Földrajzi klaszterezés és napi útvonal-hatékonyság (`LocationScore` 0–10).
- [ ] **Experience Intelligence & Nyitvatartás Verifikáció:**
  - [ ] 12-dimenziós élményilleszkedés koszinusz-szorzata a profilhoz.
  - [ ] Nyitvatartási idők és zárva tartó napok élő validálása (pl. „Keddre nem ajánlott: zárva”).

### 🎯 Phase 3 Acceptance Criteria
1. A rendszer nem közvetlenül 3 ajánlatot gyárt a nyers adatokból, hanem strukturált Candidate Poolt épít és földrajzilag/logisztikailag dúsítja azt.

---

## 📌 Phase 4: Constraint Engine & Optimization Orchestration
> **Cél:** Szigorú Pass/Fail szűrés és kompromisszummentes többkritériumos optimalizálás.

- [ ] **Hard Constraint Engine:**
  - [ ] Szigorú kizárás (Büdzsékeret, dátumhatárok, utasszám, tiltott légitársaságok, csillagszám).
  - [ ] Hard constraint pontszámmal NEM kompenzálható!
- [ ] **Multikritériumos Rendező Motor:**
  - [ ] AHP súlyvektor alkalmazása a fennmaradó jelöltekre.
  - [ ] PROMETHEE II outranking számítás a járatokra és szállásokra.
  - [ ] Kompozit TripScore és Pareto-határ kalkuláció.

### 🎯 Phase 4 Acceptance Criteria
1. Egyetlen opció sem kerülhet be a végső készletbe, amely megsérti a kötelező Hard megkötéseket.

---

## 📌 Phase 5: Option Synthesis & Transparent Explainability
> **Cél:** A 3 döntési archetípus előállítása és transzparens pontszám-dekompozíció.

- [ ] **3 Döntési Archetípus Szintézise:**
  - [ ] `Option A (Best Overall)`: Legmagasabb kiegyensúlyozott TripScore.
  - [ ] `Option B (Best Value)`: Optimális költségvetés és szilárd minőségi bázis.
  - [ ] `Option C (Best Experience)`: Prémium 4-5★ szállás, gazdag program és maximális élmény fit.
- [ ] **Transzparens Score Decomposition:**
  - [ ] „Mi húzza fel?” és „Mi húzza le?” determinisztikus indoklások kártyánként.
  - [ ] Részletes dimenzióbontás: Ár (40%), Lokáció (25%), Hotel (20%), Élmények (15%).
- [ ] **Relatív Összehasonlító Mátrix (`RelativeComparisonService`):**
  - [ ] Option A-hoz viszonyított ár- és kényelmi különbségek szöveges és táblázatos levezetése (pl. „B 130 000 Ft-tal olcsóbb, de gyengébb lokációjú”).

### 🎯 Phase 5 Acceptance Criteria
1. A tanácsadó azonnal látja és megérti, hogy miért az adott 3 opció nyert, és mi a köztük lévő pontos trade-off.

---

## 📌 Phase 6: Geo-Optimized Itinerary & Multi-Tier Backup Engine
> **Cél:** Valós idejű napi útiterv és több szintű alternatív programok biztosítása.

- [ ] **Napi Útiterv Generátor (Day 1..N):**
  - [ ] Érkezési és indulási logisztika, transzferek, étkezési ablakok (Lunch, Dinner).
  - [ ] Földrajzilag klaszterezett látványosságok a felesleges oda-vissza utazások kizárásával.
- [ ] **Multi-Tier Backup Engine (Primary + 3 Backup):**
  - [ ] Minden kulcsprogramhoz 3 rangsorolt alternatíva az ügyfélprofil és kategória alapján.
  - [ ] Eső/rossz idő esetén automatikusan aktiválható beltéri alternatíva javaslat.

### 🎯 Phase 6 Acceptance Criteria
1. A napi útiterv minden programjához tartozik validált nyitvatartási idő és személyre szabott backup alternatíva.

---

## 📌 Phase 7: Interactive Advisor Editing, Pinning & Component Locking
> **Cél:** Teljes kontroll a tanácsadó kezében: elemek rögzítése, cseréje és intelligens újraszámítás.

- [ ] **Interaktív Műveletek (Advisor Editing Layer):**
  - [ ] `Pin` (Rögzítés), `Remove` (Eltávolítás), `Replace` (Csere), `Add manually` (Kézi hozzáadás).
  - [ ] Komponens-szintű csere: Járatcsere, Szálláscsere, Programcsere, Napcsere.
- [ ] **Komponens Zárolási Rendszer (Locking):**
  - [ ] 🔒 `flight_locked`, `hotel_locked`, `destination_locked`, `activity_locked`, `date_locked`, `budget_locked`.
- [ ] **Impact Analysis & Re-Optimization:**
  - [ ] Változtatás hatásvizsgálata: „A hotel cseréje +42 000 Ft, de a napi átlagos utazási idő 31 perccel csökken.”
  - [ ] Újraszámítás kizárólag az érintett rétegeken a zárolt elemek szigorú megőrzésével.

### 🎯 Phase 7 Acceptance Criteria
1. A tanácsadó bármely elemet zárolhat vagy cserélhet; a rendszer azonnal levezeti a döntés hatásait és újrahangolja a tervet.

---

## 📌 Phase 8: Diagnostic Constraint Relaxation & Provenance Tracking
> **Cél:** Dead-end mentes működés és megbízható adat-eredet nyilvántartás.

- [ ] **Strukturált Feltétel-enyhítés (0 találat esetén):**
  - [ ] Diagnózis kimutatása (pl. „800k keret mellett nincs közvetlen járat 4★ hotellel”).
  - [ ] 1-kattintásos opciók: +10% büdzsé, $\pm 1$ nap rugalmasság, 1 átszállás engedélyezése, 4★ $\to$ 3★.
  - [ ] Nincs automatikus lazítás: kizárólag a tanácsadó dönthet róla!
- [ ] **Provider Provenance & Frissesség:**
  - [ ] Forrás, ellenőrzési időpont, TTL és státusz (`VERIFIED`, `ESTIMATED`, `STALE`, `UNAVAILABLE`) minden ajánlati elemen.

### 🎯 Phase 8 Acceptance Criteria
1. Sikertelen keresés esetén a rendszer azonnali feloldási alternatívákat kínál anélkül, hogy a megkötéseket csendben feladná.

---

## 📌 Phase 9: Shortlist, Proposal Snapshotting & 2-Way Client Feedback Loop
> **Cél:** Professzionális ajánlatkészítés, megosztás és kétirányú ügyféli iteráció.

- [ ] **Shortlist Kezelés:**
  - [ ] Candidate Pool $\to$ 3 Ajánlott opció $\to$ Tanácsadói shortlist $\to$ Ügyfélnek küldött végleges ajánlat.
- [ ] **Immutábilis Proposal Verziók & Kriptográfiai Megosztás:**
  - [ ] Proposal v1, v2, v3 snapshotok előzményekkel.
  - [ ] 256 bites tokenes publikus megosztás belső jegyzetek és árrések kiszűrésével.
  - [ ] A4 nyomtatási és PDF nézet (`proposal_print.html`).
- [ ] **Kétirányú Ügyféli Visszacsatolási Hurok:**
  - [ ] Ügyféli módosítási kérés rögzítése $\to$ Kritérium frissítés $\to$ Érintett komponens újraszámítás $\to$ Proposal v2.

### 🎯 Phase 9 Acceptance Criteria
1. Az ügyfél visszajelzései alapján a csomag percek alatt újratervezhető és új verzióként megosztható.

---

## 📌 Phase 10: 5-Phase UI/UX Implementation & Quality Hardening
> **Cél:** A modern 5-fázisú asztali felület megépítése és teljes körű tesztelése.

- [ ] **5-Fázisú Felhasználói Folyamat UI:**
  - [ ] ① **UNDERSTAND:** Brief, ügyféladatok, meglévő elemek és szándék-megerősítés.
  - [ ] ② **DEFINE:** Releváns dimenziók, AHP súlyozás és korlátok meghatározása.
  - [ ] ③ **RESEARCH:** Candidate pool építés, intelligencia dúsítás és élő státusz.
  - [ ] ④ **DECIDE:** 3 archetípus kártya, pontszám-bontás, térkép, útiterv és backupok.
  - [ ] ⑤ **DELIVER:** Szerkesztés, zárolás, shortlist, ajánlatkészítés és ügyfél hurok.
- [ ] **Admin Mód / v1 Elérhetőség:**
  - [ ] Admin profilból elérhető toggle / link az eredeti v1 felülethez.
- [ ] **Automatizált Tesztelés & Validáció:**
  - [ ] Unit tesztek a `ResearchState`, `IntentEngine`, `GeoEngine` és `BackupEngine` modulokra.
  - [ ] Playwright E2E tesztek az 5 UX fázis teljes bejárására (`tests/e2e/test_advisor_workspace_v2_e2e.py`).
  - [ ] Tudásgráf ellenőrzése: `python scripts/knowledge/validate.py`.

### 🎯 Phase 10 Acceptance Criteria
1. A teljes 5-fázisú UX folyamat intuitív, gyors, és a háttérben futtatja a komplex döntési motorokat.
2. 100%-os zöld tesztlefedettség és hibátlan tudásgráf kapcsolatok.