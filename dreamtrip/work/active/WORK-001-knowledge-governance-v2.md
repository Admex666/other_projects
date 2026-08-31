---
id: work-001-knowledge-governance-v2
aliases:
  - WORK-001
type: work_item
name: AI-Native Knowledge & Governance System v2.0
status: completed

description: A projekt AI-Native Knowledge & Governance v2.0 architektúrájának bevezetése, szigorú réteghatárok, automatizált tartalmi és kapcsolati minőségellenőrzés kiépítése.

governed_by:
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[QUALITY_GATES]]"

related:
  - "[[GOVERNANCE_INDEX]]"
  - "[[PURPOSE]]"
  - "[[NORTH_STAR]]"
  - "[[CURRENT_STATE]]"
  - "[[PRIORITIES]]"
  - "[[CONSTRAINTS]]"
  - "[[master-planner-wizard]]"
  - "[[unified-trip-model]]"
---

# 🔨 Work Item: AI-Native Knowledge & Governance System v2.0

## 🎯 Célkitűzés (Goal)
A projekt hosszú távú stratégiai, termék, UX, dizájn és szoftverarchitekturális koherenciájának biztosítása az új **v2.0 specifikáció** szerinti rétegzéssel. Cél, hogy a projekt operációs modellje (Operating Model) és tudásgráfja önmagában navigálható és fenntartható legyen mind az emberi fejlesztők, mind az AI ágensek számára kontextusvesztés nélkül.

---

## 🧭 Stratégiai & Jelenlegi Kontextus (Strategic & Current Context)
* **Stratégia:** [[PURPOSE]], [[NORTH_STAR]], [[MISSION]], [[VISION]], [[THESIS]], [[PRINCIPLES]]
* **Jelenlegi Irány:** [[CURRENT_STATE]], [[OBJECTIVES]], [[PRIORITIES]], [[CONSTRAINTS]]
* **Központi Kapcsolódó Entitások & Folyamatok:** [[trip]], [[unified-trip-model]], [[master-planner-wizard]]

---

## 🏛️ Vonatkozó Szabályozás (Relevant Governance)
* [[PRODUCT_PRINCIPLES]] — Döntéstámogatás, egyszerűség és transzparens adatok elve.
* [[ENGINEERING_PRINCIPLES]] — Felelősségi körök szétválasztása és modularitás.
* [[ARCHITECTURE_RULES]] — Réteghatárok és tiltott közvetlen UI-adatbázis függőségek.
* [[DEFINITION_OF_DONE]] — Kötelező érvényű szállítási feltételrendszer.
* [[QUALITY_GATES]] — Minőségi ellenőrzőkapuk minden kód- és dokumentációmódosítás előtt.

---

## 📐 Megvalósítási Hatókör & Változások (Scope & Implementation)

### 1. Stratégiai Réteg Kiépítése (`knowledge/strategy/`)
* Modularizáltuk a stratégiai kontextust: `PURPOSE.md`, `NORTH_STAR.md`, `MISSION.md`, `VISION.md`, `THESIS.md`, `TARGET_CUSTOMER.md`, `VALUE_PROPOSITION.md`, `BUSINESS_MODEL.md`, `PRINCIPLES.md`.

### 2. Jelenlegi Állapot Réteg (`knowledge/current/`)
* Létrehoztuk a dinamikus állapotréteget: `CURRENT_STATE.md`, `OBJECTIVES.md`, `PRIORITIES.md`, `CONSTRAINTS.md`.

### 3. Governance Réteg (`governance/`)
* **Product:** `PRODUCT_PRINCIPLES.md`, `DEFINITION_OF_DONE.md`
* **UX:** `UX_PRINCIPLES.md`, `UX_PATTERNS.md`
* **Design:** `DESIGN_PRINCIPLES.md`, `DESIGN_SYSTEM.md`
* **Engineering:** `ENGINEERING_PRINCIPLES.md`, `ARCHITECTURE_RULES.md`, `CODE_QUALITY.md`, `TESTING.md`
* **Quality:** `QUALITY_GATES.md`, `REVIEW_PROTOCOL.md`

### 4. Munkaszervezési Réteg (`work/`)
* Felállítottuk az aktív, tervezett és lezárt munkaelemek struktúráját (`work/active/`, `work/planned/`, `work/completed/`).

### 5. Automata Minőségbiztosítás (`scripts/knowledge/validate.py`)
* Kiterjesztettük a validátort, hogy ellenőrizze az összes réteget, a YAML frontmatter metaadatokat, a wikilinkeket és a tartalmi teljességet (üres vagy csonka dokumentumok tiltása).

---

## 🧪 Elfogadási Kritériumok (Acceptance Criteria)
- [x] Minden új stratégiai és governance dokumentum tartalmazza a kötelező YAML fejlécet (`id`, `type`, `name`, `status`, `related`).
- [x] A `scripts/knowledge/validate.py` 100%-os hibamentességgel lefut.
- [x] Az Obsidianban a gyökérkönyvtárat megnyitva a teljes tudásgráf egyetlen integrált, színekkel rétegzett hálóként jelenik meg.
- [x] Nincsenek üres vagy minimális vázlatos dokumentumok a rendszerben.

---

## ⚖️ Kockázatok & Kompromisszumok (Risks & Trade-offs)
* **Kockázat:** A szabályok túlszaporodása lassíthatja az egyszerűbb fejlesztési lépéseket.
* **Mitigáció:** A kontextus-hierarchia és a progresszív megnyitás (Progressive Disclosure) biztosítja, hogy csak a feladathoz közvetlenül kapcsolódó governance szabályok töltődjenek be.

---

## 📊 Eredmény & Státusz
* **Státusz:** `completed`
* **Eredmény:** A v2.0 architektúra teljes mértékben aktív és validált.
