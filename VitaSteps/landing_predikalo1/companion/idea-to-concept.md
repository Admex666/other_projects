# 🥾 Hiking Companion – az ötlettől az MVP-koncepcióig

## 1. Honnan indultunk? – A probléma

A kiinduló kérdés az volt, hogy melyek az egyéni gyalogtúrák szervezésének legnagyobb painpointjai, különösen többnapos túráknál.

A sok lehetséges probléma közül végül egy szűkebb, konkrétabb területre fókuszáltunk:

Az útvonal, a saját gyalogtempó, a tömegközlekedés, a pihenők és az időzítés összehangolása.

A probléma lényege, hogy ezeket jelenleg többnyire külön-külön kell megtervezni:

- Mikor indulok otthonról?
- Melyik járattal jutok el a túra kezdőpontjához?
- Reálisan mennyi idő alatt teljesítem az útvonalat?
- Mennyi és milyen hosszú pihenőt iktathatok be?
- Melyik járatot érem el a célállomásról hazafelé?
- Mi történik, ha gyorsabb vagy lassabb vagyok a tervezettnél?

Ez sok manuális keresést és számolgatást igényel.

## 2. Hova jutottunk? – A termékkoncepció

Egy Python-alapú Hiking Companion, amely egy adott túraútvonalhoz automatikusan elkészíti a teljes, otthontól otthonig tartó logisztikai tervet.

Nem újabb térképes vagy túraútvonal-tervező alkalmazást akarunk készíteni.

A cél egy olyan döntéstámogató eszköz, amely összekapcsolja:

1. A tömegközlekedési menetrendeket.
2. A túra útvonalát és szintadatait.
3. A felhasználó saját gyalogtempóját.
4. A pihenőket és időbeli puffereket.
5. A hazafelé közlekedő járatok lehetőségeit.

## 3. Az első MVP – Egynapos túrák

Egyelőre kizárólag egynapos túrákkal foglalkozunk. Az útvonalat adottnak vesszük, tehát a felhasználó választja ki vagy tölti be.

### Felhasználói inputok

| Input                       | Mit ad meg?                               |
| --------------------------- | ----------------------------------------- |
| Otthoni kiindulópont        | Honnan indul és hova szeretne visszajutni |
| Túra kezdőpontja            | Az útvonal indulási helye                 |
| Túra végpontja              | Az útvonal érkezési helye                 |
| Útvonal                     | Előre adott útvonal / GPX                 |
| Indulási időintervallum     | Mikor indulhat el otthonról               |
| Hazaérkezési időintervallum | Mikorra szeretne hazaérni                 |
| Sétatempó                   | Saját átlagos tempója sík terepen         |
| Pihenők száma               | Minimum és maximum                        |
| Pihenők hossza              | Minimum és maximum időtartam              |

### 4. A számítási logika

A legfontosabb alapelv az általad javasolt Energy Kilometers formula:

\\[ EK = D + \frac{E}{95} \\]

- \\(D\\): tényleges távolság km-ben
- \\(E\\): pozitív szintemelkedés méterben
- 95 méter emelkedés = 1 extra energia-kilométer.

A becsült gyaloglási idő:

\\[ T = \frac{EK}{v} \\]

Ahol \\(v\\) a felhasználó sík terepen mért tempója.

Ehhez hozzáadjuk a pihenőket és a szükséges időbeli puffereket.

### 5. Mi történik a háttérben?

1. Odaút megtervezése

   Megkeresi az otthonról a túra kezdőpontjához induló járatokat a megadott indulási időintervallumban.
2. Túra kiszámítása

   Feldolgozza az útvonal távolságát és szintemelkedését, majd kiszámolja az energy kilometert és a várható gyaloglási időt.
3. Pihenők és pufferek optimalizálása

   A megadott minimumok és maximumok között olyan pihenőstratégiát keres, amely lehetővé teszi a kényelmes és reális teljesítést.
4. Hazautazás megtervezése

   Megkeresi az érkezési pontról hazafelé induló járatokat, figyelembe véve a gyaloglás és a pihenők lehetséges időigényét.
5. Alternatív forgatókönyvek

   Megvizsgálja, mi történik, ha gyorsabban vagy lassabban haladunk, illetve ha nem érjük el az eredetileg tervezett járatot.

## 6. Milyen adatforrásokra építhetünk Magyarországon?

| Adat                               | Lehetséges forrás                   |
| ---------------------------------- | ----------------------------------- |
| Túraútvonalak, turistautak         | OpenStreetMap, Turistautak.hu       |
| Közösségi közlekedés               | MÁV / Volán menetrendi adatok, GTFS |
| Domborzati adatok                  | SRTM, EU-DEM                        |
| Szállások, infrastruktúra (később) | OSM, MTSZ, kézi adatbázis           |

A menetrendi adatok tényleges hozzáférhetősége, frissessége és felhasználási feltételei még ellenőrzendők.

## 7. Milyen outputot szeretnénk?

Nem egy egyszerű menetidő-kalkulátort, hanem egy komplett, összehasonlítható túratervet.

Például:

## Túraterv – Példa

Ajánlott forgatókönyv

Odaút

- 07:12 – indulás otthonról
- 08:35 – érkezés a túra kezdőpontjához

Túra

- 18 km tényleges távolság
- 450 m pozitív szintemelkedés
- 22,74 energy km
- 4 km/h sík tempó
- 5 óra 41 perc becsült gyaloglás
- Optimalizált pihenők és pufferek

Hazautazás

- 15:45 – várható érkezés a célállomáshoz
- 16:10 – lehetséges járat
- 17:35 – hazaérkezés

Alternatív forgatókönyvek

| Forgatókönyv   | Várható eredmény         |
| -------------- | ------------------------ |
| Gyorsabb tempó | Korábbi hazautazás       |
| Normál tempó   | Tervezett járat          |
| Lassabb tempó  | Következő elérhető járat |

A fenti menetrendek és számok kizárólag szemléltető példák, nem valós járatok vagy számítások.

Az output további elemei:

- Teljes idővonal otthontól otthonig.
- Alternatív oda- és hazautazási lehetőségek.
- Pihenők optimális elhelyezése.
- Járatlekésési kockázatok.
- Biztonsági időtartalék.
- Térképes útvonal és szintprofil.

## 8. Hol tartunk, és mi a következő lépés?



Koncepció kialakítva

MVP specifikáció hátravan