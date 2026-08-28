# AI Operating Protocol — Optivoya (DreamTrip)

## 1. Core Principle

Treat the project repository as the persistent source of truth.

Chat history is temporary context. Project knowledge, decisions, code, data, and configuration stored in the repository are persistent context.

Do not rely on remembered conversation context when the information can be verified from the project.

---

## 2. Project Knowledge Model

The project uses a graph-based knowledge system.

```text
AGENTS.md
    ↓
knowledge/INDEX.md
    ↓
relevant knowledge nodes
    ↓
source data / systems / code
```

Knowledge is distributed across small, connected nodes rather than stored in one large memory document.

The `knowledge/` directory is the semantic layer of the project.

Markdown documents describe:

* concepts
* entities
* processes
* systems
* metrics
* decisions
* learnings
* operations
* relationships between them

Dynamic data should remain in its canonical source.

---

## 3. Startup Procedure

Before starting a non-trivial task:

1. Read this file.
2. Read `knowledge/INDEX.md`.
3. Identify the relevant knowledge nodes.
4. Follow their relationships and source references.
5. Read only the additional code, data, or documentation required for the task.

Do not scan the entire repository unless necessary.
Do not load the entire knowledge graph into context.
Build the smallest relevant context graph for the task.

---

## 4. Knowledge Graph Rules

* Prefer existing knowledge nodes over creating duplicates.
* Use `[[wikilinks]]` to connect related concepts.
* Create a new node only when the information represents durable, reusable knowledge.
* Important relationships should be explicit:
  * `depends_on`
  * `uses`
  * `used_by`
  * `implements`
  * `implemented_by`
  * `part_of`
  * `produces`
  * `consumes`
  * `derived_from`
  * `measured_by`
  * `replaces`
  * `supersedes`

The folder structure is for organization. The links and relationships form the actual knowledge graph.

---

## 5. Single Source of Truth

Every important fact or value must have one canonical source.
Never duplicate canonical values across multiple documents.

Knowledge documents should reference the source rather than duplicate its value:

```text
Knowledge Node → Canonical Source → Current Value
```

---

## 6. Dynamic Data

Do not treat Markdown as a database.
Current values should be retrieved from their authoritative source whenever practical:

* **Kiwi.com GraphQL API** → live flight prices & itineraries
* **Cozycozy Scraper** → live accommodation options & prices
* **Open-Meteo API** → historical climate and real-time weather
* **Numbeo Database** (`data/live_numbeo_indices.json`) → cost of living and safety indices
* **FastAPI Sessions** (`app/main.py`) → active user sessions and workspace state
* **LocalStorage** (`optivoya_trip_workspace`) → client-side trip cart

---

## 7. Decisions, Learnings & Operations

* **Decisions**: Record significant architectural or business decisions in `knowledge/decisions/` using the ADR format. Superseded decisions are marked `status: superseded` with `superseded_by: "[[ADR-...]]"`.
* **Learnings**: Record durable discoveries in `knowledge/learnings/`. Promote stable learnings to systems, concepts, or decisions.
* **Operations**: Document reusable execution procedures in `knowledge/operations/`.

---

## 8. Change Handling & Final Check

After completing a task, ask:
* *Did the project state change?*
* *What durable knowledge changed?*
* *Which nodes are affected?*
* *Did any decision or source of truth change?*
* *Does `knowledge/INDEX.md` need updating?*

Validate the graph with `python scripts/knowledge/validate.py`.
