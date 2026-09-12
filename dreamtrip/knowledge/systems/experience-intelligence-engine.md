---
id: experience-intelligence-engine
type: system
name: Experience & Activity Intelligence Engine
status: active

description: Az Optivoya élmény- és aktivitás-intelligencia alrendszere, amely 4 külső forrásból (OSM, Wikidata, Wikipedia, Google Maps) gyűjt, deduplikál, gazdagít és profiloz élményeket 6 fázisban, ultra-gyors gyorsítótárazással és Supabase felhőperzisztenciával.

source:
  type: code
  ref: app.services.experience

code:
  - app/services/experience/connectors/base.py
  - app/services/experience/connectors/osm_connector.py
  - app/services/experience/connectors/wikidata_connector.py
  - app/services/experience/connectors/wikipedia_connector.py
  - app/services/experience/connectors/google_maps_connector.py
  - app/services/experience/raw_store.py
  - app/services/experience/entity_resolution.py
  - app/services/experience/enrichment.py
  - app/services/experience/destination_profiler.py
  - app/services/experience/cache.py
  - app/services/experience/trip_generator.py
  - app/services/experience/experience_db.py

related:
  - "[[experience-graph-modeling]]"
  - "[[experience-ingestion-pipeline]]"
  - "[[experience-entity]]"
  - "[[ADR-009-experience-activity-intelligence-engine]]"
  - "[[destination-search-stability-and-cache-optimization]]"
  - "[[run-experience-pipeline]]"
  - "[[destination-matching]]"
  - "[[supabase-database]]"
  - "[[fastapi-backend]]"

used_by:
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
  - "[[itinerary-optimization]]"
---

# ⚙️ System: Experience & Activity Intelligence Engine

Az **Experience & Activity Intelligence Engine** az Optivoya döntési motorjának azon kulcsfontosságú alrendszere, amely lehetővé teszi, hogy az utazási döntések ne csupán repülőjegy- és szállásárakon, hanem a **célállomások valós, ellenőrzött programkínálatán, látványosságain, strandjain és kulturális élményein** alapuljanak.

A rendszer 6 egymásra épülő fázisban működik:

```text
┌────────────────────────────────────────────────────────┐
│ 1. CONNECTORS (Külső Források)                         │
│    OSM Overpass | Wikidata SPARQL | Wikipedia | Google │
└───────────────────────────┬────────────────────────────┘
                            │ Raw Ingestion
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. RAW DATA STORE & PROVENANCE                         │
│    JSON Store + Supabase public.raw_source_records     │
└───────────────────────────┬────────────────────────────┘
                            │ QID + Haversine + Jaccard
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. ENTITY RESOLUTION & DEDUPLICATION                   │
│    Több forrásból származó rekordok egyesítése         │
└───────────────────────────┬────────────────────────────┘
                            │ Multi-Dimensional Enrichment
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. DATA ENRICHMENT & EXPERIENCE MODELING               │
│    Időbeli slotok, időjárás-állóság, perszóna címkék   │
└───────────────────────────┬────────────────────────────┘
                            │ Rollup & Caching
                            ▼
┌────────────────────────────────────────────────────────┐
│ 5. DESTINATION PROFILER & ULTRA-FAST CACHE             │
│    L1 Memória (<1ms) + L2 Supabase + L3 Lemez          │
└───────────────────────────┬────────────────────────────┘
                            │ Instant Matcher & Routing
                            ▼
┌────────────────────────────────────────────────────────┐
│ 6. REQUEST-TIME INTEGRATION                            │
│    Destination Matcher Kártyák & Sétálható Útiterv     │
└────────────────────────────────────────────────────────┘
```

## 🧱 A 6 Fázis Architektúrája

### 1. Fázis: Külső Forrás Csatlakozók (Connectors)
* **OpenStreetMap (OSM Overpass BBox):** Földrajzi koordináták, nyilvános strandok, kilátók, műemlékek, világítótornyok, terek és parkok kinyerése ODbL licenccel.
* **Wikidata SPARQL:** Ontológiai besorolás (templom, múzeum, stadion, palota), Wikimedia Commons szabad kép URL-ek, többnyelvű címkék.
* **Wikipedia Geosearch REST API:** Koordináták alapján releváns szócikkek összefoglalói (extract) és narratív leírásai a kártyákhoz.
* **Google Maps Scraper (Playwright):** 0 Ft API költségű, headless Chromium alapú böngészős adatgyűjtő automatikus GDPR consent kezeléssel, valós csillagértékelésekkel és véleményszámokkal.

### 2. Fázis: Nyers Adattár (Raw Data Store)
* Minden forrásból beérkező payload módosítás nélkül elmentésre kerül JSON formátumban és a Supabase `public.raw_source_records` táblájában.
* Szigorú metaadatok (provenance): forrás neve, külső azonosító, licenc, lekérdezési időbélyeg és parser verzió.

### 3. Fázis: Entitás Feloldás & Deduplikáció (Entity Resolution)
* **QID összekapcsolás:** Determinisztikus összekötés, ha az OSM rekord tartalmaz `wikidata: "Q..."` hivatkozást.
* **Térbeli & Szöveges szűrés:** 200 méteren belüli Haversine távolság és Jaccard token hasonlóság kombinációja.
* Kanonikus entitások előállítása egyedi `entity_id` azonosítóval.

### 4. Fázis: Adatgazdagítás & Élménymodellezés
* **Idősávok & Időtartamok:** Látogatási idők (0.5h – 3.5h) és optimális idősávok (`morning`, `afternoon`, `sunset`, `evening`).
* **Környezeti profil:** `indoor` (rain safe esőbiztos helyszínek) vs `outdoor` vs `mixed`.
* **Árkategóriák:** `free`, `budget`, `moderate`, `premium`.
* **Utazói perszónák:** `culture_aficionado`, `solo_explorer`, `family_friendly`, `couples_romantic`, `foodie_local`, `beach_seeker`.
* **Sétálhatósági Gráf:** 500 méteren belüli szomszédok feltérképezése a gyalogos útiterv-készítéshez.

### 5. Fázis: Profil Generátor & Ultra-Gyors Cache
* Többszintű, rekurzióbiztos gyorsítótár:
  1. **L1 Memória:** Python szótár < 0.01 ms lekérdezési idővel, negatív gyorsítótárazással (`None` eltárolása nem profilozott városokhoz a felesleges ismételt lekérdezések elkerülésére).
  2. **L2 Helyi Lemezes Cache:** `data/experience_profiles/{id}.json` (<0.1 ms gyors elérés, még a hálózati réteg előtt).
  3. **L3 Távoli Supabase:** `public.destination_experience_profiles` tábla perzisztens tárolásra.
  4. **L4 Fallback Generátor:** POI cache-ből és `maps_service`-ből történő profilozás `check_experience_engine=False` védelemmel, kizárva a kölcsönös rekurziót. Lásd: [[destination-search-stability-and-cache-optimization]].

### 6. Fázis: Kérés-idejű Integráció
* **Destination Matcher:** A desztinációs kártyák a felületen azonnal megjelenítik a valós programok számát, kiemelt látnivalókat, a Vibe profilt és a Level 2 koszinusz illeszkedési pontszámot.
* **Személyre Szabott Ajánló Motor („Ezeket ajánljuk nektek”):** Kanonikus élmények rangsorolása `fit_score` és magyar nyelvű ajánlási indoklás kíséretében.
* **Complete Trip Generator:** Intelligens napi útiterv generálás a sétálhatósági gráf alapján, a felhasználó által megadott napi idősávokhoz (`day_start`, `day_end`) és sétakorláthoz (`max_walking_minutes`) igazítva.
* **Automatikus Tranzit Ajánlások:** Túl nagy séta-távolság esetén automatikus közlekedési/taxi javaslat beillesztése.
* **Kiszolgáló REST Végpontok:** `/api/v2/destinations/{id}/experience-profile`, `/api/v2/destinations/{id}/activities`, `/api/v2/destinations/{id}/itinerary`.
