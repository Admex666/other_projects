---
id: master-planner-blueprint
type: system
name: Master Planner Blueprint & System Architecture Specification
status: active

description: Az Optivoya Master Travel Planner teljes, implementációs szintű műszaki specifikációja (Master Architecture Blueprint). Részletezi az 5-lépéses progresszív döntési állapotgépet, a Pydantic adatmodelleket, a kétfázisú AHP Döntési DNS motort, a PROMETHEE II vektorizált outranking algoritmust, a 4-pilléres desztináció- és TripScore matematikai modelleket, a Shannon-entrópia élménydiverzitást, a valós idejű külső integrációkat, a kliensoldali Facade architektúrát és a REST API szerződéseket.

source:
  type: code
  ref: app.services.planner_service

code:
  - app/models/models.py
  - app/api/v2/planner.py
  - app/services/planner_service.py
  - app/services/destination_scoring_service.py
  - app/services/trip_scoring_service.py
  - app/services/destination_service.py
  - app/services/numbeo_service.py
  - app/services/weather_service.py
  - app/services/accommodation_market_service.py
  - app/services/experience/trip_generator.py
  - templates/planner/planner_wizard.html
  - static/js/planner/planner_state.js
  - static/js/planner/planner_intake.js
  - static/js/planner/planner_destinations.js
  - static/js/planner/planner_flights.js
  - static/js/planner/planner_stays.js
  - static/js/planner/planner_activities.js
  - static/js/planner/planner_summary.js
  - static/js/planner_wizard.js
  - static/js/trip_cart.js

related:
  - "[[master-planner-wizard]]"
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[proposal-generation]]"
  - "[[itinerary-optimization]]"
  - "[[experience-ingestion-pipeline]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[guided-progressive-decision-flow]]"
  - "[[numbeo-cost-model]]"
  - "[[honest-scraping-policy]]"
  - "[[progressive-async-prefetching]]"
  - "[[trip-cart-engine]]"
  - "[[fastapi-backend]]"
  - "[[supabase-database]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
  - "[[open-meteo-api]]"
  - "[[numbeo-database]]"
  - "[[effective-vacation-time]]"
  - "[[unified-trip-score]]"
  - "[[experience-intelligence-engine]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"

used_by:
  - "[[fastapi-backend]]"
---

# 🧭 Optivoya Master Travel Planner — Master Architecture Blueprint (v2.0)

Ez a dokumentum az **Optivoya Master Travel Planner** teljes, implementációs szintű műszaki specifikációja. Célja, hogy egy rendszermérnök vagy AI ágens a forráskód, a matematikai algoritmusok, az adatmodellek és a REST API szerződések alapján a teljes döntési motort külső kontextus nélkül reprodukálni és üzemeltetni tudja.

---

## 1. Rendszerarchitektúra és Futásidejű Topológia

Az Optivoya Master Travel Planner egy vezérelt, lineáris, mégis dinamikusan újrakalkuláló döntési állapotgépet valósít meg a **[[guided-progressive-decision-flow]]** elv szerint.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPTIVOYA PLANNER TOPOLÓGIA                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. KLIENS RÉTEG (Browser PWA / Desktop / Mobile):                                      │
│    - Vanilla JS Moduláris Facade: `PlannerState`, `TripCart`, `DecisionDNAWizard`      │
│    - Reaktív Stepper Állapotgép (Step 0 → Step 5, függőségi zárolással)                │
│    - Kliensoldali Cache (SessionStorage, 30 perces TTL) & Telemetria                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. API RÉTEG (FastAPI v2 — `app/api/v2/planner.py`):                                  │
│    - POST `/api/planner/init-destinations` (Aszinkron háttérszámítás indítása)         │
│    - GET  `/api/planner/destinations-status` (Polling & progresszív állapot lekérdezés) │
│    - POST `/api/planner/search-flights` (PROMETHEE II vektorizált járatszűrés/rangsor) │
│    - POST `/api/planner/search-stays` (Cozycozy aggregált szálláslekérdezés)          │
│    - POST `/api/trip/sync` & GET `/api/trip/active` (UnifiedTrip szinkronizáció)       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. SZOLGÁLTATÁSI & SZÁMÍTÁSI MOTOROK (`app/services/`):                                │
│    - `PlannerService` (AHP súlyok, Kiwi repülőjegy kombinációk, PROMETHEE II motor)    │
│    - `DestinationScoringService` (4-pilléres normalizálás, Experience koszinusz vektor)│
│    - `TripScoreService` (Kompozit 0–100 TripScore, Shannon-entrópia diverzitás, EVT)   │
│    - `TripGenerator` & `ItineraryOptimizationService` (Napi bontás, POI ütemezés)      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. KANONIKUS KÜLSŐ ÉS BELSŐ FORRÁSOK:                                                 │
│    - Kiwi.com GraphQL API → Élő menetrendek, viteldíjak és átszállási idők            │
│    - Cozycozy Scraper → Hotelek, apartmanok valós árai és minősítései                  │
│    - Open-Meteo API → 10 éves historikus és előrejelzett éghajlati adatok              │
│    - Numbeo Adatbázis (`data/live_numbeo_indices.json`) → 45+ európai város költségei  │
│    - Experience Intelligence Cache → 12-dimenziós élményvektorok és POI profilok       │
│    - Supabase PostgreSQL / Helyi SQLite → Felhasználók, munkamenetek, telemetria       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Kanonikus Adatmodellek & Entitások (`app/models/models.py`)

A rendszer szigorúan típusos **Pydantic v2** modellekre épül:

### 2.1 Bemeneti és Preferencia Modellek
* `MasterPlannerIntake`: A kezdeti intake űrlap és a Döntési DNS modál által küldött aggregált kérés:
  * `origin`: Indulási város vagy IATA kód (pl. `"Budapest (BUD)"`).
  * `date_mode`: Dátumválasztási mód: `"exact"` (pontos napok), `"interval"` (rugalmas ablak), `"month"` (egész hónap).
  * `month`, `year`: Célhónap (1–12) és év.
  * `exact_out_date`, `exact_in_date`: ISO dátumsztringek (`YYYY-MM-DD`).
  * `out_from`, `out_to`, `in_from`, `in_to`: Intervallum határok.
  * `min_stay`, `max_stay`, `duration`: Tartózkodási napok száma.
  * `adults`, `children`: Utasok száma.
  * `target_temp`: Preferált nappali hőmérséklet (°C, alapértelmezett: 24.0).
  * `min_safety`: Minimális Numbeo biztonsági index küszöb (0–100).
  * `ahp_weights`: A 4 fő pillér súlya (`total_cost`, `weather`, `safety`, `experience`).
  * `experience_preferences`: 12 dimenziós élménypreferencia vektor (`culture`, `gastronomy`, `beach`, `nature`, `nightlife`, `authenticity`, `adventure`, `relaxation`, `family`, `romance`, `shopping`, `sightseeing`).
  * `logistics_preferences`: Napi menetrend preferenciák (`day_start_time`, `day_end_time`, `max_walking_minutes`, `transport_modes`).
  * `dummy_mode`: Boolean jelző szimulációs teszteléshez.

### 2.2 Desztináció és Eredmény Modellek
* `TripDestination`:
  * `dest_id`, `name`, `city`, `country`, `region`: Desztináció azonosítók.
  * `rank`: Globális sorrend (1..N).
  * `score`: 4-pilléres kompozit alkalmassági pontszám (0.0–100.0).
  * `flight_price_huf`, `flight_price_per_person`: Becsült járatköltség.
  * `temp_avg`: Várható átlagos/csúcshőmérséklet.
  * `safety_index`: Numbeo biztonsági mutató (0–100).
  * `daily_cost_eur`, `numbeo_breakdown`: Helyi fogyasztói kosár struktúra.
  * `highlights`, `explanation`, `tradeoff`: Determinisztikus indoklás és kompromisszum.

### 2.3 Járat és Szállás Modellek
* `TripFlightItem`:
  * `airline`, `out_airport`, `in_airport`: Járatparaméterek.
  * `price_total_huf`, `price_per_person_huf`: Teljes és per-fő költség.
  * `out_date`, `in_date`, `out_time`, `in_time`: Menetrend.
  * `duration_h`: Menetidő órában oda-vissza.
  * `stops`: Átszállások száma.
  * `phi_net`: PROMETHEE II nettó preferencia áramlás ($\Phi^{\text{net}} \in [-1.0, +1.0]$).
  * `relevance_pct`: Normalizált illeszkedési százalék ($45\% - 99\%$).
  * `booking_token`, `booking_url`: Mélylink a partner felületére.

* `TripAccommodationItem`:
  * `name`, `stars`, `rating`, `review_count`: Minőségi indikátorok.
  * `price_total_huf`, `price_per_night_huf`, `nights`: Költségstruktúra.
  * `address`, `city`, `lat`, `lon`, `amenities`, `booking_url`: Lokáció és szolgáltatások.

### 2.4 Központi Döntési Aggregátum (`UnifiedTrip`)
A `UnifiedTrip` entitás a teljes utazási folyamat állandó állapotmodellje:
```python
class UnifiedTrip(BaseModel):
    trip_id: str
    user_id: Optional[str] = "default_user"
    status: str  # initialized | destination_selected | flight_selected | accommodation_selected | proposal_ready
    input: TripInput
    destination: Optional[TripDestination]
    flight: TripFlightSearch
    accommodation: TripAccommodationSearch
    budget: TripBudgetBreakdown
    experience_preferences: Optional[ExperiencePreferences]
    logistics_preferences: Optional[LogisticsPreferences]
    trip_score: Optional[Union[float, Dict[str, Any]]]
    activities: Optional[Dict[str, Any]]
```

---

## 3. Döntési DNS Architektúra & Kétfázisú AHP Súlyozó Motor

A rendszer nem kényszerít a felhasználóra merev, beégetett súlyokat. A súlyvektort az **[[ahp-weighting]]** módszertan segítségével állítja elő a `compute_ahp_weights_from_comparisons` függvény.

### 3.1 Kétfázisú Szempont-Jóváhagyási Folyamat
1. **1. Fázis (Aktiválás & Előszűrés):** A felhasználó kiválasztja a releváns szempontokat a 4 alappillérből (Költség, Időjárás, Biztonság, Élmények). A páros összehasonlító csúszkák nem jelennek meg mindaddig, amíg a felhasználó jóvá nem hagyja a szempontokat.
   * Ha csak 1 szempontot választ: $w_1 = 1.0$ (100%), a felesleges páros összehasonlítások automatikusan átugrásra kerülnek.
2. **2. Fázis (Páros Súlyozás):** Kizárólag a kiválasztott $k$ szempont közötti feszültségek kerülnek kiértékelésre.

### 3.2 Maximum 5 Összehasonlítás & Geometriai Tranzitivitás
Kognitív túlterhelés elkerülésére legfeljebb **5 feszítő páros összehasonlítás** jelenik meg. Ha $n = 4$ esetén $\frac{n(n-1)}{2} = 6$ pár létezne, a kimaradó $a_{ik}$ értéket a motor a Saaty-féle multiplikatív tranzitivitási szabállyal határozza meg:

$$a_{ik} = a_{ij} \cdot a_{jk}$$

### 3.3 Kiterjesztett 9-Pontos Saaty-Skála
A csúszkák mindkét irányban 4 diszkrét lépést tesznek lehetővé ($1, 3, 5, 7, 9$ és reciprokaik):
* $1$: Egyenlő fontosság ($a_{ij} = 1.0$)
* $3$: Mérsékelten fontosabb ($a_{ij} = 3.0$, illetve $1/3$)
* $5$: Erősen fontosabb ($a_{ij} = 5.0$, illetve $1/5$)
* $7$: Nagyon erősen fontosabb ($a_{ij} = 7.0$, illetve $1/7$)
* $9$: Extrém mértékben fontosabb ($a_{ij} = 9.0$, illetve $1/9$)

### 3.4 Súlyvektor Számítás (Geometric Mean Method)
A páros összehasonlító mátrixból ($A \in \mathbb{R}^{n \times n}$) a normalizált sajátvektor-súlyok geometriai átlaggal adódnak:

$$r_i = \left( \prod_{j=1}^n a_{ij} \right)^{1/n}, \quad w_i = \frac{r_i}{\sum_{k=1}^n r_k}, \quad \sum_{i=1}^n w_i = 1.0$$

---

## 4. A 4-Pilléres Célállomás Rangsoroló Modell (`DestinationScoringService`)

A desztinációk kiértékelése és rangsorolása a `calculate_destination_rankings` függvényben valósul meg a 4 pillér normalizált pontszámainak súlyozott összegeként:

$$\text{TotalScore} = \left( w_{\text{cost}} \cdot s_{\text{cost}} + w_{\text{weather}} \cdot s_{\text{weather}} + w_{\text{safety}} \cdot s_{\text{safety}} + w_{\text{exp}} \cdot s_{\text{exp}} \right) \times 100.0$$

### 4.1 Az Egyes Pillérek Számítási Képletei

#### 1. Költség Pillér ($s_{\text{cost}} \in [0.0, 1.0]$)
A desztináció teljes várható utazási költsége:

$$\text{Cost}_{\text{total}} = \text{FlightPrice}_{\text{HUF}} + \text{HotelCost}_{\text{HUF}} + (\text{DailyCost}_{\text{HUF}} \cdot \text{DurationDays})$$

Normalizálás min-max inverz skálázással (alacsonyabb költség = magasabb pontszám):

$$s_{\text{cost}} = \frac{\max(\text{Cost}_{\text{total}}) - \text{Cost}_{\text{total}}}{\max(\text{Cost}_{\text{total}}) - \min(\text{Cost}_{\text{total}})}$$

#### 2. Időjárás Pillér ($s_{\text{weather}} \in [0.0, 1.0]$)
Az Open-Meteo 10 éves historikus napi maximum hőmérséklete ($T_{\max}$) és a célhőmérséklet ($T_{\text{target}}$) eltérése alapján:

$$s_{\text{weather}} = \max\left(0.0, 1.0 - \frac{|T_{\max} - T_{\text{target}}|}{15.0}\right)$$

#### 3. Biztonsági Pillér ($s_{\text{safety}} \in [0.0, 1.0]$)
Numbeo Safety Index ($0–100$) skálázva:

$$s_{\text{safety}} = \text{clip}\left(\frac{\text{SafetyIndex}}{100.0}, 0.0, 1.0\right)$$

#### 4. Élményilleszkedési Pillér ($s_{\text{exp}} \in [0.2, 1.0]$)
Ha a felhasználó megadta az élménypreferenciáit ($\vec{u}$), a motor a desztináció 12-dimenziós profilvektorával ($\vec{d}$) számítja ki az illeszkedést:

$$s_{\text{exp}} = \sum_{k=1}^{12} u_k \cdot \left(\frac{d_k}{100.0}\right), \quad \text{ahol } \sum u_k = 1.0$$

Ha nincsenek egyéni preferenciák, a desztináció top-3 élménydimenziójának átlaga és a POI-entitások száma adja a pontszámot:

$$s_{\text{exp}} = \text{clip}\left(\frac{\text{Top3Avg}}{100.0} \times 0.80 + \min\left(1.0, \frac{N_{\text{entities}}}{45.0}\right) \times 0.20, 0.40, 1.0\right)$$

---

## 5. PROMETHEE II Vektorizált Járatoptimalizáló Motor

A kiválasztott városba induló repülőjáratok rangsorolása a **[[promethee-ranking]]** (Preference Ranking Organization METHod for Enrichment Evaluations) outranking algoritmusával történik a `search_and_rank_planner_flights` függvényben.

### 5.1 Kritériumok Definíciója (Mind Minimalizálandó)
1. $g_1$: Repülőjegy teljes ára oda-vissza (HUF)
2. $g_2$: Teljes menetidő oda-vissza (óra)
3. $g_3$: Átszállások száma oda-vissza (db)
4. $g_4$: Tartózkodási idő eltérése a cél-tartózkodástól (nap)
5. $g_5$: Indulási és érkezési napszak eltérése a kívánt órától (óra)

### 5.2 Dinamikus Kritérium-Súlyok ($w_k$)
A súlyvektor a dátumválasztási mód és a felhasználói prioritások függvényében dinamikusan átrendeződik:
* **Pontos dátum (`date_mode = exact`):** $w_{\text{stay}} = 0.0$ (a napok száma kőbe vésett), $w_{\text{price}} = 0.40$, $w_{\text{time}} = 0.35$, $w_{\text{stops}} = 0.25$.
* **Rugalmas intervallum (`date_mode = interval`):** $w_{\text{stay}} = 0.20$, $w_{\text{price}} = 0.35$, $w_{\text{time}} = 0.25$, $w_{\text{stops}} = 0.15$.

### 5.3 Preferenciafüggvények és Küszöbértékek
A kritérium-különbség minimalizálás esetén: $d_k(a, b) = g_k(b) - g_k(a)$ (ha $a$ értéke kisebb, akkor $a$ jobb mint $b$, így $d_k > 0$).

A rendszer 5 standard Brans-Vincke preferenciafüggvényt támogat:
* **Type 1 (Usual / Szigorú):** $P(d) = 1$, ha $d > 0$; különben $0$.
* **Type 2 (U-shape / Quasi):** $P(d) = 1$, ha $d > q$; különben $0$.
* **Type 3 (V-shape / Lineáris):** $P(d) = \text{clip}\left(\frac{d}{p}, 0, 1\right)$.
* **Type 4 (Level / Lépcsős):** $P(d) = 0$, ha $d \le q$; $0.5$, ha $q < d \le p$; $1.0$, ha $d > p$.
* **Type 5 (V-shape with Indifference — Alapértelmezett):**

$$P_k(d) = \begin{cases} 
0, & \text{ha } d \le q_k \\
\frac{d - q_k}{p_k - q_k}, & \text{ha } q_k < d \le p_k \\
1, & \text{ha } d > p_k 
\end{cases}$$

Alapértelmezett küszöbök ($q$: közömbösségi határ, $p$: abszolút preferencia határ):
* Ár ($g_1$): $q = 5\,000\text{ Ft}, \quad p = 35\,000\text{ Ft}$ (Type 5)
* Menetidő ($g_2$): $q = 0.5\text{ óra}, \quad p = 3.0\text{ óra}$ (Type 5)
* Átszállás ($g_3$): $q = 0.0, \quad p = 1.0$ (Type 1)
* Tartózkodás ($g_4$): $q = 1.0\text{ nap}, \quad p = 3.0\text{ nap}$ (Type 5)
* Napszak ($g_5$): $q = 0.0, \quad p = 5.0\text{ óra}$ (Type 3)

### 5.4 Vektorizált Tenzor Számítás és Outranking Flows
A számítás $N$ alternatívára optimalizált NumPy tenzorműveletekkel fut ($O(N^2)$ komplexitás):
1. **Páros különbség tenzor:** $D \in \mathbb{R}^{N \times N \times 5}$
2. **Aggregált preferencia index:** $\Pi(a, b) = \sum_{k=1}^5 w_k \cdot P_k(d_k(a, b))$
3. **Pozitív kiáramló erő (Leaving Flow):** $\Phi^+(a) = \frac{1}{N - 1} \sum_{b \ne a} \Pi(a, b)$
4. **Negatív beáramló gyengeség (Entering Flow):** $\Phi^-(a) = \frac{1}{N - 1} \sum_{b \ne a} \Pi(b, a)$
5. **Nettó Outranking Flow:** $\Phi^{\text{net}}(a) = \Phi^+(a) - \Phi^-(a) \in [-1.0, +1.0]$

A nettó flow-ból származtatott felhasználóbarát relevancia mutató:

$$\text{RelevancePct} = \text{clip}\left(\text{round}\left( \frac{\Phi^{\text{net}} + 1.0}{2.0} \times 100 \right), 45, 99\right)$$

---

## 6. Szállás-aggregációs & Minőségbiztosítási Motor

A szálláskeresés a `search_stays` és `get_all_stays` modulokon keresztül, valós idejű Cozycozy adatfolyamból táplálkozik:
* **Dátumzárolt Keresés:** A Step 2-ben zárolt repülőjárat pontos érkezési és indulási dátumaira szűkít ($N_{\text{nights}} = \text{date}_{\text{checkout}} - \text{date}_{\text{checkin}}$).
* **Értékelési Skála Normalizálás:** Cozycozy 100-as skáláról standard 10-es bázisra ($R_{10} = R_{\text{cozy}} / 10.0$).
* **Minőségi Küszöbök:** Minimális csillagszám ($\ge 3\star$), értékelési küszöb ($\ge 7.5$), ellátási szűrés (reggeli).
* **[[honest-scraping-policy]]:** Nincsenek generált vagy kamu szállásajánlatok. Valós API hiba esetén a rendszer kontrollált béta mock fallbackre vált átlátható jelzéssel.

---

## 7. Élményintelligencia, Hasznos Nyaralási Idő & Shannon-Entrópia

### 7.1 Shannon-Entrópia Alapú Élménydiverzitás (`TripScoreService`)
A motor Shannon-féle információ-entrópiával méri a napi programcsomag kategória-egyensúlyát ($K$ élménykategória között):

$$H(X) = - \sum_{i=1}^K p_i \log_2(p_i), \quad \text{ahol } p_i = \frac{n_i}{N_{\text{total}}}$$

A normalizált diverzitási mutató ($D_{\text{exp}} \in [0.0, 1.0]$):

$$D_{\text{exp}} = \min\left(1.0, \frac{H(X)}{\log_2(\min(\max(K, 2), 5))}\right)$$

### 7.2 Hasznos Nyaralási Idő (`calculate_effective_vacation_time`)
A [[effective-vacation-time]] koncepció a célállomáson tölthető, ébren lévő, aktív órákat számszerűsíti:
* **Érkezési nap:** Nappali órák a járat érkezése után 1.5 órás reptéri és transzfer pufferrel ($T_{\text{arr}} + 1.5$).
* **Hazautazási nap:** Nappali órák a járat indulása előtt 2.5 órás reptéri pufferrel ($T_{\text{dep}} - 2.5$).
* **Teljes köztes napok:** Napi fix 10 aktív órával kalkulálva:

$$\text{EVT} = \max(0, 20.0 - \max(8.0, T_{\text{arr}} + 1.5)) + \max(0, \min(18.0, T_{\text{dep}} - 2.5) - 8.0) + \max(0, \text{Days} - 2) \times 10.0$$

---

## 8. Kompozit Unified TripScore™ Matematikai Modell

A teljes utazási csomag összegző pontszáma ($0–100$) a 4 pillér harmonizált szintézise:

$$\text{TripScore} = \text{clip}\left(\text{round}\left( w_d S_{\text{dest}} + w_f S_{\text{flight}} + w_s S_{\text{stay}} + w_e S_{\text{exp}} - \text{FrictionPenalty} \right), 30, 99\right)$$

### 8.1 Komponens Pontszámok és Módosítók
1. **$S_{\text{dest}}$:** Célállomás pontszám ($0–100$).
2. **$S_{\text{flight}}$:** Járat pontszám a PROMETHEE relevanciából ($45–99$), EVT módosítóval:
   * $\text{EVT} \ge 20\text{ óra} \implies +4\text{ pont}$
   * $\text{EVT} \le 10\text{ óra} \implies -6\text{ pont}$
3. **$S_{\text{stay}}$:** Szállás pontszám a vendégértékelésből ($R_{10} \times 10$), prémium csillag bónusszal:
   * $\text{Stars} \ge 4 \implies +3\text{ pont}$
4. **$S_{\text{exp}}$:** Élmény pontszám: $\frac{\text{Rating}_{\text{avg}}}{5.0} \times 85.0 + D_{\text{exp}} \times 15.0$.
5. **$\text{FrictionPenalty}$:** Logisztikai súrlódási büntetés:
   * Átszállásos járat esetén: $\text{FrictionPenalty} = 5.0\text{ pont}$.

---

## 9. Kliensoldali Állapotgép & Facade Architektúra

A kliensoldal Vanilla JS alapon épül fel a maximális sebesség és nulla függőségi többlet érdekében:

### 9.1 Reaktív Stepper Állapotgép (`PlannerState`)
* **Szigorú Lépés-Zárolási Invariáns (`canAccessStep`):**
  * Step 0 (Preferenciák): Mindig elérhető.
  * Step 1 (Célállomások): Csak ha lefutott a keresés és `destinations.length > 0`.
  * Step 2 (Járatok): Csak ha `selectedDest` kiválasztva és `flights.length > 0`.
  * Step 3 (Szállások): Csak ha `selectedFlight` kiválasztva és `stays.length > 0`.
  * Step 4 (Élmények) & Step 5 (Kész Terv): Csak ha a célállomás, járat és szállás zárolva van.
* **Gyorsítótárazás:** `sessionStorage` alapú válasz-gyorsítótár 30 perces TTL-lel (`getSessionCache` / `setSessionCache`).

### 9.2 Lebegő Utazási Kosár Facade (`TripCart` / `TripEngine`)
A kosár motor 4 rétegre bontott Facade architektúrát követ ([trip_cart.js](file:///e:/Data/other_projects/dreamtrip/static/js/trip_cart.js)):
1. `TripStore`: Állapotperzisztencia (`localStorage`, szerver szinkronizáció `/api/trip/sync`).
2. `TripCalculator`: Numbeo alapú dinamikus költségvetés-bontás (repülő, hotel, napi étkezés, transzfer).
3. `TripDrawer`: Reszponzív lebegő sáv és oldalsó csúszó fiók renderelése.
4. `TripReport`: Nyomtatható és megosztható B2B utazási ajánlat exportáló.

---

## 10. REST API Szerződések & Végpont Katalógus

| Végpont | Metódus | Request Modell | Response / Funkció |
| :--- | :--- | :--- | :--- |
| `/api/planner/init-destinations` | `POST` | `MasterPlannerIntake` | Aszinkron háttérszámítás indítása (`planner_status = running`). |
| `/api/planner/destinations-status` | `GET` | — | Polling végpont: progress (0–100%), státusz szöveg és kész desztináció lista. |
| `/api/planner/search-flights` | `POST` | `PlannerFlightSearchRequest` | PROMETHEE II rangsorolt járatok listája (`flights`, `phi_net`, `relevance_pct`). |
| `/api/planner/search-stays` | `POST` | `PlannerStaySearchRequest` | Cozycozy aggregált szálláslista tartózkodási összköltséggel (`stays`). |
| `/api/trip/sync` | `POST` | `UnifiedTrip` | Aktív kosár és tervezési állapot mentése a szerveroldali memóriába / DB-be. |
| `/api/trip/active` | `GET` | `trip_id` (opcionális query) | Aktív mentett utazási kosár lekérdezése munkamenet alapján. |

---

## 11. Automatizált E2E Tesztarchitektúra & Minőségbiztosítás

A Master Planner megbízhatóságát és regresszió-mentességét szisztematikus Playwright E2E tesztcsomag garantálja (`tests/e2e/test_master_planner_e2e.py`):

### 11.1 Tesztcsoportok
1. `test_planner_page_load_and_elements`: 0 fatális konzolhiba és alapvető UI elemek jelenléte.
2. `test_step0_intake_controls_and_presets`: Naptár üzemmódok (Exact, Interval, Month), létszám számlálók és stílus chipek.
3. `test_decision_dna_modal_workflow`: Kétfázisú döntési DNS modál megnyitása, szempont jóváhagyás, Saaty csúszkák mozgatása és AHP súlymentés.
4. `test_full_golden_flow_dummy_mode`: A teljes 5-lépéses Golden Flow (Célállomás kiválasztás $\to$ Járat zárolás $\to$ Szállás kiválasztás $\to$ Programok $\to$ Kész Terv és Lebegő Kosár) szimulálása.
5. `test_stepper_back_and_forward_navigation`: Lépések közötti közvetlen ugrás és állapotmegőrzés.
6. `test_mobile_viewport_no_horizontal_overflow`: 375px mobil nézet (iPhone SE) túlcsordulás-mentességének validálása.

### 11.2 Futtatási Parancs
```powershell
python -m pytest tests/e2e/test_master_planner_e2e.py -v
```

---

## 12. Governance & Minőségi Invariánsok

1. **[[honest-scraping-policy]]:** Nincsenek szintetikus vagy rejtett dummy árak éles módban; forráskiesés esetén transzparens állapotjelzés lép életbe.
2. **[[ANTI_AI_SLOP_POLICY]]:** Belső technikai algoritmusnevek (PROMETHEE II, AHP sajátvektor, Saaty mátrix) nem jelennek meg közvetlenül a végfelhasználói B2C felületen; helyettük emberközpontú magyarázatok (pl. „94% személyes egyezés”) láthatók.
3. **[[DESIGN_SYSTEM]]:** Sötét/világos prémium paletta, JetBrains Mono számszerűségi elemek, Inter folyószöveg, Plus Jakarta Sans címek.
4. **[[QUALITY_GATES]] & [[DEFINITION_OF_DONE]]:** A kód, az adatmodellek, a matematikai algoritmusok és a Markdown tudásgráf 100%-os szinkronban vannak:
   ```powershell
   python scripts/knowledge/validate.py
   ```
