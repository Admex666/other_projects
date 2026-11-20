---
id: WORK-005-event-intelligence-mvp
type: work_item
name: Event Intelligence Engine MVP Implementációs Munkaterv
status: in_progress

description: Az Optivoya időfüggő esemény-intelligencia motorjának (Event Intelligence Engine MVP) részletes, fázisokra bontott fejlesztési terve, adatmodellje, külső connectorai, deduplikációs és hitelesítési logikája, AHP élménypillér integrációja és elfogadási kritériumai (Acceptance Criteria).

created_at: 2026-11-20
updated_at: 2026-11-20

related:
  - "[[ADR-011-event-intelligence-engine]]"
  - "[[ADR-009-experience-activity-intelligence-engine]]"
  - "[[ADR-004-honest-scraping-mode]]"
  - "[[event-intelligence-engine]]"
  - "[[event]]"
  - "[[experience-entity]]"
  - "[[destination-matching]]"
  - "[[ahp-weighting]]"
  - "[[numbeo-cost-model]]"
  - "[[master-planner-wizard]]"
  - "[[advisor-workspace-blueprint-v2]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[QUALITY_GATES]]"
---

# 🔨 WORK-005: Event Intelligence Engine MVP Implementációs Munkaterv

Ez a dokumentum az **Event Intelligence Engine MVP** részletes megvalósítási tervét, feladatbontását és elfogadási kritériumait rögzíti az **[[ADR-011-event-intelligence-engine]]** döntési rekord és a `newyear_handover.md` stratégiai útmutató alapján.

> **Alapelv:** Az utazástervező döntési motor ne csupán azt vizsgálja, hogy egy adott városban milyen állandó látványosságok léteznek, hanem azt is, hogy **a kiválasztott utazási időpontban milyen valós, hitelesített koncertek, fesztiválok, bulik, gasztronómiai és kulturális események látogathatók**, és ezek hogyan valósíthatók meg optimális ár-érték arány és éjszakai logisztika mellett.  
> **Kompatibilitás:** Az Evergreen Experience Engine (`[[ADR-009-experience-activity-intelligence-engine]]`) sértetlen marad; az Event Engine egy különálló, időfüggő rétegként épül rá és egészíti ki azt.

---

## 📌 Phase 1: Esemény Adatmodell & Adatbázis Séma (Data Model & Schema)
> **Cél:** A kanonikus `[[event]]` adatmodell, a Pydantic sémák és a Supabase PostgreSQL táblák kialakítása időzóna-támogatással.

- [ ] **Pydantic Adatmodellek definiálása (`app/models/event_models.py`):**
  - [ ] `EventBase`, `EventCreate`, `EventUpdate`, `EventResponse` és `EventFilterParams` sémák.
  - [ ] `starts_at` és `ends_at` kötelező `datetime` mezők explicit időzóna (tz-aware) kezeléssel.
  - [ ] `price_min`, `price_max`, `currency`, `is_free` költségmezők.
  - [ ] `confidence_score` (0.00 – 1.00 adatmegbízhatóság) és `status` (`verified`, `partially_verified`, `unverified`, `cancelled`, `expired`, `historical`) mezők.
  - [ ] `source_url`, `source_name`, `source_event_id`, `booking_url` forráshitelesítési mezők.
- [ ] **Supabase PostgreSQL Migráció (`supabase_events_schema.sql`):**
  - [ ] `public.events` tábla létrehozása indexekkel (`destination_id`, `starts_at`, `status`, `category`).
  - [ ] `public.event_sources` tábla létrehozása a nyers, forrásszintű rekordok (Zero-Loss Raw JSON) tárolására.
  - [ ] Térbeli (PostGIS / lat-lon) és időbeli keresőindexek a gyors lekérdezésekhez.

### 🎯 Phase 1 Acceptance Criteria
1. Az események időzóna-helyesen, veszteségmentesen menthetők és kérdezhetők le.
2. A Pydantic validáció elutasítja a hiányos vagy érvénytelen időponttal ellátott rekordokat.

---

## 📌 Phase 2: Esemény Connectorok & Discovery Réteg (Connectors & Discovery)
> **Cél:** Hiteles, külső eseményforrások integrálása a `[[ADR-004-honest-scraping-mode]]` elvei szerint.

- [ ] **Absztrakt Esemény Connector Alaposztály (`app/services/events/connectors/base.py`):**
  - [ ] Egységes aszinkron interfész: `fetch_events_for_destination(destination_id, start_date, end_date)`.
  - [ ] Rate-limiting, timeout és Honest Failure hibakezelés (nincs kamu/mock eseménygenerálás).
- [ ] **Zenei & Élőzenei Connectorok:**
  - [ ] Bandsintown API Connector (`bandsintown_connector.py`) koncertekre és előadókra.
  - [ ] Songkick API / Scraper Connector (`songkick_connector.py`) turnékra és klubkoncertekre.
- [ ] **Helyi és Közösségi Rendezvény Connectorok:**
  - [ ] Eventbrite Connector (`eventbrite_connector.py`) partikra, workshopokra és helyi fesztiválokra.
  - [ ] Helyi Városi / Önkormányzati & Kulturális Naptár adapter (szilveszteri és szezonális városi rendezvények).
- [ ] **Adatforrás-Regiszter (`knowledge/systems/event-source-registry.md`):**
  - [ ] Források API kulcsainak, díjmentes kvótáinak, ToS és scraping szabályainak hivatalos dokumentálása.

### 🎯 Phase 2 Acceptance Criteria
1. A connectorok valós adatokat adnak vissza; hiba vagy eseményhiány esetén transzparens üres listát adnak fiktív adatok generálása nélkül.
2. Az adatforrások licencfeltételei ellenőrzöttek és dokumentáltak.

---

## 📌 Phase 3: Ingestion, Deduplikáció & Dátumhitelesítés (Resolution & Provenance)
> **Cél:** A több forrásból beérkező események összevonása, az évszám-reciklálás megakadályozása és a megbízhatóság pontozása.

- [ ] **Dátum- és Évszám-Validátor (`event_verification.py`):**
  - [ ] Szigorú ellenőrzés: korábbi évek (pl. 2025) eseményei nem jelenhetnek meg aktuális (2026) eseményként.
  - [ ] Kétes vagy nem megerősített évszámú találatok kizárása vagy `historical` / `unverified` státuszba helyezése.
- [ ] **Esemény Deduplikáció & Entity Resolution (`event_deduplication.py`):**
  - [ ] Térbeli (helyszín koordináták $\le 300\text{ m}$) és időbeli ($\Delta t \le 2\text{ h}$) klaszterezés.
  - [ ] Cím- és fellépő-összehasonlítás (Jaccard és token hasonlóság $\ge 0.75$).
  - [ ] Duplikáció esetén a források összefűzése (`sources_present`) és a `confidence_score` növelése.
- [ ] **Konfidencia-Pontozás:**
  - [ ] `confidence_score` számítása forráshitelesség, jegyirodai megerősítés és forrásszám alapján.

### 🎯 Phase 3 Acceptance Criteria
1. Nincs duplikált koncert/party ugyanabban a desztinációban és idősávban.
2. Nincs elavult vagy hibás naptári évvel megjelenített esemény.

---

## 📌 Phase 4: AHP Élmény-Pillér & Destination Scoring Integráció
> **Cél:** Az események beépítése a 4-pilléres döntési modellbe és a célállomások rangsorolásába.

- [ ] **Destination Scoring Kiterjesztése (`app/services/destination_scoring_service.py`):**
  - [ ] AHP Level 2 élménypontszám szintézise: $S_{\text{exp}} = w_{\text{evergreen}} \cdot S_{\text{evergreen}} + w_{\text{event}} \cdot S_{\text{event}}$.
  - [ ] Szezonális kontextusfüggő dinamikus súlyozás (pl. Szilveszter esetén kiemelt $w_{\text{event}}$).
- [ ] **Téli / Szezonális Célváros Készlet Hangolása:**
  - [ ] Teszt célállomások lefedése: Budapest, Bécs, Prága, Krakkó, Róma, Barcelona, Lisszabon, Páfosz.
  - [ ] Meleg téli célállomások klíma- és eseményegyensúlyának validálása.
- [ ] **Teljes Költség (Total Trip Cost) Frissítése:**
  - [ ] Az események minimális belépőjegy-árainak hozzáadása a Numbeo alapú kalkulációhoz.

### 🎯 Phase 4 Acceptance Criteria
1. Egy kiemelkedő eseménykínálattal rendelkező város magasabb élménypontszámot kap a kiválasztott utazási időablakban.
2. Az események belépődíja megjelenik a desztinációs kártya összköltség-bontásában.

---

## 📌 Phase 5: Logisztikai Megvalósíthatóság & Útiterv (Logistics & Feasibility)
> **Cél:** Annak ellenőrzése, hogy a felhasználó ténylegesen el tud-e jutni az eseményre és vissza a szállására.

- [ ] **Éjszakai Hazajutás & Tranzit Ellenőrzés (`event_feasibility.py`):**
  - [ ] Késő esti / hajnali befejezés (`ends_at` éjfél után) esetén éjszakai járatok vagy becsült taxiköltség jelzése.
  - [ ] Távolságvizsgálat a városközponttól / szálláscsomópontoktól.
- [ ] **Napi Útitervbe Illesztés (`itinerary_optimization`):**
  - [ ] Az esemény idősávjának zárolása (Hard Block), hogy a nappali POI programok ne ütközzenek a koncerttel vagy partival.

### 🎯 Phase 5 Acceptance Criteria
1. Az éjfél után véget érő rendezvényeknél a rendszer megjelöli az éjszakai logisztikai igényt.
2. A generált útitervben nem szerepel átfedés az esemény és az egyéb programok között.

---

## 📌 Phase 6: Automatizált Tesztelés & Minőségbiztosítás (QA & Gates)
> **Cél:** A teljes pipeline automatizált tesztelése és a hibás adatok kizárásának igazolása.

- [ ] **Egységtesztek (`tests/test_event_intelligence.py`):**
  - [ ] Dátum- és évszám-szűrés tesztje (pl. 2025-ös esemény elutasítása).
  - [ ] Deduplikációs algoritmus pontossági tesztje (azonos koncertek összevonása).
  - [ ] `confidence_score` és életciklus-státusz tesztek.
- [ ] **Integrációs & Scoring Tesztek:**
  - [ ] Destination Scoring élménypillér szintézis tesztelése eseményekkel és események nélkül.
  - [ ] Honest Scraping teszt: scraper hiba esetén a rendszer nem omlik össze és nem állít elő fiktív rekordokat.

### 🎯 Phase 6 Acceptance Criteria
1. Minden teszt sikeresen lefut (`pytest tests/test_event_intelligence.py`).
2. A `qa-validator` igazolja a minőségi kapuk (`[[QUALITY_GATES]]`) teljesülését.
