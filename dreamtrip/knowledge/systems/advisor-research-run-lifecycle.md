---
id: advisor-research-run-lifecycle
type: system
name: Advisor ResearchRun Lifecycle & Resilience Engine
status: active

description: Az aszinkron kutatási futások (ResearchRun) állapotgépe (QUEUED, RUNNING, PARTIAL, COMPLETED, FAILED, CANCELLED), szolgáltatói státuszkövetése és a részleges hibatűrés (Partial Failures) kezelése.

source:
  type: code
  ref: app.services.advisor_orchestration_service

code:
  - app/models/advisor_models.py
  - app/services/advisor_orchestration_service.py
  - app/routers/advisor_api.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[advisor-research-pipeline]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# ⚙️ Advisor ResearchRun Lifecycle & Resilience Engine

Ez a dokumentum specifikálja a háttérben futó kutatási folyamatok állapotgépét, az aszinkron életciklus kezelését és az egyedi szolgáltatói kiesésekkel szembeni hibatűrést.

---

## 1. Az Állapotgép (`ResearchRunStatus`)

```text
    ┌──────────┐
    │  QUEUED  │ (Kutatási kérés regisztrálva a feladatmedencében)
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │ RUNNING  │ (Kiwi, Cozycozy, Open-Meteo párhuzamos lekérdezések)
    └────┬─────┘
         ├───────────────────────────────┬───────────────────────────────┐
         │                               │                               │
         ▼ (Minden forrás sikeres)       ▼ (Egyes források késtek/hibásak)▼ (Minden forrás elérhetetlen)
    ┌───────────┐                 ┌───────────┐                  ┌──────────┐
    │ COMPLETED │                 │  PARTIAL  │                  │  FAILED  │
    └───────────┘                 └───────────┘                  └──────────┘
         │                               │
         └───────────────┬───────────────┘
                         │ (Tanácsadó leállítja a folyamatot)
                         ▼
                  ┌───────────┐
                  │ CANCELLED │
                  └───────────┘
```

---

## 2. Szolgáltatói Státuszkövetés (`providers_status`)

Minden kutatási futás részletesen naplózza az egyes szolgáltatók állapotát:

```yaml
providers_status:
  kiwi:
    status: "completed" # "pending" | "running" | "completed" | "partial" | "failed" | "cached"
    count: 14           # Talált járatkandidátusok száma
    error: null
    latency_ms: 1240

  cozycozy:
    status: "completed"
    count: 22           # Talált szálláskandidátusok száma
    error: null
    latency_ms: 2150

  open_meteo:
    status: "cached"    # Cache-ből kiszolgált időjárási profil
    count: 1
    error: null

  poi_wikidata:
    status: "completed"
    count: 8
    error: null
```

---

## 3. Részleges Hibatűrés (Partial Failure Resilience)

### Fő Alapelv:
> **Egyetlen külső szolgáltató átmeneti hibája vagy lassúsága miatt tilos az egész kutatási folyamatot automatikusan megszakítani.**

1. **Kiwi időtúllépés (Timeout)**:
   - Ha az élő járatkeresés 10 mp után sem válaszol, a rendszer a legutóbbi gyorsítótárazott (Cached) vagy benchmark járatadatokkal dolgozik tovább, és `verification_status: ESTIMATED` jelölést ad a járatoknak.
2. **Cozycozy részleges találat**:
   - Ha a szálláskereső kevesebb hotelt ad vissza a vártnál, a rendszer feldolgozza a meglévőket, és `status: PARTIAL` jelzéssel befejezi a szintézist.
3. **Open-Meteo kiesés**:
   - Történeti éghajlati átlagokat (`destination_profiles.json`) használ fallbackként.
