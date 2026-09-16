# AI Operating Protocol — Optivoya (DreamTrip) v2.0

## 1. Core Principle

Treat the project repository as the persistent operating model of the project.

Chat history is temporary context. The repository contains the project's persistent strategic direction, current state, knowledge, governance rules, active work items, decisions, architecture, implementation, data, and operational procedures.

Do not rely on remembered conversation context when information can be verified from the project.

---

## 2. Project Architecture Layers

The project is organized into interconnected conceptual layers:

```text
AGENTS.md / PROJECT_MAP.md
    ↓
Project Governance (governance/INDEX.md → [[PROJECT_GRAPH]])
    ↓
Knowledge Index (knowledge/INDEX.md)
    ↓
Strategic Context (knowledge/strategy/)
    ↓
Current State (knowledge/current/)
    ↓
Active Work Items (work/active/)
    ↓
Relevant Knowledge & System Graph (knowledge/entities/, concepts/, systems/)
    ↓
Canonical Data Sources (API, DB, Config)
    ↓
Implementation (app/, static/, templates/)
    ↓
Quality Control & Validation (scripts/knowledge/validate.py, tests/)
```

---

## 3. Context Hierarchy & Startup Procedure

Before starting a non-trivial task, traverse using progressive disclosure:

1. Read this file (`AGENTS.md`) and high-level map (`PROJECT_MAP.md`).
2. Read `governance/INDEX.md` and check relevant governance rules (Product, UX, Design, Engineering, [[PROJECT_GRAPH]], Quality).
3. Read `knowledge/INDEX.md` to identify the strategic context and current focus.
4. Follow relevant relationships (`[[wikilinks]]`) to affected entities, processes, systems, and modules.
5. Read only the implementation, data, and tests required.

```text
LEVEL 0 — PROJECT IDENTITY: Purpose, North Star, Mission, Vision
LEVEL 1 — STRATEGY: Thesis, Customers, Value Proposition, Business Model, Principles
LEVEL 2 — CURRENT DIRECTION: Current State, Objectives, Priorities, Constraints
LEVEL 3 — GOVERNANCE: Product, UX, Design, Engineering, Project Graph & Quality Rules
LEVEL 4 — WORK: Active, Planned and Completed Work Items
LEVEL 5 — DOMAIN & SYSTEM KNOWLEDGE: Entities, Concepts, Processes, Systems, Metrics
LEVEL 6 — HISTORY: Decisions (ADRs) & Durable Learnings
LEVEL 7 — IMPLEMENTATION: Code, Modules, Configuration, Templates, Tests
LEVEL 8 — RUNTIME DATA: Live APIs, Database, LocalStorage
```


---

## 4. The Three Fundamental Invariants

1. **KNOWLEDGE ("What is true?"):**
   * Describes reality (e.g. `[[flight]]`, `[[kiwi-scraper]]`, `[[numbeo-cost-model]]`).
2. **GOVERNANCE ("What must remain true?"):**
   * Defines invariants and constraints that protect product quality, UX, design, and architecture (e.g. `[[PRODUCT_PRINCIPLES]]`, `[[ARCHITECTURE_RULES]]`, `[[DESIGN_SYSTEM]]`).
3. **WORK ("What are we accomplishing?"):**
   * Connects strategic intent with implementation tasks (e.g. `[[WORK-001]]`, `[[WORK-002]]`).

---

## 5. Single Source of Truth & Dynamic Data

Every important fact or value must have one canonical source:
* **Kiwi.com GraphQL API** → live flight prices & schedules
* **Cozycozy Scraper** → live accommodation options
* **Open-Meteo API** → climate & weather data
* **Numbeo Database** (`data/live_numbeo_indices.json`) → cost of living indices
* **FastAPI Backend** (`app/`) → session orchestration & business workflows
* **Design System** (`static/css/theme.css`, `components.css`) → UI tokens and styles

Do not treat Markdown as a database. Dynamic values are retrieved at runtime from their canonical sources.

---

## 6. Definition of Done & Quality Gates

Before completing a task, verify against `[[DEFINITION_OF_DONE]]` and `[[QUALITY_GATES]]`:
1. Requested functionality is implemented and verified.
2. UI changes adhere to `[[UX_PRINCIPLES]]` and `[[DESIGN_SYSTEM]]`.
3. Architecture boundaries (`[[ARCHITECTURE_RULES]]`) and separation of concerns are preserved.
4. No hardcoded or duplicated canonical values introduced.
5. All graph nodes, YAML frontmatter, and wikilinks are validated with:
   ```bash
   python scripts/knowledge/validate.py
   ```

---

## 7. AI Operations Hub & Specialized Subagent Grid

This project is integrated into the central **AI Operations Hub** (`E:\Data\AI_ops`).
Live Mission Control is available at: `http://localhost:3300`.

### Specialized Subagent Personas & Responsibilities

| Subagent Persona | Primary Responsibilities | Core Purpose / Invariant Guard | Hub Skill Reference |
| :--- | :--- | :--- | :--- |
| 🧠 **Product / Decision Architect** (`decision_architect`) | Planner logika, Trip modell, scoring modellek, AHP prioritások, trade-offok. | Ő őrzi, hogy ne feature-halmaz, hanem valódi Decision Engine épüljön. | `E:\Data\AI_ops\skills\product-decision-architect\SKILL.md` |
| 🔬 **Travel Intelligence Agent** (`travel_intelligence`) | Destination & Experience KG, adatforrások, vibe profilok, Numbeo modellek, enrichment. | Az Optivoya „utazási tudása” és adatbázisa innen származik. | `E:\Data\AI_ops\skills\travel-intelligence\SKILL.md` |
| 🤖 **AI / Optimization Agent** (`ai_optimization`) | Recommendation engine, TripScore, diversity ranking, itinerary & constraint optimization. | A rendszer intelligenciája, többcélú optimalizálása itt koncentrálódik. | `E:\Data\AI_ops\skills\ai-optimization\SKILL.md` |
| 🗺️ **Maps & Routing Agent** (`maps_routing`) | Google/OSM/routing API-k, travel time kalkuláció, nyitvatartási idők, transzfer logisztika. | A fizikailag és időben reális napi útiterv és logisztikai megvalósíthatóság garanciája. | `E:\Data\AI_ops\skills\maps-routing\SKILL.md` |
| 💻 **Full-Stack Engineer Agent** (`fullstack_engineer`) | Backend (FastAPI) + frontend (HTML/CSS/JS) + API útvonalak + state management + integrációk. | A tényleges termék, a reszponzív UI és a robusztus architektúra implementációja. | `E:\Data\AI_ops\skills\fullstack-engineer\SKILL.md` |
| 🧪 **QA / Validation Agent** (`qa_validator`) | Automated tests, golden trips, regressziós tesztek, human-vs-AI benchmark, gráf integritás. | Megakadályozza, hogy „működő”, de hibás döntéseket adó rendszert építsünk. | `E:\Data\AI_ops\skills\qa-validation\SKILL.md` |
| 📊 **B2B Product / Growth Agent** (`b2b_growth`) | Advisor workflow, usability, pricing modell, üzleti validáció, telemetria és piacra lépés. | Biztosítja, hogy a platform ne csak technikailag jó, hanem üzletileg is sikeres legyen. | `E:\Data\AI_ops\skills\b2b-growth\SKILL.md` |

### Central Task & Memory Synchronization
- **Log a new task:**
  ```powershell
  python scripts/ai_ops_bridge.py log-task --title "Task title" --agent decision_architect --priority high
  ```
- **Sync active work items & memories to Mission Control:**
  ```powershell
  python scripts/ai_ops_bridge.py sync
  ```

