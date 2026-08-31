---
id: testing-standards
aliases:
  - TESTING
type: governance
name: Testing Standards & Quality Verification
status: active

description: A projekt tesztelési követelményei és ellenőrzési szintjei.

related:
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[QUALITY_GATES]]"
---

# 🧪 Engineering Governance: Testing Standards

A projektben három szintű minőségellenőrzés működik:

1. **Szintaxis és Típusellenőrzés:**
   * Python: `python -m py_compile` vagy modul-szintű import ellenőrzés.
   * JavaScript: `node -c static/js/...` szintaktikai ellenőrzés minden módosítás után.
2. **Kanonikus Tudásbázis Validáció:**
   * `python scripts/knowledge/validate.py` — 100%-os node-integritás, frontmatter és wikilink érvényesség.
3. **End-to-End Playwright Tesztek (`scratch/test_*.py`):**
   * A felhasználói felület lényeges interakcióit (pl. varázsló lépések, lebegő kosár gombjai, keresési folyamatok) Playwright böngészőteszttel validáljuk a módosítások után.
