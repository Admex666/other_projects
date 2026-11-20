# DREAMTRIP – PROJECT HANDOVER
## Event Intelligence Engine és a következő fejlesztési fázis

**Projekt:** `Admex666/other_projects/dreamtrip`  
**Repository:** https://github.com/Admex666/other_projects  
**Projektmappa:** `dreamtrip/`  
**Handover célja:** A jelenlegi projektállapot és a következő fejlesztési irány átadása egy másik AI-asszisztensnek vagy fejlesztőnek.  
**Státusz:** Architektúra-feltárás megtörtént, új fejlesztési irány meghatározása folyamatban. Kódmódosítás még nem történt.

---

# 1. A projekt célja

A Dreamtrip célja egy olyan intelligens utazástervező rendszer létrehozása, amely nem pusztán repülőjegyeket, szállásokat és klasszikus turistalátványosságokat keres.

A rendszernek olyan utazásokat kell tudnia összeállítani, amelyek az adott időpontban elérhető, valóban érdekes és releváns élményekre épülnek.

A hangsúly:

- Egyedi és különleges programokon.
- Helyi, autentikus élményeken.
- Koncerteken, bulikon, fesztiválokon és kulturális eseményeken.
- Gasztronómiai programokon és helyi különlegességeken.
- Jó ár-érték arányon.
- A teljes utazási költség optimalizálásán.
- A programok tényleges megvalósíthatóságán.

A cél nem egy újabb általános utazási ajánló, hanem egy olyan rendszer, amely képes felismerni, hogy egy adott városban, egy adott időpontban miért érdemes odautazni.

## 1.1. Fontos termékfilozófia

A legolcsóbb program nem feltétlenül a legjobb program.

A rendszer különbséget tegyen:
- Olcsó, de gyenge élmény.
- Közepes árú, kiváló ár-érték arányú élmény.
- Drágább, de igazán különleges élmény.

A felhasználó számára a teljes utazás értéke számít, nem kizárólag a repülőjegy ára.

Például egy olcsó repülőjegy önmagában nem jó ajánlat, ha a célállomáson nincs érdekes program, drága a közlekedés, vagy az esemény után nem lehet visszajutni a szállásra.

---

# 2. A jelenlegi projektállapot

A GitHub-repository és a releváns dokumentumok, illetve kódfájlok áttekintése megtörtént.

**Repository:**  
https://github.com/Admex666/other_projects/tree/main/dreamtrip

A projektben már létezik egy fontos alaparchitektúra:

**ADR-009 – Experience & Activity Intelligence Engine**

Ez azt jelenti, hogy nem egy teljesen új élménykereső rendszert kell létrehozni. A meglévő megoldást kell továbbfejleszteni egy új, időfüggő eseményfelderítő réteggel.

## 2.1. Már meglévő komponensek

A vizsgálat során az alábbi elemeket azonosítottuk:

| Komponens | Feladat |
|---|---|
| OpenStreetMap / Overpass | Helyszínek, POI-k és földrajzi objektumok keresése |
| Wikidata | Szemantikus kategorizálás és entitásadatok |
| Wikipedia | Leírások és háttérinformációk |
| Google Maps scraper | Értékelések és véleményadatok gyűjtése |
| Experience Intelligence Service | Élmények feldolgozása és intelligens kezelése |
| Experience connectors | Külső adatforrások integrációja |
| Vibe profiling | Helyszínek és élmények karakterének meghatározása |
| Itinerary generation | Többnapos útiterv összeállítása |

A rendszer tehát már rendelkezik egy evergreen, azaz nem feltétlenül dátumhoz kötött élménykatalógussal.

## 2.2. Áttekintett fájlok

- `AGENTS.md`
- `PROJECT_MAP.md`
- `package.json`
- `requirements.txt`
- `supabase_experience_schema.sql`
- `knowledge/INDEX.md`
- `knowledge/decisions/ADR-009-experience-activity-intelligence-engine.md`
- `knowledge/processes/experience-ingestion-pipeline.md`
- `knowledge/systems/experience-intelligence-engine.md`
- `app/services/experience_intelligence_service.py`
- `app/services/experience/connectors/base.py`
- `app/services/experience/connectors/osm_connector.py`
- `knowledge/concepts/experience-vector-and-vibe-profiling.md`

A következő munkafázis előtt a fejlesztőnek ismét ellenőriznie kell a repository aktuális állapotát, mert az áttekintés óta történhettek módosítások.

---

# 3. A legfontosabb hiányosság

A jelenlegi rendszer alapvetően helyszíneket és állandó élményeket tud keresni.

Ez nem ugyanaz, mint egy konkrét időpontra szóló esemény keresése.

Példák:

| Meglévő rendszer által megtalálható | Új rendszer által keresendő |
|---|---|
| Koncerthelyszín | Koncert december 31-én |
| Bár vagy szórakozóhely | Szilveszteri party konkrét kezdési idővel |
| Stadion | Konkrét mérkőzés |
| Színház | Adott napi előadás |
| Helyi piac | Különleges ünnepi vásár |
| Étterem | Adott napi gasztronómiai esemény |
| Fesztiválhelyszín | Ténylegesen megrendezett fesztivál |

A rendszernek tehát nem elég tudnia, hogy egy hely létezik.

Azt is tudnia kell, hogy:
- Mi történik ott?
- Mikor történik?
- Milyen időpontban kezdődik és ér véget?
- Mennyibe kerül?
- Hol lehet jegyet venni?
- Mennyire biztos, hogy az esemény ténylegesen megrendezésre kerül?
- Milyen forrás igazolja az adatokat?
- Hogyan lehet oda- és visszajutni?

**Ez a Dreamtrip következő nagy fejlesztési iránya.**

---

# 4. Javasolt új architektúra

A meglévő Experience Intelligence Engine maradjon meg.

Erre épüljön egy külön:

# Event Intelligence Engine

A két rendszer együtt működjön.

### A. Evergreen Experience Engine

A meglévő ADR-009 szerinti rendszer.

Feladata:
- POI-k és látványosságok.
- Hidden gems.
- Helyi gasztronómia.
- Állandó programlehetőségek.
- Természeti és kulturális helyszínek.
- Helyszínek vibe- és minőségprofilozása.

### B. Event Intelligence Engine

Az új fejlesztés.

Feladata:
- Koncertek.
- Buli- és nightlife-események.
- Fesztiválok.
- Sportesemények.
- Gasztronómiai rendezvények.
- Helyi kulturális programok.
- Ünnepi és szezonális események.
- Szilveszteri és egyéb különleges események.
- Workshopok és közösségi programok.

### C. Unified Recommendation Engine

A két rendszer eredményeit közös ajánlási rendszer dolgozza fel.

A cél az, hogy ne különálló listákat kapjon a felhasználó, hanem az érdeklődéséhez, az utazási időpontjához és a költségkeretéhez illeszkedő ajánlatokat.

### D. Trip & Itinerary Optimizer

Az ajánlott élményekből megvalósítható utazási tervet állít össze.

Figyelembe veszi:
- Repülőjegy és szállás költsége.
- Programok belépődíja.
- Helyi közlekedés.
- Távolságok és menetidők.
- Nyitvatartás.
- Események kezdési és befejezési időpontja.
- Átszállások.
- Éjszakai hazajutás.
- Napi programok közötti földrajzi és időbeli kompatibilitás.

---

# 5. Eseményadatok – lehetséges adatforrások

A rendszer több adatforrásból dolgozzon, ne függjön egyetlen szolgáltatótól.

| Forrás | Elsődleges felhasználás |
|---|---|
| Bandsintown | Koncertek, fellépők |
| Songkick | Koncertek és turnék |
| Eventbrite | Helyi rendezvények, workshopok, partik |
| Meetup | Közösségi programok |
| Ticketmaster | Nagyobb koncertek és sportesemények |
| Helyi önkormányzatok | Városi rendezvények, ünnepi programok |
| Turisztikai oldalak | Helyi események és szezonális programok |
| Kulturális intézmények | Kiállítások, előadások, koncertek |
| Venue-weboldalak | Konkrét helyszínek programnaptárai |
| Keresőmotoros discovery | Helyi, kisebb és kevésbé ismert események |

Fontos: az adatforrások integrációjánál ellenőrizni kell az API-hozzáférést, a felhasználási feltételeket, az adatlicencet és a scrapingre vonatkozó szabályokat.

Nem szabad automatikusan feltételezni, hogy minden weboldal szabadon scrapelhető.

## 5.1. Különösen fontos: helyi események

A rendszer ne csak nemzetközi jegyértékesítő oldalakat használjon.

Sok érdekes program csak helyi nyelvű oldalakon található meg.

Például:
- Városi szilveszteri rendezvények.
- Ingyenes szabadtéri koncertek.
- Helyi gasztrofesztiválok.
- Kisebb klubok programjai.
- Hagyományos ünnepi események.
- Helyi közösségi rendezvények.

A keresésnek lehetőség szerint a célország és a célváros nyelvén is működnie kell.

---

# 6. Az eseményadatok megbízhatósága

Ez az egyik legfontosabb fejlesztési követelmény.

A rendszer semmilyen körülmények között ne mutasson egy korábbi rendezvényt úgy, mintha az aktuális évben is megrendezésre kerülne.

Például egy 2025-ös szilveszteri buli nem tekinthető automatikusan 2026-os eseménynek.

Minden eseményhez szükséges:
- Forrásazonosítás.
- Eredeti eseményoldal.
- Dátum és időpont.
- Utolsó ellenőrzés időpontja.
- Forrásból származó azonosító, ha van.
- Adatminőségi és bizonyossági érték.
- Esemény státusza.

Javasolt státuszok:
- `verified`
- `partially_verified`
- `unverified`
- `cancelled`
- `expired`
- `historical`

A `confidence_score` az adat megbízhatóságát jelentse, ne az esemény minőségét.

A két fogalmat külön kell kezelni.

## 6.1. Korábbi adatminőségi kockázat

A korábban vizsgált Experience Intelligence Service egyes esetekben fallback értékeket használhat hiányzó adatok esetén, például értékeléseknél, véleményszámoknál vagy becsült költségeknél.

Ezt külön ellenőrizni kell.

Az új eseményrendszerben nem szabad:
- Kitalált eseményárat megadni.
- Kitalált értékelést megjeleníteni.
- Nem ellenőrzött dátumot biztosként feltüntetni.
- Régi eseményből automatikusan új eseményt generálni.
- Nem létező foglalási vagy jegyvásárlási linket létrehozni.

A megoldást össze kell hangolni a meglévő `ADR-004 Honest Scraping Policy` elveivel.

---

# 7. Javasolt eseményadatmodell

Az események külön entitásként szerepeljenek, ne egyszerűen a meglévő `experience_entities` táblába kerüljenek.

Ennek oka, hogy egy esemény időbeli életciklusa teljesen más, mint egy állandó helyszíné.

Javasolt új `events` tábla:

| Mező | Funkció |
|---|---|
| `id` | Belső azonosító |
| `event_id` | Egyedi eseményazonosító |
| `destination_id` | Célállomás |
| `title` | Esemény neve |
| `description` | Leírás |
| `category` | Főkategória |
| `subcategory` | Alkategória |
| `venue_name` | Helyszín |
| `latitude` / `longitude` | Koordináták |
| `starts_at` | Kezdés |
| `ends_at` | Befejezés |
| `price_min` / `price_max` | Árintervallum |
| `currency` | Pénznem |
| `is_free` | Ingyenes-e |
| `booking_url` | Jegyvásárlás |
| `source_url` | Eredeti forrás |
| `source_name` | Adatforrás |
| `source_event_id` | Forrásazonosító |
| `confidence_score` | Adatmegbízhatóság |
| `status` | Esemény státusza |
| `last_verified_at` | Utolsó ellenőrzés |
| `retrieved_at` | Lekérdezés időpontja |
| `raw_payload` | Eredeti forrásadat JSON formátumban |
| `created_at` / `updated_at` | Létrehozás és módosítás |

További lehetséges táblák:

- `event_sources`: az eseményhez kapcsolódó források és bizonyítékok.
- `event_occurrences`: ismétlődő események konkrét dátumai.
- `event_user_feedback`: felhasználói visszajelzések.
- `user_travel_preferences`: utazási és programpreferenciák.

A pontos adatmodellt a jelenlegi Supabase-séma és a meglévő migrációs konvenciók vizsgálata után kell véglegesíteni.

**Technikai követelmény:** a dátumokat és időpontokat időzónával együtt kell kezelni. A célállomás helyi időzónája legyen az események megjelenítésének alapja.

---

# 8. Ajánlási és rangsorolási modell

A rendszer ne egyszerűen népszerűség szerint rangsoroljon.

Javasolt értékelési dimenziók:

| Dimenzió | Mit mér? |
|---|---|
| Preference fit | Mennyire illik a felhasználó érdeklődéséhez? |
| Authenticity | Mennyire helyi és autentikus? |
| Uniqueness | Mennyire különleges? |
| Value for money | Mennyire jó az ár-érték arány? |
| Social atmosphere | Mennyire társasági vagy közösségi élmény? |
| Seasonality | Mennyire releváns az adott időszakban? |
| Accessibility | Mennyire könnyen megközelíthető? |
| Time fit | Illeszkedik-e az utazás dátumához és időbeosztásához? |

A rangsorolás során az adatmegbízhatóságot is figyelembe kell venni.

Fontos, hogy a minőségi rangsor és az adatbizonyosság külön dimenzió maradjon.

Egy nagyon jó, de nem ellenőrzött esemény nem jelenhet meg ugyanolyan biztos ajánlatként, mint egy hivatalos forrásból megerősített rendezvény.

---

# 9. A felhasználó utazási preferenciái

A beszélgetések alapján az alábbi preferenciák tekinthetők kiinduló hipotézisnek, nem végleges felhasználói profilnak:

| Preferencia | Ideiglenes prioritás |
|---|---:|
| Ár-érték arány | 95/100 |
| Különleges, egyedi programok | 95/100 |
| Helyi, autentikus élmények | 90/100 |
| Éjszakai élet és társasági programok | 80/100 |
| Gasztronómia | 75/100 |
| Kultúra | 65/100 |
| Klasszikus turistalátványosságok | 20/100 |
| Strandolás | 5/100 |

Ezeket később tényleges felhasználói visszajelzések alapján kell tanítani és módosítani.

Ne építsük be ezeket végleges, merev szabályként.

---

# 10. Különösen fontos: közlekedés és megvalósíthatóság

A Dreamtrip egyik fontos megkülönböztető eleme lehet, hogy nemcsak az eseményt ajánlja, hanem annak tényleges elérhetőségét is vizsgálja.

Például:

Egy koncert lehet kiváló, de ha:
- 35 kilométerre van a szállástól,
- éjfél után ér véget,
- nincs éjszakai busz,
- a taxi 60 euróba kerül,

akkor nem feltétlenül jó ajánlat.

Ezért a rendszernek külön kell értékelnie:
- Odaút.
- Visszaút.
- Közösségi közlekedés.
- Menetidő.
- Átszállások.
- Éjszakai közlekedés.
- Alternatív közlekedési lehetőségek.
- Teljes programköltség.

A felhasználó számára a megvalósítható program fontosabb, mint egy önmagában jól hangzó esemény.

---

# 11. Javasolt fejlesztési roadmap

## P0 – Event Intelligence MVP

Elsődleges cél: működő, dátumspecifikus eseménykeresés.

Feladatok:
1. A jelenlegi repository teljes releváns állapotának újbóli feltérképezése.
2. A meglévő ADR-ek és munkafolyamatok ellenőrzése.
3. Event Intelligence architektúra dokumentálása.
4. Eseményadatmodell megtervezése.
5. Adatforrás-regiszter létrehozása.
6. Legalább néhány megbízható eseményforrás integrálása.
7. Dátumspecifikus keresés.
8. Deduplikáció.
9. Forrásmegőrzés és bizonyossági érték.
10. Események frissítése és lejáratkezelése.
11. Alapvető személyre szabott rangsorolás.
12. Automatizált tesztek és QA.

A cél nem a lehető legtöbb esemény összegyűjtése, hanem a releváns és ellenőrizhető események megtalálása.

## P1 – Trip & Transport Intelligence

Feladatok:
- Közlekedési útvonalak és menetidők.
- Események és napi útiterv összehangolása.
- Nyitvatartási és időbeli korlátozások.
- Éjszakai hazajutás.
- Teljes költségoptimalizálás.

## P2 – Personalization & Learning

Feladatok:
- Like/dislike.
- Mentett programok.
- Elutasított ajánlatok.
- Preferenciák tanulása.
- Utazási profil.
- Személyre szabott eseményrangsorolás.
- Relevancia-visszacsatolás.

## P3 – Monitoring & Notifications

Feladatok:
- Eseményadatok rendszeres ellenőrzése.
- Lemondott vagy módosított események felismerése.
- Jegyárváltozás.
- Új események megjelenése.
- Értesítések.

---

# 12. Első MVP – javasolt célvárosok

Az első verzióban érdemes korlátozott számú európai várossal indulni.

Javasolt lista:

1. Budapest
2. Bécs
3. Prága
4. Krakkó
5. Róma
6. Barcelona
7. Lisszabon
8. Páfosz

Ez csak javasolt tesztkészlet, nem végleges döntés.

A cél az, hogy különböző típusú célállomásokon teszteljük:
- Nagyvárosi koncert- és nightlife-kínálat.
- Helyi kulturális események.
- Szezonális rendezvények.
- Kisebb turisztikai célpontok eseménykínálata.
- Eltérő közlekedési infrastruktúrák.

Mérési célként kezdetben városonként és dátumonként 10–20 releváns esemény keresése elképzelhető, de a minőség és az ellenőrizhetőség fontosabb a darabszámnál.

---

# 13. Javasolt dokumentáció

A fejlesztés előtt ellenőrizni kell, hogy az alábbi dokumentumok vagy ezek megfelelői léteznek-e már.

Javasolt új dokumentumok:

- `knowledge/decisions/ADR-011-event-intelligence-engine.md`
- `knowledge/systems/event-discovery-architecture.md`
- `knowledge/systems/event-source-registry.md`
- `knowledge/concepts/event-data-model.md`
- `knowledge/concepts/event-ranking-model.md`
- `knowledge/processes/event-discovery-pipeline.md`
- `knowledge/work/WORK-005-event-intelligence-mvp.md`

A pontos fájlneveket a repository jelenlegi struktúrájához kell igazítani.

Az ADR-011 feladata a fő architekturális döntések rögzítése.

A WORK-005 feladata a tényleges fejlesztési feladatok és azok elfogadási kritériumainak meghatározása.

---

# 14. Fejlesztési és minőségbiztosítási szabályok

A projekt meglévő `AGENTS.md` utasításait kötelező követni.

Különösen:
- A fejlesztési feladatokat a projekt által előírt specialistákra kell bontani.
- A meglévő architektúrát nem szabad indokolatlanul lecserélni.
- Új komponenseknek illeszkedniük kell a meglévő struktúrához.
- A dokumentációt a kódváltozásokkal együtt kell frissíteni.
- QA és tesztelés szükséges.
- A hibás vagy bizonytalan adatokat nem szabad valós tényként feltüntetni.

A fejlesztés során először tervet kell készíteni, majd a feladatokat kisebb, ellenőrizhető egységekre bontani.

---

# 15. Következő konkrét lépések

A következő fejlesztési ciklus ajánlott sorrendje:

1. Repository aktuális állapotának ellenőrzése.
2. `AGENTS.md` és `PROJECT_MAP.md` ismételt áttekintése.
3. Az ADR-ek és a meglévő work itemek ellenőrzése.
4. A meglévő Experience Engine és a Supabase-séma kapcsolatainak feltérképezése.
5. Az eseményforrások technikai és licencelési lehetőségeinek vizsgálata.
6. ADR-011 elkészítése.
7. Az Event Intelligence MVP technikai specifikációja.
8. WORK-005 feladatbontás és elfogadási kritériumok.
9. A felhasználói termékpreferenciák véglegesítése.
10. Csak ezután kezdődjön a kódolás.

---

# 16. A termék irányának véglegesítéséhez szükséges kérdések

A fejlesztés megkezdése előtt három termékdöntést kell tisztázni.

**1. Milyen programokat keressen a rendszer?**

- Minden érdekes programot: koncertek, bulik, gasztronómia, sport, helyi események.
- Elsősorban koncerteket, bulikat és nightlife-programokat.
- Elsősorban autentikus helyi eseményeket, gasztronómiát és hidden gemeket.

**2. Mennyire legyen árérzékeny az ajánlórendszer?**

- Mindig a lehető legolcsóbb megoldás legyen az elsődleges.
- Erős árérzékenység, de különleges programért lehessen többet fizetni.
- Az élmény legyen az elsődleges, rugalmas költségkerettel.

**3. Mi legyen a termék elsődleges célja?**

- Először saját utazások támogatása, majd általánosítható termék.
- Már az elejétől általános, több felhasználós utazástervező termék.
- Elsősorban B2B megoldás.

Ezek a döntések befolyásolják az adatmodellt, a rangsorolást, az architektúrát és az MVP prioritásait.

---

# 17. Hivatkozások

**Repository és fontos fájlok:**

- [Dreamtrip repository](https://github.com/Admex666/other_projects/tree/main/dreamtrip)
- [AGENTS.md](https://github.com/Admex666/other_projects/blob/main/dreamtrip/AGENTS.md)
- [PROJECT_MAP.md](https://github.com/Admex666/other_projects/blob/main/dreamtrip/PROJECT_MAP.md)
- [ADR-009 – Experience & Activity Intelligence Engine](https://github.com/Admex666/other_projects/blob/main/dreamtrip/knowledge/decisions/ADR-009-experience-activity-intelligence-engine.md)
- [Experience ingestion pipeline](https://github.com/Admex666/other_projects/blob/main/dreamtrip/knowledge/processes/experience-ingestion-pipeline.md)
- [Experience Intelligence Service](https://github.com/Admex666/other_projects/blob/main/dreamtrip/app/services/experience_intelligence_service.py)
- [Supabase experience schema](https://github.com/Admex666/other_projects/blob/main/dreamtrip/supabase_experience_schema.sql)

---

# 18. Indító instrukció a következő AI-asszisztensnek

A handover alapján folytasd a Dreamtrip fejlesztési tervezését.

Ne kezdj azonnal kódolni.

Elsőként:
1. Nyisd meg a GitHub repository aktuális állapotát.
2. Ellenőrizd a `AGENTS.md`, `PROJECT_MAP.md`, az ADR-ek és a kapcsolódó work itemek tartalmát.
3. Vizsgáld meg, hogy az Event Intelligence Engine koncepcióból mi létezik már.
4. Kerüld a meglévő funkciók duplikálását.
5. Készíts egy, a jelenlegi kódhoz és adatmodellhez illeszkedő ADR-011 tervet.
6. Mutasd be a szükséges módosításokat, azok függőségeit és kockázatait.
7. A fejlesztési tervet bontsd kis, tesztelhető feladatokra.
8. A felhasználó három termékdöntését még kérdezd meg, mielőtt véglegesítenéd a rangsorolási és MVP-követelményeket.

**Fontos:** A jelen handover architekturális javaslatokat és korábbi repository-feltárási eredményeket tartalmaz. Nem jelenti azt, hogy az új Event Intelligence Engine már implementálva van. A GitHubon semmilyen módosítás nem történt a feltárás során.

**Végső cél:** A Dreamtrip legyen képes nemcsak azt megmondani, hogy hová érdemes utazni, hanem azt is, hogy az adott időpontban miért érdemes oda menni, milyen különleges élmények várják az utazót, és hogyan lehet ezeket a lehető legjobb ár-érték arány mellett ténylegesen megvalósítani.