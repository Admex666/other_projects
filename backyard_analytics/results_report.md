# Backyard Ultra Esztergom 2026 - Részletes Adatelemzési Riport

Ez a riport a **Backyard Ultra Esztergom 2026** futóverseny részletes eredményeinek és köridő-dinamikájának statisztikai és gépi tanulás alapú elemzését tartalmazza.

---

## 1. Túlélési (Survival) Elemzés & Kiesési Eloszlás

A Backyard Ultra lényege a lemorzsolódás: mindenki kiesik, kivéve az egyetlen győztest (*"Last Man Standing"*). 

* **Összes induló száma:** 124 futó
* **Medián túlélés:** **13.0 kör** (Ez azt jelenti, hogy a mezőny fele legfeljebb 13 kört teljesített, azaz 13 órán át maradt versenyben, ami 87.2 km távnak felel meg).
* **Győztes:** **Keller Sándor**, aki **45 kört** teljesített (összesen **301.75 km**-t lefutva).

### Kaplan-Meier Túlélési Görbe következtetései:
A túlélési görbe ([Kaplan-Meier Görbe](file:///e:/Data/other_projects/backyard_analytics/plots/1_survival_curve.png)) megmutatja a kiesések dinamikáját:
* **Az első komoly töréspont:** A **2. és 4. kör** között látható, ahol a mezőny közel 25%-a esik ki. Sokan itt szembesülnek először a monotonitással vagy fizikai problémákkal.
* **A középmezőny kiesése:** A 6. és 12. kör között a mezőny újabb 30%-a adja fel a versenyt. A 12. kör (80,4 km, azaz közel egy dupla maraton) egy hatalmas lélektani határ.
* **A szűk elit ("Tail"):** A 24. kör (160,9 km, azaz 100 mérföld) után már csak a futók legszűkebb elitje (kevesebb mint 10%) marad versenyben, alkotva a túlélési görbe elnyúló, hosszú "farkát".

![Túlélési Görbe](file:///e:/Data/other_projects/backyard_analytics/plots/1_survival_curve.png)
![Kiesések eloszlása](file:///e:/Data/other_projects/backyard_analytics/plots/1_dropout_distribution.png)

---

## 2. Köridő Dinamika (Fáradás és Stratégia)

A köridők idősoros elemzése feltárja a futók tempó-stratégiáját és a fáradás mértékét.

* **Köridő Drift (Lassulás):** A versenyben maradó futók átlagosan **napi szinten 0,15 - 0,35 perc/kör** ütemben lassultak. 
* **Egyéni mintázatok:** 
  A top futók ([Köridő grafikon](file:///e:/Data/other_projects/backyard_analytics/plots/2_top5_pacing.png)) két fő csoportra oszthatók:
  1. *A rendkívül stabil gépek:* Keller Sándor és Válent Sándor szinte másodpercre pontosan azonos köridőket futottak (többnyire 44 és 52 perc között), hatalmas kontrollt mutatva.
  2. *A limiten egyensúlyozók:* Egyes futók a verseny késői szakaszában (30. kör után) veszélyesen közel kerültek a 60 perces limitsávhoz (55-58 perces körök), minimális pihenőidőt hagyva maguknak.
  
![Top 5 Pacing](file:///e:/Data/other_projects/backyard_analytics/plots/2_top5_pacing.png)
![Mezőny Pacing Trend](file:///e:/Data/other_projects/backyard_analytics/plots/2_field_pacing_trend.png)

---

## 3. Stratégia Klaszterek (Gépi Tanulás K-Means)

A futók köridő-statisztikáit (átlagidő, szórás, drift meredekség, minimális köridő és teljes körszám) standardizáltuk, majd **K-Means klaszterezéssel** 4 jól elkülöníthető stratégiai csoportba soroltuk őket:

1. **Steady Grinders (Stabil Túlélők):**
   * *Jellemzők:* Magas körszám, rendkívül alacsony köridő-ingadozás (szórás < 2.5 perc), mérsékelt tempó. 
   * *Stratégia:* Tudatosan nem futnak gyors köröket, a hangsúly a tökéletes regeneráción és az egyenletes ritmuson van.
2. **Fast Sprinters (Korai Kiégők):**
   * *Jellemzők:* Nagyon gyors korai köridők (gyakran 35-42 perc között), de alacsony végső körszám (< 10 kör).
   * *Hiba:* Túl sokat futottak ki magukból az elején, a túl hosszú pihenőidő (15-25 perc) alatt az izmaik bemerevedtek, és a gyors tempó túl hamar felemésztette az energiatartalékaikat.
3. **Limit Survivors (Határon Futók):**
   * *Jellemzők:* Közepes vagy magas körszám, de nagyon magas köridő-szórás. Az éjszaka vagy a fáradás hatására hirtelen lelassulnak, majd újra próbálnak gyorsulni.
   * *Hiba/Siker:* Mentálisan hatalmas harcosok, de a kaotikus tempó miatt a pihenőidejük rendszertelen.
4. **Average Pack (Átlagos Mezőny):**
   * *Jellemzők:* Átlagosan 5-12 kört teljesítő, mérsékelt tempójú és stabilitású futók.

![Klaszterek](file:///e:/Data/other_projects/backyard_analytics/plots/3_strategy_clusters.png)

---

## 4. Demográfia vs. Teljesítmény

Az életkor és a Backyard Ultra teljesítmény kapcsolatának elemzése rendkívül érdekes eredményt hozott:

* **Korreláció:** Az életkor és a teljesített körök száma között **gyenge, de pozitív korreláció** mutatkozik (Pearson r = 0.03). 
* **"Peak Age" (A csúcskor):** A legtöbb kört teljesítő és legstabilabb futók a **40 és 52 év közötti korosztályból** kerültek ki. 
* **Túlélési görbék korcsoport szerint:** A 45 év feletti korcsoport túlélési görbéje ([Korcsoportos görbe](file:///e:/Data/other_projects/backyard_analytics/plots/4_survival_by_age.png)) laposabb és elnyúlóbb, mint a fiatalabbaké. A tapasztalat, a mentális állóképesség és az ego háttérbe szorítása ebben a műfajban egyértelműen felülmúlja a fiatalkori robbanékonyságot.

![Életkor vs Teljesítmény](file:///e:/Data/other_projects/backyard_analytics/plots/4_age_vs_performance.png)
![Túlélés kor szerint](file:///e:/Data/other_projects/backyard_analytics/plots/4_survival_by_age.png)

---

## 5. Verseny-dinamika (Mezőny szétesése)

A mezőny lemorzsolódási aránya (*attrition rate*) pontosan megmutatja, hol vannak a kritikus krízispontok:

* **A mezőny összeomlási pontja:** A kiesési ráta a **6. körben (40 km)** és a **12. körben (80 km)** ugrik meg ugrásszerűen. Itt a futók közel 15-20%-a dönt úgy egy időben, hogy nem indul el a következő órában.
* **Az éjszakai szakasz (14-21. körök):** A sötétség beálltával a kiesések üteme egyenletessé válik, minden órában átlagosan a megmaradt mezőny 10%-a esik ki a hideg és a fáradtság miatt.

![Lemorzsolódás](file:///e:/Data/other_projects/backyard_analytics/plots/5_field_attrition.png)

---

## 6. Extra: Pszichológiai Proxyk

A köridők változékonyságából következtetni tudunk a futók mentális és fiziológiai állapotára:

### Éjszakai degradáció (22:00 - 06:00)
A futók átlagosan **2.60 perccel futottak lassabb köröket éjszaka**, mint nappal. 
* Ennek oka a látási viszonyok romlása miatti óvatosabb futás, valamint a cirkadián ritmus miatti természetes álmosság és testhőmérséklet-csökkenés.
* Az igazán elit futóknál (pl. a győztesnél) ez az éjszakai lassulás szinte elhanyagolható (kevesebb mint 1 perc) volt, ami kiemelkedő éjszakai adaptációt mutat.

![Éjszaka vs Nappal](file:///e:/Data/other_projects/backyard_analytics/plots/6_night_vs_day.png)

### Regenerációs képesség ("Bounce-back")
Megvizsgáltuk azokat az eseteket, amikor egy futó "krízisbe" került (azaz a köre 55 percnél hosszabb ideig tartott, ami kevesebb mint 5 perc pihenőt jelentett az újabb rajt előtt):
* A futók **44.3%-a** képes volt a következő körben felgyorsulni ("visszapattanni") és legalább 1-2 perccel gyorsabb kört futni.
* A megmaradt futók a kríziskör után vagy azonnal kiestek, vagy a következő körben túllépték a 60 perces limitet. Ez bizonyítja, hogy a Backyard Ultra-ban a mentális regeneráció képes felülírni a közvetlen fizikai fáradtságot.

---

## Következtetés & Tanácsok a következő versenyre

1. **A lassabb tempó kifizetődőbb:** A sprintek és a 45 percnél gyorsabb korai körök szinte garantálják a korai kiesést. A sikeres stratégia a 48-52 perc közötti egyenletes tempó.
2. **Készülj az éjszakára:** Az éjszakai 2-3 perces lassulást bele kell kalkulálni a frissítési tervbe. A megvilágítás minősége kulcsfontosságú az esések és a bizonytalanság elkerülésére.
3. **A mentális határ a 12. kör:** A dupla maratoni táv elérésekor jelentkezik a legnagyobb feladási hullám. Ha a futó fejben túllép ezen, a 20. körig viszonylag stabil szakasz következik.
