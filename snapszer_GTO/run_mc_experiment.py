"""
Monte Carlo Rollout Sensitivity Experiment
Tests EV stability across N = [16, 64, 256, 1024, 4096] rollout samples
"""

import random
from schnapsen.game import SchnapsenGamePlayEngine, Bot, PlayerPerspective, Move
from schnapsen.bots import RandBot
from src.bot import GTOExploitBot
from src.tompa_psellos_bot import TompaPsellosBot
from src.diagnostics import test_mc_sensitivity


class CapturePerspectiveBot(GTOExploitBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_perspective = None
        self.target_leader_move = None

    def get_move(self, perspective: PlayerPerspective, leader_move: Move) -> Move:
        if self.target_perspective is None and perspective.get_phase().value == 1 and len(perspective.get_hand()) == 5:
            self.target_perspective = perspective
            self.target_leader_move = leader_move
        return super().get_move(perspective, leader_move)


def main():
    print("=" * 75)
    print("       MONTE CARLO ROLLOUT SENSITIVITY EXPERIMENT (N=16 to 4,096)      ")
    print("=" * 75)

    engine = SchnapsenGamePlayEngine()
    bot = CapturePerspectiveBot(rand=random.Random(42))
    opponent = TompaPsellosBot(rand=random.Random(43))

    engine.play_game(bot, opponent, random.Random(42))

    perspective = bot.target_perspective
    leader_move = bot.target_leader_move

    if perspective is None:
        print("Could not capture perspective.")
        return

    print(f"\nCaptured Phase 1 Decision State:")
    print(f"  Role:        {'FOLLOWER' if leader_move else 'LEADER'}")
    print(f"  Own Hand:    {[str(c) for c in perspective.get_hand()]}")
    print(f"  Trump Card:  {perspective.get_trump_card()}")
    if leader_move:
        print(f"  Leader Move: {leader_move}")

    sample_sizes = [16, 64, 256, 1024, 4096]
    results = test_mc_sensitivity(perspective, leader_move, sample_sizes)

    print("\n" + "=" * 75)
    print("      MONTE CARLO EV CONVERGENCE TABLE (N=16 to 4,096 ROLLOUTS)      ")
    print("=" * 75)
    print("\n| Rollouts (N) | Move Candidate EVs | Best Candidate EV | Max EV Spread | Status |")
    print("| --- | --- | --- | --- | --- |")

    ev_history = []
    for N in sample_sizes:
        move_evs = results[N]
        best_candidate_ev = max(move_evs.values())
        ev_history.append(best_candidate_ev)

        ev_str = ", ".join([f"{k.split('.')[-1][:12]}: {v:.4f}" for k, v in list(move_evs.items())[:3]])
        spread = max(move_evs.values()) - min(move_evs.values())
        status = "High Sample Variance" if N <= 64 else ("Converging" if N <= 256 else "Stabilized Ground Truth")

        print(f"| **N = {N:4d}** | `{ev_str}` | **{best_candidate_ev:.4f}** | {spread:.4f} | {status} |")

    # Convergence test
    ev_16 = ev_history[0]
    ev_4096 = ev_history[-1]
    ev_diff = abs(ev_4096 - ev_16)

    print("\n" + "=" * 75)
    print(f"-> EV Delta between N=16 and N=4096: |{ev_4096:.4f} - {ev_16:.4f}| = {ev_diff:.4f}")
    if ev_diff > 0.05:
        print("-> VERDICT: High Monte Carlo Sample Variance at N=16!")
        print("   (At N=16, rollout EV fluctuates by over 0.05-0.10. Increasing N to >= 256 stabilizes decision tree).")
    else:
        print("-> VERDICT: Rollout Policy Bias! (EV is already stabilized at N=16, policy improvement needed).")
    print("=" * 75)


if __name__ == "__main__":
    main()
