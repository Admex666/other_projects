---
id: ADR-011-event-intelligence-engine
aliases:
  - ADR-011
type: decision
name: "ADR-011: Event Intelligence Engine Architektúra és Időfüggő Élményintegráció"
status: accepted
date: 2026-11-20

governed_by:
  - "[[ARCHITECTURE_RULES]]"
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[ENGINEERING_PRINCIPLES]]"

related:
  - "[[ADR-004-honest-scraping-mode]]"
  - "[[ADR-009-experience-activity-intelligence-engine]]"
  - "[[ADR-001-unified-trip-architecture]]"
  - "[[ADR-003-promethee-ii-outranking]]"
  - "[[ahp-weighting]]"
  - "[[destination-matching]]"
  - "[[experience-intelligence-engine]]"
  - "[[event-intelligence-engine]]"
  - "[[event]]"
  - "[[experience-entity]]"
  - "[[numbeo-cost-model]]"
  - "[[honest-scraping-policy]]"

used_by:
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"
  - "[[advisor-workspace-blueprint-v2]]"
  - "[[itinerary-optimization]]"
---

# 📜 ADR-011: Event Intelligence Engine Architektúra és Időfüggő Élményintegráció

## 📌 1. Kontextus & Problémafelvetés (Context)

Az Optivoya utazástervező döntési motorja eddig két szinten vizsgálta az élményeket:
1. **Statikus látványosságok és POI-k:** Az [[ADR-009-experience-activity-intelligence-engine]] révén kiépült az Evergreen Experience Engine (OSM, Wikidata, Wikipedia, Google Maps vélemények), amely kiválóan térképezi fel az állandó kulturális, gasztronómiai, természeti látnivalókat és a desztinációk Vibe-profilját.
2. **Költség és éghajlat:** Járatárak (Kiwi), szállások (Cozycozy), időjárás (Open-Meteo) és megélhetési költségek (Numbeo).

### A Megoldandó Kritikus Hiányosság:
Egy utazó vagy B2B tanácsadó számára a valódi döntési értékajánlat nem csupán az, hogy *létezik-e egy városban operaház, stadion vagy bár*, hanem az, hogy:
* **Mi történik ott pontosan az utazás időpontjában?** (Pl. Szilveszterkor, hosszú hétvégén, nyári fesztiválszezonban).
* **Milyen konkrét koncertek, fesztiválok, klubesemények, gasztronómiai vásárok vagy kulturális programok látogathatók?**
* **Megvalósítható-e a részvétel logisztikailag és pénzügyileg?** (Jegyárak, éjszakai hazajutás a szállásra, menetidők).

Egy olcsó repülőjegy önmagában nem jó ajánlat, ha a célállomáson az adott időszakban nincsenek releváns programok; és fordítva: egy drágább desztináció azonnal prioritást élvezhet, ha ott egy kihagyhatatlan, autentikus rendezvény zajlik.

---

## 💡 2. A Meghozott Döntés (Decision)

Létrehozzuk a dedikált **Event Intelligence Engine** alrendszert, amely az Evergreen Experience Engine (ADR-009) mellé rendelve, azzal szoros szimbiózisban bővíti ki az Optivoya döntési motorját.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   OPTIVAYA DÖNTÉSI ÉS AJÁNLÓMOTOR                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐   ┌──────────────────────────────────┐
│  EVERGREEN EXPERIENCE ENGINE    │   │     EVENT INTELLIGENCE ENGINE    │
│  (ADR-009)                      │   │     (ADR-011 - Új Rendszer)      │
│  • Időfüggetlen POI-k           │   │  • Dátum- & időponthoz kötött    │
│  • Hidden gem helyek            │   │  • Koncertek, fesztiválok, bulik │
│  • Vibe Profiling (Z-score)     │   │  • Gasztro- & kulturális vásárok │
│  • Sétagráfok (500m Walkable)   │   │  • Időablak & logisztika         │
└────────────────┬────────────────┘   └────────────────┬─────────────────┘
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     UNIFIED RECOMMENDATION ENGINE                      │
│   • Blended Experience Score (AHP Level 2 szintézis)                   │
│   • Teljes Utazási Költség kalkuláció (Repülő + Hotel + Numbeo + Jegy) │
│   • Megvalósíthatósági szűrő (Nyitvatartás, tranzit, éjszakai járat)   │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Réteghatárok és Felelősségek
1. **Evergreen Experience Engine (ADR-009):** Felelős a desztináció állandó identitásáért (múzeumok, parkok, történelmi terek, kilátók, állandó éttermek) és az alap Vibe-profilért. Élettartam: hónapok/évek.
2. **Event Intelligence Engine (ADR-011):** Felelős a diszkrét időablakhoz (`starts_at`, `ends_at`) kötött valós eseményekért, jegyárakért, forráshitelesítésért és az események életciklusáért (`verified`, `partially_verified`, `unverified`, `cancelled`, `expired`, `historical`). Élettartam: napok/órák.
3. **Unified Recommendation & Itinerary Optimizer:** Egyesíti az állandó látnivalókat és a dinamikus eseményeket egy koherens, földrajzilag és időben nem ütköző útitervvé.

---

## 🛡️ 3. Megbízhatósági Elvek és Honest Scraping (Data Integrity & Anti-AI-Slop)

A rendszer alapvető értéke a **sziklaszilárd valósághűség**. Az [[ADR-004-honest-scraping-mode]] és az [[ANTI_AI_SLOP_POLICY]] elveivel összhangban a rendszerre az alábbi zéró-toleranciás szabályok vonatkoznak:

1. **Szigorú Dátumellenőrzés & Évszám-Reciklálás Tilalma:**
   - Szigorúan tilos korábbi (pl. 2025-ös) eseményeket feltételezésből vagy mesterségesen átcímkézni a következő évre (pl. 2026-os szilveszterként).
   - Ha egy esemény időpontja nem megerősített az adott naptári évre/hónapra, nem tekinthető aktuális eseménynek.
2. **Zero-Hallucination Adatpolitika:**
   - Tilos fiktív eseményárakat, kitalált értékeléseket vagy generált jegyértékesítő linkeket generálni.
   - Ha egy esemény ingyenes, azt az `is_free: True` mező jelöli; ha az ár ismeretlen, `price_min: null`, `price_max: null` és transzparens felületi jelzés kötelező.
3. **Kettéválasztott Értékelési Rendszer:**
   - **`confidence_score` (0.0 – 1.0):** Kizárólag az **adat hitelességét és forrásmegbízhatóságát** méri (pl. hivatalos jegyiroda és városi oldal megerősítette = 0.95; automatikus webkereső találat külső validáció nélkül = 0.40).
   - **Élmény Relevancia / Vibe Fit (0.0 – 1.0):** Az esemény vonzerejét, minőségét és a felhasználói profilhoz való illeszkedését méri.
   - Magas relevancia melletti alacsony konfidencia esetén az ajánlat „Nem ellenőrzött forrású program” figyelmeztetéssel jelenhet csak meg.
4. **Esemény Életciklus Státuszok:**
   - `verified`: Hivatalos API vagy megbízható elsődleges forrás által igazolt, érvényes dátumú esemény.
   - `partially_verified`: Másodlagos aggregátor által listázott esemény, amely még nem rendelkezik közvetlen jegyirodai visszaigazolással.
   - `unverified`: Felfedező scraper által talált program, ellenőrzésre vár.
   - `cancelled`: Lemondott rendezvény (figyelmeztető jelzéssel vagy azonnali szűréssel).
   - `expired`: Lezárult, múltbeli rendezvény (ajánlásból kizárva).
   - `historical`: Elemzési célra megőrzött archív adat.
5. **Időzóna-Kezelés:**
   - Minden dátumot és időpontot ISO-8601 formátumban, a **célállomás hivatalos helyi időzónájában** és UTC eltolással kell tárolni és megjeleníteni.

---

## 🎯 4. Integráció a 4-Pilléres AHP Célállomás-Választóba

Az Optivoya célállomás-kiválasztó motorja ([[ahp-weighting]], [[destination-matching]]) a Saaty-féle kétfázisú AHP döntési mátrixra épül. Az események integrálása az alábbiak szerint valósul meg:

### 4.1. Élmény Pillér (Level 2) Szintézis:
Az élménypontszám ($S_{\text{exp}}$) a statikus és dinamikus kínálat súlyozott kombinációjává válik:

$$S_{\text{exp}} = w_{\text{evergreen}} \cdot S_{\text{evergreen}} + w_{\text{event}} \cdot S_{\text{event}}$$

Ahol:
* $S_{\text{evergreen}}$: A desztináció 12-dimenziós Vibe profiljának és a felhasználó preferenciáinak koszinusz hasonlósága Bayes-i simítással.
* $S_{\text{event}}$: Az utazási dátumra eső aktív, ellenőrzött (`verified` / `partially_verified`) események preferencia-illeszkedése, relevanciája és sokszínűsége.
* A súlyozás dinamikusan alkalmazkodik a keresési kontextushoz:
  - **Szezonális / Ünnepi utazás (pl. Szilveszter, fesztiválhétvége):** $w_{\text{event}} = 0.55$, $w_{\text{evergreen}} = 0.45$.
  - **Általános városlátogatás:** $w_{\text{event}} = 0.25$, $w_{\text{evergreen}} = 0.75$.

### 4.2. Meleg Téli Célvárosok és Vegyes Kínálat Egyensúlya:
A téli/szilveszteri időszakban a rendszer különös figyelmet fordít a klíma és események egyensúlyára:
* A meleg téli célállomások (pl. Barcelona, Róma, Lisszabon, Páfosz) magas klímapontszámot kapnak.
* Ugyanakkor az élménypillér biztosítja, hogy ha egy hűvösebb közép-európai városban (pl. Bécs, Prága, Budapest) kiemelkedő év végi kulturális/zenei programkínálat érhető el, a rendszer képes ezt felmutatni a kompromisszumos döntési alternatívák között.

### 4.3. Teljes Utazási Költség (Total Trip Cost) Kibővítése:
A költségpillér ($S_{\text{cost}}$) képlete kiegészül a tervezett programok költségeivel:

$$\text{Total Cost} = C_{\text{flight}} + C_{\text{accommodation}} + (N_{\text{days}} \cdot C_{\text{Numbeo\_daily}}) + C_{\text{events}} + C_{\text{night\_transit}}$$

Ahol az események jegyárai ($C_{\text{events}}$) és a rendezvények utáni esetleges éjszakai transzfer ($C_{\text{night\_transit}}$) expliciten beépül az összköltségbe, megelőzve a rejtett költségek miatti csalódást.

---

## ⚖️ 5. Következmények & Érintett Rendszerek (Consequences)

### Pozitív Következmények:
* **Valódi Döntési Érték:** A felhasználó pontosan látja, hogy a kiválasztott időpontban *miért érdemes az adott városba utazni*.
* **Időszerű és Reális Ajánlatok:** Nincs többé „halott szezonba” vagy zárt kapukhoz szervezett utazási javaslat.
* **Védelem a Hibás Adatok Ellen:** Az életciklus-státuszok és a forráshitelesítés garantálják a megbízhatóságot.
* **Szinergia az ADR-009-cel:** Nem váltjuk le a meglévő élménymotort, hanem funkcionálisan kiterjesztjük.

### Kockázatok & Kompenzáció:
* **Scraper és API törékenység:** A külső eseményoldalak változékonyak. Megoldás: standard API-k előnyben részesítése (Bandsintown, Songkick, Eventbrite) és hibatűrő connector architektúra (`[[ADR-004-honest-scraping-mode]]`).
* **Késleltetés:** Valós idejű eseménykeresés lassíthatja a válaszidőt. Megoldás: előtöltés, aszinkron háttérfrissítés és többszintű gyorsítótárazás (Redis/L1 memóriacache + Supabase).
