---
id: experience-vector-and-vibe-profiling
type: concept
name: Experience Vector & Vibe Profiling Engine
status: active

description: >
  Többdimenziós célállomás-jellemzési rendszer, amely objektív OSM/Google adatokból
  Bayes-i simítással és robusztus Z-score normalizációval számítja ki egy úti cél
  valódi karakterét (Vibe Profile) és a felhasználó személyes illeszkedését (Fit Score).

source:
  type: code
  path: app/services/experience/vibe_engine.py
  data: data/peer_groups.json

depends_on:
  - "[[experience-graph-modeling]]"
  - "[[ahp-weighting]]"

used_by:
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"

governed_by:
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[PRODUCT_PRINCIPLES]]"
---

# Experience Vector & Vibe Profiling Engine

## Mi ez?

Az Optivoya célja nem egyetlen összesített pontszám adása egy úti célhoz.
Ehelyett minden desztinációhoz egy **Experience Vector** készül:
12 dimenzió, mindegyik 0–100 abszolút értékkel, robusztus Z-score-ral és konfidencia szinttel.

## Miért így?

- **Nem LLM**: a pontszámok valós OSM kategóriákból, értékelésekből, vélemény-diverzitásból és térbeli közelségből deriváltak.
- **Adatmélység ≠ büntetés**: kevés adat → alacsony konfidencia, nem alacsony pontszám (Bayes-i simítás véd a félrevezető szélsőértékektől).
- **Hidden Gem = levezetett mutató**: soha nem nyers input, hanem `Authenticity × Locality × Quality × (1 - TouristIntensity) × pop_correction`.

## Dimenziók (0–100)

| Dimenzió           | Mit mér |
|--------------------|---------|
| `culture`          | Múzeumok, műemlékek, örökség sűrűsége és minősége |
| `food`             | Helyi gasztronómia, piacok, street food arány |
| `beach`            | Strandterület, fürdési lehetőségek, tengerparti hozzáférés |
| `nature`           | Parkok, panorámapontok, természeti látnivalók |
| `nightlife`        | Bárok, klubok, késői nyitvatartás koncentrációja |
| `romance`          | Sétányok, hangulatos sikátorok, romantikus pontok |
| `authenticity`     | Helyi független helyek vs. turisztikai láncok aránya |
| `locality`         | Helyiek által látogatott terek, termelői piacok |
| `walkability`      | 500 méteres séta-szomszédsági hálózat sűrűsége |
| `tourist_intensity`| Turista forgalom és zsúfoltság szintje |
| `adventure`        | Aktív tevékenységek, túrák, kaland |
| `family`           | Gyerekbarát programok és helyszínek |

## Multi-Aspektus Reprezentáció (minden dimenzióra)

```json
{
  "absolute": 91,
  "relative_z": 1.72,
  "confidence": 0.94,
  "freshness": 0.98
}
```

- **`absolute`** (0–100): Bayes-i simított objektív érték.
- **`relative_z`** (-3..+3): Robusztus Z-score a Peer Grouphoz viszonyítva.
- **`confidence`** (0–1): Adatforrások diverzitása és entitások számossága.
- **`freshness`** (0–1): Utolsó szinkronizáció óta eltelt idő alapján.

## Statisztikai Modell

### Bayes-i Simítás

```
w(n) = n / (n + K),  K=15
score_bayes = w(n) × score_observed + (1 - w(n)) × score_prior
```

**K=15**: 15 adatpont esetén w=0.5, tehát az adat és a peer-csoport átlag fele-fele arányban számít.
Ha nincs adat (n=0), a score 0 marad — nem kap hamis pontszámot a hiányos adat.

### Robusztus Z-Score (MAD alapú)

```
z_robust = (x - median) / (1.4826 × MAD)
```

A klasszikus szórás helyett **MAD** (Median Absolute Deviation) véd a szélsőértékek (Párizs, Ibiza) torzítása ellen.

### Peer Groupok

A normalizáció dinamikus kohorszon belül történik (`data/peer_groups.json`):
- `mediterranean_coastal` — Bari, Palermo, Valencia, Split, Marseille...
- `european_midsize` — Bologna, Porto, Sevilla, Ljubljana, Krakkó...
- `european_capital` — Budapest, Bécs, Prága, Lisszabon...
- `island_resort` — Santorini, Ibiza, Mallorca, Hvar...
- `mountain_alpine` — Innsbruck, Bled, Annecy, Zermatt...
- `european_all` — teljes katalógus

## Felhasználói Felület (UX elvek szerint)

A statisztika a motorháztető alatt fut. A user csak emberi formátumot lát:

- **Vibe összefoglaló**: *"Bari: autentikus, gasztro-fókuszú olasz város erős helyi karakterrel"*
- **Kiemelkedési badge-ek**: *"Gasztronómia: +1.7σ kiemelkedő"*
- **Personalized Fit Score**: *"Ez a hely neked 87-es illeszkedés"* (a te preferenciáid alapján súlyozva)

## Implementáció

```
app/services/experience/
├── vibe_engine.py          # ExperienceVectorCalculator, BayesianShrinker,
│                           # RobustZScoreNormalizer, HiddenGemCalculator,
│                           # VibeSummarizer, VibeEngine (facade)
├── destination_profiler.py # VibeEngine integrálva: experience_vector → cache
data/
└── peer_groups.json        # Peer group kohorsz definíciók és dimenziónkénti priorok
```

## Kapcsolódó Rendszerek

- `destination_scoring_service.py` → `experience_vector` olvasása → `s_exp` pillérscore
- `experience_cache` → `experience_vector` dict cache-elése
- Master Planner Step 1 (Destination Cards) → Vibe badge-ek és fit score megjelenítése
