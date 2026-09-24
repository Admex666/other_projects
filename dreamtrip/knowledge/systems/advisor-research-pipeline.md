---
id: advisor-research-pipeline
type: system
name: Advisor Research Pipeline & Scope Engine
status: active

description: Az Optivoya B2B Advisor Workspace 9 specializált kutatási munkafolyamata (Research Strategies) és tetszőlegesen kombinálható kutatási hatókörei (Research Scope).

source:
  type: code
  ref: app.services.advisor_orchestration_service

code:
  - app/services/advisor_orchestration_service.py
  - app/services/destination_matching_service.py
  - app/services/flight_intelligence_service.py
  - app/services/accommodation_intelligence_service.py
  - app/services/experience_intelligence_service.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
  - "[[honest-scraping-policy]]"
  - "[[trip-case]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 🔍 Advisor Research Pipeline & Scope Engine

Ez a dokumentum specifikálja az **Optivoya Advisor Workspace** 9 specializált kutatási stratégiáját és a rugalmasan kombinálható kutatási hatóköröket.

---

## 1. A 9 Specializált Kutatási Stratégia (`ResearchStrategy`)

| # | Stratégia Azonosító | Megnevezés | Működési Mechanizmus |
| :--- | :--- | :--- | :--- |
| **1** | `DESTINATION_DISCOVERY` | **Felfedező Keresés** | 45+ európai város párhuzamos rangsorolása AHP vibe profil és élő járatárak alapján. |
| **2** | `KNOWN_DESTINATION` | **Ismert Város Deep-Dive** | Adott célvárosra fókuszált járat-, szállás- és programkutatás. |
| **3** | `FLIGHT_FIRST` | **Járat-Vezérelt Keresés** | Optimális légitársasági menetrend és kedvező viteldíjak priorizálása. |
| **4** | `STAY_FIRST` | **Szállás-Fókuszú Keresés** | Prémium 4-5★ szállodák elérhetősége vezérli a csomag összeállítást. |
| **5** | `FULL_TRIP_OPTIMIZATION` | **Teljes Csomag Optimalizálás** | Egyidejű, többcélú Pareto-optimalizálás (Desztináció + Járat + Hotel + POI). |
| **6** | `COMPONENT_ONLY` | **Részleges Hatókör** | Csak járat keresése VAGY csak szállás keresése a meglévő tervekhez. |
| **7** | `MIXED_SCOPE` | **Több-Város Összehasonlítás** | 2-4 konkrét desztináció egymás melletti valós idejű versenyeztetése. |
| **8** | `RE_OPTIMIZATION` | **1-Kattintásos Újrahangolás** | Megváltozott ügyféligények alapján új ajánlatverzió (v2, v3) generálása. |
| **9** | `FIND_BETTER` | **Célzott Komponens-Csere** | Globális kontextus megőrzése mellett egyetlen elem (hotel/járat) feljavítása. |

---

## 2. Tetszőlegesen Kombinálható Hatókörök (`ResearchScope`)

A rendszer nem kényszeríti rá a tanácsadóra, hogy minden ügy teljes utazás (Full Trip) legyen:

- `FULL_TRIP`: Desztináció + Járat + Szállás + Programok
- `FLIGHT_AND_STAY`: Csak járat és hotel (a POI és útiterv motorok futtatása opcionális)
- `FLIGHT_ONLY`: Csak járatkutatás
- `STAY_ONLY`: Csak szálláskutatás
- `ACTIVITIES_ONLY`: Csak program- és látnivaló tervezés
- `DESTINATION_DISCOVERY`: Csak célpont ajánlás
