# Pincer Simulation Engine

A faithful, deterministic, testable, and modular Python simulation engine for the **Pincer** board game.

This engine separates pure board game rules and state transitions from AI decision-making algorithms, providing a headless environment for rule verification, bot simulation, and game-theoretic analysis.

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- `pytest`

### Installation
Clone the repository and install dependencies (or run directly in editable mode):
```bash
git clone <repo-url>
cd pincer
pip install -e .
```

### Run Tests
```bash
pytest
```
Run tests with verbose output:
```bash
pytest -v
```

### Play Against Bot (Interactive Visual Web Interface)
Launch the local web UI (automatically opens in your browser at `http://localhost:8000`):
```bash
python scripts/web_ui.py
```

### Run Automated Headless Match (Random Bots)
Run a headless simulation between two bots with a deterministic seed:
```bash
python scripts/run_simulation.py --seed 42 --turns 100
```

---

## 2. Architecture & Design Principles

```
src/pincer/
  ├── core/             # Enums, custom exceptions, GameConfig
  ├── board/            # Graph topology, nodes, edges, distance, synthetic test board
  ├── entities/         # Units, colonies, infrastructure (harbor, wall, road, bridge), player
  ├── cards/            # Dice roller, resource cards, standard deck
  ├── state/            # GameState, CounterMoveState, classic initial setup
  ├── actions/          # Harvest, Mobilization, Development, Counter-move action descriptors
  ├── engine/           # Phase managers, movement validator, combat resolver, state transition pipeline
  ├── ai/               # RandomBot and SimulationRunner
  └── victory/          # Domination and Classic Rules colony threshold victory evaluators
```

### Architectural Guarantees:
1. **Graph-Agnostic Topology:** The board geometry is modeled as a mathematical graph of nodes and edges. The engine makes no hardcoded hexagonal or square coordinate assumptions.
2. **State Immutability & Validation Precedence:** All player actions are validated against current state rules before any mutation occurs. Invalid actions raise explicit exceptions (`InvalidActionError`, `RuleViolationError`, `IllegalMovementError`) leaving game state completely uncorrupted.
3. **Deterministic Simulation:** Stochastic mechanics (dice rolls, deck shuffling) utilize seeded pseudo-random number generators (`random.Random(seed)`).
4. **Separation of Concerns:** Core engine modules contain zero AI search logic or UI dependencies.

---

## 3. Implemented Rules

### Setup (Classic Rules)
- Two players (P1, P2).
- Each player starts with **1 Colony** and **1 Musketeer**.
- Initial colonies are spaced at graph distance $\ge 3$ and never on edge tiles.
- Configurable resource catalog supporting both classic and quick reference terminology.

### Turn Structure
1. **Harvest Phase:**
   - Active player rolls the 6-sided resource die (`HarvestRollAction`).
   - Every eligible colony produces 1 resource card matching adjacent terrain tiles.
   - Resource harvest is blocked if an enemy unit occupies the adjacent producing tile.
   - Annexed colonies award harvest to the occupying player.
2. **Mobilization Phase:**
   - Active player moves and attacks with eligible units.
   - Single unit per tile maximum (no stacking).
   - **Musketeer:** Range 1 tile (land only, no mountains or water).
   - **Cavalry:** Range 2 tiles (cannot traverse mountain or enemy-occupied tiles).
   - **Cannon:** Range 1 tile; retreats/returns immediately to origin tile after attacking; MUST return when attacking naval units.
   - **Frigate:** Range 1–2 tiles on water; transports 1 land unit.
   - **Combat & Counter-Moves:**
     - Attacking removes defender's piece and occupies tile.
     - Enters `CounterMoveState`: Defender executes 1 immediate counter-move/attack with an available piece (or passes) before active player's turn resumes.
     - Defender must use separate units for each counter-move before reusing.
   - **Road Transfer:** Units may transfer between road-connected friendly colonies in 1 move.
3. **Development Phase:**
   - Bank trading: base 5:1 rate, reduced by 1 per harbor or road-connected colony (minimum 2:1 limit).
   - Harbor trade discount is blockaded if an enemy naval unit occupies the harbor tile.
   - Construction:
     - **Colony:** Built on friendly unit tile, distance $\ge 3$ from other colonies, not on edge tile.
     - **Wall / Fort:** Built on friendly colony; forces enemies to siege with cannon/frigate + land unit for a full turn.
     - **Harbor / Port:** Built on water tile adjacent to friendly colony.
     - **Road:** Built along edges connecting friendly colonies/roads.
     - **Bridge:** Built on water crossing edge touching land on both sides.
   - Recruitment:
     - Units placed in empty eligible colonies/harbors.
     - Cannot recruit land/naval units from an annexed colony.
     - **Newly recruited units are inactive until their next eligible turn.**

### Annexation Mechanics
- When an enemy occupies a colony tile, the colony is annexed (`is_annexed == True`).
- Occupier receives harvest from the colony.
- Occupier cannot recruit units from the colony.
- Occupier may build a fort/wall a turn after annexing.
- When the occupier vacates the colony tile, ownership reverts to the original owner on their turn, and any fort built by the occupier is destroyed.

### Victory Evaluation
- **Classic Target:** Controlling 4 colonies (via construction or annexation).
- **Domination:** Controlling $\ge 75\%$ of all colonies when the board has no valid room left for new colonies.

---

## 4. Unresolved Questions & Configurable Mechanics

All unstated or ambiguous mechanics from the source material are cataloged in [`docs/open_questions.md`](docs/open_questions.md) and exposed via `GameConfig`:

1. **Board Layout Options:** Both the complete 58-tile physical game board layout (`pincer.board.classic_board`) and the 10-tile synthetic test board (`pincer.board.synthetic`) are fully supported. The Web UI and engine allow switching between them.
2. **Resource Catalog Aliases:** Speech-to-text transcript mentions "fish" and "Mustang", which are mapped via aliases in `ResourceType`.
3. **Cavalry Movement:** Configurable `cavalry_requires_exact_2_tiles` (defaults to True per literal wording, configurable to False).
4. **Maneuver Cards & Advanced Deck Mechanics:** Card descriptors exist in `pincer.cards`, but complex card draw timing and deck exhaustion rules remain disabled until finalized in future phases.
