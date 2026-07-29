"""
Tompa-style Expert Heuristic Bot for Schnapsen
Implements human expert play principles:
- Trump control
- Ace/Ten protection
- Strategic marriage timing
- Disciplined closing decisions
- Exact point tracking & Phase 2 Alpha-Beta endgame
"""

import random
from typing import Optional, List
from schnapsen.game import (
    Bot,
    Card,
    GamePhase,
    LeaderPerspective,
    Marriage,
    Move,
    PlayerPerspective,
    Rank,
    RegularMove,
    Suit,
    TrumpExchange,
)
from schnapsen.bots import AlphaBetaBot


class ExpertBot(Bot):
    """
    Expert Schnapsen bot modeled on human master play guidelines.
    """

    RANK_POINTS = {
        Rank.ACE: 11,
        Rank.TEN: 10,
        Rank.KING: 4,
        Rank.QUEEN: 3,
        Rank.JACK: 2,
    }

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "ExpertBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()
        self.phase2_bot = AlphaBetaBot()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        # Phase 2: Perfect information -> Exact Minimax / AlphaBeta
        if perspective.get_phase() == GamePhase.TWO:
            return self.phase2_bot.get_move(perspective, leader_move)

        valid_moves: List[Move] = perspective.valid_moves()
        if len(valid_moves) == 1:
            return valid_moves[0]

        won_cards = perspective.get_won_cards()
        own_points = sum(self.RANK_POINTS[c.rank] for c in won_cards)

        opp_won_cards = perspective.get_opponent_won_cards()
        opp_points = sum(self.RANK_POINTS[c.rank] for c in opp_won_cards)

        hand = list(perspective.get_hand())
        trump_card = perspective.get_trump_card()
        trump_suit = trump_card.suit if trump_card else None

        # 1. Trump Exchange priority: if holding Trump Jack and Talon open, exchange it!
        for move in valid_moves:
            if move.is_trump_exchange():
                return move

        # 2. Marriage Timing: If marriage available and pushes us over 66 or gives strong lead, play it!
        marriages = [m for m in valid_moves if m.is_marriage()]
        if marriages:
            for m in marriages:
                bonus = 40 if m.queen_card.suit == trump_suit else 20
                if own_points + bonus >= 66:
                    return m
            # Otherwise play Trump Marriage first if available, else play regular marriage
            trump_marriages = [m for m in marriages if m.queen_card.suit == trump_suit]
            if trump_marriages:
                return trump_marriages[0]
            if own_points >= 20:
                return marriages[0]

        # 3. Leading (imperfect information)
        if leader_move is None:
            return self._choose_leader_move(valid_moves, hand, own_points, opp_points, trump_suit)

        # 4. Following (imperfect information)
        return self._choose_follower_move(valid_moves, leader_move, hand, trump_suit)

    def _choose_leader_move(
        self, valid_moves: List[Move], hand: List[Card], own_pts: int, opp_pts: int, trump_suit: Optional[Suit]
    ) -> Move:
        """
        Expert Leader strategy:
        - Ace/Ten Protection: Avoid leading unprotected Tens or Aces early unless taking a trick to reach 66.
        - Prefer leading low non-trump cards (Jacks/Queens).
        """
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        if not regular_moves:
            return valid_moves[0]

        scored_moves = []
        for m in regular_moves:
            card = m.card
            card_val = self.RANK_POINTS[card.rank]
            is_trump = card.suit == trump_suit

            score = 0.0

            # Low non-trump leads are safest
            if not is_trump:
                if card.rank in (Rank.JACK, Rank.QUEEN):
                    score += 10.0  # Safe probing lead
                elif card.rank in (Rank.TEN, Rank.ACE):
                    score -= 5.0  # Unprotected high lead penalty
            else:
                # Trump leads
                if card.rank in (Rank.ACE, Rank.TEN):
                    if own_pts >= 45:
                        score += 15.0  # Push to victory with top trumps
                    else:
                        score -= 2.0  # Hold top trumps early
                else:
                    score += 3.0

            scored_moves.append((score, m))

        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return scored_moves[0][1]

    def _choose_follower_move(
        self, valid_moves: List[Move], leader_move: Move, hand: List[Card], trump_suit: Optional[Suit]
    ) -> Move:
        """
        Expert Follower strategy:
        - Capture opponent Tens/Aces with trumps or higher cards if available.
        - Throw off low cards (Jacks/Queens) when opponent plays low.
        """
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        if not regular_moves:
            return valid_moves[0]

        leader_card = leader_move.queen_card if leader_move.is_marriage() else leader_move.card
        leader_val = self.RANK_POINTS[leader_card.rank]

        scored_moves = []
        for m in regular_moves:
            card = m.card
            card_val = self.RANK_POINTS[card.rank]
            is_trump = card.suit == trump_suit

            score = 0.0

            if leader_card.suit == card.suit:
                if card_val > leader_val:
                    # Capturing opponent card
                    score += 10.0 + leader_val
                else:
                    # Ducking under
                    score -= card_val
            elif is_trump:
                # Ruffing opponent high card
                if leader_val >= 10:
                    score += 12.0
                else:
                    score -= 4.0  # Wasting trump on low card
            else:
                # Discarding non-trump
                score -= card_val  # Prefer discarding lowest card

            scored_moves.append((score, m))

        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return scored_moves[0][1]
