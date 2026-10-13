"""Shared pytest fixtures for Pincer simulation engine."""
import pytest
from pincer.board.synthetic import create_synthetic_test_board
from pincer.cards.cards import create_standard_deck
from pincer.cards.dice import DiceRoller
from pincer.core.config import GameConfig
from pincer.core.enums import PlayerId, TurnPhase
from pincer.entities.player import Player
from pincer.state.state import GameState


@pytest.fixture
def base_state() -> GameState:
    """Provides a fresh game state on the synthetic test board with two players."""
    board = create_synthetic_test_board()
    players = {
        PlayerId.PLAYER_1: Player(player_id=PlayerId.PLAYER_1),
        PlayerId.PLAYER_2: Player(player_id=PlayerId.PLAYER_2),
    }
    return GameState(
        board=board,
        players=players,
        current_player=PlayerId.PLAYER_1,
        phase=TurnPhase.HARVEST,
        turn_number=1,
        deck=create_standard_deck(seed=42),
        dice=DiceRoller(seed=42),
        config=GameConfig(),
    )
