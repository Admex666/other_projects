---
id: quality-gates
aliases:
  - QUALITY_GATES
type: governance
name: Quality Gates
status: active

description: A módosítások elfogadásának kötelező minőségi ellenőrzőkapui.

related:
  - "[[DEFINITION_OF_DONE]]"
  - "[[REVIEW_PROTOCOL]]"
---

# 🚪 Quality Governance: Quality Gates

Minden jelentős változtatás előtt ellenőrizni kell az alábbi kapukat:

### 1. Funkcionalitási Kapu (Functionality Gate)
- [ ] A megvalósított kód hibamentesen lefut valós bemenetekre.
- [ ] Nem omlik össze hiányzó vagy üres találati halmaz esetén (üres járat/szálláslista).

### 2. UX & Dizájn Kapu (UX & Design Gate)
- [ ] Illeszkedik a meglévő felületi folyamatokhoz (Master Planner lépések).
- [ ] Használja a Design System CSS tokenjeit és színvilágát.

### 3. Architektúra & Adatintegritás Kapu (Architecture & Data Gate)
- [ ] Tiszteletben tartja a réteghatárokat (nincs üzleti logika a UI rétegben).
- [ ] A kanonikus adatforrásokat használja (Kiwi, Cozycozy, Numbeo).

### 4. Tudásbázis & Validációs Kapu (Knowledge Gate)
- [ ] A `python scripts/knowledge/validate.py` hiba nélkül, 100%-os zöld eredménnyel lefut.
