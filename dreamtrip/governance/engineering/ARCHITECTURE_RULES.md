---
id: architecture-rules
aliases:
  - ARCHITECTURE_RULES
type: governance
name: Architecture Rules & Dependency Boundaries
status: active

description: A rétegek közötti függőségi és hívási szabályok.

related:
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[CODE_QUALITY]]"
  - "[[fastapi-backend]]"
---

# 🏗️ Engineering Governance: Architecture Rules

A projekt architektúrája szigorúan rétegzett:

```text
UI / Kliens (Templates + Vanilla JS)
        ↓
FastAPI Web & REST API Layer (app/main.py)
        ↓
Application Services (app/services/planner_service.py, etc.)
        ↓
Domain Logic & Decision Engines (AHP, PROMETHEE, Cost Models)
        ↓
Infrastructure & Scrapers (app/scrapers/scraper.py, Cozycozy, Open-Meteo)
```

### 🚫 Megengedett és Tiltott Függőségek:
* **Engedélyezett:**
  * `UI` → `FastAPI REST API`
  * `FastAPI API` → `Application Services`
  * `Services` → `Domain Logic` & `Scrapers`
* **Szigorúan Tiltott:**
  * `UI (JavaScript)` → Közvetlen külső API hívás (pl. Kiwi API kliensoldali hívása a Python proxy helyett).
  * `Scrapers / Infrastructure` → `UI Templates` vagy `Web Routing` importálása.
  * Üzleti döntési mátrixok (AHP, PROMETHEE) implementálása a JavaScript kliensben a Python szerviz helyett.
