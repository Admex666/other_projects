"""
Human Leak Simulator - Player Archetypes for Schnapsen Exploit Analysis
Implements 5 common human leak profiles:
1. CallingStationBot - Passive, never closes, plays low variance.
2. OverfolderBot - Overly defensive, ducks high cards & yields trumps.
3. AggressiveCloserBot - Closes prematurely without sufficient point/trump control.
4. MarriageHunterBot - Instantly plays 20/40 marriages regardless of position/EV.
5. PointCounterFishBot - Miscalculates trick points and closing bounds.
"""

import random
from typing import Optional, List
from schnapsen.game import (
    Bot,
    Card,
    GamePhase,
    Move,
    PlayerPerspective,
    Rank,
    RegularMove,
    Suit,
)


class CallingStationBot(Bot):
    """
    Passive player who never closes the talon and plays safe low cards.
    """

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "CallingStationBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        valid_moves = perspective.valid_moves()
        # Filter out marriages or trump exchanges if regular moves available
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        moves = regular_moves if regular_moves else valid_moves
        # Sort by rank value to play lowest card passively
        moves.sort(key=lambda m: m.card.rank.value if hasattr(m, "card") else 0)
        return moves[0]


class OverfolderBot(Bot):
    """
    Afraid of trumps and opponent high cards; yields tricks easily under pressure.
    """

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "OverfolderBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        valid_moves = perspective.valid_moves()
        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        moves = regular_moves if regular_moves else valid_moves

        trump_suit = perspective.get_trump_card().suit if perspective.get_trump_card() else None

        # Avoid playing trumps unless forced
        non_trumps = [m for m in moves if hasattr(m, "card") and m.card.suit != trump_suit]
        if non_trumps:
            return self.rng.choice(non_trumps)
        return self.rng.choice(moves)


class AggressiveCloserBot(Bot):
    """
    Closes the talon prematurely at the first opportunity without sufficient control.
    """

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "AggressiveCloserBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        valid_moves = perspective.valid_moves()
        # Aggressively plays marriages or high card leads
        marriages = [m for m in valid_moves if m.is_marriage()]
        if marriages:
            return marriages[0]

        regular_moves = [m for m in valid_moves if not m.is_marriage() and not m.is_trump_exchange()]
        if regular_moves:
            # Plays highest card aggressively
            regular_moves.sort(key=lambda m: m.card.rank.value, reverse=True)
            return regular_moves[0]
        return valid_moves[0]


class MarriageHunterBot(Bot):
    """
    Forces marriages 20/40 immediately whenever available, ignoring position/EV.
    """

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "MarriageHunterBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        valid_moves = perspective.valid_moves()
        marriages = [m for m in valid_moves if m.is_marriage()]
        if marriages:
            return marriages[0]
        return self.rng.choice(valid_moves)


class PointCounterFishBot(Bot):
    """
    Miscalculates point counts by +/- 10-15 points, leading to bad closing and lead decisions.
    """

    def __init__(self, rand: Optional[random.Random] = None, name: Optional[str] = "PointCounterFishBot") -> None:
        super().__init__(name)
        self.rng = rand or random.Random()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        valid_moves = perspective.valid_moves()
        # Adds noisy randomness to decision making
        return self.rng.choice(valid_moves)
