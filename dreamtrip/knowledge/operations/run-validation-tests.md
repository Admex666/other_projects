---
id: op-run-tests
type: operation
name: Run Validation Tests
status: active

description: A teljes rendszerfolyamat (Python Pydantic modell, FastAPI végpontok, Node.js kliens motor, Numbeo kalkuláció és Knowledge Graph) automatizált tesztelése.

requires:
  - "[[fastapi-backend]]"
  - "[[trip-cart-engine]]"

code:
  - scratch/test_unified_trip_flow.py
  - scripts/knowledge/validate.py

related:
  - "[[unified-trip-model]]"
---

# Operation: Run Validation Tests

## Lépések

1. **Teljes utazási folyamat és Numbeo kalkuláció tesztelése**:
   ```bash
   python scratch/test_unified_trip_flow.py
   ```
   * Ellenőrzi a Destination Matcher ➔ Flight ➔ Accommodation adatátadást.
   * Ellenőrzi a Numbeo matematikai képleteket.

2. **Knowledge Graph épségének és linkjeinek ellenőrzése**:
   ```bash
   python scripts/knowledge/validate.py
   ```
   * Ellenőrzi az összes node ID-t, YAML frontmattert, wikilink kapcsolatok érvényességét és kódhivatkozásokat.
