# 🗺️ Optivoya — Project Map

Ez a dokumentum a projekt gyors, magas szintű navigációs térképe emberek és AI ágensek számára.

---

## 🏛️ Governance & Szabályrendszer
* `governance/` — Minőségi szabályok, UX irányelvek és architekturális korlátok
* `governance/INDEX.md` — Központi szabályrendszer index
* `governance/engineering/PROJECT_GRAPH.md` — AI-Native Project Graph architektúra
* `governance/engineering/PERFORMANCE_STANDARDS.md` — Iparági válaszidő és sebesség standardok

---

## 🧠 Tudásbázis & Szemantikai Modell
* `knowledge/` — Szemantikai koncepciók, entitások, rendszerek és mérőszámok
* `knowledge/INDEX.md` — A tudásbázis gyökérindexe
* `knowledge/strategy/` — Termékvízió, értékajánlat és célközönség
* `knowledge/systems/` — Szolgáltatások és integrációk (Kiwi, Cozycozy, Open-Meteo, Numbeo)
* `knowledge/metrics/response-time-latency.md` — Válaszidő és késleltetés telemetria
* `knowledge/decisions/` — Elfogadott döntések (ADR-ek) és következményeik


---

## 🚀 Aktív Fejlesztési Feladatok
* `work/active/` — Folyamatban lévő fejlesztési munkák (`WORK-001`, `WORK-002`, `WORK-003`)
* `work/planned/` — Tervezett funkciók
* `work/completed/` — Befejezett és archivált feladatok

---

## 💻 Implementáció (Forráskód)

### Backend (Python / FastAPI)
* `app/main.py` — Belépési pont, REST API útvonalak és FastAPI szerver
* `app/services/planner_service.py` — Teljes utazástervezési munkafolyamat orchestrator
* `app/services/kiwi_flight_service.py` — Kiwi.com járatkeresés és szűrés
* `app/services/cozycozy_stay_service.py` — Cozycozy szálláskereső és integráció
* `app/engine/ahp.py` — Döntési analitika és súlyozás
* `app/scrapers/` — Web scraper infrastruktúra

### Frontend (HTML / CSS / JS)
* `templates/planner/planner_wizard.html` — Master Travel Planner egybefüggő varázsló sablon
* `static/js/planner/` — Planner részegységek (intake, dest, flights, stays, trip)
* `static/js/decision_dna/` — 7-lépéses Döntési DNS modulok
* `static/css/theme.css` — CSS design tokenek és változók
* `static/css/components.css` — Komponens stílusok és mobil reszponzivitás
* `static/css/trip_cart.css` — Lebegő kosársáv és fiók stílusai

---

## 📊 Adatforrások & Adatmodellek
* `data/live_numbeo_indices.json` — Numbeo megélhetési és biztonsági indexek
* `data/destinations.json` — Célállomások adatbázisa

---

## 🧪 Validáció & Minőségbiztosítás
* `scripts/knowledge/validate.py` — Knowledge graph és wikilink automata validátor
* `tests/` — Backend és integrációs tesztek
