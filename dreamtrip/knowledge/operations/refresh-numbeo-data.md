---
id: op-refresh-numbeo
type: operation
name: Refresh Numbeo Data
status: active

description: A Numbeo megélhetési és biztonsági adatok frissítése és szinkronizálása a helyi adatbázisba.

requires:
  - "[[numbeo-database]]"

code:
  - scripts/refresh_numbeo_data.py
  - data/live_numbeo_indices.json

related:
  - "[[numbeo-cost-model]]"
---

# Operation: Refresh Numbeo Data

## Lépések

1. Futtasd a Numbeo frissítő parancsfájlt:
   ```bash
   python scripts/refresh_numbeo_data.py
   ```
2. A szkript letölti/frissíti az adatokat és kiírja a `data/live_numbeo_indices.json` fájlba.
3. Szükség esetén frissítsd a `static/js/trip_cart.js` beágyazott `NUMBEO_DB` konstansát a kliensoldali gyorsítótárazáshoz.
