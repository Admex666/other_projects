# AGENTS.md — Project Governance & Operational Blueprint

## 1. Project Purpose & North Star
**Project:** Pincer AI (Phase 1: Rule Engine Foundation)
**North Star:** A faithful, deterministic, high-performance, and modular simulation engine for the *Pincer* board game, strictly adhering to the game rules without inventing mechanics silently.

## 2. Governance Principles
1. **Rule Fidelity & Transparency:**
   - The engine implements the documented rules from `docs/spec/player_card.md`.
   - Never invent missing rules silently. Any ambiguities or unstated numbers (e.g., exact resource costs, deck composition) are cataloged in `docs/open_questions.md` and kept configurable.
2. **Separation of Concerns:**
   - Pure game rules and state transition validation are isolated from AI decision-making or search algorithms.
   - Core game engine has no dependencies on external AI libraries or GUI frameworks.
3. **Immutability & State Safety:**
   - Action validation must precede state mutations. Invalid actions must raise explicit exceptions or return rejection results without corrupting the game state.
   - Deep copying or pure state transitions allow tree search (MCTS, Minimax, RL) in later phases without unintended mutation leaks.
4. **Graph-Agnostic Topology:**
   - The board geometry is represented as an arbitrary graph of tiles and edges. Hexagonal, square, or custom board layouts can be loaded without changing engine rules.
5. **Deterministic Simulation:**
   - All stochastic events (dice rolls, card shuffling) use an explicit, seeded random number generator (`random.Random(seed)`).
6. **Test-Driven Rigor:**
   - Every rule, phase transition, combat interaction, movement constraint, and invalid action must have dedicated unit tests using `pytest`.

## 3. Module Boundaries
```
src/pincer/
  ├── core/             # Fundamental abstractions: enums, types, config, errors
  ├── board/            # Graph topology, nodes, edges, terrain, distances
  ├── entities/         # Units, infrastructure, players
  ├── cards/            # Resource cards, maneuvers, deck, dice
  ├── state/            # Game state, turn phases, counter-move state
  ├── actions/          # Legal action generation, action descriptors
  ├── engine/           # Phase managers, combat resolver, state transition pipeline
  └── victory/          # Victory condition evaluators (Domination)
```
