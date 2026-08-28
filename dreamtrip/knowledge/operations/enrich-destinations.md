---
id: op-enrich-destinations
type: operation
name: Enrich Destinations Metadata
status: active

description: A célállomások listájának dúsítása éghajlati és repülési referenciaárakkal.

requires:
  - "[[destination]]"
  - "[[open-meteo-api]]"

code:
  - scripts/enrich_destinations.py
  - data/destinations.json

related:
  - "[[destination-matching]]"
---

# Operation: Enrich Destinations Metadata

## Lépések

1. Futtasd az adatdúsító szkriptet:
   ```bash
   python scripts/enrich_destinations.py
   ```
2. A szkript frissíti a `data/destinations.json` fájlt az Open-Meteo éghajlati és történelmi adatokkal.
