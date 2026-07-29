# Changelog

## [0.2.1] - 2026-07-29
### Added
- Added `play.py` interactive CLI game allowing human players to play directly against `GTOExploitBot` in the terminal.
- Added `play_gui.py` launching the built-in `SchnapsenServer` web browser interface (http://127.0.0.1:8080) for graphical gameplay against `GTOExploitBot`.

## [0.2.0] - 2026-07-29
### Added
- Implemented Tompa-style `ExpertBot` (`src/expert_bot.py`) modeling human master principles (trump control, 10/Ace protection, marriage timing, closing discipline).
- Implemented `DecisionLogger` (`src/decision_logger.py`) logging state, chosen move, alternative moves, and candidate EVs to `logs/decisions.jsonl`.
- Implemented 5 Human Leak Simulator archetypes (`src/archetypes.py`): `CallingStationBot`, `OverfolderBot`, `AggressiveCloserBot`, `MarriageHunterBot`, `PointCounterFishBot`.
- Implemented `SchnapsenCFRSolver` (`src/cfr.py`) for Counterfactual Regret Minimization GTO learning.
- Added Expected Net Game Point Difference per deal (`Net GP Diff / deal`) metric to `MatchResult`.
- Executed 9-opponent league tournament: `GTOExploitBot` achieved positive EV (+0.07 Net GP/deal) against `ExpertBot` and positive EV against all human leak archetypes (+1.24 to +2.38 Net GP/deal).
