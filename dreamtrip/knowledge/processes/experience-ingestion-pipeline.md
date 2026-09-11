---
id: experience-ingestion-pipeline
type: process
name: End-to-End Experience Ingestion & Profiling Workflow
status: active

description: A célállomások élmény- és programkínálatának többforrásos begyűjtési, nyers tárolási, összefésülési, gazdagítási és profilozási munkafolyamata.

related:
  - "[[experience-intelligence-engine]]"
  - "[[experience-graph-modeling]]"
  - "[[experience-entity]]"
  - "[[destination-matching]]"
  - "[[run-experience-pipeline]]"

used_by:
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
---

# 🔄 Process: End-to-End Experience Ingestion & Profiling Workflow

Ez a folyamat definiálja, hogyan alakul át egy új úticél (pl. Bari, Róma, Barcelona) a nyers külső webes és API lekérdezésekből egy élesben, azonnal lekérdezhető (<5ms) desztinációs élményprofillá és útitervvé.

```text
  [Seed: Név, Ország, Koordináták, Sugár]
                     │
                     ▼
  [1. Párhuzamos Adatgyűjtés: OSM, Wikidata, Wikipedia, Google Maps]
                     │
                     ▼
  [2. Nyers Adattár Mentés (JSON Store + Supabase public.raw_source_records)]
                     │
                     ▼
  [3. Entitás-feloldás & Klaszterezés (QID + Haversine <200m + Jaccard)]
                     │
                     ▼
  [4. Adatgazdagítás: Idősávok, Árkategóriák, Perszónák, Sétagráf]
                     │
                     ▼
  [5. Desztinációs Profil Generálás & Többszintű Gyorsítótárazás]
                     │
                     ▼
  [6. Kiszolgálás: Destination Matcher Kártyák & Sétálható Útiterv]
```

## 📋 A Folyamat Részletes Lépései

### 1. Lépés: Desztináció Inicializálás (Seed)
A folyamat a `DestinationSeed` objektummal indul: célállomás azonosító (pl. `IT_BARI`), név (`Bari`), ország (`Italy`), középponti koordináták és lekérdezési sugár (`radius_km: 15.0`).

### 2. Lépés: Külső Források Lekérdezése
* **OSMConnector:** Térbeli BBox indexeléssel lekéri a turisztikai, kulturális, természeti és strand objektumokat.
* **WikidataConnector:** SPARQL lekérdezéssel kinyeri a földrajzi ontológiát és Commons fotókat.
* **WikipediaConnector:** A hivatalos Wikipedia Geosearch API-val lekéri a koordináták körzetébe eső szócikkek összefoglalóit.
* **GoogleMapsConnector:** Playwright headless böngészővel begyűjti a népszerű helyszíneket csillagértékeléssel és véleményszámmal.

### 3. Lépés: Nyers Perzisztálás (Raw Store)
Minden beérkező rekord elmentésre kerül:
1. Lokális lemezes fájlba (`data/raw_sources/{dest_id}/{source}/`) azonnali inspekcióhoz.
2. A Supabase Cloud `public.raw_source_records` táblájába idempotens módon (`UNIQUE (destination_id, source, source_id)`).

### 4. Lépés: Entitás-feloldás és Klaszterezés
Az `EntityResolutionEngine` klaszterekbe rendezi az azonos helyszíneket:
* Determinisztikus összerendelés a közös Wikidata QID alapján.
* Térbeli távolság ($\le 200\text{ m}$) és névhasonlóság ($\ge 0.35$) kombinációja.
* Kanonikus entitások létrehozása ütközésmentes `entity_id` azonosítóval.

### 5. Lépés: Adatgazdagítás és Sétagráf Építés
Az `ExperienceEnricher` hozzárendeli az entitásokhoz:
* Tartózkodási időtartam és ideális napszak (`est_duration_hours`, `best_time_of_day`).
* Időjárás-érzékenység (`indoor_outdoor`, `weather_sensitivity`).
* Költségkeret (`price_level`).
* Utazói személyiség-címkék (`persona_tags`).
* 500 méteres szomszédsági gráf (`nearby_walkable_entities`).
* Mentés a Supabase `public.experience_entities` táblába.

### 6. Lépés: Profilozás és Gyorsítótárazás
A `DestinationProfiler` összesíti a statisztikákat:
* Kategória-eloszlás és top élmények összefoglalója.
* Perszóna illeszkedési százalékok és sétálhatósági index.
* Mentés a Supabase `public.destination_experience_profiles` táblába és az L1 memóriagyorsítótárba (`ExperienceMemoryCache`).

### 7. Lépés: Kérés-idejű Integráció
* A Destination Matcher a gyorsítótárból < 1 ms alatt hozzáilleszti a kártyákhoz az élményprofilt.
* Az `ExperienceTripGenerator` a szomszédsági gráf segítségével generál többnapos, sétálható útitervet.
