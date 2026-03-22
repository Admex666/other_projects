# APP_PLAN.md

## 1️⃣ PROBLÉMA DEFINÍCIÓ

* **Ki használja?**

  * Mobilos játékosok, akik szeretik a gyűjthető kártyajátékokat, gyors meccseket és a humoros, karaktervezérelt világot.
  * Olyan felhasználók, akik szeretik a deck-building mechanikát és a gyűjtést, de nincs idejük hosszú meccsekre vagy komplex RPG-re.

* **Milyen konkrét problémát old meg?**

  * Hiányzik egy könnyen hozzáférhető, magyar kulturális hangulatú, rövid meccsekkel játszható kártyajáték.
  * Biztosítja a játékosnak a deck-building élményt, a stratégiai döntéseket és a kontrollált káoszt (random események + “félremegy” mechanika).
  * Gyors, pörgős meccseket ad, ami mobilra optimalizált és nem veszi el az időt hosszú sessionökben.

* **Miért jobb, mint egy már létező alternatíva?**

  * Nem csak statikus kártyajáték: minden lapnak karaktere, saját személyisége van.
  * Random események + stabilitás/luck mechanika → kontrollált, de szórakoztató kiszámíthatatlanság.
  * Pörgős és rövid, de elég stratégiai mélység van a deck-building, ritkasági lapok és factionok révén.
  * Skálázható: később tournament, season, új factionok, eventek, story módok adhatók hozzá.

---

## 2️⃣ SCOPE LOCK

**Mi NEM része az első kiadásnak?**

* Teljesen digitális Hearthstone-szintű animációk
* Multiplayer liga / ranking ladder (ez a későbbi bővítés)
* Story mód / roguelike kampány
* Heavy particle effektek vagy Unity alapú vizuális extrák
* 40+ lapos komplex deck, első verzió csak MVP deck (20–30 lap)

**Szándékosan kihagyva:**

* Párhuzamos platform (csak mobil első körben)
* Co-op vagy 2v2 meccsek
* Komplex matchmaking algoritmus

---

## 3️⃣ DOMAIN MODELL

**Fő entitások:**

1. **Player** – statok, deck, HP, stabilitás, resource pontok
2. **Card** – karakter/event/equipment, statok (HP, ATK, Skill, Luck, Stabilitás), képességek, rarity
3. **Deck** – Player-hez kötött laphalmaz
4. **Game / Match** – körök, állapot, event queue, current turn, active cards
5. **Faction** – karakterekhez kötött stílus/mechanika
6. **Event** – globális/lokális események, trigger feltételek

**Kapcsolatok:**

* Player *tartalmaz* Deck
* Deck *tartalmaz* Card
* Card *hozzá van rendelve* Faction-hoz
* Game *tartalmaz* Player-eket + Event queue

**Aggregátum gyökér:** Game

* Lifecycle: Game létrejön → meccs zajlik körönként → Game vége → pontok/XP/lap unlock → Game archiválódik

---

## 4️⃣ USE CASE → FLOW DESIGN

**Fő use case: 1v1 meccs**

* **Indító esemény:** Player elkezdi a meccset
* **Flow:**

  1. Húzás fázis → lap húzása deckből
  2. Action phase → Attack / Ability / Pass
  3. Event phase → kör végi esemény trigger
  4. End phase → stat update, cooldowns
* **Hibák:**

  * Lap nem hajtja végre a képességet (“félremegy”)
  * Event nem teljesül a Luck/Stabilitás miatt
* **Eredmény:**

  * HP változás, lap állapot frissítés, kontrollált káosz hatás
  * Game vége → győztes / vesztes → stat update, lap unlock

---

## 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

* **State management:** Riverpod
* **Dependency injection:** provider pattern vagy egyszerű singleton, feature-alapú DI
* **Local vs remote storage:** kezdéskor lokális, később leaderboard / multiplayer backend
* **Offline-first vagy online-only:** offline-first
* **Feature-based struktúra:**

  * `/game` – logika, match state
  * `/ui` – screens, widgets
  * `/data` – repository, local storage

---

## 6️⃣ UI STRUKTÚRA

* **Képernyők:**

  * Main Menu
  * Deck Builder
  * Match Screen (1v1)
  * Card Collection
  * Settings
* **Navigáció:** Tab / Stack kombináció
* **Állapotok:**

  * Loading (deck, match)
  * Empty (nincs lap / deck)
  * Error (hálózati hiba, adatbetöltés)
  * Active match / turn-based UI

---

## 7️⃣ ITERÁCIÓS STRATÉGIA

1. **Domain:** Player, Card, Deck, Game entitások + statok + controlled chaos logika
2. **Feature vertical slice:**

   * 1v1 match
   * deck building 20 lapos MVP
   * pörgős turn-based játékmenet + stabilitás/luck mechanika
   * események triggerelése körönként
3. **Refactor:** code cleanup, stat formulas, event handling
4. **Következő feature:**

   * gyűjthető ritkasági lapok, faction bővítés, event chains, tournament / ranking rendszer