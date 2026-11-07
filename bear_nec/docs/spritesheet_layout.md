# Bear Necessities - Card Spritesheet & Visual Asset Pipeline

## 1. Executive Summary & Spritesheet Structure

The card visual pipeline for *Bear Necessities* utilizes a single unified spritesheet containing all playable card faces, card backs, and grid placeholders.

### Key Metrics
- **Source File**: `assets/sources/cards.jpg` (Encoding: **WEBP** container despite the `.jpg` extension, RGB color mode).
- **Sheet Dimensions**: **3200 px × 4990 px**.
- **Layout Grid**: **10 columns × 10 rows** (100 total slots).
- **Single Card Dimensions**: **320 px × 499 px**.
- **Aspect Ratio**: **1.5594** (Height / Width = 499 / 320). In BGA CSS, this is styled as `height: calc(var(--bn-cw) * 1.54 + 12px)`.

```
        Col 0       Col 1       Col 2       ...       Col 8       Col 9
      ┌───────────┬───────────┬───────────┬─────────┬───────────┬───────────┐
Row 0 │  Slot 00  │  Slot 01  │  Slot 02  │   ...   │  Slot 08  │  Slot 09  │
      ├───────────┼───────────┼───────────┼─────────┼───────────┼───────────┤
Row 1 │  Slot 10  │  Slot 11  │  Slot 12  │   ...   │  Slot 18  │  Slot 19  │
      ├───────────┼───────────┼───────────┼─────────┼───────────┼───────────┤
      │    ...    │    ...    │    ...    │   ...   │    ...    │    ...    │
      ├───────────┼───────────┼───────────┼─────────┼───────────┼───────────┤
Row 9 │  Slot 90  │  Slot 91  │  Slot 92  │   ...   │  Slot 98  │  Slot 99  │
      │ (Mtn #20) │ (Mtn #21) │ (Mtn #22) │         │  (Blank)  │  (Blank)  │
      └───────────┴───────────┴───────────┴─────────┴───────────┴───────────┘
```

---

## 2. Layout Verification & Slot Distribution

### Crucial Architectural Discovery: Interleaved Card Backs
Prior to analysis, the spritesheet was hypothesized to have cards 0–93 contiguous with 4 card backs grouped at slots 94–97. **Pixel-level inspection revealed the true layout:**

The 4 suit card backs are **interleaved directly at the end of each suit group**, rather than being clustered at the end:

1. **Water (Blue)**:
   - **Game Cards (23 cards)**: Slots `0` to `22` (Game Card IDs `1` to `23`).
   - **Suit Card Back**: Slot `23` (`Row 2, Col 3`).
2. **Desert (Yellow)**:
   - **Game Cards (21 cards)**: Slots `24` to `44` (Game Card IDs `24` to `44`).
   - **Suit Card Back**: Slot `45` (`Row 4, Col 5`).
3. **City (Red)**:
   - **Game Cards (24 cards)**: Slots `46` to `69` (Game Card IDs `45` to `68`).
   - **Suit Card Back**: Slot `70` (`Row 7, Col 0`).
4. **Mountain (Green)**:
   - **Game Cards (26 cards)**: Slots `71` to `96` (Game Card IDs `69` to `94`).
     *(Note: Slots 94, 95, and 96 are Mountain game cards #24, #25, and #26, complete with standard card illustrations, text boxes, and victory point badges).*
   - **Suit Card Back**: Slot `97` (`Row 9, Col 7`).
5. **Blank Slots**:
   - Slots `98` and `99` (`Row 9, Col 8` and `Row 9, Col 9`): Confirmed pure white blank padding (`#ffffff`).

### Summary Totals
| Category | Slot Indices | Count | Description |
| :--- | :--- | :---: | :--- |
| **Water Game Cards** | 0 – 22 | 23 | Playable cards with Blue border |
| **Water Card Back** | 23 | 1 | Symmetrical Blue card back with center bear crest |
| **Desert Game Cards** | 24 – 44 | 21 | Playable cards with Yellow/Amber border |
| **Desert Card Back** | 45 | 1 | Symmetrical Yellow card back with center bear crest |
| **City Game Cards** | 46 – 69 | 24 | Playable cards with Red/Coral border |
| **City Card Back** | 70 | 1 | Symmetrical Red card back with center bear crest |
| **Mountain Game Cards** | 71 – 96 | 26 | Playable cards with Green/Lime border |
| **Mountain Card Back** | 97 | 1 | Symmetrical Green card back with center bear crest |
| **Blank Padding** | 98 – 99 | 2 | Unused white slots |
| **Total Slots** | **0 – 99** | **100** | **10 × 10 Grid** |

Total playable cards: **23 + 21 + 24 + 26 = 94 cards** (matches official rulebook count).

---

## 3. Color Palette & Card Anatomy

### Color Palette by Suit
Each suit features a distinctive border frame, corner accents, and card back color:

| Suit / Habitat | Color | Border RGB (Sampled) | Border Hex | Typical Art Tone | Card Back Slot |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Water** | Blue / Teal | `(105, 187, 192)` | `#69bbc0` | Cool cyans, lake greens, water reflections | 23 |
| **Desert** | Yellow / Amber | `(253, 211, 130)` | `#fdd382` | Warm sands, desert yellows, sunlit woods | 45 |
| **City** | Red / Coral | `(246, 127, 103)` | `#f67f67` | Warm terracotta, brick reds, urban tones | 70 |
| **Mountain** | Green / Lime | `(201, 217, 134)` | `#c9d986` | Foliage greens, forest earth, mountain flora | 97 |

### Design System & Theme CSS Variables
Extracted from `assets/sources/bearnecessities.css`:
```css
:root {
  --bn-honey: #e8a020;
  --bn-honey-light: #ffd23f;
  --bn-honey-dark: #b97a10;
  --bn-gold: #ffc93c;
  --bn-wood: #6b4a2c;
  --bn-wood-dark: #4e3218;
  --bn-paper: #f6ecd8;
  --bn-page: #f9f0da;
  --bn-frame: #fffdf6;
  --bn-ink: #3c2a18;
  --bn-leaf: #2f7d4f;
}
```

### Card Anatomy
1. **Outer Frame (`.bn-card`)**: 320 × 499 px rounded rectangle (`border-radius: ~6px`), bordered in the suit's color.
2. **Header Bar**: Displays the card name, primary suit indicator, and type icons (Bearfolk, Building, Item, Plant, Animal).
3. **Artwork Window**: Hand-drawn illustration by Kerri Aitken occupies the upper-middle half (~320 × 240 px).
4. **Scoring & Effect Box (Bottom)**: Standardized parchment box (`RGB ~ (228, 214, 167)` / `#e4d6a7`) detailing activation rules, bee token requirements, and victory point values.
5. **Card Backs**: Full-bleed background in suit color with border ornamentation and a centered circular seal containing the game's bear emblem.

---

## 4. CSS Sprite Rendering Mechanics

### Percentage Calculation Formula
When using a CSS spritesheet with a scaled container:
```
background-size: 1000% 1000%;
background-position: X% Y%;
```
Where:
$$\text{Position X} = \frac{\text{col}}{9} \times 100\% = \text{col} \times 11.1111\%$$
$$\text{Position Y} = \frac{\text{row}}{9} \times 100\% = \text{row} \times 11.1111\%$$

Because the background image is 10 times the width of a single card, shifting by `(col / 9) * 100%` shifts the sprite left by exactly `col * card_width` pixels regardless of zoom level or display DPI.

### Grid Coordinate Lookup Table
| Index (Col/Row) | Offset Percentage | Offset Exact Fraction |
| :---: | :---: | :---: |
| 0 | `0.0000%` | `0 / 9` |
| 1 | `11.1111%` | `1 / 9` |
| 2 | `22.2222%` | `2 / 9` |
| 3 | `33.3333%` | `3 / 9` |
| 4 | `44.4444%` | `4 / 9` |
| 5 | `55.5556%` | `5 / 9` |
| 6 | `66.6667%` | `6 / 9` |
| 7 | `77.7778%` | `7 / 9` |
| 8 | `88.8889%` | `8 / 9` |
| 9 | `100.0000%` | `9 / 9` |

### CSS Implementation Examples

#### Spritesheet Base Style
```css
.bn-card-face {
  display: block;
  width: 100%;
  height: 100%;
  background-image: url('assets/sources/cards.jpg');
  background-size: 1000% 1000%;
  background-repeat: no-repeat;
  border-radius: 4px;
}

/* Card 1 (Water #1, Slot 0) */
.bn-card-face[data-card-id="1"] {
  background-position: 0.0000% 0.0000%;
}

/* Card 24 (Desert #1, Slot 24 -> Row 2, Col 4) */
.bn-card-face[data-card-id="24"] {
  background-position: 44.4444% 22.2222%;
}

/* Card Backs */
.bn-card-back-water    { background-position: 33.3333% 22.2222%; } /* Slot 23 */
.bn-card-back-desert   { background-position: 55.5556% 44.4444%; } /* Slot 45 */
.bn-card-back-city     { background-position: 0.0000% 77.7778%; }  /* Slot 70 */
.bn-card-back-mountain { background-position: 77.7778% 100.0000%; } /* Slot 97 */
```

---

## 5. IP & Licensing Modularity Guidelines

### Legal Context
The original artwork of *Bear Necessities* (created by Kerri Aitken and published by Super Meeple / Board Game Arena) is proprietary copyrighted intellectual property. Game mechanics, rule structures, and card attributes (e.g. "Score 2 VP per Water card") are typically not subject to copyright, but the visual assets and exact rulebook illustrations cannot be distributed without explicit licensing.

### Asset Abstraction Architecture
To allow both high-fidelity development with official assets and safe open-source distribution, the codebase implements an **Asset Provider Abstraction**:

```
                  ┌────────────────────────┐
                  │    Game State & Logic  │
                  │  (Semantic Card Model) │
                  └───────────┬────────────┘
                              │
                    Card ID & Metadata
                              │
                              ▼
                  ┌────────────────────────┐
                  │   ICardAssetProvider   │
                  └───────────┬────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ SpriteAsset       │ │ SlicedAsset       │ │ ProceduralMock    │
│ Provider          │ │ Provider          │ │ Provider (Open)   │
│ (Single Sheet)    │ │ (Individual WebP) │ │ (SVG / Pure CSS)  │
└───────────────────┘ └───────────────────┘ └───────────────────┘
```

1. **Semantic ID Decoupling**:
   - Game logic references cards purely by numeric ID (`1..94`) or semantic keys (`water_01`, `mountain_berries`), never by pixel coordinates or slot offsets.
2. **Provider Pluggability**:
   - **`SpriteAssetProvider`**: Points to `cards.jpg` (or WebP) and applies `background-position` classes from `docs/card_spritesheet_map.json`.
   - **`SlicedAssetProvider`**: Points to individual files in `public/assets/cards/card_{id}.webp` generated by `scripts/slice_cards.py`.
   - **`MockAssetProvider`**: Renders clean, color-coded SVG/HTML mock cards with suit icons and text, suitable for public open-source repositories and headless unit testing without copyright encumbrance.
3. **Repository Management Best Practices**:
   - Proprietary asset files (`assets/sources/*.jpg`, `assets/sources/*.pdf`, `public/assets/cards/`) are tracked in `.gitignore` or packaged as an optional local bundle.
   - The slicing script `scripts/slice_cards.py` allows end-users or authorized developers to ingest their own licensed source files locally.

---

## 6. Automation Scripts Reference

### 1. `scripts/analyze_spritesheet.py`
Analyzes the source spritesheet, inspects all 100 slots, measures color statistics, classifies card suits, verifies integrity, and generates the canonical JSON mapping.

```bash
python scripts/analyze_spritesheet.py \
  --input assets/sources/cards.jpg \
  --output docs/card_spritesheet_map.json
```

**Key Output Fields in `docs/card_spritesheet_map.json`**:
- `metadata`: Dimensions, grid dimensions, slot counts, suit breakdown.
- `slots[]`:
  - `slot_index`: 0–99
  - `column`, `row`: 0–9
  - `slot_type`: `"game_card"`, `"card_back"`, or `"blank"`
  - `game_card_id`: 1–94 (or `null`)
  - `suit`: `"Water"`, `"Desert"`, `"City"`, `"Mountain"`, or `null`
  - `css_background_position`: e.g. `"11.1111% 22.2222%"`
  - `color_stats`: Measured RGB and Hex for overall, border, art, and text box regions.

### 2. `scripts/slice_cards.py`
Slices the spritesheet into individual card assets with configurable format, compression, and scaling.

```bash
# Export individual WebP cards at 100% resolution with card backs
python scripts/slice_cards.py \
  --input assets/sources/cards.jpg \
  --output-dir public/assets/cards \
  --format webp \
  --quality 85 \
  --generate-css

# Export half-scale thumbnails (160x250) for mobile/preview
python scripts/slice_cards.py \
  --scale 0.5 \
  --output-dir public/assets/cards/thumbnails \
  --format webp

# Dry run with semantic naming
python scripts/slice_cards.py \
  --naming semantic \
  --dry-run
```

**Supported Options**:
- `--format`: `webp` (default), `png`, `jpg`
- `--quality`: 1–100 (default: 85)
- `--scale`: Multiplier (e.g. 0.5 for 50% scale)
- `--target-width` / `--target-height`: Target pixel dimensions with Lanczos resampling
- `--naming`:
  - `card` -> `card_01.webp` .. `card_94.webp`, `back_water.webp`
  - `slot` -> `slot_00.webp` .. `slot_99.webp`
  - `semantic` -> `water_01_card_01.webp` ..
- `--generate-css`: Outputs a ready-to-use CSS file (`cards.css`) with all card face and card back classes.
