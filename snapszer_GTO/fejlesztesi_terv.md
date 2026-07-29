# Schnapsen GTO + exploit modell – fejlesztési terv

## 0. Projektcél definiálása

Nem az a cél, hogy:

> „verje meg az átlagos játékost”

hanem:

> „minden döntési helyzetben maximalizálja a hosszú távú várható értéket (EV), és alkalmazkodjon az ellenfél hibáihoz.”

A rendszer két rétegből állna:

```
             Schnapsen AI

        ┌─────────────────┐
        │  Exploit réteg   │
        │ ellenfél hibák   │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │  GTO alapmotor   │
        │ optimális játék  │
        └─────────────────┘
```

---

# 1. Játékmodell létrehozása

Első lépés: a szabályokat gépi formába öntjük.

## Lap reprezentáció

20 lap:

```
Suit:
- Trump
- Hearts
- Diamonds
- Clubs

Rank:
- Ace = 11
- Ten = 10
- King = 4
- Queen = 3
- Jack = 2
```

Minden lap:

```
Card {
 suit,
 rank,
 value
}
```

---

# 2. Állapotmodell (state)

Minden döntési pontot egy állapot ír le.

Példa:

```
STATE:

Saját kéz:
A♠
10♠
K♥
Q♥
J♣


Ellenfél ismert információ:
K♠ már kijött
A♦ kijött


Talon:
7 lap


Trump:
♠


Saját pont:
42


Ellenfél becsült pont:
28


Ki vezet:
Én
```

Ez a solver bemenete.

---

# 3. Döntési lehetőségek (action space)

A modell minden helyzetben ezeket vizsgálja:

## Normál játék

* melyik lapot játssza ki?

## Extra döntések

* zárás?
* tromf Unter csere?
* 20/40 bemondás?
* 66 bemondása?

Példa:

```
Akciók:

1. kijátszom A♠
2. kijátszom 10♠
3. zárás
4. Unter csere + zárás
```

---

# 4. A legfontosabb elem: rejtett információ kezelése

Itt különbözik a póker solverektől.

A rendszer nem tudja:

„Az ellenfélnél biztosan ez van.”

Hanem:

```
Lehetséges ellenfél kezek:

Hand 1:
A♥ K♥ J♣

20%


Hand 2:
10♣ Q♦ J♦

15%


Hand 3:
...
```

Ezt hívják **belief state modellnek**.

---

# 5. Monte Carlo kereső motor

A Schnapsen ideális erre.

Egy döntésnél:

Példa:

Kezed:

```
Trump A
Trump 10
Trump K
Heart Q
Club J
```

Kérdés:

„Zárjak?”

A motor:

1. generál 100 000 lehetséges ellenfél kezet
2. minden esetben végigjátssza a partit
3. számolja:

```
Zárás:

nyerés:
74%

vesztés:
26%


EV:
+1,84 játékpont
```

Nem zárás:

```
EV:
+1,22
```

Döntés:

→ ZÁRÁS

---

# 6. GTO tanulás

A Monte Carlo után jönne az önfejlesztés.

## Self-play

A bot saját maga ellen játszik:

```
AI v1
  |
  |
millió parti
  |
  ↓
AI v2
```

Minden parti után:

* melyik döntés volt rossz?
* mennyivel?

Példa:

```
Helyzet:

40 bemondás

AI választotta:
nem mondja be


Utólagos EV:
+0,8


Tanulság:
ebben az állapotban
70%-ban mondani kell
```

---

# 7. Külön modul: zárási stratégia

Ez lenne a legnagyobb edge.

A szabályzat is írja:

> a zárás a kulcselem.

Külön modellt építenék rá.

Input:

```
Saját biztos pont:
52

Lehetséges még:
+18


Ellenfél:
minimum 20
maximum 45


Trump kontroll:
erős
```

Output:

```
Close probability:
86%

Recommendation:
ZÁRJ
```

---

# 8. Ellenfél exploit modell (cash game miatt kötelező)

A GTO önmagában kevés.

Gyűjtenénk statokat:

## Ellenfél profil

Példa:

```
Player A:

Zár túl korán:
+15%

Túl ritkán mond 40-et:
-20%

Trumpot félti:
igen

Blöfföl zárással:
igen
```

Majd adaptáció:

Példa:

Ha valaki túl korán zár:

GTO:

```
40% megadás
60% dobás
```

Exploit:

```
70% megadás
```

---

# 9. Tesztelési rendszer

Nem emberekkel kezdeném.

Hanem:

## Bot liga

```
Random bot

↓

Basic strategy bot

↓

Monte Carlo bot

↓

GTO bot

↓

Exploit bot
```

100 000 parti.

Mérőszám:

## Elsődleges:

```
Game points / 100 hand
```

## Másodlagos:

```
- zárási hibák
- rossz bemondások
- elvesztett nagy potok
- variancia
```

---

# 10. Fejlesztési iteráció

## Fázis 1 (2-3 hét)

Szabálymotor

* lapok
* osztás
* szabályos lépések
* pontozás

Cél:
100%-os szimulátor

---

## Fázis 2

Monte Carlo bot

Cél:

emberi szint

---

## Fázis 3

Self-play

Cél:

erős játékos szint

---

## Fázis 4

Opponent modelling

Cél:

cash game exploit

---

# 11. A végső használati forma

A legpraktikusabb nem egy automata bot lenne, hanem egy **Schnapsen HUD / döntési asszisztens**:

Beírod:

```
Trump: Herz

Kezem:
A♥
10♥
K♣
Q♣
J♦

Pont:
54-31

Én vezetek
```

Output:

```
Legjobb döntés:

ZÁRÁS

EV:
+2,14

Indok:
- 5 biztos trump kontroll
- ellenfél maximum 1 magas trump
- 40 bemondási lehetőség
```