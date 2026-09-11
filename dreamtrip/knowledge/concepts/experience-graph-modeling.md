---
id: experience-graph-modeling
type: concept
name: Experience Graph Modeling & Multi-Source Synthesis
status: active

description: A nyers térbeli, szemantikai, enciklopédikus és kereskedelmi forrásokból szintetizált, többdimenziós utazási élménygráf elméleti és gyakorlati modellje az Optivoyában.

related:
  - "[[experience-intelligence-engine]]"
  - "[[experience-ingestion-pipeline]]"
  - "[[experience-entity]]"
  - "[[unified-trip-model]]"
  - "[[guided-progressive-decision-flow]]"

used_by:
  - "[[destination-matching]]"
  - "[[itinerary-optimization]]"
---

# 💡 Concept: Experience Graph Modeling & Multi-Source Synthesis

A hagyományos online utazástervezők és járatkeresők az úticélokat csupán repülőterek és szállodák koordinátáiként kezelik. Az Optivoya **Élménygráf Modellezése** szerint egy desztináció valódi vonzerejét és illeszkedését a rajta végrehajtható élmények struktúrája, sűrűsége és minősége határozza meg.

## 🎯 Miért szükséges a többforrásos szintézis?

Egyetlen külső adatbázis sem rendelkezik a teljes igazsággal egy városról:
1. **OpenStreetMap (OSM):** Kiváló geometriai és infrastruktúra-adatok (szabad strandok, kilátók, műemlékek, világítótornyok), de hiányzik a népszerűség és a szubjektív minőségérzet.
2. **Wikidata:** Formális ontológia és gazdag szemantika (UNESCO besorolás, entitás típusok, szabad Commons képek), de nincs benne látogatási élmény vagy élő értékelés.
3. **Wikipedia:** Autentikus kulturális leírások és kontextus, de nem strukturált adatbázis.
4. **Google Maps:** Hatalmas volumenű felhasználói vélemény, csillagértékelés és népszerűség, de zárt rendszer és hiányzik belőle a mély kulturális ontológia.

A négy forrás összeolvasztásával egy **öntisztuló, magasan ellenőrzött élménygráf** jön létre.

## 📐 A Modellezés 5 Alappillére

### 1. Zero Data Loss Nyers Tárolás (Raw Ingestion)
Mielőtt bármilyen átalakítás vagy szűrés történne, minden forrás válasza változatlanul elmentésre kerül szigorú időbélyeggel és verziózással a Supabase `public.raw_source_records` táblájába, lehetővé téve a parser-szabályok utólagos módosítását újbóli külső lekérdezések nélkül.

### 2. Determinisztikus & Térbeli Entitás-Feloldás
* **QID azonosság:** Ha az OSM entitás tartalmazza a `wikidata: "Q..."` azonosítót, az összekapcsolás 100%-os biztonságú.
* **Térbeli közelség & Névhasonlóság:** A fennmaradó elemeket a $\le 200\text{ méteres}$ Haversine távolság és a normalizált Jaccard token átfedés ($\ge 0.35$) alapján csoportosítjuk klaszterekbe.

### 3. Többdimenziós Élmény-Klasszifikáció
Minden kanonikus entitás a következő dimenziók mentén kerül modellezésre:
* **Időbeli dimenzió:** Becsült látogatási időtartam és optimális idősáv (`morning`, `afternoon`, `sunset`, `evening`, `anytime`).
* **Környezeti & Időjárási dimenzió:** Beltéri (esőbiztos, `rain_safe`), Kültéri (napfényfüggő, `sun_dependent`) vagy Vegyes.
* **Költségvetési dimenzió:** `free` (közterek, szabad strandok), `budget` (<10 € belépők), `moderate`, `premium` (hajóbérlés, túrák).
* **Utazói perszónák:** `culture_aficionado`, `solo_explorer`, `family_friendly`, `couples_romantic`, `foodie_local`, `beach_seeker`.

### 4. Megbízhatósági Motor (Quality & Confidence Engine)
A helyszínekhez 0.0 és 1.0 közötti bizalmi pontszám tartozik:
* **3+ forrásból igazolt helyszín:** 0.85 – 0.98 pontszám (Tier 1 Flagship).
* **2 forrásból igazolt vagy 1000+ véleményes:** 0.70 – 0.84 pontszám (Tier 2 Recommended).
* **Egyetlen forrásból származó kisebb helyszín:** 0.60 pontszám (Tier 3 Supplemental).

### 5. Sétálhatósági Gráf & Útiterv-Párosítás (Proximity Graph)
A helyszínek közötti $\le 500\text{ méteres}$ gyalogos kapcsolatok gráffá rendezése biztosítja, hogy a generált napi útiterv egymást logikusan követő, kis távolságú sétákból álljon, elkerülve a kaotikus városi ingázást.
