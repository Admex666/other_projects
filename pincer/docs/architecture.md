# Engine Architecture Specification

## 1. Design Overview
The Pincer simulation engine is a headless, deterministic, testable Python framework designed for game-theoretic analysis, rule verification, and future AI agent training.

```
                           +------------------------+
                           |       GameConfig       |
                           +------------------------+
                                       |
                                       v
+------------------+       +------------------------+       +------------------------+
|   Board Graph    | ----> |       GameState        | <---- |     Player State       |
| (Nodes, Edges,   |       | (Turn, Phase, Reaction,|       | (Hand, Colonies, Units,|
|  Terrain, Dist)  |       |  Active Player, RNG)   |       |  Exchange Rate)        |
+------------------+       +------------------------+       +------------------------+
                                       |
                     +-----------------+-----------------+
                     |                                   |
                     v                                   v
         +-----------------------+           +-----------------------+
         | LegalActionGenerator  |           |     Engine Pipeline   |
         | (Phase-specific moves)|           |  (Validate & Apply)   |
         +-----------------------+           +-----------------------+
                     |                                   |
                     +-----------------+-----------------+
                                       |
                                       v
                           +------------------------+
                           |  Next GameState / Win  |
                           +------------------------+
```

## 2. Core Modules
- `pincer.core`: Common types, `PlayerId`, `TerrainType`, `UnitType`, `InfrastructureType`, `ManeuverType`, `GameConfig`, custom exceptions (`InvalidActionError`, `RuleViolationError`).
- `pincer.board`: `BoardNode` (tile), `BoardEdge`, `BoardGraph`. Handles graph topology, adjacency, edge flags (road/bridge), shortest path / distance calculation, edge-tile identification, and placement validity.
- `pincer.entities`:
  - `Unit`: id, unit_type, player_id, tile_id, built_turn, cargo (for Frigate transporting land units).
  - `Colony`: id, tile_id, original_owner, current_occupant, fort_present, fort_owner.
  - `Port`: id, tile_id, owner, adjacent_colony_id.
  - `Road` / `Bridge`: edge_id, owner.
  - `Player`: id, resources hand, maneuver hand, units, colonies, exchange rate.
- `pincer.cards`: `ResourceCard`, `ManeuverCard`, `Deck`, `DiceRoller`.
- `pincer.state`: `GameState` dataclass:
  - `board`: `BoardGraph`
  - `players`: `dict[PlayerId, Player]`
  - `current_player`: `PlayerId`
  - `phase`: `TurnPhase` (HARVEST, MOBILIZATION, DEVELOPMENT)
  - `turn_number`: `int`
  - `counter_move_state`: Optional pending counter-move reaction (`attacker_unit_id`, `defender_player_id`, `counter_moved_unit_ids`)
  - `units_moved_this_turn`: `set[str]`
  - `colonies`: `dict[str, Colony]`
  - `units`: `dict[str, Unit]`
  - `rng`: `random.Random`
- `pincer.actions`:
  - `Action` base class
  - `HarvestRollAction`, `MoveUnitAction`, `AttackAction`, `CounterMoveAction`, `PassCounterMoveAction`, `TradeWithBankAction`, `BuildColonyAction`, `BuildPortAction`, `BuildFortAction`, `BuildRoadAction`, `BuildBridgeAction`, `RecruitUnitAction`, `PlayManeuverAction`, `EndPhaseAction`.
- `pincer.engine`:
  - `PincerEngine`: Orchestrator that validates actions and computes state transitions. Supports `copy()` / snapshotting for search algorithms.
- `pincer.victory`:
  - `VictoryChecker`: Checks Domination condition (board fully colonized & player controls >= 75% colonies).

## 3. Turn Flow & State Transitions
1. **Harvest Phase**:
   - Active player rolls resource die (`HarvestRollAction`).
   - For every colony, if adjacent tiles match the die roll and are not occupied by enemy units, the colony's current controller collects 1 matching resource card.
   - Automatically transitions or awaits player transition to **Mobilization**.
2. **Mobilization Phase**:
   - Active player may move or attack with eligible units (units not built this turn, not already moved/attacked if limited).
   - If an attack occurs:
     - Target piece is removed or retreated.
     - Game enters `CounterMoveState`.
     - Defending player must choose an eligible unit (that has not yet counter-moved this turn, unless exhausted) to move/attack, or pass.
     - Once counter-move completes, control returns to active player in Mobilization.
   - Player executes `EndPhaseAction` to enter **Development**.
3. **Development Phase**:
   - Active player may trade with the bank (exchange rate reduced by ports/roads down to 2:1).
   - Active player may build infrastructure (validating tile/edge distance and prerequisites).
   - Active player may recruit units (placed in appropriate colonies/ports; marked with `built_turn = current_turn` so they cannot act until next turn).
   - Active player executes `EndPhaseAction` to end turn, incrementing turn counter and advancing to next player's Harvest Phase.
