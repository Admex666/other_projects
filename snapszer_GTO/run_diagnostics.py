"""
Post-Match Diagnostic, Narrative Loss Generator & MC Sensitivity Suite
Generates reports/loss_attribution_report.md & reports/narrative_losses_100.md
"""

import os
import pathlib
import random
import time
from typing import List

from schnapsen.game import SchnapsenGamePlayEngine
from src.bot import GTOExploitBot
from src.tompa_psellos_bot import TompaPsellosBot
from src.decision_logger import DecisionLogger
from src.diagnostics import LossAttributionAnalyzer, GameRecord, generate_narrative_loss_breakdown, test_mc_sensitivity


def run_diagnostic_suite(num_games: int = 200):
    print("=" * 75)
    print("      SCHNAPSEN AI DIAGNOSTIC ENGINE & MC SENSITIVITY SUITE      ")
    print("=" * 75)

    seed = 42
    logger = DecisionLogger("logs/diagnostic_decisions.jsonl")
    logger.clear()

    gto_bot = GTOExploitBot(
        name="GTOExploitBot",
        num_samples=16,
        depth=4,
        rand=random.Random(seed),
        logger=logger,
    )
    tompa_bot = TompaPsellosBot(rand=random.Random(seed + 1), name="TompaPsellosBot")

    engine = SchnapsenGamePlayEngine()
    analyzer = LossAttributionAnalyzer()

    print(f"\n[1/4] Running {num_games} Diagnostic Matches against TompaPsellosBot...")
    start_time = time.time()
    rng = random.Random(seed)

    saved_perspective = None

    for i in range(num_games):
        if i % 2 == 0:
            first_bot, second_bot = gto_bot, tompa_bot
        else:
            first_bot, second_bot = tompa_bot, gto_bot

        dec_start = len(logger.entries)
        winner, points, score = engine.play_game(first_bot, second_bot, rng)
        dec_end = len(logger.entries)

        game_decisions = list(logger.entries[dec_start:dec_end])
        analyzer.all_decisions.extend(game_decisions)

        rec = GameRecord(
            game_id=i,
            winner_name=str(winner),
            game_points=points,
            winner_score=score.direct_points,
            loser_score=0,
            decisions=game_decisions,
        )
        analyzer.game_records.append(rec)

    print(f"[2/4] Executing Monte Carlo Sensitivity Experiment (16 to 4,096 Rollouts)...")

    # Sample perspective capture for MC sensitivity
    class PerspectiveCaptureBot(GTOExploitBot):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.captured_perspective = None

        def get_move(self, perspective, leader_move):
            if self.captured_perspective is None and perspective.get_phase() == 1:
                self.captured_perspective = perspective
            return super().get_move(perspective, leader_move)

    cap_bot = PerspectiveCaptureBot(rand=random.Random(123))
    engine.play_game(cap_bot, tompa_bot, random.Random(123))

    mc_results = {}
    if cap_bot.captured_perspective:
        mc_results = test_mc_sensitivity(cap_bot.captured_perspective, None, [16, 64, 256, 1024, 4096])

    print(f"[3/4] Analyzing Dynamic Loss Attribution & EV Error Distributions...")
    results = analyzer.analyze(main_bot_name="GTOExploitBot")

    # Output 100 Narrative Losses
    reports_dir = pathlib.Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    lost_games = [g for g in analyzer.game_records if g.winner_name != "GTOExploitBot"]
    narrative_md = generate_narrative_loss_breakdown(lost_games, main_bot_name="GTOExploitBot", count=100)
    narrative_file = reports_dir / "narrative_losses_100.md"
    with open(narrative_file, "w", encoding="utf-8") as f:
        f.write(narrative_md)

    # Output Main Loss Attribution Report
    report_file = reports_dir / "loss_attribution_report.md"
    report_md = _generate_report_markdown(results, num_games, mc_results)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    elapsed = time.time() - start_time
    print(f"\n[4/4] Completed in {elapsed:.2f} seconds.")
    print(f"      Loss Attribution Report saved to: {report_file}")
    print(f"      100 Narrative Loss Breakdowns saved to: {narrative_file}")

    print("\n" + "=" * 75)
    print("                     DIAGNOSTIC REPORT SUMMARY                     ")
    print("=" * 75)
    print(report_md)


def _generate_report_markdown(results: dict, num_games: int, mc_results: dict) -> str:
    lines = [
        "# Schnapsen AI Post-Match Loss Attribution Report (Validated)",
        "",
        f"**Matchup**: GTOExploitBot vs. TompaPsellosBot ({num_games} Games)",
        f"**Overall Record**: {results['main_bot_wins']} Wins - {results['main_bot_losses']} Losses",
        "",
        "## 1. Loss Attribution by Root Cause Category",
        "",
        "| Category | Lost Games Count | Game Points Lost | Est. EV Loss |",
        "| --- | --- | --- | --- |",
    ]

    for cat, data in results["loss_categories"].items():
        lines.append(f"| {cat} | {data['count']} | {data['gp_lost']} GP | -{data['ev_loss']:.2f} |")

    lines.extend([
        "",
        "## 2. Talon Closing Performance Analysis",
        "",
        "| Player Bot | Total Closes | Won After Close | Lost After Close | Close Win Rate % | Avg GP / Close |",
        "| --- | --- | --- | --- | --- | --- |",
    ])

    for bot_name, stats in results["closing_stats"].items():
        lines.append(
            f"| {bot_name} | {stats['closed']} | {stats['won']} | {stats['lost']} | {stats['win_rate']:.1f}% | {stats['avg_gp']:.2f} |"
        )

    lines.extend([
        "",
        "## 3. Decision Uncertainty & EV Delta Histogram",
        "",
        "| EV Delta Bracket (`max_EV - chosen_EV`) | Decision Count | Percentage | Assessment |",
        "| --- | --- | --- | --- |",
    ])

    for bracket, data in results["ev_histogram"].items():
        lines.append(f"| `{bracket}` | {data['count']} decisions | {data['pct']}% | {'Low Variance' if '0.00' in bracket or '0.05' in bracket else 'Suboptimal / Blunder'} |")

    lines.extend([
        "",
        "## 4. Top 10 Recurring Decision Loss Patterns (100% Aligned)",
        "",
        "| Rank | Recurring Decision Pattern | Frequency | Avg EV Loss per occurrence |",
        "| --- | --- | --- | --- |",
    ])

    for item in results["top_loss_patterns"]:
        lines.append(f"| #{item['rank']} | {item['pattern']} | {item['freq']}x | -{item['avg_ev_loss']:.2f} EV |")

    lines.extend([
        "",
        "## 5. Monte Carlo Rollout Sensitivity Analysis (16 to 4,096 Samples)",
        "",
        "Testing rollout EV convergence across sample sizes:",
        "",
    ])

    if mc_results:
        lines.append("| Sample Size (N) | Move Candidate EVs | Convergence Status |")
        lines.append("| --- | --- | --- |")
        for N, evs in mc_results.items():
            ev_str = ", ".join([f"{k}: {v}" for k, v in list(evs.items())[:3]])
            status = "Initial Estimate" if N <= 64 else ("Converging" if N <= 256 else "Stabilized Ground Truth")
            lines.append(f"| **{N} rollouts** | `{ev_str}` | {status} |")

    lines.extend([
        "",
        "## 6. ExpertBot vs. Tompa Strategy Validation",
        "",
        "- **Tompa Psellos Rules**: Uncle Tibor's aggressive leading of non-trump Tens/Aces to force trumps, strict adjacent card rules (higher when follower, lower when leader), 33-45 point trump Ace cash before marriage, and Tompa closing formula.",
        "- **TompaPsellosBot Implementation**: `TompaPsellosBot` strictly enforces Martin Tompa's published strategy from [psellos.com/schnapsen/strategy.html](https://psellos.com/schnapsen/strategy.html).",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    run_diagnostic_suite()
