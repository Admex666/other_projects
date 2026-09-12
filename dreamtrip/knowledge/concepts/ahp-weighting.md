---
id: ahp-weighting
type: concept
name: Analytic Hierarchy Process (AHP)
status: active

description: Döntéselméleti matematikai eljárás, amely páros összehasonlító mátrixok sajátvektor-számításával állítja elő a felhasználói kritériumok súlyait a célállomás, repülőjárat és szállás döntésekben.

source:
  type: code
  ref: app.services.destination_scoring_service

code:
  - app/services/destination_scoring_service.py
  - app/services/scoring_service.py
  - static/js/decision_dna/dna_math.js
  - static/js/decision_dna/dna_dest_step.js

related:
  - "[[promethee-ranking]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[experience-vector-and-vibe-profiling]]"
  - "[[effective-vacation-time]]"
  - "[[unified-trip-score]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[master-planner-wizard]]"
---

# Concept: Analytic Hierarchy Process (AHP)

Az Optivoya az Analytic Hierarchy Process (AHP, Saaty-módszer) eljárást használja a döntési szempontok többdimenziós súlyozására. A redundáns összehasonlítások és a kognitív túlterhelés elkerülésére a döntési folyamat strukturált szintekre tagolódik.

---

## 1. 4-Pilléres Célállomás Döntési Modell (Master Planner & Destination Matcher)

A célállomás-kiválasztás egy kétszintű (Level 1 + Level 2) döntési folyamatra épül:

### Level 1: 4x4 Saaty Páros Összehasonlító Mátrix
Négy független, egymást nem átfedő pillér súlyozása $n=4$ dimenzióban (6 db páros csúszka):
1. **💰 Teljes Utazási Költség (`total_cost` / `price`)**: Repülőjegy + napi étkezés és megélhetés (Numbeo) + becsült szállásköltség.
2. **☀️ Időjárás & Klíma (`weather`)**: Nappali átlaghőmérséklet és napsütés illeszkedése az ideális célhőmérséklethez (Open-Meteo).
3. **🛡️ Közbiztonság (`safety`)**: Nemzetközi Numbeo Safety Index és biztonságérzet.
4. **🎭 Élmények & Látnivalók (`experience`)**: A desztináció élménykínálatának gazdagsága és személyes illeszkedése.

A páros értékekből a Saaty-féle geometriai átlagolással és normalizálással származtatjuk a pillérek súlyvektorát: $\mathbf{w} = [w_{cost}, w_{weather}, w_{safety}, w_{exp}]$, ahol $\sum w_i = 1.0$.

### Level 2: Vektoros Élményilleszkedés (Koszinusz Hasonlóság)
Az élménypillér (`s_exp`) nem puszta látnivalódarab-számolás (amely igazságtalanul a metropoliszokat előnyözné), hanem a célállomás 12-dimenziós **Vibe Profilja** és a felhasználó élménykategória-vektora közötti **koszinusz hasonlóság**:

$$\text{similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

- **Felhasználói vektor ($\mathbf{u}$)**: normalizált preferenciák a 6 főkategóriában (*Gasztronómia*, *Kultúra*, *Autentikusság*, *Természet*, *Tengerpart*, *Aktív*).
- **Célállomás vektor ($\mathbf{v}$)**: Bayes-i simított Vibe Engine profilértékek.
- Az élménypontszám Bayes-i konfidencia-súlyozással és lefedettségi szorzóval kerül kiszámításra:
  $$s_{\text{exp}} = 100 \cdot \left[ \text{sim} \cdot \left(0.40 + 0.60 \cdot \min(1.0, \sqrt{\frac{N_{\text{poi}}}{15}})\right) \right]$$

---

## 2. Repülőjárat AHP & PROMETHEE II Modell

A járatok rangsorolásakor az AHP preferenciák határozzák meg a PROMETHEE II outranking kritériumsúlyait:
- **Ár** ($g_1$): Retúr jegyár 1 főre vagy a teljes utazócsoportra.
- **Menetidő** ($g_2$): Tiszta utazási órák száma.
- **Átszállások száma** ($g_3$): Közvetlen vs. 1 vagy több átszállás súrlódási büntetése.
- **Tartózkodási keret / Hasznos Nyaralási Idő** ($g_4$): [[effective-vacation-time]] — a délelőtti érkezés és esti hazaindulás bónusza (+16–22 óra hasznos helyszíni idő).

---

## 3. Szálláshely AHP Modell

A szállások értékelése 4 mikroszintű szempont súlyozásával történik:
1. **Ár / Éjszaka**: Teljes kinttartózkodási költség.
2. **Értékelés & Csillagszám**: Hitelesített vendégértékelések (Cozycozy/Booking).
3. **Központi Elhelyezkedés**: Belvárostól és főbb élménycsomópontoktól mért távolság.
4. **Felszereltség & Reggeli**: Ingyenes reggeli, Wi-Fi, légkondicionáló, rugalmas lemondás.

