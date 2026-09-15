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

## 0. Kétfázisú Szempont-Jóváhagyás & Kiterjesztett Saaty-Skála (AHP v2.5)

A kognitív terhelés minimalizálására és a döntési szabadság növelésére az Optivoya a következő döntési architektúrát alkalmazza:

### 1. Kétfázisú Kiválasztási és Jóváhagyási Folyamat
- **1. Fázis (Előzetes Kiválasztás & Jóváhagyás):** A felhasználó minden döntési pillérnél (Célállomás, Járat, Szállás) **először kijelöli, mely szempontok relevánsak számára, és ezt egy jóváhagyó gombbal megerősíti**. A csúszkák e megerősítés előtt rejtve maradnak.
- **2. Fázis (Páros Súlyozás):** Csak a jóváhagyott szempontok kerülnek összehasonlításra. A felhasználó bármikor visszatérhet a szempontok módosításához a „✎ Szempontok módosítása” gombbal.
- **Inaktív szempontok:** Automatikusan **0% súlyt** kapnak.
- **Egyetlen kiválasztott szempont esetén:** Nincs szükség páros összehasonlításra, a kiválasztott szempont automatikusan **100%-os prioritást** kap.

### 2. Maximum 5 Összehasonlítás Szabálya & Tranzitivitásos Kiegészítés
- A kognitív túlterhelés („Analysis Paralysis”) megelőzésére a felhasználónak **legfeljebb 5 páros összehasonlítást** kell elvégeznie egy lépésben.
- Ha 4 szempont aktív (amely elméletben $\frac{4 \cdot 3}{2} = 6$ párt jelentene), a felület **pontosan 5 kulcsfontosságú feszítő párt** jelenít meg.
- A kimaradó párt a döntési motor a meglévő párok közötti **geometriai tranzitivitás** alapján automatikusan és konzisztensen számítja ki:
  $$M_{ij} = \left( \prod_{k \neq i,j} (M_{ik} \cdot M_{kj}) \right)^{1/m}$$
  Ez biztosítja a Saaty-féle reciprocitást ($M_{ji} = 1 / M_{ij}$) és a mátrix matematikai zárt konzisztenciáját.

### 3. Kiterjesztett 9-Pontos Saaty-Skála (3-5-7-9)
- A csúszka **9 fokozatú skálát** valósít meg (+1 barázda mindkét irányba a középponttól, összesen 9 jelölő barázda, középpont = 4):
  - **Index 0:** Extrém mértékben inkább $c_1$ felé (Saaty-arány: $9.0$)
  - **Index 1:** Sokkal inkább $c_1$ felé (Saaty-arány: $7.0$)
  - **Index 2:** Kifejezetten inkább $c_1$ felé (Saaty-arány: $5.0$)
  - **Index 3:** Kissé inkább $c_1$ felé (Saaty-arány: $3.0$)
  - **Index 4:** Egyformán fontos (Saaty-arány: $1.0$)
  - **Index 5:** Kissé inkább $c_2$ felé (Saaty-arány: $1/3.0$)
  - **Index 6:** Kifejezetten inkább $c_2$ felé (Saaty-arány: $1/5.0$)
  - **Index 7:** Sokkal inkább $c_2$ felé (Saaty-arány: $1/7.0$)
  - **Index 8:** Extrém mértékben inkább $c_2$ felé (Saaty-arány: $1/9.0$)
- A felhasználói felület szigorúan **emberközpontú, természetes utazási nyelvezetet** használ (nincsenek matematikai zsargonok).

---

## 1. 4-Pilléres Célállomás Döntési Modell (Master Planner & Destination Matcher)

A célállomás-kiválasztás egy kétszintű (Level 1 + Level 2) döntési folyamatra épül:

### Level 1: Saaty Páros Összehasonlító Mátrix (Dinamikus Részhalmaz)
Négy független, egymást nem átfedő pillér súlyozása:
1. **💰 Teljes Utazási Költség (`total_cost` / `price`)**: Repülőjegy + napi étkezés és megélhetés (Numbeo) + becsült szállásköltség.
2. **☀️ Időjárás & Klíma (`weather`)**: Nappali átlaghőmérséklet és napsütés illeszkedése az ideális célhőmérséklethez (Open-Meteo).
3. **🛡️ Közbiztonság (`safety`)**: Nemzetközi Numbeo Safety Index és biztonságérzet.
4. **🎭 Élmények & Látnivalók (`experience`)**: A desztináció élménykínálatának gazdagsága és személyes illeszkedése.

A páros értékekből a Saaty-féle geometriai átlagolással és normalizálással származtatjuk az aktív pillérek súlyvektorát: $\mathbf{w} = [w_{cost}, w_{weather}, w_{safety}, w_{exp}]$, ahol $\sum w_i = 1.0$.

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
- **Preferált indulási napok és időpontok**:
  - *Indulási napok (Hétfő–Vasárnap)*: Kizárólagos szűrőfeltétel (**hard constraint**), a nem egyező járatok kizárásra kerülnek.
  - *Indulási időpontok*: Körkörös órakülönbség alapján beépítve a járat preferenciapontszámába.

---

## 3. Szálláshely AHP Modell

A szállások értékelése az aktív szempontok súlyozásával történik:
1. **Ár / Éjszaka**: Teljes kinttartózkodási költség (szigorúan összehangolva a járat éjszakaszámával).
2. **Értékelés & Csillagszám**: Hitelesített vendégértékelések (Cozycozy/Booking).
3. **Központi Elhelyezkedés**: Belvárostól és főbb élménycsomópontoktól mért távolság.
4. **Felszereltség & Reggeli**: Ingyenes reggeli, Wi-Fi, légkondicionáló, rugalmas lemondás.

