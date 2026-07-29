# Schnapsen GTO & Exploit Bot

## Overview
Schnapsen GTO + Exploit AI engine built using the standard Python `schnapsen` library ecosystem.
The primary goal is to maximize long-term expected value (EV) in all decision points and adapt to opponent errors.

## Core Features
- Game rule integration via `schnapsen` library.
- Belief state modeling for hidden card distributions.
- Monte Carlo rollout engine for Phase 1 imperfect-information play.
- Exact Minimax / Alpha-Beta search for Phase 2 perfect-information endgame play.
- Rule-based & heuristic Talon Closing strategy evaluator.
- Benchmarking engine against Schnapsen baseline bots (`RandBot`, `BullyBot`, `RdeepBot`, `AlphaBetaBot`).

## Key Technologies
- Python 3.13
- `schnapsen` library
