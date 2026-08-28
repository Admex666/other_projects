# Agent Operating Protocol

## 1. Core Principle
Treat the project repository as the persistent source of truth.
Chat history is temporary context. The `knowledge/` graph, codebase, database, and configuration are the persistent reality.

---

## 2. Startup Procedure
Before starting a non-trivial task:
1. Read this file (`AGENTS.md`).
2. Read [`knowledge/INDEX.md`](file:///e:/Data/other_projects/VitaSteps/knowledge/INDEX.md).
3. Identify the relevant knowledge nodes.
4. Follow their `[[wikilinks]]`, source references, and linked code files.
5. Read only the additional code, data, or documentation required for the task.

Do **not** scan the entire repository or load the entire graph into context. Build the smallest relevant context graph for the task (Progressive Disclosure).

---

## 3. Knowledge Graph Rules
- **One Fact → One Canonical Source:** Never duplicate dynamic values across markdown documents. Markdown describes meaning, formulas, relationships, and points to the authoritative source.
- **Wikilinks & Relationships:** Use `[[wikilinks]]` to connect concepts, processes, entities, systems, and decisions.
- **Durable Knowledge Only:** Create or update a node only when durable architecture, business logic, system behavior, processes, or decisions change. Do not document trivial refactors or formatting changes.
- **Decision Tracking:** Record significant architectural or business decisions as separate ADR nodes in `knowledge/decisions/`. When a decision changes, mark the previous as `superseded` and link it to the new one.

---

## 4. Single Source of Truth References
* **PostgreSQL / DB Data:** `https://ncsathcqpvlrygkphced.supabase.co` (`runners`, `runs`, `orders`, `shipments`)
* **Live Payments:** Stripe Checkout & Payments API
* **Marketing Performance:** Meta Marketing API (`scripts/fetch_meta_daily.py`, `meta_kreativ_napi_riport.csv`)
* **Shipping / Tracking:** Foxpost API (`api/create-foxpost-parcels.js`, `scripts/daily_tracking.py`)
* **E-Invoicing:** Számlázz.hu Agent (`api/process-payment.js`)

---

## 5. Definition of Done
Before completing any task:
1. Verify the implementation works.
2. If durable knowledge changed, update affected knowledge nodes.
3. Verify that all wikilinks resolve properly.
4. Run `python scripts/validate_knowledge_graph.py` if graph structure was modified.
