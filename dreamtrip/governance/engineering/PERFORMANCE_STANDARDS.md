---
id: performance-standards
aliases:
  - PERFORMANCE_STANDARDS
  - LATENCY_STANDARDS
type: governance
name: Performance & Latency Engineering Standards
status: active

description: Iparági szabványokon (Google Flights, Skyscanner, Booking.com) alapuló sebességi, válaszidő és skálázási mérföldkövek az Optivoyához.

related:
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[ARCHITECTURE_RULES]]"
  - "[[QUALITY_GATES]]"
  - "[[response-time-latency]]"
---

# ⚡ Performance & Latency Engineering Standards

Az utazási döntéstámogató rendszerekben a sebesség és az azonnali visszajelzés közvetlenül meghatározza a felhasználói élményt és a döntési folyamat gördülékenységét.

---

## 1. Iparági Válaszidő Sztenderdek & SLA Célok

Az Optivoya az alábbi szigorú válaszidő korlátokhoz tartja magát:

| Művelet / Szerviz | Célidő (Target p50) | Elfogadható Felsőhatár (p95) | Max Timeout (SLA) | Stratégia |
| :--- | :--- | :--- | :--- | :--- |
| **UI Interakciók & Váltások** | `< 50 ms` | `< 100 ms` | `150 ms` | Optimista UI frissítés, azonnali DOM renderelés |
| **Város Autocomplete & Szűrők** | `< 80 ms` | `< 150 ms` | `250 ms` | Kliens & szerver memóriagyorsítótár |
| **Döntési DNS & AHP Számítások** | `< 10 ms` | `< 30 ms` | `50 ms` | Kliensoldali vektorizált mátrixműveletek |
| **Célállomás Matcher & Rangsorolás** | `< 600 ms` | `< 1 200 ms` | `2 000 ms` | Párhuzamos szálkezelés + Numbeo memóriaindex |
| **Kiwi.com Élő Repülőjárat Keresés** | `< 1 500 ms` | `< 2 800 ms` | `4 500 ms` | Párhuzamos GraphQL chunking + 30 perces TTL cache |
| **Cozycozy Élő Szállás Keresés** | `< 2 000 ms` | `< 3 500 ms` | `5 000 ms` | Párhuzamos Session lekérés + 30 perces TTL cache |
| **Teljes Master Planner Munkafolyamat** | `< 3 000 ms` | `< 4 500 ms` | `6 000 ms` | Aszinkron ThreadPoolExecutor + intelligens invalidáció |

---

## 2. Sebességmérési Követelmények (Telemetry Invariants)

Minden backend API végpontnak és frontend modulnak mérnie kell a saját végrehajtási idejét:

1. **`Server-Timing` HTTP Fejléc:**
   * Minden backend válasz tartalmazza a `Server-Timing: total;dur=..., kiwi;dur=..., cozycozy;dur=..., ahp;dur=...` fejlécet a szabványos böngésző DevTools Network diagnosztikához.
2. **Strukturált `meta.timings_ms` Válaszobjektum:**
   * A JSON válaszok tartalmazzák a komponensek pontos futási idejét ezredmásodpercben.
3. **Kliensoldali Logolás & Figyelmeztetés:**
   * Ha egy keresési lépés túllépi az SLA p95 határát, a rendszer konzol figyelmeztetést generál a szűk keresztmetszet azonosítására.

---

## 3. Architekturális Gyorsítási Invariánsok

* **Aszinkron Párhuzamosítás:** A független külső API hívások (Kiwi járatok, Cozycozy szállások, Open-Meteo időjárás) **soha nem futhatnak szekvenciálisan**, hanem `ThreadPoolExecutor`-ral vagy `asyncio.gather`-rel párhuzamosan kell indulniuk.
* **Memória- és Session Cache:** A dinamikus repjegy- és szállásadatokat 30 perces TTL memóriagyorsítótár tárolja a redundáns kaparások elkerülésére.
* **Non-Blocking UI:** Hosszabb hálózati műveletek közben a felület skeleton shimmer animációt és pontos folyamatjelző szövegeket jelenít meg; a böngésző UI szála sosem blokkolódhat.
