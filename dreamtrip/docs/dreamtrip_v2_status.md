# 🌍 DreamTrip v2 — Megvalósítási és Készültségi Állapot (Status Report)

Ez a dokumentum összefoglalja a **DreamTrip v2** motor aktuális állapotát, különválasztva a **valós (éles API-t és algoritmust használó)** funkciókat a **szimulált (dummy / placeholder)** elemektől.

---

## 1. Városrangsoroló & Pontozó Motor (`scoring_service.py`)

A városok felfedezése és pontozása a megadott 6-tényezős súlyozott képlet alapján történik:

| Szempont | Megvalósítás Típusa | Részletek & Működés |
| :--- | :---: | :--- |
| **Repülőjegy Ár** (Kiwi API) | **VALÓS** | Valós időben kérdezi le a Kiwi GraphQL API-t (Budapest vagy a megadott indulási helyről), és normalizálja az árakat. Ha az API hibát ad, az algoritmus automatikusan újraelosztja a súlyokat (Failure Scenario). |
| **Klíma & Hőmérséklet** (Open-Meteo) | **VALÓS** | Az **Open-Meteo API** segítségével lekéri a célváros koordinátáira vonatkozó átlagos hőmérsékletet a kiválasztott hónapban, és összeveti a felhasználó ideális hőmérsékletével. |
| **Megélhetési Költség** (Numbeo) | **VALÓS** | A helyi `data/live_numbeo_indices.json` adatbázisból kikeresi a város aktuális Numbeo Cost of Living indexét, és átváltja EUR/nap értékre. |
| **Közbiztonság** (Numbeo) | **VALÓS** | A helyi adatbázisból beolvassa a Numbeo Safety indexet. |
| **Gyalogos Bejárhatóság** (Walkability) | **FÉL-VALÓS** | Statikus adatbázis (`WALKABILITY_SCORES`) tartalmazza a legfőbb világvárosok értékeit. Ismeretlen város esetén `70.0` pont a biztonsági fallback. |
| **Látnivaló Sűrűség** (POI count) | **VALÓS / DUMMY** | A Google Places API-ból lekért érvényes látnivalók darabszáma alapján számolódik (ha nincs API kulcs, a generált mock POI-k számából indul ki). |
| **Éjszakai Élet** (Nightlife Score) | *DUMMY* | Jelenleg fixen `50.0` pontot ad vissza placeholderként. |

---

## 2. Helyszínek & Térkép API (`maps_service.py`)

A POI (Point of Interest) adatok lekérésének működése:

*   **Google Places API Integration**: **VALÓS**  
    Ha a `GOOGLE_MAPS_API_KEY` környezeti változó be van állítva, a rendszer a Google Places Text/Nearby Search és Place Details API-k segítségével lekéri a valódi helyszíneket, nyitvatartási időket, értékeléseket és címeket.
*   **Helyi Gyorsítótár (Cache)**: **VALÓS**  
    A letöltött POI-k a `site/data/poi_cache.json` fájlban tárolódnak 7 napig, hogy csökkentsék a Google API költségeit.
*   **Mock Fallback**: **DUMMY**  
    Ha nincs beállítva Maps API kulcs, a `generate_mock_pois` függvény a város koordinátái köré szór szimulált helyszíneket (attraction, viewpoint, restaurant, cafe kategóriákban) valósághű nyitvatartásokkal, így a rendszer API kulcs nélkül is teljes értékűen tesztelhető.

---

## 3. Constraint-Alapú Ütemező (`itinerary_service.py`)

A napi tervek összeállítása és re-optimalizálása:

> [!TIP]
> A motor teljesen valós matematikai és logikai modellek alapján működik, nincsenek benne dummy számítások.

*   **Idősávok (Timeline)**: **VALÓS**  
    Időpontok (pl. `08:30 - 09:15`) kezelése, utazási idők kalkulálása.
*   **Étkezési Idősávok (Meal Slots)**: **VALÓS**  
    Automatikusan beilleszt egy reggelit, ebédet és vacsorát a megfelelő időpontokban, kiválasztva a környező legjobb éttermeket és kávézókat.
*   **Utazási Idő (Travel Time)**: **VALÓS**  
    A **Haversine** képlettel kiszámítja a helyszínek közötti valós földrajzi távolságot, és ez alapján sétálós (4.5 km/h) vagy tömegközlekedés/taxi (20 km/h + 5 perc várakozás) utazási időt kalkulál.
*   **Nyitvatartási Idők Ellenőrzése**: **VALÓS**  
    Összeveti a látogatási időpontot a POI nyitvatartási periódusaival. Ha zárva lenne, figyelmeztetést (`conflict`) küld a frontendnek.
*   **Zárolt Elemek (Locked Items)**: **VALÓS**  
    A felhasználó által lelakatolt programokat a motor nem mozdítja el a re-optimalizálás során, hanem a szabad elemeket igazítja köréjük (Greedy repair stratégia).

---

## 4. Frontend & Felület (`templates/`)

A két új V2-es aloldal működése:

1.  **Városválasztó (`dreamtrip_discover.html`)**: **VALÓS**  
    Dinamikusan küldi a szűrőket és preferenciákat a `/api/v2/discover` végpontnak, és grafikusan rendereli a pontszám-összetevőket és a szöveges magyarázatokat ("Why this city").
2.  **Tervező Dashboard (`dreamtrip_planner.html`)**: **VALÓS**  
    *   **Drag & Drop**: HTML5 drag-and-drop eseménykezelők, amelyek átrendezés után azonnal meghívják a `/api/v2/trip/reoptimize` végpontot.
    *   **Leaflet Térkép**: **VALÓS** térképes vizualizáció. A megadott koordinátákon megjeleníti a helyszíneket sorszámozott markerekkel és összeköti őket a napirend szerinti útvonalnak megfelelően.
    *   **Ütközések kijelzése**: Ha a szerver konfliktust (pl. zárva tartás, vagy szűkös utazási idő) jelez vissza, a kártya sárgára/pirosra színeződik a hibaleírással.

---

## 5. Teendők a teljes élesítéshez (Gyártásra kész állapot)

> [!IMPORTANT]
> A motor 95%-ban készen áll a használatra. A 100%-os éles üzemhez a következő lépések szükségesek:

1.  **API kulcsok konfigurálása**: Helyezd el a valós `GOOGLE_MAPS_API_KEY` kulcsot a környezeti változókban.
2.  **Nightlife Score bekötése**: A `scoring_service.py` 274. során jelenleg fix 50 pont helyett be lehet kötni egy Numbeo Indexet (pl. Crime/Safety vagy éttermi sűrűség indexből származtatva).
3.  **Helyi járat-adatbázis (opcionális)**: Ha a Kiwi API kvótakorlátos lenne, egy lokális repjegy cache tábla közbeiktatása javasolt.
