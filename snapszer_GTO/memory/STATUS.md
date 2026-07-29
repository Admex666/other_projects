# Project Status

## Current State
- `GTOExploitBot` implemented and benchmarked against Tompa-style `ExpertBot` and 5 Human Leak Archetypes.
- Structured decision logging active (`logs/decisions.jsonl`).
- Interactive gameplay interfaces added for playing against `GTOExploitBot`:
  - `play.py`: Interactive Terminal CLI game.
  - `play_gui.py`: Built-in Web Browser GUI server using `SchnapsenServer` (http://127.0.0.1:8080).

## Benchmark Results (100 games per matchup, alternating initial leader)

| Opponent Bot | GTO Win Rate % | Total GP (GTO vs Opp) | **Net GP Diff / deal** |
| --- | --- | --- | --- |
| **ExpertBot (Tompa)** | 48.0% | 76 - 69 | **+0.07** |
| **OverfolderBot** | 90.0% | 248 - 10 | **+2.38** |
| **CallingStationBot** | 92.0% | 192 - 12 | **+1.80** |
| **PointCounterFishBot** | 86.0% | 198 - 18 | **+1.80** |
| **MarriageHunterBot** | 86.0% | 188 - 18 | **+1.70** |
| **RandMiniMaxBot** | 77.0% | 180 - 29 | **+1.51** |
| **MLPlayingBot** | 76.0% | 170 - 26 | **+1.44** |
| **AggressiveCloserBot** | 71.0% | 156 - 32 | **+1.24** |
| **RdeepBot** | 63.0% | 92 - 57 | **+0.35** |
