---
id: run-experience-pipeline
type: operation
name: Run Experience Ingestion & Profiling Pipeline
status: active

description: Operatív útmutató a többforrásos élmény- és aktivitás-begyűjtő, deduplikáló és Supabase szinkronizáló pipeline futtatásához tetszőleges célállomásra.

related:
  - "[[experience-intelligence-engine]]"
  - "[[experience-ingestion-pipeline]]"
  - "[[ADR-009-experience-activity-intelligence-engine]]"
  - "[[supabase-database]]"
  - "[[run-local-development]]"

used_by:
  - "[[destination-matching]]"
---

# 🛠️ Operation: Run Experience Ingestion & Profiling Pipeline

Ez az útmutató bemutatja, hogyan kell új célállomást feldolgozni vagy meglévő nyers adatokat újrafuttatni az Experience & Activity Intelligence Engine segítségével.

## 🚀 1. Új célállomás teljes feldolgozása (End-to-End)

Tetszőleges új város feldolgozása a 4 külső forrásból (OSM, Wikidata, Wikipedia, Google Maps), automatikus deduplikációval, gazdagítással és Supabase felhőbe mentéssel:

```bash
# Példa: Bari, Olaszország
python scripts/run_experience_pipeline.py --city Bari --country Italy --lat 41.1171 --lon 16.8719 --radius 15.0

# Példa: Róma, Olaszország
python scripts/run_experience_pipeline.py --city Rome --country Italy --lat 41.9028 --lon 12.4964 --radius 20.0
```

A parancs lefutása:
1. Lekéri az OSM, Wikidata, Wikipedia és Google Maps nyers adatokat.
2. Lementi őket a lokális lemezre és a Supabase `public.raw_source_records` táblába.
3. Lefuttatja az entitás-feloldást (`EntityResolutionEngine`).
4. Gazdagítja az adatokat idősávokkal, árkategóriákkal és sétagráffal (`ExperienceEnricher`).
5. Perzisztálja a kanonikus entitásokat a Supabase `public.experience_entities` táblába.
6. Legenerálja a desztinációs profilt és frissíti a memóriagyorsítótárat.

---

## ⚡ 2. Meglévő nyers adatok újrafeldolgozása (Offline Re-run)

Ha módosítottuk a deduplikációs vagy gazdagítási szabályokat, és nem akarunk újra külső forrásokat hívni:

```bash
python scripts/run_experience_pipeline.py --from-raw IT_BARI
```

---

## 🔍 3. Csak a csatlakozók diagnosztikája (Connectors Test)

Ha ellenőrizni szeretnénk, mit ad vissza a 4 külső forrás egy városra:

```bash
python scripts/test_experience_connectors.py --city Bari --country Italy --osm-limit 150 --wd-limit 100 --wp-limit 30 --gm-limit 30
```

---

## 🌐 4. REST API Végpontok Ellenőrzése

A futó szerveren (`http://localhost:8000`) közvetlenül elérhetők az alábbi végpontok:
* **Desztináció profil lekérése:** `GET /api/v2/destinations/IT_BARI/experience-profile`
* **Kanonikus aktivitások szűrése:** `GET /api/v2/destinations/IT_BARI/activities?category=culture_history`
* **Intelligens útiterv kérése:** `GET /api/v2/destinations/IT_BARI/itinerary?days=3`
