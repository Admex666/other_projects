---
id: ADR-009-experience-activity-intelligence-engine
type: decision
name: "ADR-009: Architecture of the Experience & Activity Intelligence Engine"
status: accepted

description: Döntés a többforrásos (OSM, Wikidata, Wikipedia, Google Maps) nyílt adatgyűjtési, deduplikációs, élménymodellezési és gyorsítótárazási architektúra bevezetéséről az Optivoyában.

related:
  - "[[experience-intelligence-engine]]"
  - "[[experience-graph-modeling]]"
  - "[[experience-entity]]"
  - "[[ADR-001-unified-trip-architecture]]"
  - "[[ADR-008-supabase-cloud-database]]"

used_by:
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"
---

# 📜 Decision: ADR-009 — Architecture of the Experience & Activity Intelligence Engine

## 📌 Kontextus & Problémafelvetés
Az Optivoya utazástervező döntési motorja eddig elsősorban repülőjárat-árakra, szállásköltségekre, éghajlati mutatókra és közbiztonsági indexekre támaszkodott. Ugyanakkor egy utazó vagy B2B utazási tanácsadó számára lehetetlen érdemben desztinációt választani és teljes utazást értékelni a **helyszínen elérhető programok, látványosságok, strandok, kilátók és kulturális élmények** figyelembe vétele nélkül.

A meglévő megoldások korlátai:
1. A fizetős Google Places API költségei tömeges keresésnél fenntarthatatlanok lennének.
2. A mesterséges dummy POI adatok sértik a `[[honest-scraping-policy]]` és `[[ANTI_AI_SLOP_POLICY]]` elveket.
3. Egyetlen adatforrás sem nyújt egyszerre pontos koordinátákat, valós értékeléseket, szabad képeket és kulturális leírásokat.

## 💡 A Meghozott Döntés
Bevezetjük a **6 Fázisú Élmény- és Aktivitás-Intelligencia Rendszert**:
1. **Fázis 1 — Connectors:** 4 kiegészítő forrás összekapcsolása (OSM Overpass BBox térbeli indexelés + Wikidata SPARQL ontológia + Wikipedia Geosearch leírások + nyílt Playwright Google Maps scraper 0 Ft API költséggel).
2. **Fázis 2 — Raw Data Store & Supabase:** Zero-data-loss nyers JSON tárolás lokálisan és a Supabase felhő `public.raw_source_records` táblájában.
3. **Fázis 3 — Entity Resolution:** Térbeli (Haversine $\le 200\text{ m}$) és szöveges Jaccard token hasonlóság alapú deduplikáció és Wikidata QID összerendelés.
4. **Fázis 4 — Enrichment & Experience Modeling:** Látogatási időtartamok, idősávok, esőbiztosság, árkategóriák, utazói perszóna címkék és 500 méteres gyalogos szomszédsági gráf (`nearby_walkable_entities`) felépítése.
5. **Fázis 5 — Profiler & Ultra-Fast Cache:** L1 memóriagyorsítótár (< 1 ms), L2 Supabase Cloud és L3 lemezes perzisztencia.
6. **Fázis 6 — Request-Time Integration:** A Destination Matcher kártyák gazdagítása és a gyalogos szomszédsági gráfra épülő többnapos útiterv generálás.

## ⚖️ Következmények & Előnyök
* **Valós, gazdag adatok:** A korábbi mock POI-k helyett minden városban több száz valós, értékelt program áll rendelkezésre.
* **0 Ft API költség:** Nincs szükség fizetős Google Places API kulcsra.
* **Koherens útiterv:** A gyalogos szomszédsági gráf megelőzi a kaotikus városi ingázást (a délelőtti és délutáni programok 50–300 méterre vannak egymástól).
* **Minimális késleltetés (< 2 ms):** Az L1 memóriacache révén a felhasználói keresések alatt nincs külső hálózati késleltetés.
