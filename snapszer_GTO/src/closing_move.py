"""
Talon Closing Move & Engine Integration for Schnapsen
"""

from typing import Optional, List
from schnapsen.game import Move, Card, GameState, Talon, GamePhase, GamePlayEngine


class CloseTalonMove(Move):
    """
    Move representing closing the talon in Phase 1.
    """

    def __init__(self) -> None:
        super().__init__()

    def _cards(self) -> List[Card]:
        return []

    def is_marriage(self) -> bool:
        return False

    def is_trump_exchange(self) -> bool:
        return False

    def is_close_talon(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "CloseTalonMove()"

    def __str__(self) -> str:
        return "🔒 CLOSE TALON"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CloseTalonMove)

    def __hash__(self) -> int:
        return hash("CloseTalonMove")


def execute_close_talon(game_state: GameState) -> GameState:
    """
    Empties the talon to trigger immediate transition to GamePhase.TWO.
    """
    trump_suit = game_state.trump_suit
    new_talon = Talon([], trump_suit=trump_suit)
    game_state.talon = new_talon
    assert game_state.game_phase() == GamePhase.TWO, "GamePhase must transition to TWO after closing talon!"
    return game_state
