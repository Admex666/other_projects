---
id: op-local-dev
type: operation
name: Run Local Development Server
status: active

description: A FastAPI fejlesztői szerver indítása élő újratöltéssel (live reload).

requires:
  - "[[fastapi-backend]]"

code:
  - main.py
  - app/main.py

related:
  - "[[ADR-005-fastapi-modular-structure]]"
---

# Operation: Run Local Development Server

## Lépések

1. Nyiss egy terminált a projekt gyökérkönyvtárában (`e:\Data\other_projects\dreamtrip`).
2. Indítsd el a Python alkalmazást:
   ```bash
   python main.py
   ```
3. A szerver a `http://127.0.0.1:8000` címen érhető el.
4. Főbb oldalak:
   * Főoldal: `http://127.0.0.1:8000/home`
   * Destination Matcher: `http://127.0.0.1:8000/destination-matcher`
   * Flight Intelligence: `http://127.0.0.1:8000/flight-intelligence`
   * Accommodation Intelligence: `http://127.0.0.1:8000/accommodation-intelligence`
