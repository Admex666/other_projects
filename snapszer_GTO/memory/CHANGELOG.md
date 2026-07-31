# Changelog

## [0.4.0] - 2026-07-31
### Added
- Implemented `ExactOracleSolver` (`src/oracle.py`) providing exact Minimax Ground-Truth EV evaluations across determinizations.
- Added seamless Talon Closing engine support (`game_state.talon = Talon([])`) in `src/bot.py` and `src/tompa_psellos_bot.py`.
- Integrated Expert Rollout Policy (`TompaPsellosBot`) into `GTOExploitBot` Monte Carlo simulations.
- Created `run_phase3_diagnostics.py` generating Ground-Truth Oracle Calibration Report ([reports/phase3_ground_truth_report.md](file:///e:/Data/other_projects/snapszer_GTO/reports/phase3_ground_truth_report.md)).
- Evaluated Decision Disagreement Matrix (% wrong choices, True EV Loss) and true Oracle-calibrated EV Error Delta Histogram.

## [0.3.1] - 2026-07-31
### Added
- Resolved internal inconsistency between Loss Attribution categories and Top 10 Decision Loss Patterns by unifying dynamic log extraction in `LossAttributionAnalyzer`.
- Created `reports/narrative_losses_100.md` providing turn-by-turn human narrative explanations for 100 lost games against `TompaPsellosBot`.
- Created `run_mc_experiment.py` measuring Monte Carlo EV convergence across N=[16, 64, 256, 1024, 4096] rollouts.
