---
id: work-002-poi-itinerary-module
aliases:
  - WORK-002
type: work_item
name: Point of Interest (POI) & Itinerary Optimizer Module
status: planned

description: Látnivalók, élmények, éttermek és idő-távolság optimalizált napi útiterv készítő modul beépítése az Optivoya Master Plannerbe.

governed_by:
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[ARCHITECTURE_RULES]]"
  - "[[DEFINITION_OF_DONE]]"

related:
  - "[[poi]]"
  - "[[itinerary-optimization]]"
  - "[[google-places-service]]"
  - "[[master-planner-wizard]]"
  - "[[proposal-generation]]"
  - "[[VISION]]"
  - "[[TARGET_CUSTOMER]]"
---

# 📋 Work Item: Point of Interest (POI) & Itinerary Optimizer Module

## 🎯 Célkitűzés (Goal)
Az Optivoya hosszú távú víziójának megfelelően a Master Planner 4. Lépése (Összegzés és Ajánlatkészítés) kiegészül egy **interaktív napi útiterv-készítő és látványosság-ajánló (POI) motorral**. Az utazási szakember vagy a végfelhasználó nemcsak járatot és szállást foglal, hanem egy kattintással megkapja a célállomás top látnivalóit időablakokba és optimalizált földrajzi útvonalakba rendezve.

---

## 🧭 Stratégiai & Jelenlegi Kontextus
* **Stratégia:** [[VISION]] (End-to-End utazástervező platform), [[THESIS]] (Döntéstámogatás a manuális kutatás helyett)
* **Célközönség:** [[TARGET_CUSTOMER]] (Utazási irodák és tanácsadók, akik komplett programtervet adnak át)
* **Központi Entitások:** [[poi]], [[trip]], [[destination]]

---

## 🏛️ Vonatkozó Szabályozás (Governance)
* [[PRODUCT_PRINCIPLES]] — Kurált és értékelések alapján rangsorolt látványosságok, nem végtelen ömlesztett lista.
* [[UX_PATTERNS]] — Drag-and-drop vagy kártyás napra osztási felület a meglévő Advisor Card dizájnnal.
* [[DESIGN_SYSTEM]] — A meglévő CSS színek és komponensosztályok szigorú használata.
* [[ARCHITECTURE_RULES]] — A helymeghatározási és útvonaloptimalizálási algoritmusok a Python backendben (`app/services/itinerary_service.py`) futnak, tiszta REST végponton keresztül.

---

## 📐 Megvalósítási Terv & Hatókör (Scope)

1. **Adatforrás Integráció:**
   * OpenStreetMap / Wikidata / Google Places POI API integrálása a 40 célvárosra.
   * Látványosságok kategorizálása (Múzeum, Természet, Gasztronómia, Történelmi helyszín).
2. **Útiterv Optimalizáló Algoritmus (`app/services/itinerary_service.py`):**
   * Utazási időtartam ($N$ nap) és tartózkodási hely (kiválasztott szálloda koordinátái) figyelembevétele.
   * TSP / Klaszterező algoritmus a napi gyalogos/tömegközlekedési útvonalak minimalizálására.
3. **Frontend Munkafolyamat Bővítés:**
   * Új "4. Lépés: Programok & Útiterv" beépítése a varázslóba a végső B2B ajánlat előtt.
   * Interaktív idővonal (Timeline) és térképes előnézet.
4. **B2B Export Frissítés:**
   * A PDF és nyomtatható ajánlat kiegészítése a napi bontású programtervvel és fotókkal.

---

## 🧪 Elfogadási Kritériumok (Acceptance Criteria)
- [ ] A 40 támogatott célvárosban legalább 15-20 ellenőrzött POI azonnal betöltődik.
- [ ] A napi útiterv automatikusan illeszkedik a repülőgép érkezési és indulási napjához.
- [ ] Az exportált PDF ajánlat tartalmazza a látnivalók leírását és nyitvatartási javaslatait.
- [ ] A `scripts/knowledge/validate.py` 100%-os zöld futást biztosít.

---

## 📊 Státusz
* **Státusz:** `planned`
