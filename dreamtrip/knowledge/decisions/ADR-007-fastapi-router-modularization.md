---
id: adr-007-fastapi-router-modularization
aliases:
  - ADR-007
type: decision
name: FastAPI Monolit Dekompozíció és Moduláris APIRouter Architektúra
status: accepted

governed_by:
  - "[[ARCHITECTURE_RULES]]"
  - "[[CODE_QUALITY]]"
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[DEFINITION_OF_DONE]]"

related:
  - "[[fastapi-backend]]"
  - "[[master-planner-wizard]]"
  - "[[trip-cart-engine]]"
  - "[[ADR-005-fastapi-modular-structure]]"
  - "[[ADR-006-master-planner-wizard]]"
---

# 📜 ADR-007: FastAPI Monolit Dekompozíció és Moduláris APIRouter Architektúra

## 📌 Kontextus (Context)
A projekt kezdeti növekedési fázisában a repülőjegy, szállás és desztináció végpontok fokozatosan az `app/main.py` fájlba kerültek. A Master Travel Planner integrációjával a `main.py` mérete meghaladta az 1800 sort, egyetlen fájlban keverve a Jinja2 weboldal-routingot, a REST API-kat, a session-kezelést és a háttérszálakat. Ez megsértette a projekt `[[ARCHITECTURE_RULES]]` és `[[CODE_QUALITY]]` governance szabályait (felelősségi körök szétválasztása, modulméret kontroll).

---

## 🎯 Döntés (Decision)
Az `app/main.py` monolitot szétbontottuk tiszta, dedikált `APIRouter` modulokra az `app/routers/` és `app/core/` rétegekben:

1. **`app/core/` (Központi infrastruktúra):**
   * `app/core/config.py`: Jinja2 template instance, környezeti változók (`APP_ENV`, `IS_PRODUCTION`), könyvtár útvonalak.
   * `app/core/auth.py`: Felhasználók adatbázisa, session token generálás és `get_current_user` segédfüggvény.
2. **`app/routers/` (Felelősségi körök szerinti végpontcsoportok):**
   * `auth.py`: Bejelentkezés (`/login`), kijelentkezés (`/logout`), kezdőoldal.
   * `planner.py`: Master Travel Planner weboldal (`/planner`) és a 4-lépéses folyamat API-jai (`/api/planner/*`, `/api/trip/sync`).
   * `flights.py`: Kiwi járatkereső modul és AHP súlyozás (`/flight-intelligence`, `/api/locations/autocomplete`).
   * `stays.py`: Cozycozy szálláskereső és előnézeti felületek (`/accommodation-intelligence`, `/accommodation-ui-*`).
   * `destinations.py`: Célállomás ajánló és szűrő végpontok (`/destination-matcher`).
   * `trip.py`: V2 Itinerary és POI végpontok (`/home`, `/api/v2/trip/*`, `/api/v2/poi/*`).
3. **`app/main.py` (Központi alkalmazás összeszerelő):**
   * Mindössze ~45 soros belépési pont, amely a lifespan eseményt kezeli, felcsatolja a statikus fájlokat (`/static`), és regisztrálja a fenti routereket (`app.include_router(...)`).

---

## ⚖️ Következmények & Előnyök (Consequences & Benefits)
* **Karbantarthatóság:** Minden üzleti modul függetlenül tesztelhető és módosítható anélkül, hogy a többi domaint érintenénk.
* **Architektúra Invariánsok Védelme:** Nincs körkörös import vagy kontrolálatlan globális állapot a `main.py`-ban.
* **Gyorsabb fejlesztés:** Az AI ágensek és fejlesztők csak az adott feladathoz tartozó routert nyitják meg kontextusba.
