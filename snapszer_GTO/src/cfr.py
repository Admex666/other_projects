"""
Counterfactual Regret Minimization (CFR) Engine Foundation for Schnapsen GTO Learning
Section 5 of user request & fejlesztesi_terv.md
"""

from collections import defaultdict
import random
from typing import Dict, List, Tuple
from schnapsen.game import GamePhase, Move, PlayerPerspective, Rank


class SchnapsenCFRSolver:
    """
    CFR solver maintaining regret tables and average strategy for Schnapsen decision buckets.
    """

    def __init__(self) -> None:
        # regret_sum[info_set][action_category] -> float
        self.regret_sum: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # strategy_sum[info_set][action_category] -> float
        self.strategy_sum: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def get_info_set_key(self, perspective: PlayerPerspective, is_leader: bool) -> str:
        """
        Abstracts complex Schnapsen state into discrete information buckets.
        """
        phase_str = "P2" if perspective.get_phase() == GamePhase.TWO else "P1"
        role_str = "LEAD" if is_leader else "FOLL"

        won_pts = sum(c.rank.value for c in perspective.get_won_cards() if hasattr(c.rank, "value"))
        pt_bucket = "LOW" if won_pts < 30 else ("MID" if won_pts < 50 else "HIGH")

        hand = perspective.get_hand()
        has_trump = any(c.suit == perspective.get_trump_card().suit for c in hand) if perspective.get_trump_card() else False
        trump_str = "TRUMP" if has_trump else "NOTRUMP"

        return f"{phase_str}_{role_str}_{pt_bucket}_{trump_str}"

    def categorize_move(self, move: Move) -> str:
        if move.is_marriage():
            return "MARRIAGE"
        if move.is_trump_exchange():
            return "EXCHANGE"
        return "REGULAR"

    def get_strategy(self, info_set: str, legal_categories: List[str]) -> Dict[str, float]:
        """
        Calculates current strategy using Regret Matching.
        """
        regrets = self.regret_sum[info_set]
        positive_regrets = {cat: max(regrets[cat], 0.0) for cat in legal_categories}
        total_positive = sum(positive_regrets.values())

        strategy = {}
        num_legal = len(legal_categories)

        if total_positive > 0:
            for cat in legal_categories:
                strategy[cat] = positive_regrets[cat] / total_positive
        else:
            for cat in legal_categories:
                strategy[cat] = 1.0 / num_legal

        return strategy

    def update_regrets(
        self, info_set: str, chosen_category: str, legal_categories: List[str], payoff: float, alt_payoffs: Dict[str, float]
    ) -> None:
        """
        Updates cumulative regrets based on counterfactual payoffs.
        """
        strategy = self.get_strategy(info_set, legal_categories)
        for cat in legal_categories:
            cf_payoff = alt_payoffs.get(cat, payoff)
            regret = cf_payoff - payoff
            self.regret_sum[info_set][cat] += regret
            self.strategy_sum[info_set][cat] += strategy[cat]

    def get_average_strategy(self, info_set: str) -> Dict[str, float]:
        """
        Returns converged GTO average strategy.
        """
        strat_sum = self.strategy_sum[info_set]
        total = sum(strat_sum.values())
        if total > 0:
            return {k: v / total for k, v in strat_sum.items()}
        return {}
