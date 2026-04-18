# ChainNetwork Decision Simulator - Architektúra Terv

Ez a dokumentum a ChainNetwork hűségprogram és viselkedés-optimalizáló rendszer **Decision Simulator** moduljának technikai felépítését és működési elvét vázolja fel. A cél egy olyan Streamlit alapú demo alkalmazás, amely valósághű (szimulált) adatokon keresztül mutatja be a rendszer üzleti hasznát.

## 1. A Szimulátor Célja
A szimulátor nem egy statikus dashboard, hanem egy **"Digital Twin"** modell, amely:
- Imitálja egy étterem/lánc napi forgalmát.
- Modellezi a vendégek egyéni és csoportos viselkedését.
- Kimutatja a különbséget a "Hagyományos üzemmód" (Baseline) és a "ChainNetwork üzemmód" (Intervention) között.

---

## 2. Technológiai Stack
- **Nyelv:** Python 3.x
- **Frontend/UI:** Streamlit (Interaktív csúszkák, "What-if" szcenáriók)
- **Adatkezelés:** Pandas, NumPy
- **Vizualizáció:** Plotly (Dinamikus grafikonok)
- **Statisztikai modellezés:** SciPy (Eloszlásfüggvények a látogatási időközökhöz)

---

## 3. Rendszerarchitektúra

### A. Data Generation Engine (A motor)
Ez a komponens felelős a szintetikus adatok előállításáért.
- **User Generator:** Egyedi profilok létrehozása (demográfia, bázis-visszatérési hajlandóság, átlagos költési keret).
- **Group Logic:** Véletlenszerű csoportképzés (Solo, Duo, Family, Friends) változó eloszlásokkal.
- **Event Generator:** Idősoros látogatási események (timestamps, table_id, order_value).

### B. Behavioral Models (A szimulált valóság)
A motor két párhuzamos valóságot szimulál:
1. **Baseline Model:** Az étterem jelenlegi állapota (nincs célzott incentive, alacsonyabb group-retention).
2. **ChainNetwork Model:** Beépített ösztönzők hatása:
    - **Host Incentive:** Aki társaságot hoz, extra jutalmat kap $\rightarrow$ növekvő átlagos csoportméret.
    - **Retention Trigger:** Prediktív push üzenetek hatása a visszatérési időre.
    - **Group Join Bonus:** Ha az asztaltársaság többi tagja is regisztrál, közös kedvezmény $\rightarrow$ magasabb azonosított júzerszám.

### C. Analytics Layer (Az üzleti logika)
A szimulált eseményekből számított KPI-k:
- **Uplift Calculation:** $\Delta$ Revenue, $\Delta$ Retention Rate, $\Delta$ Customer Lifetime Value (CLTV).
- **Network Metrics:** Host influence score, group connectivity.
- **ROI Model:** A rendszer költsége vs. a generált többletprofit.

---

## 4. Adatmodell (Séma)

| Entitás | Mezők | Leírás |
| :--- | :--- | :--- |
| **User** | `user_id`, `segment`, `loyalty_score` | Alapvető vevői adatok. |
| **Visit** | `visit_id`, `user_id`, `timestamp`, `spend` | Egyéni vásárlási esemény. |
| **GroupSession** | `session_id`, `host_id`, `members[]`, `table_id` | Csoportos látogatási adatok. |
| **Incentive** | `type`, `uplift_factor`, `cost` | A beavatkozás paraméterei. |

---

## 5. Streamlit UI Tervezett Funkciók

### Oldalsáv (Paraméterezés)
- **Étterem típusa:** Fast-casual, Fine dining, Pub (más-más bázis eloszlásokkal).
- **"What-if" Sliders:**
    - *Host Reward %:* Mennyire ösztönözzük a csoportvezetést?
    - *Retention Push Frequency:* Milyen agresszíven hívjuk vissza a lassan elmaradókat?
    - *Adoption Rate:* A vendégek hány százaléka regisztrál az appba?

### Főpanel (Vizualizáció)
- **Financial Growth:** Ösztönző hatása bevételre (Baseline vs. Optimized).
- **Retention Curve:** Cohort analízis vizualizációja.
- **Network Graph:** Host-guest kapcsolatok és a hálózat terjedése.
- **Profit Summary:** Összegző kártyák a "Total Value Created" bemutatására.

---

## 6. Implementációs Ütemterv (Roadmap)
1. **V0.1:** Alapvető Python generátor script (CSV kimenet).
2. **V0.2:** Streamlit alapváz interaktív grafikonokkal.
3. **V0.3:** Beavatkozási modell (Intervention) és Uplift logika.
4. **V0.4:** "Executive Summary" export funkció.
