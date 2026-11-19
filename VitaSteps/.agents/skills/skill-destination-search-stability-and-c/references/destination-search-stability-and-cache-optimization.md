---
id: destination-search-stability-and-cache-optimization
type: learning
name: Destination Search Stability, Recursion Prevention, and Multi-Tier Cache Optimization
status: active

description: A célállomás-keresés és a 4-pilléres döntési mátrix kalkulációjának stabilizálása, a kölcsönös rekurzió megszüntetése, a POI model validációs javítása, valamint az ultra-gyors többszintű L1/L2 cache és negatív gyorsítótárazás bevezetése.

source:
  type: code
  ref: app.services.maps_service

code:
  - app/services/maps_service.py
  - app/services/experience/cache.py
  - app/services/destination_scoring_service.py

related:
  - "[[experience-intelligence-engine]]"
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"
  - "[[fastapi-backend]]"
---

# 🧠 Learning: Destination Search Stability, Recursion Prevention, and Multi-Tier Cache Optimization

## 1. Háttér és Problémafelismerés
A Master Planner célállomás-keresési folyamata során a "Multikritériumos döntési mátrix kalkulációja..." állapotban (90%-os előrehaladásnál) a háttérfolyamat megakadt, miközben a kliens másodpercenként lekérdezte a `/api/planner/destinations-status` végpontot. A szerverlogban végtelenített ismétlődések jelentek meg:
```text
[INFO] Using real Optivoya Experience Engine activities for New York (21 places)!
[WARN] Experience Engine POI lookup fallback: name 'standard_hours' is not defined
[INFO] Mock POI adatok generálása ehhez a városhoz: New York (ny_us)...
```

## 2. A Három Összefüggő Hibaforrás

### A. Lokális Változó Scope Hiba (`standard_hours`)
* Az `app/services/maps_service.py` fájlban a `standard_hours` szótár csupán a `generate_mock_pois()` függvényen belüli lokális változó volt.
* Amikor az Experience Engine entitásokból POI objektumokat építettünk, a `opening_hours=standard_hours` hivatkozás `NameError` kivételt dobott, és automatikusan eldobta a valós entitásokat a mock fallback ágra.

### B. Pydantic Típusvalidációs Hiba (`price_level`)
* Az Experience Engine entitások szöveges árszinteket (`"free"`, `"budget"`, `"moderate"`, `"premium"`) tartalmaznak.
* A `POI` Pydantic modell viszont szigorú `Optional[int]` értéket várt (0–3 skála). A string átadása azonnali `ValidationError`-t okozott a fallback POI készítésekor is.

### C. Kölcsönös Rekurzió és Negatív Gyorsítótárazás Hiánya
* A 4-pilléres döntési mátrix kiértékelésekor (`calculate_destination_rankings`) a rendszer mind a 40 célállomásra lekérte az élményprofilt (`experience_cache.get_destination_profile`).
* Ha egy városnak nem volt profilja, a cache `_load_fallback_entities` metódusa meghívta a `get_city_pois` függvényt.
* A `get_city_pois` viszont alapértelmezetten visszahívott az `experience_cache.get_destination_entities` függvénybe, körkörös függőséget kialakítva.
* Mivel a hiányzó profilok nem kerültek negatív gyorsítótárazásra az L1 memóriában, minden egyes desztináció és minden státusz-polling újraindította a lassú távoli Supabase hívásokat és fallback generálást.

## 3. Rendszerszintű Megoldások

1. **Modulszintű Nyitvatartási Sablonok és Biztonságos Típusleképezés:**
   * A `STANDARD_HOURS`, `RESTAURANT_HOURS`, `CAFE_HOURS`, `VIEWPOINT_HOURS` konstansok modulszintre kerültek.
   * A szöveges árszintek determinisztikusan egész számokra képeződnek le:
     ```python
     p_map = {"free": 0, "budget": 1, "moderate": 2, "premium": 3, "luxury": 4}
     ```
2. **Körmentesítés (`check_experience_engine=False`):**
   * A fallback POI betöltésekor az `experience_cache` expliciten kikapcsolja az élménymotoros visszacsatolást a `get_city_pois` hívásában.
3. **Multi-Tier Cache Hierarchia Helyreállítása:**
   * A lekérdezési sorrend optimalizálva lett: **1. L1 Memória** (<0.01ms) → **2. Helyi Lemezes Cache** (<0.1ms) → **3. Távoli Supabase Adatbázis** (200-500ms) → **4. Fallback Generálás**.
   * **Negatív gyorsítótárazás:** Ha egy célállomáshoz nincs élményprofil, az L1 memóriában `None` / `[]` tárolódik a TTL időtartamára.

## 4. Eredmény & Mérőszámok
* 40 célállomás 4-pilléres rangsorolása **0.48 másodperc** alatt fut le.
* A POI betöltés és profilozás megbízhatóan, figyelmeztetések és rekurzió nélkül működik.
