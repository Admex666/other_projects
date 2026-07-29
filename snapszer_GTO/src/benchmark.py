"""
Schnapsen Bot Benchmarking Suite
Calculates win rates, game points per 100 hands (GP/100), Expected Net Game Point Difference per deal, and trick point stats.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple
from schnapsen.game import Bot, SchnapsenGamePlayEngine


@dataclass
class MatchResult:
    bot1_name: str
    bot2_name: str
    num_games: int
    bot1_wins: int
    bot2_wins: int
    bot1_game_points: int
    bot2_game_points: int
    bot1_trick_points: float
    bot2_trick_points: float

    @property
    def bot1_win_rate(self) -> float:
        return (self.bot1_wins / self.num_games) * 100 if self.num_games > 0 else 0.0

    @property
    def bot2_win_rate(self) -> float:
        return (self.bot2_wins / self.num_games) * 100 if self.num_games > 0 else 0.0

    @property
    def bot1_gp_100(self) -> float:
        return (self.bot1_game_points / self.num_games) * 100 if self.num_games > 0 else 0.0

    @property
    def bot2_gp_100(self) -> float:
        return (self.bot2_game_points / self.num_games) * 100 if self.num_games > 0 else 0.0

    @property
    def net_gp_diff_per_deal(self) -> float:
        """
        Expected Net Game Point Difference per deal (+GP EV for bot1 per hand).
        Similar to EV in poker cash games.
        """
        return (self.bot1_game_points - self.bot2_game_points) / self.num_games if self.num_games > 0 else 0.0

    def summary_table(self) -> str:
        lines = [
            f"| Metric | {self.bot1_name} | {self.bot2_name} |",
            "| --- | --- | --- |",
            f"| Wins | {self.bot1_wins} | {self.bot2_wins} |",
            f"| Win Rate % | {self.bot1_win_rate:.1f}% | {self.bot2_win_rate:.1f}% |",
            f"| Game Points Total | {self.bot1_game_points} | {self.bot2_game_points} |",
            f"| Game Points / 100 hands | {self.bot1_gp_100:.1f} | {self.bot2_gp_100:.1f} |",
            f"| **Net GP Diff / deal** | **{self.net_gp_diff_per_deal:+.2f}** | **{-self.net_gp_diff_per_deal:+.2f}** |",
            f"| Avg Trick Points / game | {self.bot1_trick_points:.1f} | {self.bot2_trick_points:.1f} |",
        ]
        return "\n".join(lines)


class BenchmarkSuite:
    """
    Runs pairwise bot tournaments and measures relative performance and EV diffs.
    """

    def __init__(self, seed: int = 42) -> None:
        self.engine = SchnapsenGamePlayEngine()
        self.seed = seed

    def run_matchup(self, bot1: Bot, bot2: Bot, num_games: int = 100) -> MatchResult:
        """
        Runs a series of games between bot1 and bot2 with alternating initial leaders.
        """
        bot1_wins = 0
        bot2_wins = 0
        bot1_gp = 0
        bot2_gp = 0
        bot1_tp_sum = 0
        bot2_tp_sum = 0

        rng = random.Random(self.seed)

        for i in range(num_games):
            # Alternate starter each game to remove first-player bias
            if i % 2 == 0:
                first_bot, second_bot = bot1, bot2
            else:
                first_bot, second_bot = bot2, bot1

            winner, points, score = self.engine.play_game(first_bot, second_bot, rng)

            if winner is bot1:
                bot1_wins += 1
                bot1_gp += points
                bot1_tp_sum += score.direct_points
            else:
                bot2_wins += 1
                bot2_gp += points
                bot2_tp_sum += score.direct_points

        return MatchResult(
            bot1_name=str(bot1),
            bot2_name=str(bot2),
            num_games=num_games,
            bot1_wins=bot1_wins,
            bot2_wins=bot2_wins,
            bot1_game_points=bot1_gp,
            bot2_game_points=bot2_gp,
            bot1_trick_points=bot1_tp_sum / num_games if num_games > 0 else 0.0,
            bot2_trick_points=bot2_tp_sum / num_games if num_games > 0 else 0.0,
        )

    def run_league(self, main_bot: Bot, opponents: List[Bot], num_games_per_opponent: int = 100) -> List[MatchResult]:
        results = []
        for opp in opponents:
            res = self.run_matchup(main_bot, opp, num_games=num_games_per_opponent)
            results.append(res)
        return results
