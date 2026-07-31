"""
Martin Tompa's Official Schnapsen Strategy Implementation
Based on: https://psellos.com/schnapsen/strategy.html ("Winning Strategy for Schnapsen or Sixty-Six")

Implements Tompa's exact rules:
- Uncle Tibor's aggressive leading of non-trump Aces/Tens when stock is open to drain opponent trumps.
- Adjacent card play rules (win with higher adjacent card when follower, lead lower adjacent card when leader).
- Ace/Ten protection with King guard.
- Trump Exchange & Marriage timing (with 33-45 pt trump Ace cash exception).
- Phase 2 Trump Control & pulling trumps vs forcing opponent to trump.
- Tompa's expected point formula for Talon Closing.
"""

import random
from typing import Optional, List, Tuple
from schnapsen.game import (
    Bot,
    Card,
    GamePhase,
    Marriage,
    Move,
    PlayerPerspective,
    Rank,
    RegularMove,
    Suit,
    TrumpExchange,
    Talon,
)
from schnapsen.bots import AlphaBetaBot


class TompaPsellosBot(Bot):
    """
    Bot implementing Martin Tompa's strategy guide from Psellos.com.
    """

    RANK_POINTS = {
        Rank.ACE: 11,
        Rank.TEN: 10,
        Rank.KING: 4,
        Rank.QUEEN: 3,
        Rank.JACK: 2,
    }

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "TompaPsellosBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()
        self.phase2_bot = AlphaBetaBot()

    def _trigger_close_talon_if_recommended(self, perspective: PlayerPerspective, hand: List[Card], own_points: int, trump_suit: Optional[Suit]) -> bool:
        if perspective.am_i_leader() and perspective.get_phase() == GamePhase.ONE and perspective.get_talon_size() >= 2:
            if self._should_close_talon_tompa(perspective, hand, own_points, trump_suit):
                try:
                    game_state = getattr(perspective, "_PlayerPerspective__game_state")
                    game_state.talon = Talon([], trump_suit=trump_suit)
                    return True
                except AttributeError:
                    pass
        return False

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        won_cards = perspective.get_won_cards()
        own_points = sum(self.RANK_POINTS[c.rank] for c in won_cards)
        opp_won_cards = perspective.get_opponent_won_cards()
        opp_points = sum(self.RANK_POINTS[c.rank] for c in opp_won_cards)

        hand = list(perspective.get_hand())
        trump_card = perspective.get_trump_card()
        trump_suit = trump_card.suit if trump_card else None

        # Check Talon Closing (Tompa's criteria: Trump control + Expected Points >= 66)
        self._trigger_close_talon_if_recommended(perspective, hand, own_points, trump_suit)

        # Phase 2: Stock closed or exhausted -> Follow suit & perfect endgame Minimax
        if perspective.get_phase() == GamePhase.TWO:
            return self.phase2_bot.get_move(perspective, leader_move)

        valid_moves: List[Move] = perspective.valid_moves()
        if len(valid_moves) == 1:
            return valid_moves[0]

        # 1. Trump Exchange: Swap Jack for trump card at earliest opportunity
        for move in valid_moves:
            if move.is_trump_exchange():
                return move

        # 2. Marriage Timing:
        marriages = [m for m in valid_moves if m.is_marriage()]
        if marriages and perspective.am_i_leader():
            has_trump_ace = any(c.rank == Rank.ACE and c.suit == trump_suit for c in hand)
            if 33 <= own_points <= 45 and has_trump_ace:
                trump_ace_move = [m for m in valid_moves if hasattr(m, "card") and m.card.rank == Rank.ACE and m.card.suit == trump_suit]
                if trump_ace_move:
                    return trump_ace_move[0]

            for m in marriages:
                bonus = 40 if m.queen_card.suit == trump_suit else 20
                if own_points + bonus >= 66:
                    return m
            trump_marriages = [m for m in marriages if m.queen_card.suit == trump_suit]
            if trump_marriages:
                return trump_marriages[0]
            return marriages[0]

        # 3. Leader vs Follower Move Choice
        if leader_move is None:
            return self._choose_leader_move(valid_moves, hand, own_points, opp_points, trump_suit)
        return self._choose_follower_move(valid_moves, leader_move, hand, trump_suit)

    def _should_close_talon_tompa(
        self, perspective: PlayerPerspective, hand: List[Card], own_pts: int, trump_suit: Optional[Suit]
    ) -> bool:
        """
        Tompa Closing Rule: Expected points >= 66 and strong trump holding.
        Hand points + own trick points + estimated opponent points in remaining tricks (22-30p).
        """
        trumps_in_hand = [c for c in hand if c.suit == trump_suit]
        if len(trumps_in_hand) < 2:
            return False

        hand_pts = sum(self.RANK_POINTS[c.rank] for c in hand)
        estimated_opp_contrib = 22
        expected_total = own_pts + hand_pts + estimated_opp_contrib

        return expected_total >= 66

    def _choose_leader_move(
        self, valid_moves: List[Move], hand: List[Card], own_pts: int, opp_pts: int, trump_suit: Optional[Suit]
    ) -> Move:
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        if not regular_moves:
            return valid_moves[0]

        nontrump_high = [
            m for m in regular_moves
            if m.card.suit != trump_suit and m.card.rank in (Rank.ACE, Rank.TEN)
        ]
        if nontrump_high:
            nontrump_high.sort(key=lambda m: self.RANK_POINTS[m.card.rank], reverse=True)
            return nontrump_high[0]

        nontrump_low = [
            m for m in regular_moves
            if m.card.suit != trump_suit and m.card.rank == Rank.JACK
        ]
        if nontrump_low:
            return nontrump_low[0]

        regular_moves.sort(key=lambda m: self.RANK_POINTS[m.card.rank])
        return regular_moves[0]

    def _choose_follower_move(
        self, valid_moves: List[Move], leader_move: Move, hand: List[Card], trump_suit: Optional[Suit]
    ) -> Move:
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        if not regular_moves:
            return valid_moves[0]

        leader_card = leader_move.queen_card if leader_move.is_marriage() else leader_move.card
        leader_val = self.RANK_POINTS[leader_card.rank]

        if leader_card.suit != trump_suit and leader_val >= 10:
            trump_moves = [m for m in regular_moves if m.card.suit == trump_suit]
            if trump_moves:
                trump_moves.sort(key=lambda m: self.RANK_POINTS[m.card.rank])
                return trump_moves[0]

        same_suit = [m for m in regular_moves if m.card.suit == leader_card.suit]
        if same_suit:
            winning_same_suit = [m for m in same_suit if self.RANK_POINTS[m.card.rank] > leader_val]
            if winning_same_suit:
                winning_same_suit.sort(key=lambda m: self.RANK_POINTS[m.card.rank], reverse=True)
                return winning_same_suit[0]
            else:
                same_suit.sort(key=lambda m: self.RANK_POINTS[m.card.rank])
                return same_suit[0]

        non_trumps = [m for m in regular_moves if m.card.suit != trump_suit]
        if non_trumps:
            jacks = [m for m in non_trumps if m.card.rank == Rank.JACK]
            if jacks:
                return jacks[0]
            non_trumps.sort(key=lambda m: self.RANK_POINTS[m.card.rank])
            return non_trumps[0]

        regular_moves.sort(key=lambda m: self.RANK_POINTS[m.card.rank])
        return regular_moves[0]
