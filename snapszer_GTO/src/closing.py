"""
Talon Closing Evaluator & Strategy Module based on Section 7 of fejlesztesi_terv.md
"""

from typing import NamedTuple, Optional
from schnapsen.game import PlayerPerspective, Card, Rank, Suit, Marriage, RegularMove, Move, GamePhase


class ClosingEvaluation(NamedTuple):
    should_close: bool
    confidence: float
    guaranteed_points: int
    potential_points: int
    opponent_estimated_points: int
    trump_control_score: float
    reason: str


class TalonClosingEvaluator:
    """
    Evaluates whether closing the talon / pushing aggressive endgame play
    is mathematically favorable for the leader.
    """

    RANK_VALUES = {
        Rank.ACE: 11,
        Rank.TEN: 10,
        Rank.KING: 4,
        Rank.QUEEN: 3,
        Rank.JACK: 2,
    }

    def evaluate_closing(self, perspective: PlayerPerspective) -> ClosingEvaluation:
        """
        Evaluates the current state from the player's perspective to determine
        closing recommendation and game control metrics.
        """
        # Calculate own direct points from tricks won so far
        won_cards = perspective.get_won_cards()
        own_points = sum(self.RANK_VALUES[card.rank] for card in won_cards)

        # Calculate opponent direct points
        opp_won_cards = perspective.get_opponent_won_cards()
        opp_points = sum(self.RANK_VALUES[card.rank] for card in opp_won_cards)

        # Calculate hand strength
        hand_cards = list(perspective.get_hand())
        trump_suit = perspective.get_trump_card().suit if perspective.get_trump_card() else None

        trump_count = 0
        trump_high_count = 0
        hand_point_sum = 0

        for card in hand_cards:
            hand_point_sum += self.RANK_VALUES[card.rank]
            if trump_suit and card.suit == trump_suit:
                trump_count += 1
                if card.rank in (Rank.ACE, Rank.TEN, Rank.KING):
                    trump_high_count += 1

        # Trump control score (0.0 to 1.0)
        trump_control_score = min(1.0, (trump_count * 0.25) + (trump_high_count * 0.25))

        guaranteed_points = own_points
        potential_points = own_points + hand_point_sum

        # Check Marriage potential in hand
        suits_in_hand = {card.suit for card in hand_cards}
        for suit in suits_in_hand:
            has_q = any(c.rank == Rank.QUEEN and c.suit == suit for c in hand_cards)
            has_k = any(c.rank == Rank.KING and c.suit == suit for c in hand_cards)
            if has_q and has_k:
                bonus = 40 if suit == trump_suit else 20
                potential_points += bonus

        should_close = False
        confidence = 0.0
        reason = "Talon open play standard EV"

        if potential_points >= 66 and trump_control_score >= 0.5:
            should_close = True
            confidence = min(0.95, 0.5 + (potential_points - 66) * 0.02 + trump_control_score * 0.3)
            reason = f"Strong potential points ({potential_points}) and trump control ({trump_control_score:.2f})"
        elif own_points >= 33 and trump_high_count >= 2:
            should_close = True
            confidence = 0.75
            reason = f"High direct points ({own_points}) with {trump_high_count} top trumps"

        return ClosingEvaluation(
            should_close=should_close,
            confidence=confidence,
            guaranteed_points=guaranteed_points,
            potential_points=potential_points,
            opponent_estimated_points=opp_points,
            trump_control_score=trump_control_score,
            reason=reason,
        )
