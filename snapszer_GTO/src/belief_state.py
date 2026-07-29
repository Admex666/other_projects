"""
Belief State & Hidden Information Tracking Module
Section 4 & 8 of fejlesztesi_terv.md
"""

from random import Random
from typing import Dict, List, Optional, Set
from schnapsen.game import (
    Card,
    CardCollection,
    GameState,
    Move,
    PlayerPerspective,
    Rank,
    Suit,
)


class OpponentProfile:
    """
    Tracks statistics and tendencies of the opponent for exploit adjustments.
    """

    def __init__(self, name: str = "Opponent"):
        self.name = name
        self.total_games = 0
        self.total_marriages_played = 0
        self.total_trump_exchanges = 0
        self.wins = 0

    def update_game_end(self, won: bool) -> None:
        self.total_games += 1
        if won:
            self.wins += 1

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_games if self.total_games > 0 else 0.5


class BeliefStateModel:
    """
    Manages belief distributions over hidden card configurations and generates
    plausible state determinizations for Monte Carlo sampling.
    """

    def __init__(self, rng: Optional[Random] = None) -> None:
        self.rng = rng or Random()
        self.opponent_profile = OpponentProfile()

    def get_seen_cards(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Set[Card]:
        """
        Returns all cards known to the bot (own hand, trump card, past tricks, leader move).
        """
        return set(perspective.seen_cards(leader_move))

    def get_unseen_cards(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> List[Card]:
        """
        Returns cards that have not yet been revealed to this bot.
        """
        all_deck = perspective.get_engine().deck_generator.get_initial_deck()
        seen = self.get_seen_cards(perspective, leader_move)
        return [card for card in all_deck if card not in seen]

    def sample_determinization(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> GameState:
        """
        Generates a perfect-information GameState by randomly sampling unseen cards
        into opponent's hand and talon positions.
        """
        return perspective.make_assumption(leader_move=leader_move, rand=self.rng)

    def generate_samples(
        self, perspective: PlayerPerspective, leader_move: Optional[Move], num_samples: int
    ) -> List[GameState]:
        """
        Generates N determinized perfect-information game states for Monte Carlo evaluation.
        """
        return [self.sample_determinization(perspective, leader_move) for _ in range(num_samples)]
