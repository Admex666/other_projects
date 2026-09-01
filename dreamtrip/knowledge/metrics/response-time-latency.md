---
id: response-time-latency
type: metric
name: Response Time & Search Latency
status: active

description: A rendszer válaszideje és keresési késleltetése ezredmásodpercben (ms), rétegekre bontva (Kiwi repjegy, Cozycozy szállás, Open-Meteo, AHP/PROMETHEE és teljes orchestráció).

source:
  type: telemetry
  system: FastAPI Server-Timing & Endpoint Timings

code:
  - app/main.py
  - app/services/planner_service.py
  - static/js/planner/planner_wizard.js

depends_on:
  - "[[PERFORMANCE_STANDARDS]]"
  - "[[fastapi-backend]]"

used_by:
  - "[[QUALITY_GATES]]"
  - "[[ENGINEERING_PRINCIPLES]]"
---

# ⏱️ Metric: Response Time & Search Latency

## 1. Meghatározás & Cél

A válaszidő az a teljes időtartam (ms), amely egy felhasználói kérés elküldésétől a válasz kliensoldali megérkezéséig és feldolgozásáig eltelik.

## 2. Mérési Módszertan (Telemetry)

1. **Backend Server-Timing Header:**
   ```http
   Server-Timing: total;dur=1450, kiwi;dur=820, cozycozy;dur=1100, ahp;dur=12
   ```
2. **JSON Meta Válaszmező:**
   ```json
   {
     "meta": {
       "timings_ms": {
         "destination_matcher": 540,
         "kiwi_flights": 1420,
         "cozycozy_stays": 1850,
         "ahp_promethee": 15,
         "total": 2380
       }
     }
   }
   ```

## 3. SLA Célértékek & Küszöbök

* **Kiváló (Target p50):** `< 1 500 ms`
* **Elfogadható (Target p95):** `< 3 500 ms`
* **Kritikus Lassulás (Alert):** `> 5 000 ms`

Ha a p95 válaszidő meghaladja a 4,5 másodpercet, a háttérben párhuzamosítási és gyorsítótárazási (cache invalidation) auditot kell végezni a `[[PERFORMANCE_STANDARDS]]` alapján.
