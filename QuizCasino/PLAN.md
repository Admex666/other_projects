# 1️⃣ PROBLÉMA DEFINÍCIÓ

Ez egy **gyors multiplayer trivia battle-royale mobiljáték**, ahol a játékosok **pontokat (stacket) tesznek fel a válaszaikra**, és a hibázók tétei kerülnek a potba, amit a helyesen válaszolók osztanak szét.

A célközönség:

* casual mobiljátékosok
* trivia rajongók
* versengő típusú játékosok
* rövid session játékot keresők (3–5 perc)

A probléma, amit megold:

A legtöbb trivia játék:

* lassú
* solo
* nincs tét
* nincs valódi feszültség

Ez a játék **kockázatot és versenyt visz a quiz műfajba**.

A játék különlegessége:

* **betting mechanika trivia kérdésekre**
* **battle royale struktúra**
* **pot system (hibázók finanszírozzák a győzteseket)**

A játék:

* rövid meccsek
* gyors elimináció
* nagy leaderboard swingek
* látványos effektek

Ez kombinálja:

* quiz
* poker risk
* battle royale pacing

Ezzel **addiktív short-session mobiljáték** jön létre.

---

# 2️⃣ SCOPE LOCK (MVP-ből szándékosan kimarad)

Az első verzió **nem tartalmazza**:

### ❌ valós idejű player-to-player támadások

nincs attack mechanic

### ❌ komplex PvP chat

### ❌ open text trivia válaszok

### ❌ túl sok játékmód

MVP-ben csak:

* standard battle royale

---

### ❌ komplex guild warfare

Guild csak:

* pontgyűjtés
* leaderboard

---

### ❌ túl komplex numeric scoring

Numeric kérdések:

* **top X% closest = correct**

---

### ❌ spectator mode

Csak később.

---

### ❌ marketplace / trading

Cosmetics csak unlock.

---

### ❌ túl nagy kérdéskészlet

MVP:

```text
2000–3000 kérdés
```

---

# 3️⃣ DOMAIN MODELL

Fő domain entitások.

---

## Player

Attribútumok:

* id
* username
* rank
* rating / ladder points
* currency
* guild_id
* cosmetics

Lifecycle:

```text
create → play matches → gain points → season reset
```

---

## Match

Aggregátum gyökér.

Attribútumok:

* match_id
* status (waiting / running / finished)
* players
* rounds
* leaderboard
* created_at

Lifecycle:

```text
lobby → rounds → elimination → final → result
```

---

## MatchPlayer

Match specifikus player state.

Attribútumok:

* player_id
* stack
* bet
* answer
* eliminated
* placement

---

## Round

Attribútumok:

* round_number
* question_id
* type (MC / numeric / true-false)
* multiplier
* status

---

## Question

Attribútumok:

* question_text
* answers
* correct_answer
* category
* difficulty
* type

Stats:

* correct_rate
* avg_bet
* pot_size

---

## Bet

Attribútumok:

* player_id
* round_id
* bet_amount
* answer

---

## Pot

Derived entity.

Attribútumok:

* total_lost_bets
* winners
* distribution

---

## Guild

Attribútumok:

* id
* name
* members
* weekly_points

---

## Leaderboard

Attribútumok:

* player_id
* rank
* rating
* season_points

---

# 4️⃣ USE CASE → FLOW DESIGN

Fő use case-ek.

---

## 1. Match indítása

Trigger:

player "Play" gomb.

Flow:

```text
player queue
matchmaking
bot fill
match start
```

Hibák:

* server unavailable
* timeout

Eredmény:

player bekerül egy lobbyba.

---

## 2. Round játék

Flow:

```text
question show
player answer
player bet
timer end
reveal
pot calculation
stack update
elimination check
```

Hibák:

* no answer
* no bet

Default:

* answer = random
* bet = minimum

---

## 3. Pot elosztás

Flow:

```text
collect losing bets
determine winners
calculate weight by bet
distribute pot
update stacks
```

---

## 4. Elimináció

Trigger:

round end.

Logika:

```text
bottom X% eliminated
OR stack ≤ 0
```

---

## 5. Match vége

Flow:

```text
final leaderboard
rank points
guild points
rewards
```

---

## 6. Daily ranking

Flow:

```text
player plays matches
best X matches counted
daily score
weekly aggregation
monthly season
```

---

## 7. Guild pontok

Flow:

```text
player match result
guild points add
weekly guild leaderboard
```

---

# 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

### Client

Flutter mobil kliens.

Miért:

* rendkívül gyors UI fejlesztés (szöveg, slider, layouting)
* könnyű hálózatkezelés (WebSockets)
* letöltés és indítás gyorsasága
* kiváló animációs lehetőségek (Implicit, Rive)

---

### Backend

Node.js + NestJS.

---

### Realtime

WebSocket.

---

### Database

PostgreSQL.

---

### Cache

Redis.

---

### State

Server authoritative.

A server számolja:

* pot
* stack
* elimináció

---

### Storage stratégia

Remote first.

Offline play nincs.

---

### Code struktúra

Feature-based:

```text
match/
question/
leaderboard/
guild/
player/
```

---

# 6️⃣ UI STRUKTÚRA

Fő képernyők.

---

## 1. Home

* Play gomb
* Rank
* Daily progress
* Guild status

---

## 2. Match lobby

* player count
* countdown

---

## 3. Question screen

* question
* answers
* bet slider
* timer

---

## 4. Reveal screen

* correct answer
* pot animation
* stack changes

---

## 5. Leaderboard screen

* round ranking
* eliminations

---

## 6. Match result

* placement
* points gained
* guild points

---

## 7. Profile

* stats
* cosmetics

---

## 8. Guild

* leaderboard
* member list

---

UI állapotok:

* loading
* match starting
* round active
* reveal
* elimination
* result

---

# 7️⃣ ITERÁCIÓS STRATÉGIA

Fejlesztési ciklus.

---

### Phase 1 — core prototype

Vertical slice:

```text
question
bet
pot
stack update
```

Single match.

---

### Phase 2 — multiplayer

* matchmaking
* bots
* elimination

---

### Phase 3 — meta game

* ranking
* daily limit
* guild

---

### Phase 4 — polish

* effects
* animations
* UX

---

Fejlesztési ciklus:

```text
domain
vertical slice
test
refactor
next feature
```