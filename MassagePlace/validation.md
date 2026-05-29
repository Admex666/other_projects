# Last-Minute Wellness - Validációs Stratégia

Ez a dokumentum összefoglalja a "Last-Minute Wellness" (idle capacity marketplace) koncepció keresleti (demand) és kínálati (supply) oldalának legköltséghatékonyabb, gyakorlati validációs lépéseit és elvárt metrikáit.

## 1. Keresleti Oldal (Demand) Validálása
**Módszer:** "Fake Door" (Ál-ajtó) teszt, Supabase / Tally integrációval, alacsony (napi 1.000 - 2.000 Ft) Facebook/Instagram hirdetési büdzsével.

### Go / No-Go Metrikák (Döntési pontok)

*   **CTR (Átkattintási arány a hirdetésen)**
    *   🟢 **GO (Tovább): > 1.5%** -> Valós a probléma, az ajánlat ("last minute masszázs kedvezménnyel") vonzó.
    *   🔴 **NO-GO (Kuka/Újratervezés): < 0.5%** -> Érdektelenség, vagy rossz a hirdetési üzenet (value proposition).
*   **CAC (Ügyfélszerzési Költség / Feliratkozó)**
    *   🟢 **GO: < 2.500 Ft** -> A tervezett ~2.100 Ft-os jutalékkal (take rate) és némi visszatérési rátával (repeat usage) a modell nyereséges tud lenni.
    *   🔴 **NO-GO: > 4.000 Ft** -> Túl drága az akvizíció, a modell minden új usert veszteséggel hozna be.
*   **CVR (Konverziós ráta a landing oldalon)**
    *   🟢 **GO: > 5%** -> Magas vásárlási szándék (High Intent). A userek a konkrét árak (10.500 Ft) és a "betelt" státusz ellenére is megadják az email címüket.
    *   🔴 **NO-GO: < 1-2%** -> Sok az "ablakvásárló" és az árérzékeny kuponvadász, akik lepattannak a konkrétumoknál.
*   **WTP (Fizetési hajlandóság és AOV)**
    *   🟢 **GO:** A userek legalább 30%-a a drágább opciót (pl. 90 perc) vagy az upsellt (pl. aromaterápia) választja.

---

## 2. Kínálati Oldal (Supply) Validálása
**Módszer:** Strukturált B2B Reachout (Partner Interjú) és kockázatmentes Próba-Ajánlat.
Nem " mystery-shopper" módszerrel trükközünk, hanem nyílt, partneri párbeszédet kezdeményezünk 10-12 budapesti prémium szalon tulajdonosával/vezetőjével (elsősorban Instagram DM-ben vagy telefonon), hogy validáljuk a problémát, az operációs súrlódást és a diszkont-hajlandóságot.

### A B2B Reachout Folyamat (Instagram DM Szekvencia)

A hideg megkereséseknél a legnagyobb hiba a "Wall of Text" (egy végtelenül hosszú, spam-szagú bemutatkozó üzenet), amire a szalonok 95%-a válaszra sem méltatja a feladót. Ehelyett egy **beszélgetésindító (conversation-first), több lépcsős értékesítési tölcsért** alkalmazunk, ahol a keresleti kampányunkból beesett valós igényeket használjuk fel **"Trójai Falóként"** (Trojan Horse), hogy azonnal konkrét értéket vigyünk az asztalra.

#### 1. Lépés: A "Horog" (The Hook - Skálázható helyi kereslet)
Nem hazudunk konkrét azonnali vendégekről (hiszen nem ígérhetjük be ugyanazt a 2 leadet 15 különböző szalonnak egyszerre), helyette a **valós keresleti kampányunk eredményeit és a helyi igényt** használjuk jégtörőnek. Ez 100%-ban etikus, skálázható, és mégis rendkívül vonzó a szalonoknak.

> 💬 **DM #1:**
> *"Szia [Keresztneve/Szalon neve]! Épp a kerületi irodaházak dolgozóinak állítjuk össze a heti last-minute masszázs-ajánlatokat, mert a napokban futó kampányunk alatt komoly helyi igényt mértünk a 90 perces kezelésekre. 
> 
> Szeretnénk nekik ajánlani titeket is partnerként. Van a napokban olyan üresedésetek vagy utolsó pillanatban lemondott időpontotok, amit szeretnétek, hogy közvetítsünk a nálunk feliratkozott helyi dolgozók felé?"*

*   **Sales Pszichológia:** Az ajánlat továbbra is rendkívül vonzó, mert nem kérünk tőlük semmit, hanem ingyenes helyi láthatóságot és potenciális vendégeket ajánlunk fel az üres óráikra. Mivel a kampányunk (Meta Ads) valóban futott és hozott leadeket a kerületben, a szöveg teljesen igaz és hiteles. Nem kelti a spam érzését, mert helyi és releváns.

#### 2. Lépés: A Híd és Kvalifikáció (The Bridge & Qualification)
Miután a szalon válaszol (hogy mikor van helyük, vagy hogy érdekes-e nekik), átkötjük a szót a ZenSlot koncepciójára, és finoman leteszteljük a problémát (Capacity Pain).

> 💬 **DM #2:**
> *"Szuper, köszönöm a gyors választ! A helyzet az, hogy a ZenSlot-nál pont az ilyen helyzetekre szakosodtunk: a környékbeli stresszes irodai dolgozókat kapcsoljuk össze a prémium szalonok aznapi üres idősávjaival 30% kedvezménnyel. 
> 
> Mi hozzuk a vendéget, ti adjátok az üres ágyat, és csak a sikeres foglalás után kérünk 20% jutalékot (így egy 0 Ft-os üres órából nettó 11 200 Ft bevételetek lesz). Nálatok is gyakori egyébként, hogy az utolsó pillanatos lemondások vagy a hétközi csendesebb órák bevételkiesést okoznak?"*

*   **Sales Pszichológia:** A 20%-os sikerdíj bemutatása teljesen természetes, hiszen mi hozzuk a vendéget (kiszűri a "túl szép, hogy igaz legyen" gyanakvást). A kérdés nyílt és szakmai, amivel validáljuk a problémát, miközben partnerként kezeljük őket.

#### 3. Lépés: A Deal Lezárása (The Close - Próbaidőszak indítása)
Miután megerősítették, hogy létezik a probléma (vagy érdekli őket a megoldás), lezárjuk a megállapodást az első 2 vendég beközvetítésére és a 7 napos manuális tesztre.

> 💬 **DM #3:**
> *"Teljesen megértem, a legtöbb partnerünknek ez a legnagyobb fejtörés. Mit szólnátok hozzá, ha most próbaképp átküldenénk nektek ezt a 2 konkrét vendéget a szabad helyeitekre, és a következő 7 napban megnéznénk, tudunk-e még hozni további 2-3 fizető vendéget az üres óráitokra? 
> 
> Nincs semmi csatlakozási vagy havidíj, csak a sikeres közvetítés utáni 20% jutalék, így teljesen kockázatmentes. Benne lennétek egy ilyen próbaidőszakban?"*

*   **Sales Pszichológia:** Az ajánlat visszautasíthatatlan, mert a meglévő 2 vendéggel azonnal profitot realizálnak, miközben kockázat nélkül tesztelhetik a platform működését és az együttműködést.

---

### Go / No-Go Metrikák a Szalonoknál (Min. 10 reachout alapján)

*   **1. Probléma Validáltsága (Capacity Pain)**
    *   🟢 **GO:** A megkérdezett szalonok legalább **60%-a** (10-ből 6) beismeri, hogy az üres órák és a lemondások érezhető, frusztráló bevételkiesést okoznak, és a jelenlegi módszereik (pl. Instagram Story-ba kiírás) nem elég hatékonyak a betöltésükre.
    *   🔴 **NO-GO:** Kevesebb mint **20%** jelez üresedési problémát (mert pl. fix hetekre előre telve vannak, vagy a saját naptárrendszerük tökéletesen megoldja ezt).
*   **2. Ajánlat Validáltsága (Risk-Free Trial Acceptance)**
    *   🟢 **GO:** A megkérdezett szalonok legalább **30%-a** (10-ből 3 szalon) nyitott a próbahét elindítására és belemegy, hogy átküldjük nekik a meglévő leadjeinket.
    *   🔴 **NO-GO:** **0%** hajlandóság (mindenki elutasítja a próbát, pl. a presztízs védelmére hivatkozva, vagy mert elvből elutasítanak bármilyen kedvezményt a last-minute órákra is).
*   **3. Operációs Hajlandóság (Friction Test)**
    *   🟢 **GO:** A szalonvezető hajlandó arra, hogy az üres óráit naponta egyszer elküldje nekünk WhatsApp-on/Viber-en keresztül a manuális próbahét alatt.
    *   🔴 **NO-GO:** A szalonok kijelentik, hogy semmilyen manuális adatközlésre nem hajlandóak, csak akkor csatlakoznának, ha már kész automata Salonic/naptár API-integrációnk van (ez jelzi, hogy az MVP nem skálázható manuálisan).
