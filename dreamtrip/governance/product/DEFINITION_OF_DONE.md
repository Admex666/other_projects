---
id: definition-of-done
aliases:
  - DEFINITION_OF_DONE
type: governance
name: Definition of Done
status: active

description: A feladatok lezárásának kötelező minőségi feltételrendszere.

related:
  - "[[QUALITY_GATES]]"
  - "[[REVIEW_PROTOCOL]]"
  - "[[PRODUCT_PRINCIPLES]]"
---

# ✅ Product Governance: Definition of Done (DoD)

Egy feladat vagy módosítás **CSAK AKKOR tekinthető befejezettnek**, ha az alábbi kritériumok mindegyike teljesül:

1. **Funkcionális Helyesség:** A kért funkció hibátlanul lefut a valós környezetben és támogatja a célmunkafolyamatot.
2. **Governance és Szabályok Betartása:**
   * A frontend réteg nem tartalmaz közvetlen üzleti vagy adatbázis-logikát.
   * Az új UI elemek a meglévő Design System CSS tokenjeit és mintáit használják.
   * Az architekturális határok épek maradtak.
3. **Automatizált Validáció & Tesztelés:**
   * Integrációs vagy Playwright böngészőteszt ellenőrizte a működést hiba nélkül.
   * A Knowledge Graph validátor (`python scripts/knowledge/validate.py`) 100%-os sikert mutat.
4. **Egységes Forrás (Single Source of Truth):**
   * Nem került be hardkódolt, duplikált kanonikus adat sehová.
5. **Tartós Tudás Frissítése:**
   * Ha a rendszer működése, architektúrája vagy forrása megváltozott, a releváns tudás- vagy döntési node (`knowledge/decisions/`, `knowledge/systems/`) frissült.
