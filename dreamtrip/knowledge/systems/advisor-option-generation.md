---
id: advisor-option-generation
type: system
name: Advisor Multi-Option & Archetype Generation Engine
status: active

description: A B2B Advisor Workspace döntési archetípus generátora (Best Overall, Best Value, Best Experience), objektív profiljai, normalizált pontszámítása és a 3-Option Rule szabályrendszere.

source:
  type: code
  ref: app.services.multi_option_engine

code:
  - app/services/multi_option_engine.py
  - app/services/trip_scoring_service.py
  - app/services/relative_comparison_service.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[trip-case]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 🗂️ Advisor Multi-Option & Archetype Generation Engine

Ez a dokumentum specifikálja az **Optivoya Advisor Workspace** 3 döntési archetípusának objektív számítási modelljét, diverzitási garanciáit és a 3-Option szabályt.

---

## 1. A 3 Döntési Archetípus

A döntéstámogató motor nem véletlenszerű csomagokat dob össze, hanem 3 jól megkülönböztethető, konzisztens stratégiát valósít meg:

```text
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│  🏆 OPTION A: BEST OVERALL   │   💡 OPTION B: BEST VALUE    │ 🌟 OPTION C: BEST EXPERIENCE │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ Kiegyensúlyozott menetrend,  │ Optimális költségvetés,      │ 4-5★ prémium szállás,        │
│ optimális ár-érték és a      │ okos járatválasztás a szilárd│ gazdag programkínálat és     │
│ legmagasabb TripScore index. │ minőségi alapok mellett.     │ maximális élmény/vibe fit.   │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## 2. Objektív Profilok & Normalizált Pontszámítás

A pontszámítás nem alkalmaz önkényes magic numberöket (pl. $10 \times \text{Stars} + 5 \times \text{Rating}$), hanem standardizált, $[0, 100]$ skálára normalizált dimenziókból épül fel:

### 1. Best Overall (Kiegyensúlyozott Összetett Index)
$$\text{Score}_{\text{Overall}} = \text{TripScore} \in [0, 100]$$
Ahol a $\text{TripScore}$ az AHP pillérsúlyok (Desztináció, Járat, Szállás, Élmény) és a PROMETHEE II rangsorolás alapján számított összetett index.

### 2. Best Value (Érték-Hatékonysági Index)
$$\text{Score}_{\text{Value}} = \min\left(100.0, \frac{\text{TripScore}}{\max\left(\frac{\text{Price}}{\text{Budget}_{\text{ref}}}, 0.3\right)} \times 0.8\right)$$
Ahol a magas minőség alacsonyabb relatív áron éri el a maximális hatékonyságot.

### 3. Best Experience (Élmény- és Minőség Fókusz)
$$\text{Score}_{\text{Exp}} = 0.35 \cdot S_{\text{stay}} + 0.25 \cdot S_{\text{act}} + 0.25 \cdot S_{\text{vibe}} + 0.15 \cdot S_{\text{flight}}$$
Ahol minden komponens standard $[0, 100]$ skálán mozog:
- $S_{\text{stay}} = \left(\frac{\text{Stars}}{5.0} \times 50\right) + \left(\frac{\text{Rating}}{10.0} \times 50\right)$
- $S_{\text{act}} = \min\left(\frac{N_{\text{activities}}}{4.0}, 1.0\right) \times 100$
- $S_{\text{vibe}} = \text{DestinationVibeScore} \in [0, 100]$
- $S_{\text{flight}} = 100.0 \text{ (ha közvetlen)}, 75.0 \text{ (ha 1 átszállás)}, 50.0 \text{ (több)}$

---

## 3. A 3-Option Szabály (Quality Invariant)

```text
Cél: 3 opció (Target: 3)
Előnyben részesített: 3 (Preferred: 3)
Elfogadható: 2 (Acceptable: 2)
Minimum: 1 (Minimum: 1)
```

### Kritikus Minőségi Garancia:
- **Tilos gyenge minőségű hotelt vagy kényelmetlen járatot mesterségesen beilleszteni kizárólag azért, hogy meglegyen a 3 kártya!**
- Ha a szűrés után csak 2 valóban kiváló és érvényes kombináció maradt, a rendszer **2 valid opciót** ad vissza (`[Option A, Option B]`).

---

## 4. Valódi Diverzitás (True Trade-Offs)

A 3 opció közötti különbségeknek érdeminek kell lenniük:
- **Árkülönbség**: Szignifikáns költségmegtakarítás a Best Value javára.
- **Szálláskategória**: Magasabb csillag/értékelés a Best Experience javára.
- **Logisztika**: Közvetlenebb menetrend a Best Overall javára.
- **Nem rontjuk le az opció minőségét kizárólag a diverzitás kedvéért.**
