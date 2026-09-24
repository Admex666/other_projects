---
id: advisor-budget-and-constraints
type: system
name: Advisor Budget & Constraint Management Engine
status: active

description: Az Optivoya B2B Advisor Workspace költségvetési modellje (teljes utazási keret, komponens keretek, per-fő és csoportos bázis, hard vs. target állapot) és 4 rétegű megkötési hierarchiája (Hard, Soft, Avoid, Nice-to-have, Overrides).

source:
  type: code
  ref: app.models.advisor_models

code:
  - app/models/advisor_models.py
  - app/services/preference_resolver.py
  - app/services/constraint_relaxation_service.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[trip-case]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 💰 Advisor Budget & Constraint Management Engine

Ez a dokumentum specifikálja az **Optivoya B2B Advisor Workspace** kibővített költségvetési és megkötési architektúráját.

---

## 1. Költségvetési Adatmodell (`BudgetConstraint`)

A rendszer nem pusztán egyetlen lebegőpontos számot tárol, hanem egy explicit, többvalutás, komponensekre bontható költségvetési struktúrát kezel:

```yaml
BudgetConstraint:
  currency: "HUF" | "EUR" | "USD" | "GBP"
  total:
    amount: 350000.0
    basis: "group" | "per_person"
    hardness: "hard" | "target"
    relaxation_allowed: true
    max_relaxation_pct: 15.0

  components:
    flight:
      amount: 100000.0
      basis: "group"
      hardness: "hard"
      currency: "HUF"

    stay:
      amount: 180000.0
      basis: "group"
      hardness: "target"
      currency: "HUF"

    activities:
      amount: 50000.0
      basis: "per_person"
      hardness: "target"
      currency: "HUF"

    local_transport:
      amount: 20000.0
      basis: "group"
      hardness: "hard"
      currency: "HUF"
```

---

## 2. Költségkeret Szemantika & Keménységi Állapotok

### Hard Budget (Szigorú Plafon)
- **Meghatározás**: `hardness == "hard"`
- **Szabály**: A kereső és rangsoroló motor **soha, semmilyen körülmények között nem lépheti túl automatikusan** a megadott összeget.
- Ha nincs olyan járat vagy szállás, ami belefér a keretbe, a rendszer **0 találatot ad (Dead-End)**, és a `ConstraintRelaxationService`-en keresztül javaslatot tesz a keret emelésére.

### Target Budget (Célköltségkeret)
- **Meghatározás**: `hardness == "target"`
- **Szabály**: A motor törekszik a megadott keret betartására, de a `max_relaxation_pct` (pl. +10-15%) mértékéig figyelembe vehet kimagasló minőségű opciókat, amennyiben azt az érték-hatékonyság (Value Efficiency) indokolja.
- Az ajánlatban explicit trade-offként jelenik meg a keret feletti összeg.

### Per-Fő vs. Csoportos Bázis
- `basis: "group"`: A megadott összeg a teljes utazócsoportra (felnőttek + gyerekek) értendő.
- `basis: "per_person"`: A motor automatikusan felskálázza a keretet az utazók számával ($N_{\text{travelers}} = N_{\text{adults}} + N_{\text{children}}$).

---

## 3. 4 Rétegű Megkötési Hierarchia (`ResolvedTripPreferences`)

A döntési motor az alábbi 4 rétegű prioritási lánc alapján oldja fel a preferenciákat:

```text
1. Tanácsadói Kézi Felülbírálás (Advisor Override) — Legmagasabb prioritás
                    ↓
2. Ügy-specifikus Brief (Case Brief)
                    ↓
3. Ügyfél Tartós Profilja (Client Profile)
                    ↓
4. Rendszerszintű Alapértelmezések (System Defaults) — Alapértelmezett fallback
```

### A 4 Megkötési Kategória:
1. **HARD (Kötelező korlátok)**:
   - Szigorú kizáró feltételek: `direct_flights_only`, `min_hotel_stars`, `max_flight_stops`, `max_total_budget_huf`.
2. **SOFT (Súlyozott preferenciák)**:
   - AHP és PROMETHEE II rangsorolásban résztvevő súlyok: gasztro vs kultúra, hotel vs járat prioritás.
3. **AVOID (Kifejezetten kerülendő elemek)**:
   - Kizárt légitársaságok (`avoid_airlines`), hajnali indulások (`avoid_early_departures`), éjszakai érkezések.
4. **NICE-TO-HAVE (Előnyös extrák)**:
   - Bónusz pontok: ingyenes lemondás, reggeli tartalmazva, medence, tengerre néző kilátás.

---

## 4. Tanácsadói Felülbírálás és Audit Napló (`AdvisorOverrideEntry`)

Minden manuális felülbírálást a rendszer auditál:
- `actor_id`: A műveletet végző tanácsadó azonosítója.
- `timestamp`: UTC időbélyeg.
- `field`: A módosított mező (pl. `pinned_destination`, `pinned_stay_id`, `custom_markup_huf`).
- `previous_value` / `new_value`: Az eredeti és az új érték.
- `reason`: Opcionális tanácsadói indoklás.
