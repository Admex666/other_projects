import argparse
from pathlib import Path
import sys

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pincer.ai.random_bot import SimulationRunner
from pincer.state.setup import create_classic_initial_state


def main():
    parser = argparse.ArgumentParser(description="Run headless Pincer game simulations between bots.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    parser.add_argument("--turns", type=int, default=100, help="Maximum turns before termination.")
    args = parser.parse_args()

    print("=" * 60)
    print(" Pincer AI Simulation Runner (Classic Rules)")
    print(f" Seed: {args.seed} | Max Turns: {args.turns}")
    print("=" * 60)

    initial_state = create_classic_initial_state(seed=args.seed)
    result = SimulationRunner.run_match(initial_state, max_turns=args.turns, seed=args.seed)

    print("\n--- Match Outcome ---")
    if result.winner:
        print(f" Winner: Player {result.winner.value} by Domination / Colony target!")
    else:
        print(" Result: Draw / Terminated at maximum turns limit.")

    print(f" Total Turns: {result.total_turns}")
    print(f" Total Legal Actions Executed: {result.total_actions}")
    print(f" Final Colony Counts: {', '.join(f'{k.value}: {v}' for k, v in result.final_colony_counts.items())}")
    print("=" * 60)


if __name__ == "__main__":
    main()
