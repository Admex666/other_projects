# Technical Decisions Log

## Decision 1: Library Reuse
- **Decision**: Build on top of the official `schnapsen` library rather than writing a duplicate game rules engine from scratch.
- **Rationale**: `schnapsen` provides full Schnapsen rule enforcement, trick scoring, move validation, card deck generation, and built-in baseline bots (`RandBot`, `RdeepBot`, `AlphaBetaBot`, `BullyBot`).

## Decision 2: Hybrid Phase Strategy
- **Decision**: Use Monte Carlo simulation + heuristic evaluation in Phase 1 (talon open, hidden cards) and delegate to `AlphaBetaBot` in Phase 2 (talon closed/exhausted, perfect information).
- **Rationale**: Phase 2 of Schnapsen is a perfect-information finite-game tree where Alpha-Beta search yields provably optimal play, while Phase 1 requires belief state sampling.
