# 1. Alapkoncepció

**Multiplayer quiz battle royale**, ahol a játékosok **stacket (pontot)** tesznek fel a válaszaikra.

Core loop:

```id="b8sx4w"
kérdés → válasz → bet → reveal → stack változás → elimináció
```

A játékosok **kockázatot kezelnek**, nem csak tudást használnak.

---

# 2. Match struktúra

* Players: 30–80
* Start stack: 100
* Rounds: 7
* Shield rounds: 1–2
* Max meccs idő: 3–4 perc

---

# 3. Shield roundok

* Az első két körben **nincs kiesés**, csak stack változás.
* Bet limit: pl. 30–40% stack, hogy a játékosok melegedjenek.

---

# 4. Bet / stake rendszer

* Minden játékos **válasz + saját bet** (stack % vagy konkrét pont).
* Max bet: pl. 50% stack (a shield roundokon kisebb).
* Opció: **ALL IN** → drámai pillanat.

---

# 5. Pot-os pontozás (signature mechanic)

1. Hibázók tétje kerül a **potba**.
2. Helyes válaszadók **arányosan osztják szét** a potot a saját téteik súlyában.
3. Saját tétjüket is visszakapják.

**Példa:**

| Player | Stack | Bet | Correct? |
| ------ | ----- | --- | -------- |
| Anna   | 100   | 20  | ✔        |
| Ben    | 100   | 15  | ✖        |
| Kai    | 100   | 25  | ✔        |

* Pot = hibázók téte = 15 (Ben)
* Súlyok: Anna 20/(20+25)=0.444, Kai 25/(20+25)=0.556
* Pot elosztás: Anna 15*0.444 ≈ 7, Kai 15*0.556 ≈ 8
* Új stack: Anna 100-20+20+7=107, Kai 100-25+25+8=108, Ben 100-15=85

✅ Így a hibázók téte közvetlenül finanszírozza a győzteseket.

---

# 6. Elimináció

* Round 3-tól **bottom 20%** kiesik vagy stack < 0
* Shield roundok alatt nincs kiesés

---

# 7. Event roundok

* **Double round**: x2 multiplier
* **Chaos / Jackpot round**: nagy stack swingek
* Arányos pot elosztással tovább fokozza a varianciát

---

# 8. Bounty mechanika (passzív)

* Leader (top stack) jelölve bounty-val
* Ha a leader kiesik, mindenki kap kis bónuszt (stack / coins)
* Vizualizálja a **drámai célpontot**, de nincs direkt player-to-player attack

---

# 9. Spectator / dopamin pillanatok

* Reveal animáció
* Stack változás / leaderboard ugrás
* All-in / Confidence Duel pillanatok
* Final showdown

---

# 10. Signature mechanic

* **Confidence Duel / pot-os rendszer kombinálva**:

  * Nagy bet → kihívható
  * Hibázó téte arányosan a győztesek között
* Magas pszichológiai feszültség és nézhetőség

---

# 11. Kérdés típusok

* 60–70% guessable
* Példák: pop culture, geography, science, logos, images
* Risk management > pure knowledge

---

# 12. Ranked ladder

* Stack → pont → rank → arena
* Vizualizált arénák: Bronze → Silver → Gold → Platinum → Diamond

---

# 13. Season reset

* Havi reset
* **Floor mechanic**: legalább bizonyos rank / aréna szint megmarad
* Progress nem vész el teljesen, motiváló

---

# 14. Daily ranked matches

* Limit: 5–6 meccs számít / nap
* Legjobb 4–5 meccs pontja kerül beszámításra
* Csökkenti a frusztrációt, minden meccs fontos

---

# 15. Daily / Weekly / Monthly leaderboard

* **Daily:** legjobb meccsek pontja
* **Weekly:** összegzett napi pontok
* **Monthly:** season ranking
* A guild pontok is összeadódnak napi/hetente/havonta

---

# 16. Guild rendszer

* Guildbe léphetnek a játékosok
* Guild pont: player stack / pot alapján
* Heti guild leaderboard
* Guild rewards: badge, banner, coins, extra tickets

---

# 17. Jutalmak

* **Cosmetics:** avatar frame, stack skin, reveal animation
* **Titles:** Trivia Sniper, Risk Master, Weekly Champion, Diamond Brain
* **Currency:** coins → high stakes arena, cosmetics, tickets

---

# 18. Monetization

* Hybrid modell: **ads + in-app purchase**
* Mechanikák: entry tickets, revive, cosmetics, season pass, high stakes arena

---

# 19. Session loop

* Belépés → 3–6 meccs → napi pont javítása → leaderboard → guild progress
* Dopamin pillanatok: pot reveal, leaderboard swing, all-in, near-miss

---

# 20. Core retention mechanikák

1. Stack + bet: kockázatkezelés
2. Leaderboard swing: nagy ugrások
3. Near miss effect: majdnem kiesők motiválása
4. Daily limit: minden nap számít
5. Guild verseny: közösségi motiváció
6. Egyszerű játékkeresés: különböző botok csatlakoznak ha nincs elég játékos a lobby-ban

---

# 21. Addiktív mechanikák

* Pot-os rendszer: hibázók téte finanszírozza a győzteseket
* All-in / Confidence Duel pillanatok
* High multiplier rounds → comeback lehetőség
* Daily/weekly/montly ladder + guild → folyamatos cél

---

# 22. Identitás és hangulat

* **Core:** knowledge + risk management
* **Hangulat:** quiz + poker + battle royale
* **Match idő:** ~3–4 perc
* **Addiktív:** gyors eliminációk, high variance, social layer, streamable