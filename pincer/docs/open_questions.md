# Open Questions & Unresolved Rule Ambiguities

This document records all unstated, ambiguous, or incomplete rules identified between `docs/spec/player_card.md` (Turn Cards Quick Reference) and `docs/classic_rules.md` (Developer Video Overview). Per project governance, the simulation engine **never silently invents missing rules**. All unspecified parameters are exposed via `GameConfig` with transparent defaults.

---

## 1. Resource Economy & Classic Cost Terminology
- **Observation:** The Developer Video Overview provides concrete resource costs:
  - Colony: 2 wood, 2 wheat, 1 stone, 1 iron ore.
  - Wall (Fort): 3 stone.
  - Harbor (Port): 2 wood, 1 iron ore.
  - Bridge: 1 stone per bridge piece.
  - Musketeer: 2 wheat or 2 fish.
  - Cavalry: 2 wheat and 1 "Mustang" card.
  - Cannon: 4 iron ore.
  - Frigate: 2 wood and 2 iron ore.
- **Ambiguities / Speech-to-Text artifacts:**
  1. Six terrain categories are described (wheat, woods, hills, mountains, stone, water), but the transcript mentions "fish", "Mustang", and "iron ore".
  2. Does water produce "fish"? Does hills produce "iron ore"? Are "Mustang" cards special cards or a sheep/pasture equivalent?
- **Engine Handling:**
  - Resource enum supports `WOOD`, `WHEAT`, `STONE`, `IRON_ORE` (alias `ORE`), with optional aliases for `FISH` and `MUSTANG`.
  - Costs are parameterized in `GameConfig.classic_construction_costs` and `GameConfig.classic_unit_costs`.

## 2. Terminology Concordance: Wall vs Fort, Harbor vs Port
- **Observation:**
  - Quick Reference uses `Fort` and `Port`.
  - Classic Video uses `Wall` and `Harbor`.
- **Engine Handling:**
  - The engine treats `WALL` and `FORT` as synonyms, and `HARBOR` and `PORT` as synonyms, supporting both sets of terms seamlessly.

## 3. Resource Die & Harvest Mechanics
- **Observation:**
  > "Roll resource die. All players collect one resource card per colony, if die matches adjacent tile (Unless occupied by enemy unit)."
  1. What values does the die produce? (1–6 numbers assigned to tiles matching terrain).
  2. Does "Unless occupied by enemy unit" refer to the adjacent tile, the colony itself, or both?
- **Engine Handling:**
  - Tiles have an associated `harvest_value` (1–6). The die rolls from 1 to 6.
  - An adjacent tile does NOT yield resources if an enemy unit occupies that adjacent tile.
  - If the colony itself is annexed/occupied by an enemy, the *occupying player* collects the harvest (per "Annexing Colonies: During this occupation, you may collect the resources rolled for the colony").

## 4. Cavalry Movement Distance
- **Observation:**
  > "CAVALRY: move/attack only by 2 tiles away per turn. May NOT move through enemy occupied tiles or mountain tiles to attack."
  Does "only by 2 tiles away" mean cavalry *must* move exactly 2 tiles, or can it choose to move 1 or 2 tiles? Note that Frigate states "move/attack only by 1 or 2 tiles per turn", strongly suggesting the phrase "only by 2 tiles" literally means a fixed distance of 2 tiles.
- **Engine Handling:** Controlled by `GameConfig.cavalry_requires_exact_2_tiles` (default: `True`). If `False`, cavalry may also move 1 tile.

## 5. Counter-Move Tracking & Exhaustion Reset
- **Observation:**
  > "After attacking your opponent will be able to make one immediate counter move/attack with any unit before your turn resumes. Opponent must use a separate piece for each counter attack before reusing the same one, until the offensive player's turn ends."
  1. If the defender has 2 units and both have counter-moved, and the attacker executes a 3rd attack in the same turn, how does reuse work?
  2. Can the defender choose to Pass their counter-move?
- **Engine Handling:**
  - The counter-move reaction state allows the defending player to execute a move/attack with any unit not yet used for a counter-attack in the current active player's turn.
  - If all eligible defending units have already counter-attacked, the restriction resets.
  - Passing a counter-move is permitted (`PassCounterMoveAction`).

## 6. Harbor Blockades by Frigates
- **Observation:**
  - The video notes that "Frigates can blockade enemy harbors."
  - Quick Reference notes "decreases exchange rate by 1, unless occupied by an enemy naval unit."
- **Engine Handling:**
  - An enemy frigate occupying a harbor tile blocks the harbor's trade discount and prevents frigate recruitment from that harbor.

## 7. Victory Conditions: 4 Colonies vs Domination Percentage
- **Observation:**
  - Quick reference defines Domination: "Once the board is completely colonized with no room for an additional colony... player controls 3 quarters of the colonies on the board."
  - Classic video describes victory as "controlling four colonies, approximately three quarters of the board's colonies."
- **Engine Handling:**
  - Configurable victory conditions:
    - `classic_target_colonies`: int (default: 4). If set, any player reaching this number of controlled colonies triggers victory.
    - `domination_control_fraction`: float (default: 0.75).
    - `domination_requires_board_completion`: bool (default: False under classic mode, True under strict quick reference mode).
