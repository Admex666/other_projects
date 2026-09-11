---
id: experience-entity
type: entity
name: Canonical Experience Entity
status: active

description: Egy dedikált, több külső forrásból szintetizált és deduplikált látványosság, program vagy szabadidős élmény kanonikus adatmodellje az Optivoyában.

related:
  - "[[destination]]"
  - "[[poi]]"
  - "[[trip]]"
  - "[[experience-intelligence-engine]]"
  - "[[experience-graph-modeling]]"

used_by:
  - "[[itinerary-optimization]]"
  - "[[destination-matching]]"
---

# 🏛️ Entity: Canonical Experience Entity

A **Canonical Experience Entity** az Optivoya élménygráfjának alapeleme. Egyetlen fizikai helyszínt, látványosságot vagy szervezett aktivitást reprezentál, amelyhez a különböző külső forrásokból (OSM, Wikidata, Wikipedia, Google Maps) származó geometriai, enciklopédikus és minőségi adatok egyesítve lettek.

## 📋 Séma & Attribútumok

| Mező | Típus | Leírás | Példa |
| :--- | :--- | :--- | :--- |
| `entity_id` | `TEXT (PK)` | Egyedi, célállomás-specifikus azonosító | `exp_it_bari_basilica_of_st_nicholas` |
| `destination_id` | `TEXT` | Célállomás kódja | `IT_BARI` |
| `canonical_name` | `TEXT` | A helyszín szabványos, olvasható neve | `Basilica of St Nicholas \| Bari` |
| `category` | `TEXT` | Fő kategória | `culture_history`, `beach_coastal`, `nature_viewpoint`, `food_market`, `active_adventure` |
| `subcategory` | `TEXT` | Részletes altípus | `church_cathedral`, `castle_fortress`, `public_beach`, `museum`, `viewpoint` |
| `lat`, `lon` | `FLOAT` | Pontos WGS-84 földrajzi koordináták | `41.1303`, `16.8701` |
| `rating` | `FLOAT` | Ellenőrzött csillagértékelés (1.0–5.0) | `4.8` |
| `review_count` | `INTEGER` | Felhasználói vélemények száma | `24035` |
| `price_level` | `TEXT` | Költségkeret besorolás | `free`, `budget`, `moderate`, `premium` |
| `est_duration_hours` | `FLOAT` | Becsült látogatási idő órában | `1.0` |
| `best_time_of_day` | `TEXT` | Ideális látogatási idősáv | `morning`, `afternoon`, `sunset`, `evening`, `anytime` |
| `confidence_score` | `FLOAT` | Megbízhatósági pontszám (0.0–1.0) | `0.88` |
| `sources_present` | `TEXT[]` | Igazoló források listája | `['google_maps', 'wikipedia']` |
| `source_ids` | `JSONB` | Külső azonosítók leképezése | `{"osm": "node/123", "wikidata": "Q3519"}` |
| `image_urls` | `TEXT[]` | Szabad Commons / Wiki kép URL-ek | `['https://upload.wikimedia.org/...']` |
| `description` | `TEXT` | Wikipedia kivonat vagy szerkesztett leírás | *"The Pontifical Basilica of Saint Nicholas is a church in Bari..."* |
| `tags` | `TEXT[]` | Kereshető és perszóna címkék | `['culture_aficionado', 'indoor', 'must_see_flagship', 'tier_flagship']` |
| `metadata` | `JSONB` | Bővített környezeti és sétagráf adatok | `{ "indoor_outdoor": "indoor", "weather_sensitivity": "rain_safe", "nearby_walkable_entities": [...] }` |

## 🏷️ Minőségi Szintek (Quality Tiers)
1. **Tier 1 — Flagship (Score $\ge 0.80$):** A desztináció kihagyhatatlan jelképei (több ezer vélemény vagy kiemelt történelmi jelentőség).
2. **Tier 2 — Recommended (Score $0.60 - 0.79$):** Magas minőségű, ajánlott látványosságok és programok.
3. **Tier 3 — Supplemental (Score $< 0.60$):** Részletes felfedező helyszínek (szökőkutak, kisebb emléktáblák, helyi parkok).
