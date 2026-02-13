# Keldor (StoryTurak) - Állapotjelentés & Ajánlások

## 1. Jelenlegi Állapot Összefoglalása
A projekt egy működőképes **MVP (Minimum Viable Product)** fázisban van. Az alap mechanikák (térkép, mozgás, inventory, combat logika, bolt) technikailag implementálva vannak, de a tartalom és a felhasználói élmény (UX) még "fejlesztői" szinten mozog.

### ✅ Erősségek
*   **Core Loop Működik**: Mozgás a térképen -> Zóna belépés -> Encounter -> Harc/Döntés -> Loot/Jutalom -> Inventory menedzsment.
*   **Technikai Alapok**: Stabilnak tűnő backend (FastAPI), modern Flutter frontend Provider state managementtel.
*   **Vizuális Irány**: A térkép stílusa, a "Dark Mode" UI és a ritkaságszínek (Rarity Colors) egységes hangulatot teremtenek.
*   **Dinamikus Rendszerek**: A Collection rendszer most már dinamikusan épül fel az adatbázisból, ami skálázhatóvá teszi a tartalombővítést.

---

## 2. Kritikus Hiányosságok (Release Blockerek)

Ezek azok az elemek, amelyek nélkül a játékosok elveszve éreznék magukat, vagy a játékélmény megtörne 5 perc után.

### 🔴 1. Onboarding & Tutorial (A legkritikusabb!)
*   **Probléma**: Jelenleg a játékos "beledobódik" a térkép közepére. Nem tudja:
    *   Mi a célja (Questek felvétele).
    *   Hogyan működik a harc (Kő-Papír-Olló mechanika).
*   **Megoldás**: Egy rövid, scriptelt "Bevezető Kaland" (Tutorial Quest), ami a játék indításakor automatikusan elindul, és végigvezeti a játékost az első harcon és tárgyfelvételen.

### 🔴 2. Harc Visszajelzés (Combat UX)
*   **Probléma**: A harc jelenleg "gombnyomás -> szöveges eredmény" (Snackbar/Log). Hiányzik a feszültség és a vizualitás.
*   **Megoldás**:
    *   Egy dedikált **Harc Képernyő** (vagy modal), ahol látszik a játékos és az ellenfél (kép/ikon).
    *   Animáció vagy késleltetés a támadás és az eredmény között.
    *   Egyértelmű visszajelzés arról, hogy *miért* nyertél vagy vesztettél (pl. "A Csel legyőzte az Erőt!").

### 🔴 3. Tartalom (Content Starvation)
*   **Probléma**: Jelenleg ~3 zóna, 2 encounter és ~8 tárgy van a játékban. Ez kb. 5-10 perc játékidő.
*   **Megoldás**:
    *   Legalább **5-10 Quest** (különböző nehézséggel).
    *   **20+ Tárgy** (hogy a Shop és Loot érdekes legyen).
    *   Több, véletlenszerű Encounter a térképen (ne csak fix pontokon legyenek).

### 🔴 4. UI Inkonzisztencia & Kódduplikáció
*   **Probléma**: A `CharacterScreen`, `ExploreScreen` (Popup), `ShopScreen` és `CollectionScreen` mind saját logikával (másolt kóddal) jelenítik meg a tárgyak színeit és ikonjait. Ha módosítjuk a logikát, 4 helyen kell átírni.
*   **Megoldás**: Egy közös `ItemCard` vagy `ItemIcon` widget létrehozása (`widgets/item_card.dart`), amit mindenhol használunk.

---

## 3. Ajánlások "Jó Játék" Szinthez (Polish)

Ezek teszik a játékot élvezetessé és visszatérésre érdemessé.

### 🟡 1. Economy Balance
*   Jelenleg a tárgyak ára és a küldetések jutalma hasraütésszerű.
*   Szükséges egy Excel tábla a gazdaság tervezésére (Mennyi idő egy kardot megvenni? Mennyit ér egy séta?).

### 🟡 2. Hangok és Haptikus Visszajelzés
*   A "HapticFeedback" már benne van a kódban, ami szuper!
*   Kellenek hangeffektek (UI click, Harc győzelem, Szintlépés, Tárgy felvétele), hogy "éljen" az app.

### 🟡 3. Frakciók Szerepe
*   A térképen látszanak a zónák színei, de a játékosnak nincs valódi interakciója velük.
*   Jó lenne: "Zone Control" százalék kijelzése, vagy frakció-specifikus Shop ajánlatok.

### 🟡 4. Profil & Beállítások
*   Avatar testreszabása (vagy legalább választás).
*   Értesítések kezelése.

---

## 4. Technikai Adósság (Technical Debt)

*   **Duplikált Logika**: `_getRarityColor` és `_buildItemIcon` 4-5 fájlban szerepel. **Sürgősen refaktorálandó.**
*   **Hardcoded Text**: A UI szövegek (pl. gombok, üzenetek) a kódban vannak. Később nehéz lesz fordítani vagy javítani. (Localization javasolt).
*   **Error Handling**: Sok helyen `catch (e) {}` üres blokkok vagy generikus "Hiba" üzenetek vannak.

---

## Összegzés: Mi a következő lépés?

1.  **Refaktor**: Hozd létre a közös `ItemTile` widgetet a duplikáció megszüntetésére.
2.  **Tutorial**: Írj egy egyszerű "Első Lépések" scriptet.
3.  **Tartalom**: Töltsd fel az adatbázist (JSON) több tárggyal és küldetéssel.
4.  **Combat Polírozás**: Tedd látványosabbá a harc kimenetelét.

Ha ezek megvannak, a Keldor készen áll egy béta tesztre! 🚀
