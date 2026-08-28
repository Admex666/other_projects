---
id: ADR-005
type: decision
name: "ADR-005: Modular Architecture and FastAPI V2 Refactoring"
status: active
date: 2026-08-01

supersedes: null

related:
  - "[[fastapi-backend]]"
  - "[[run-local-development]]"
---

# Decision

A projektet egyetlen monolitikus szkriptből szabványos `app/` Python csomagstruktúrába szerveztük át (`app/models/`, `app/services/`, `app/scrapers/`, `app/api/v2/`).

# Context

A növekvő kódbázis tesztelhetősége, karbantarthatósága és a tiszta V2 REST API végpontok kialakítása ezt megkövetelte.

# Consequences

* Tisztán elkülönülnek a Pydantic adatmodellek, a külső scraper modulok és a belső scoring logikák.
* A gyökérbeli `main.py` egy vékony belépési pont (`app.main:app`).
