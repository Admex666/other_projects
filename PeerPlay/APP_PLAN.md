# APP_PLAN.md

# 1️⃣ PROBLÉMA DEFINÍCIÓ

## 📄 1 oldalas probléma statement

A PeerPlay egy scenario-alapú viselkedési szimulációs platform, amelyet HR vezetők, szervezetfejlesztők és felsővezetők használnak.

A célja, hogy strukturált, összehasonlítható és időben követhető képet adjon arról, hogyan működik valójában egy szervezet különböző stresszhelyzetekben.

A legtöbb vállalat:

* organogram alapján gondolkodik,
* percepciós survey-kre támaszkodik,
* workshopokon jegyzetel,
* Excelben próbál network insightot összerakni.

Ezek:

* statikusak,
* torzítottak,
* nem viselkedés-alapúak,
* nem összehasonlíthatók időben.

A PeerPlay ezt váltja ki azzal, hogy:

* kontrollált, de természetes interakciós helyzetet teremt,
* strukturáltan rögzíti az objektív tranzakciós adatokat,
* célzott percepciós kérdőívvel méri a befolyást, bizalmat, konfliktust,
* a formális struktúrával összeveti az emergens networköt,
* időben ismételhető mérést biztosít.

Ez nem csapatépítő játék.

Ez egy **Behavioral Simulation-Based Organizational Diagnostics Platform**, amely negyedévente vagy évente futtatható, és képes kimutatni a szervezeti dinamika változását.

---

# 2️⃣ SCOPE LOCK – MIT NEM CSINÁL AZ MVP?

Ez kritikus.

## 🚫 Out of scope (V1-ben NINCS):

* ❌ In-app chat vagy teljes kommunikációs platform
* ❌ Automatikus beszélgetés-elemzés (AI transcript parsing)
* ❌ Valós idejű viselkedéskövetés (face recognition, proximity, stb.)
* ❌ 10 különböző scenario
* ❌ Teljesítményértékelési modul
* ❌ HRIS integráció
* ❌ Gamification ranking rendszer
* ❌ Külső benchmarking adatbázis
* ❌ Szervezet-szintű 1000+ fős network mapping

## 🎯 MVP fókusz:

* 1 flagship scenario (pl. Economic Trade)
* Hard interaction logging
* Structured end-survey
* Org structure upload
* Network + gap analysis
* Időbeli összehasonlítás lehetősége

Ez megvéd a feature-spiráltól.

---

# 3️⃣ DOMAIN MODELL (nem adatbázis, hanem gondolkodás)

## 🧩 Fő entitások

### Organization

* id
* name
* industry
* orgStructure (hierarchia)

Lifecycle:

* létrejön
* sessionöket futtat
* évek alatt adat halmozódik

---

### User

* id
* name
* role
* organizationId
* teamMembership (session-függő)

Lifecycle:

* regisztrál
* sessionben részt vesz
* survey-t tölt

---

### Scenario

* id
* name
* behavioralFocus (pl. cross-functional dependency)
* config
* version

Lifecycle:

* verziózott
* ismételhető évek múlva

---

### Session (Aggregátum gyökér)

Ez a rendszer magja.

* id
* organizationId
* scenarioId
* status (draft, active, closed)
* participants
* rounds
* createdAt

Minden interakció ehhez kötődik.

---

### Round

* id
* sessionId
* number
* state (open, closed)

---

### Interaction

* id
* sessionId
* roundId
* fromUser
* toUser / toTeam
* type (trade, info-share, etc.)
* resourceType
* quantity
* timestamp

Ez az objektív network alapja.

---

### SurveyResponse

* sessionId
* userId
* questionId
* targetUserId (ha network kérdés)
* answer

Ez perception network.

---

## 🔗 Kapcsolatok

Organization → Sessions
Session → Rounds
Session → Interactions
Session → SurveyResponses
Session → Participants
Scenario → Sessions

Aggregátum gyökér: **Session**

Minden state change sessionen belül történik.

---

## 🧠 8 fontos use case

1. HR létrehoz sessiont
2. Résztvevők csatlakoznak
3. Kör indul
4. Trade rögzítés
5. Kör lezárás
6. Survey kitöltés
7. Network generálás
8. Időbeli összehasonlítás egy korábbi sessionnel

---

# 4️⃣ USE CASE → FLOW DESIGN

## 1️⃣ Session létrehozás

Trigger: HR új sessiont indít
Flow:

* Scenario kiválasztás
* Résztvevők hozzáadása
* Org struktúra linkelése
* Mentés → draft state

Hiba:

* Nincs résztvevő
* Scenario verzió nem aktív

Eredmény:
Session status = draft

---

## 2️⃣ Session indítás

Trigger: HR start
Flow:

* Validáció: min résztvevő?
* State → active
* Round #1 open

Hiba:

* Nem mindenki joined
* Scenario config hiba

Eredmény:
Session active

---

## 3️⃣ Trade rögzítés

Trigger: User trade-et rögzít
Flow:

* Validáció: van erőforrás?
* Interaction mentése
* Resource update
* UI feedback

Hiba:

* insufficient resource
* round closed

Eredmény:
Interaction logged

---

## 4️⃣ Round lezárás

Trigger: HR zár
Flow:

* Minden pending action lezár
* Round state → closed
* Következő round open

---

## 5️⃣ Survey kitöltés

Trigger: Session closed
Flow:

* Kérdések userenként
* Network-target kérdések
* Validáció (min válasz)
* Mentés

Hiba:

* Incomplete submission

Eredmény:
SurveyResponse entityk létrejönnek

---

## 6️⃣ Report generálás

Trigger: HR megnyitja dashboardot
Flow:

* Interaction → trade network generálás
* Survey → influence network
* Org structure overlay
* Score számítás

---

# 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

Platform jelleg miatt:

## 🧱 Backend

* Modular monolith (ne microservice-szel kezdd)
* Scenario engine config-driven
* Event-sourced interaction log (előnyös később)

## 📱 Frontend

Ha gyors MVP:

React (web) + PWA
vagy React Native, ha mobil app kell.

## State management

React esetén:

* Zustand vagy Redux Toolkit (egyszerűbb → Zustand)
* Session state elkülönítve

## Storage

* Remote first
* Nem offline-first (enterprise workshop = WiFi elérhető)

## Struktúra

Feature-based:

/session
/scenario
/survey
/report

Ne layer-based legyen az elején.

---

# 6️⃣ UI STRUKTÚRA

## PLAYER

* Join Screen
* Lobby
* Round Screen
* Trade Modal
* Resource Overview
* Survey Screen
* Completion Screen

States:

* Loading
* Waiting for round
* Round active
* Round closed
* Session ended

---

## HR DASHBOARD

* Organization Overview
* Sessions List
* Session Detail

  * Game Data
  * Network Graph
  * Survey Graph
  * Org Overlay
* Compare Sessions

---

# 7️⃣ ITERÁCIÓS STRATÉGIA

Nagyon fontos.

## Iteráció 1

* Domain model
* 1 scenario
* 1 round
* Trade logging
* Basic survey
* Simple network graph

Vertical slice:
Join → Trade → Survey → Report

---

## Iteráció 2

* Több round
* Org overlay
* Score calculation

---

## Iteráció 3

* Időbeli összehasonlítás
* Második scenario config

---

# 🎯 Végső gondolat

A skálázhatóság kulcsa nem a sok játék.

Hanem:

* session mint aggregátum
* scenario mint config
* network mint generált réteg
* időbeli összehasonlítás

Ha ezt most jól rakod le,
a rendszer 1 scenario-ról 10-re tud nőni újraírás nélkül.

---

# 8️⃣ FLAGSHIP SCENARIO: GLOBAL EXCHANGE

## ⏱ Játékmenet & Beállítás
- **Teljes idő:** 60–75 perc (10p onboarding, 35p játék, 15-20p debrief)
- **Résztvevők:** 12–24 fő (1 HR admin + 1 facilitator)
- **HR Beállítás (Pre-session):** Company name, Session name, Játék hossza, Random team allocation vagy manual.
  - Opcionális: department tag (nem látszik játékban, reporthoz kell).

## 1️⃣ LOBBY FÁZIS
- Kód alapján (Room Code) csatlakozás.
- Team Assignment: 5-6 csapat, 2-4 fő/csapat.
- **Team Types (Titkos):**
  - Alpha: High Tech, Low Raw
  - Beta: High Raw, Low Tech
  - Gamma: Balanced
  - Delta: Financial Power
  - Epsilon: Hidden Innovation

## 2️⃣ INTRO & REGLES
- Szabályok: No external communication, contracts binding, market values change. Game begins in 30 sec.

## 3️⃣ STARTING STATE (Minute 0)
- **Példa (Alpha):** Raw: 3, Tech: 5, Capital: 800, Efficiency: +40%
- **Példa (Beta):** Raw: 15, Tech: 1, Capital: 200, Efficiency: -20%

## 4️⃣ MAIN GAME LOOP (35 perc) & UI
- **Dashboard:** Csapat info, Capital, Raw, Tech, Active Contracts, Alliance.
- **Production Panel:** 
  - Circle (1 Raw, 1 Tech, 100 Base Value)
  - Triangle (2 Raw, 2 Tech, 250 Base Value)
  - Square (1 Raw, 3 Tech, 180 Base Value)
  - Hexagon (3 Raw, 4 Tech, 400 Base Value)
  - Termelés cooldownnal, Value -> Capital.

## 5️⃣ TRADE SYSTEM
- **Instant Trade:** Raw <-> Capital, Tech lease <-> Revenue %
- **Contract Trade:** Digitális szerződések pl. Tech Access <-> Future Revenue (Duration alapú). Nem visszavonható.

## 6️⃣ EVENT ENGINE
- Market Shock (Triangle value esik).
- Resource Discovery (Váratlan nyersanyag egy csapatnak).
- Secret Innovation (Titkos szorzó Token a hexához).
- UN Aid (Pénz a legszegényebbnek repayment feltétellel).
- Emergent mechanics: Cartel, Trade embargo, Protection deal, Annexation (Megnőtt wealth, de trust esik).

## 🔟 GAME END & AUTOMATIKUS REPORT
- Product termelés vége.
- Network Graph: bridge-ek, izoláltak.
- Wealth Ranking.
- Behavioral Profile (aggression, trust, short-term vs long-term).

## 1️⃣2️⃣ FACILITATED DEBRIEF
- Mérés és facilitátori bepillantás rejtett adatokba.
- "Ez nem csapatépítő játék. Ez egy szervezeti viselkedési labor."