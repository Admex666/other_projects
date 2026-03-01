# App terv összefoglaló – Ulti webapp

## 1️⃣ PROBLÉMA DEFINÍCIÓ

* **Célközönség:** Magyar kártyát ismerő fiatalok, kezdők, és régi játékosok, akik szeretnének online játszani barátokkal vagy idegenekkel.
* **Probléma:** A jelenlegi online Ulti appok elavultak, nehézkes a kezelhetőségük, nem mobilbarátak, és nem motiválják a kezdőket. A fiatalok számára nem vonzó a hagyományos felület, így a játék „kihalóban” van.
* **Megoldás:** Modern, mobilbarát webapp, ami megtartja az összes eredeti Ulti szabályt, de interaktív tutorialokkal, kezdőbarát tippekkel és statisztikákkal segíti az új játékosokat.
* **Előny a jegyzet/Excel/fejben vezetéshez képest:**

  * Automatikusan számolja a pontokat és az ütések sorrendjét
  * Könnyen játszható online bárhol, bármikor
  * Szobák és barátok meghívása egyszerű
  * Statisztika, ranglista, achievementek motiválnak
* **Cél:** Újraéleszteni a játékot a fiatalok körében, miközben megtartja a hardcore játékosoknak a teljes szabályrendszert.

---

## 2️⃣ SCOPE LOCK (mit NEM csinál az első verzió)

* Nem lesz chat vagy üzenő rendszer
* Nem lesz AI ellenfél (csak későbbi verzióban)
* Nem lesz replay funkció
* Nem lesz több játékmód (csak a klasszikus Ulti)
* Nem lesz teljes gamification (achievementek, badge-ek csak később)
* Nem cél a skálázás 10 millió felhasználóra, hobbi/prototípus szinten indul

---

## 3️⃣ DOMAIN MODELL (adatgondolkodás)

**Fő entitások:**

1. **Player** – felhasználó profil, statisztikák
2. **Game** – aktuális parti állapota
3. **Trick / Round** – az egyes ütéseket tartalmazó entitás
4. **Bid / Contract** – licit és vállalások
5. **Deck / Talon** – a kártyapakli állapota
6. **Score** – pontok, rangsor
7. **Room** – online szoba a játékhoz

**Kapcsolatok:**

* Room → 3 Player
* Game → Room, Deck, Score, Bids
* Trick → Game, Player
* Score → Game, Player

**Fontos use case-ek:**

1. Szoba létrehozása / csatlakozás
2. Licitálás kezelése
3. Kártya kijátszása, ütés validálás
4. Pontszámítás és vállalások ellenőrzése
5. Game state broadcast a játékosoknak (real-time)
6. Reconnect kezelése
7. Statisztika frissítése
8. Kezdő tutorial és tooltip támogatás
9. Ranked / casual játék kiválasztása
10. Game befejezése és eredmények tárolása

---

## 4️⃣ USE CASE → FLOW DESIGN (példa)

* **Game start:**
  Player létrehoz szobát → szerver validál → játék kezdődik → játékosok kapnak kártyát → state broadcast
* **Licit:**
  Player licitál → szerver ellenőriz → update → következő játékos
* **Kártya kijátszás:**
  Player kijátszik → szerver validál szabály szerint → update trik → broadcast
* **Game vége:**
  Összes ütés lezárva → pontszámítás → statisztika frissítés → broadcast eredmény

Hibák kezelése minden lépésnél: invalid licit, szín nem követése, network disconnect.

---

## 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

* **Frontend:** React Native (Expo) natív apphoz VAGY Next.js (web/PWA) + Tailwind
* **State management:** Zustand
* **Backend & Adattárolás:** Supabase (ingyenes PostgreSQL, autentikáció)
* **Real-time:** Supabase Realtime (beépített WebSocket / Broadcast)
* **Szabályvalidáció & Logika:** Vercel Serverless API (Next.js API Routes) a tiszta szabályvalidációért
* **Offline:** nem kritikus, online-only
* **Feature structure:** feature-based modulok (Game, Player, Room, Stats)
* **Client:** csak UI, minden döntés server-side validált

---

## 6️⃣ UI STRUKTÚRA

* **Screens / Pages:**

  1. Login / Registration
  2. Lobby / Room list
  3. Room / Game view
  4. Tutorial overlay / Tooltip
  5. Game end / Score summary
  6. Profile / Stats

* **Állapotok:** empty, loading, error, active gameplay

* **Navigáció:**
  Lobby → Room → Game → End → Lobby

---

## 7️⃣ ITERÁCIÓS STRATÉGIA

1. Domain modell kialakítása és use case-ek lefektetése
2. Vertical slice 1 játék (UI + logic + storage)
3. Refaktorálás: tiszta architektúra, state management
4. Következő feature (tutorial, statisztika, ranked, reconnect)
5. Iteratív bővítés később: AI, achievement, chat
