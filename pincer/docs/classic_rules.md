# Classic Rules Specification (Developer Video Overview)

## 1. Overview & Precedence
This document specifies the "Classic Rules" derived from the primary source: the developer's rule overview video transcript. 
The secondary source is `docs/spec/player_card.md` ("Turn Cards: A Quick Rule Reference While Playing").
Where the video transcript introduces specific numbers or terminology that differs from or refines the quick reference, the video transcript takes precedence for the Classic Rules implementation.
Any conflicting or ambiguous rules are cataloged in `docs/open_questions.md` and exposed as configurable parameters in `GameConfig`.

---

## 2. Board & Components
- **Tile Count:** The physical game contains 58 terrain tiles.
- **Terrain & Resource Categories (6 types):**
  1. **Wheat (Fields/Plains):** Produces Wheat.
  2. **Woods (Forest):** Produces Wood.
  3. **Stone (Quarry/Rock):** Produces Stone.
  4. **Hills:** Produces Ore / Iron Ore.
  5. **Mountains:** Impassable terrain for land units; does not produce harvest.
  6. **Water (Sea/Ocean):** Navigable only by naval units (Frigates) and crossed via Bridges.
- **Resource Cards:**
  - Standard resource cards: Wood, Wheat, Stone, Iron Ore (Ore).
  - Unresolved / transcript variants: "fish", "Mustang". Configured via resource catalog aliases.

---

## 3. Initial Setup
- Each player starts with:
  - 1 Colony.
  - 1 Musketeer (stationed on or adjacent to their colony).
- Colony Spacing: Minimum graph distance of 3 tiles between any two colonies.
- Edge Restriction: Colonies cannot be built on edge tiles of the board.
- The exact physical layout of the 58-tile board is not yet specified; simulation engine uses graph topology. A small synthetic test board is used for unit tests.

---

## 4. Turn Sequence
Each player's turn consists of three distinct, consecutive phases:

### Phase I: Harvest
1. The active player rolls the 6-sided resource die.
2. Every eligible colony on the board produces one resource card if the rolled value matches an adjacent terrain tile.
3. If an enemy unit occupies the adjacent producing tile, the harvest from that tile is suppressed.
4. If an enemy occupies/annexes the colony itself, the occupying player collects the harvest.

### Phase II: Mobilization
1. Active player may move and/or attack with eligible units.
2. One unit per tile max (stacking is illegal).
3. Newly recruited units (built in current turn) **cannot act until their next eligible turn**.
4. Units may move up to their range:
   - **Musketeer:** 1 tile (land only, no mountains/water).
   - **Cavalry:** 2 tiles (land only, no mountains/water; cannot move through enemy-occupied tiles).
   - **Cannon:** 1 tile move, 1 tile attack; retreats immediately after attacking.
   - **Frigate:** 1 or 2 tiles across water; transports 1 land unit.
5. Combat: Attacker moves into defender tile; defender piece is removed from the board.
6. **Immediate Counter-Move Reaction:**
   - Immediately after an attack, the defender may make 1 immediate counter-move or counter-attack with an available piece before the attacker's turn resumes.
   - Defender must use separate pieces for each counter-move in a turn before reusing.
   - Defender may pass the counter-move reaction.

### Phase III: Development
1. Active player may trade with the bank (5:1 base rate, reduced by 1 per harbor or road-connected colony down to 2:1).
2. Spend resource cards to construct infrastructure or recruit units.
3. Newly purchased units cannot act until next turn.

---

## 5. Infrastructure & Costs (Classic Rules)

| Item | Classic Cost | Prerequisites & Placement |
| :--- | :--- | :--- |
| **Colony** | 2 Wood, 2 Wheat, 1 Stone, 1 Iron Ore | On friendly unit tile; distance $\ge 3$ from other colonies; not on edge tile. Unlocks musketeers. |
| **Wall (Fort)** | 3 Stone | Built on existing colony. Protects colony; unlocks cannon recruitment. |
| **Harbor (Port)** | 2 Wood, 1 Iron Ore | Built on water tile adjacent to friendly colony. Unlocks frigates; reduces trade rate by 1. |
| **Bridge** | 1 Stone (per piece) | Built on water edge touching land on both sides. Allows land units to cross. |
| **Road** | 1 Wood, 1 Stone | Built along tile edges connecting colonies. Reduces trade rate; allows 1-move transfer between colonies; unlocks cavalry. |
| **Musketeer** | 2 Wheat (or 2 Fish) | Empty friendly colony. |
| **Cavalry** | 2 Wheat, 1 Mustang (or Iron Ore) | Colony connected to another by roads. |
| **Cannon** | 4 Iron Ore | Colony with Wall/Fort. |
| **Frigate** | 2 Wood, 2 Iron Ore | Empty friendly harbor on water. |

---

## 6. Victory Conditions
- **Provisional Classic Threshold:** Controlling **4 colonies** (through construction or annexation).
- Configurable in `GameConfig.classic_target_colonies = 4` and `GameConfig.domination_control_fraction = 0.75`.
