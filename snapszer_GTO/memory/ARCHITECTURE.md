# Architecture Overview

```text
                  GTOExploitBot
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
  Phase 1 (Imperfect Info)       Phase 2 (Perfect Info)
  - BeliefStateSampler           - AlphaBetaBot Solver
  - ClosingEvaluator
  - MonteCarlo Rollouts
```

## Component Breakdown

1. `src/closing.py`: Evaluates whether closing the talon in Phase 1 yields higher EV than leaving it open.
2. `src/belief_state.py`: Tracks opponent's revealed cards (from marriages, trump exchanges) and generates random determinizations of unseen cards.
3. `src/bot.py`: Main `GTOExploitBot` implementing `schnapsen.game.Bot`.
4. `src/benchmark.py`: League tournament framework running standard match series between bots.
