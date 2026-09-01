---
id: progressive-async-prefetching
type: concept
name: Progressive Asynchronous Prefetching & Multi-Tier Caching
status: active

description: Progresszív aszinkron adatlekérési és előtöltési architektúra, amely a repülőjáratok és szállások hálózati késleltetését 0-ra redukálja a felhasználói döntési lépések között.

code:
  - app/routers/planner.py
  - static/js/planner/planner_flights.js
  - static/js/planner/planner_stays.js
  - app/services/accommodation_market_service.py

depends_on:
  - "[[PERFORMANCE_STANDARDS]]"
  - "[[response-time-latency]]"

used_by:
  - "[[master-planner-wizard]]"
  - "[[unified-trip-model]]"
---

# ⚡ Concept: Progressive Asynchronous Prefetching & Multi-Tier Caching

## 1. Az Alapelv & Működés

A hagyományos szekvenciális adatlekérések során a felhasználó minden lépésnél másodperceket vár:
```text
Célállomás választás → [Várakozás 2s] → Járatok → Járat választás → [Várakozás 3s] → Szállások
```

A **Progressive Asynchronous Prefetching** architektúrával a lépések közötti várakozás megszűnik:
1. **Élő Repjegy Betöltés (2. Lépés):** A repjegyek beérkezésekor (`~1.8s`) a rendszer azonnal kirajzolja a járatkártyákat.
2. **Proaktív Háttér Előtöltés (Prefetch):** A frontend és backend a háttérben automatikusan elindítja a szálláslekérést az 1. helyen rangsorolt járat dátumaira.
3. **Azonnali Szállásmegjelenítés (3. Lépés):** Mire a felhasználó 5–10 másodperc alatt áttekinti a járatokat és kiválasztja a megfelelőt, a szállások már a helyi memóriában és gyorsítótárban vannak (`0 ms` átmeneti idő).

---

## 2. Multi-Tier Gyorsítótárazási Rétegek

* **1. Szint: Kliensoldali Session Storage (`sessionStorage`):** Az aktuális tervezési munkamenetben lekért szállásokat és járatokat kulcs szerint tárolja.
* **2. Szint: Backend Memória TTL Cache (`_FLIGHTS_CACHE`):** 30 perces érvényességi idejű szerveroldali gyorsítótár a redundáns külső API hívások elkerülésére.
* **3. Szint: Cozycozy Market Benchmark Cache (`cozycozy_market_cache.json`):** Valós, kapart piaci mediánárakon alapuló biztonsági puffer hálózati kimaradás vagy időtúllépés esetére (`< 100 ms` válaszidő).
