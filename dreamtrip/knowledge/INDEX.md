# Optivoya Knowledge Graph Index (v2.0)

Ez a fájl az Optivoya (DreamTrip) projekt navigációs térképe. Minden lényeges stratégiai irány, jelenlegi fókusz, governance szabály, aktív munkaelem, domain-fogalom, entitás, folyamat, rendszer, mérőszám, döntés, tapasztalat és operáció kis, összekapcsolt node-ként van dokumentálva.

---

## 🧭 Strategic Context (Stratégiai Réteg)
* [[PURPOSE]] — Miért létezik a projekt? Alapvető küldetés és indoklás.
* [[NORTH_STAR]] — Északi Csillag sikermérőszám (Accepted Unified Proposals).
* [[MISSION]] — A projekt hivatalos küldetése.
* [[VISION]] — Hosszú távú jövőkép (End-to-End utazástervező platform).
* [[THESIS]] — Terméktézis és döntéstámogatási kurációs modell.
* [[TARGET_CUSTOMER]] — Célközönség meghatározás (B2B fókusz + B2C jövőkép).
* [[VALUE_PROPOSITION]] — Egyedi értékajánlat (UVP).
* [[BUSINESS_MODEL]] — Üzleti és monetizációs modell.
* [[PRINCIPLES]] — Alapvető stratégiai döntési elvek.
* [[optivoya-strategy]] — Kanonikus összefoglaló stratégiai dokumentum.

---

## 📍 Current Direction (Jelenlegi Fókusz & Állapot)
* [[CURRENT_STATE]] — Jelenlegi éles állapot (B2B Beta fázis).
* [[OBJECTIVES]] — Aktuális célkitűzések és mérföldkövek.
* [[PRIORITIES]] — Prioritási sorrend (P1 stabilitás, P2 UX, P3 Governance).
* [[CONSTRAINTS]] — Technikai és üzleti korlátok, non-goalok.

---

## 🏛️ Governance (Szabályrendszer & Minőségvédelem)
* [[GOVERNANCE_INDEX]] — A governance szabályok navigációs gyökere.
* [[PRODUCT_PRINCIPLES]] — Döntéstámogatási és termékelvek.
* [[DEFINITION_OF_DONE]] — A feladatok lezárásának kötelező feltételei.
* [[UX_PRINCIPLES]] — Felhasználói élmény és kognitív terhelés minimalizálása.
* [[UX_PATTERNS]] — Varázsló, lebegő kosár és döntési kártyák szabványai.
* [[DESIGN_PRINCIPLES]] — Vizuális hierarchia, prémium megjelenés és konzisztencia.
* [[DESIGN_SYSTEM]] — CSS változók, színek, tipográfia és tokenek.
* [[ANTI_AI_SLOP_POLICY]] — Anti AI Slop és autentikus dizájn/szövegezési szabályok.
* [[ENGINEERING_PRINCIPLES]] — Felelősségi körök és kódminőség.
* [[ARCHITECTURE_RULES]] — Réteghatárok és függőségi szabályok.
* [[CODE_QUALITY]] — Modularitás és refaktorálási szabványok.
* [[TESTING]] — Integrációs, Playwright és egységtesztelési követelmények.
* [[QUALITY_GATES]] — Minőségi ellenőrzőkapuk minden módosítás előtt.
* [[REVIEW_PROTOCOL]] — Többszempontú áttekintési protokoll.

---

## 🔨 Work Items (Munkaszervezés)


---

## 🏛️ Entities (Entitások)
* [[trip]] — Az utazás központi aggregált entitása (UnifiedTrip).
* [[destination]] — Úti cél város, éghajlati és költségadatokkal.
* [[flight]] — Retúr vagy egyirányú repülőjárat ajánlat.
* [[accommodation]] — Szálláslehetőség és ár-érték attribútumai.
* [[poi]] — Látványosság, étterem vagy programpont (Point of Interest).

---

## 💡 Concepts (Koncepciók)
* [[unified-trip-model]] — A három modult összefogó közös utazási adatmodell és kézfogási elv.
* [[ahp-weighting]] — Analytic Hierarchy Process (AHP) páros összehasonlító döntési mátrix.
* [[promethee-ranking]] — PROMETHEE II többkritériumos preferenciarangsorolási algoritmus.
* [[guided-progressive-decision-flow]] — Vezérelt progresszív döntési folyamat és Zero Analysis-Paralysis alapelv.
* [[numbeo-cost-model]] — Hivatalos Numbeo étkezési és helyi közlekedési fogyasztói kosár modell.
* [[honest-scraping-policy]] — Transzparens hibakezelés mesterséges dummy adatok helyett.

---

## 🔄 Processes (Folyamatok)
* [[master-planner-wizard]] — Master Travel Planner: integrált 4-lépéses end-to-end utazástervező varázsló.
* [[destination-matching]] — Úticél-keresési és éghajlat/ár/biztonság optimalizálási folyamat.
* [[flight-intelligence-workflow]] — Élő repülőjegy gyűjtés, AHP súlyozás és PROMETHEE rangsorolás.
* [[accommodation-search-workflow]] — Zárolt dátumú szálláskeresés és kényelmi szűrés.
* [[proposal-generation]] — B2B ügyfélajánlat exportálása tételes képletekkel.
* [[itinerary-optimization]] — Időkorlátos és távolságoptimalizált napi útiterv készítés.

---

## ⚙️ Systems (Rendszerek)
* [[fastapi-backend]] — Python FastAPI aszinkron backend szerver és REST végpontok.
* [[kiwi-scraper]] — Kiwi.com GraphQL és REST járatkereső modul.
* [[cozycozy-scraper]] — Cozycozy szállásaggregációs modul.
* [[open-meteo-api]] — Open-Meteo éghajlati és időjárási adatforrás.
* [[numbeo-database]] — Helyi Numbeo megélhetési és biztonsági adatbázis.
* [[google-places-service]] — Google Places POI és értékelés szolgáltatás.
* [[trip-cart-engine]] — Kliensoldali JavaScript állapotkezelő és lebegő sáv/fiók UI.

---

## 📊 Metrics (Mérőszámok)
* [[flight-price]] — Teljes és egy főre jutó repülőjegy árak (HUF).
* [[daily-food-cost]] — Numbeo-alapú napi étkezési költségkeret.
* [[daily-transit-cost]] — Numbeo-alapú napi helyi közlekedési költség.
* [[accommodation-nightly-rate]] — Éjszakánkénti és teljes szállásköltség.
* [[safety-index]] — Numbeo Közbiztonsági Index (0–100 skála).
* [[promethee-phi-net]] — PROMETHEE II Net Outranking Flow relevanciaérték.

---

## 📜 Decisions (Döntések / ADR-ek)
* [[ADR-001-unified-trip-architecture]] — Közös UnifiedTrip architektúra konszolidálása.
* [[ADR-002-deterministic-numbeo-food-pricing]] — Becsült ételköltségek cseréje determinisztikus Numbeo képletekre.
* [[ADR-003-promethee-ii-outranking]] — PROMETHEE II alkalmazása AHP súlyozással kombinálva.
* [[ADR-004-honest-scraping-mode]] — Fiktív mock járatok eltávolítása, hibák transzparens jelzése.
* [[ADR-005-fastapi-modular-structure]] — Moduláris `app/` architektúra és V2 route-ok bevezetése.
* [[ADR-006-master-planner-wizard]] — Master Travel Planner: egybefüggő 4-lépéses folyamat.
* [[ADR-007-fastapi-router-modularization]] — FastAPI Monolit Dekompozíció és Moduláris APIRouter Architektúra.

---

## 🧠 Learnings (Megfigyelések & Tanulságok)
* [[kiwi-pagination-and-tokens]] — Kiwi GraphQL keresési tokenek és lapozás sajátosságai.
* [[jinja-template-block-inheritance]] — Jinja2 szkript blokkok öröklődése a lebegő kosár rendereléséhez.
* [[mobile-viewport-overflow-fixed-bars]] — Keskeny mobilképernyők (440px) és lebegő elemek illesztése.
* [[numbeo-hungarian-city-mapping]] — Magyar ékezetes városnevek leképezése Numbeo indexekhez.

---

## 🛠️ Operations (Üzemeltetési & Használati Útmutatók)
* [[run-local-development]] — Lokális fejlesztői környezet és szerver indítása.
* [[refresh-numbeo-data]] — Numbeo megélhetési indexek frissítése.
* [[enrich-destinations]] — Úti célok éghajlati és repülési adatainak dúsítása.
* [[run-validation-tests]] — Automatizált tesztek és folyamat-ellenőrzések futtatása.
* [[export-client-proposal]] — Ügyfélajánlat generálása és PDF mentése.
