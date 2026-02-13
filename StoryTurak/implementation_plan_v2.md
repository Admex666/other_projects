# Keldor: Részletes Fejlesztési & Tartalmi Terv (v2.0)

Ezen dokumentum célja, hogy a **Keldor MVP-jét** egy **publikálható, gazdag tartalmú AR-játékká** emelje.
A stratégia két fő pilléren nyugszik:
1.  **Narratív Atomok**: Végtelenül skálázható tartalomgenerálás.
2.  **Release Blockerek Megoldása**: A játékélmény elsimítása (Onboarding, Combat UX).

---

## 📅 I. Fázis: Technikai Alapozás & Refaktor (1-2 Nap)
*Cél: A technikai adósság kifizetése, hogy a tartalomgyártás akadálytalan legyen.*

### 🛠️ 1. UI Refaktor (ItemTile Widget)
*   **Probléma**: A `_getRarityColor` és `_buildItemIcon` logika 5 fájlban van duplikálva.
*   **Feladat**:
    *   Létrehozni: `lib/widgets/keldor_item_tile.dart` (ListTile wrapper) és `keldor_item_card.dart` (Grid elem).
    *   Implementálni a közös ritkaság-szín logikát (`common`, `uncommon`, `rare` stb.) egy helyen.
    *   Minden Screen (`Explore`, `Character`, `Shop`, `Collection`) használja ezeket a widgeteket.

### 💰 2. Gazdasági Balance (Quick Fix)
*   **Feladat**:
    *   Definiálni egy alapvető árképzést:
        *   T1 Tárgy (Common): 50-100 Pengő. (Kb. 1-2 séta).
        *   T2 Tárgy (Rare): 300-500 Pengő.
    *   Jutalmak normalizálása: Egy sikeres encounter = 20-50 Pengő.

---

## ⚔️ II. Fázis: Játékélmény Javítása (2-3 Nap)
*Cél: A játékos értse, mit csinál, és élvezze a harcot.*

### 🎓 1. Onboarding (Tutorial Quest)
*   **Koncepció**: "Az Első Bevetés".
*   **Script**:
    1.  Induláskor: "Üdvözöllek, ügynök. A helyzetedet bemértük. Egy anomália van a közeledben."
    2.  Automatikusan felvesz egy Questet: "Találj meg egy Anomáliát" (Távolság: <50m).
    3.  Odaérve: Tutorial Encounter.
    4.  Harc magyarázat: "Válassz Taktikát! (Kő-Papír-Olló)".
    5.  Jutalom: Első tárgy (pl. "Régi Iránytű").
    6.  Inventory megnyitása -> Item felszerelése (Loadout magyarázat).

### ⚔️ 2. Harc Rendszer (Visual Upgrade)
*   **Feladat**: A jelenlegi "Snackbar" üzenet helyett egy rendes **Combat Overlay**.
*   **UI Terv**:
    *   **Ellenfél Kártya** (Kép, Név, HP).
    *   **Te Kártyád** (Választott Stance ikonja).
    *   **Animáció**: A két kártya egymásnak feszül -> Robbanás/Vágás effekt -> Eredmény kiírása.
    *   **HP Csökkenés**: Vizuális health bar animáció.

---

## 📖 III. Fázis: A Végtelen Tartalom (Narratív Atomok)
*Cél: "Írjunk kevés, de kompatibilis narratív elemet."*

A rendszer **címkézett atomokból** épít fel történeteket dinamikusan.

### 🏗️ Adatmodell Bővítés (`backend/app/services/story_service.py`)

A történeteket nem fix JSON fájlokban tároljuk, hanem egy **Atom Pool**-ban.

#### Atom Típusok:
1.  **Anchor (Horgony)**: Tényszerű infó a helyről (pl. "Ez a szobor 1896 óta áll.").
2.  **Echo (Visszhang)**: Múltbéli esemény/érzés (pl. "Sokan gyűltek köré...").
3.  **Twist (Zavar)**: Ellentmondás/Kérdés (pl. "De senki sem nézett a szemébe.").
4.  **Open (Nyitás)**: Következtetés (pl. "Talán ezért térnek vissza.").

#### Címke Rendszer (Metaadatok):
*   `tone`: [melancholic, tense, hopeful, ironic]
*   `time`: [past, timeless, modern]
*   `poi_type`: [statue, building, park, river, general]

### 🤖 Generátor Logika (Pseudocode):

```python
def generate_story(poi_type, tone):
    anchor = get_random_atom(type="anchor", poi_type=poi_type)
    echo = get_random_atom(type="echo", tone=tone, time="past")
    twist = get_random_atom(type="twist", tone=tone)
    opening = get_random_atom(type="open", tone=tone)
    
    return f"{anchor} {echo} {twist} {opening}"
```

### 📝 Tartalomgyártási Terv:
1.  **AI Segítség**: Generáltatni 100-100 atomot kategóriánként (GPT-4 kiváló ebben).
2.  **Manuális Írás**: Csak a "Fő Questekhez" és Frakció HUB-okhoz (kb. 5-10 db).
3.  **Implementáció**: Egy script, ami feltölti az `atoms` táblát a generált CSV-ből.

---

## 🌍 IV. Fázis: Frakciók & Szociális Réteg (Későbbi patch)
*Cél: A világ élővé tétele.*

1.  **Zone Control UI**: A térképen a zónák színe változzon dinamikusan a frakciók ereje alapján.
2.  **Global Event**: "A Hétvégén a Gellért-hegyért küzdünk!" (Extra XP ott).

---

## 📋 Teendők Listája (Action Plan)

### Sprint 1: Refaktor & Onboarding
- [ ] Létrehozni a `lib/widgets` mappát és az `ItemTile` widgetet.
- [ ] Átírni a 4 fő képernyőt az új widget használatára.
- [ ] Implementálni az `IntroScreen`-ben a "Tutorial Quest" logikát (hardcoded első quest).

### Sprint 2: Combat Polish
- [ ] `EncounterScreen` átalakítása: Modal helyett teljes képernyős Combat nézet.
- [ ] Animációk hozzáadása (Flutter `Animate` package vagy egyszerű `Tween`).
- [ ] HP logika bekötése (Sérülés perzisztálása DB-ben).

### Sprint 3: Narratív Atom Rendszer
- [ ] `atoms` tábla létrehozása a DB-ben (`id`, `text`, `type`, `tags`).
- [ ] `StoryService` bővítése az atom-összerakó logikával.
- [ ] AI promptolás -> CSV generálás -> DB feltöltés.
- [ ] `Encounter` generálás átírása: ne fix szöveget adjon, hanem hívja meg a `StoryService`-t.

---

**Összegzés**: Ezzel a tervvel a Keldor megszabadul a "demo" érzéstől, és egy valódi, mély, felfedezhető világgá válik, anélkül, hogy írók hadseregét kellene alkalmazni.
