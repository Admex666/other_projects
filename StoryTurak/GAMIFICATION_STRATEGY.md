# StoryTurak / Keldor – Játékélmény és Gamifikációs Stratégia

---

## 1. Játékciklus (Core Loop)

*A játékos hősútja a mindennapokban – lezárható kalandok sorozata.*

A core loop célja nem a grind, hanem az, hogy **minden elindulásnak értelme és vége legyen**.

1. **Meghívás & Mozgás (Séta)**
   A játékos nem listát lát, hanem egy aktuális meghívást: eseményt, kalandot, következményt.
   A fizikai mozgás energiát ad, és **valós időben lépteti a történetet**.

2. **Felfedezés & Esemény**
   A városi csomópontokon (POI) rövid narratív események történnek: döntések, találkozások vagy harcok.
   Egy esemény = egy gyors interakció, minimális megállással.

3. **Harc vagy Döntés**
   Ha konfliktus alakul ki, a játékos harcol; ha nem, döntéseivel alakítja a világot.
   Kudarc esetén sincs megszakítás – a történet más irányba halad tovább.

4. **Jutalom (Loot & Következmény)**
   Minden kaland végén a játékos **mindig kap valamit**:
   tárgyat, információt, sebhelyet vagy narratív változást.

5. **Lezárás & Elraktározás**
   A kaland vizuálisan és szövegileg lezárul.
   A megszerzett tárgyakat a játékos felszereli vagy eladja – **döntést hoz**, nem csak számokat növel.

➡️ A ciklus újraindul, nem feltétlen nehezebb kihívásokkal, hanem **új helyzetekkel és következményekkel**.

---

## 2. Harcrendszer – „Taktikus Kő–Papír–Olló”

*Cél: Gyors, mobilbarát, de gondolkodásra ösztönző harc.*

### Alapkoncepció

A harc körökre osztott, de rövid (**max. 3–5 kör**).
A klasszikus Kő–Papír–Olló logikára épül, ahol a **döntés fontosabb, mint a reflex**, és a **tárgyak információt adnak**, nem puszta statbónuszt.

### Alapállások (Stance-ek)

1. **Erő (Támadás / Rock)**
   Nyers sebzés, nagy kockázat.
   Gyenge a Csel ellen.
   *Példák: Buzogány, Fokos, Szablya*

2. **Ügyesség (Csel / Paper)**
   Kitérés, gyors ellentámadás.
   Gyenge a Védekezés ellen.
   *Példák: Handzsár, Karikás ostor*

3. **Taktika (Védekezés / Scissors)**
   Távolságtartás, kontrollált harc.
   Gyenge a nyers Erő ellen.
   *Példák: Revolver, Kovás pisztoly*

### Felszerelés szerepe

A felszerelés **nem kötelező**, hanem döntést segít:

* **Török kaftán** – nagyobb Csel-hatékonyság
* **Huszár mente** – stabilabb Védekezés
* **Handzsár** – extra jutalom Csel-győzelemnél
* **Távcső** – egy körig látod az ellenfél következő lépését

### Kudarc-kezelés

* Harc elvesztése ≠ game over
* Kudarc = alternatív kimenet, sebhely, más jutalom vagy új történeti szál

---

## 3. Gazdaság – A „Pengő”

A gazdaság célja a **jelentéssel bíró döntés**, nem a farmolás.

**Valuta:** Pengő

### Szerzés

* Kalandok és események teljesítése
* Felesleges tárgyak eladása **városi kereskedőknek**
* Kis mértékben: mozgás-alapú bónuszok

### Költés

* Kereskedők speciális ajánlatai
* Felszerelés javítása vagy fejlesztése
* Ritka információk, térképrészletek

> A játékosok közti kereskedelem és piac csak későbbi fázisban jelenik meg.

---

## 4. Frakciók és Városi Hatás (Social Layer)

A játékosok később csatlakozhatnak egy frakcióhoz, amelyek **másképp értelmezik a várost**.

### Frakciók

* **Átformálók (Pest)** – stabilitás, védekezés
* **Krónikások (Buda)** – támadás, technológia
* **Elfeledettek** – csel, szerencse, loot

### Területi hatás (Zone Control)

* Kerületek dominancia-mérővel rendelkeznek
* A frakciók jelenléte **finoman alakítja az eseményeket**
* Heti lezáráskor jutalmak és világváltozások történnek

Nincs büntetés – csak pozitív következmények.

---

## 5. Pszichológia & Retenció – Kényszer nélkül

### Befejezetlenség (Zeigarnik-effektus)

* **Collection Book**, mint legendárium
* Hiányzó történetek és tárgyak

### Változó jutalmazás

* Talált ládák vizuális és hanghatásos felnyitása
* Ritkaságok: Szürke (Alap), Zöld (Gyakori), Kék (Ritka), Lila (Epikus), Narancs (Legendás)
* Heti streakek

➡️ A világ nem számon kér – **emlékszik**.

---

## Implementációs Fókusz (Technikai vázlat)

1. **Adatmodellek**
   `Character` (class, állapotok, valuta),
   `Item` (ritkaság, típus, hatás),
   `Event / Encounter`

2. **Harc logika**
   Kő–Papír–Olló + felszerelés-alapú módosítók

3. **Inventory & Kereskedők**
   Loot kezelése, eladás, felszerelés

4. **UI fókusz**
   Harc, események és lezárások gyors, mozgásbarát megjelenítése
