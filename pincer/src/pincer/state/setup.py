"""Game setup and initial state construction for Classic Rules."""
from typing import Optional
from pincer.board.graph import BoardGraph
from pincer.board.synthetic import create_synthetic_test_board
from pincer.cards.cards import create_standard_deck
from pincer.cards.dice import DiceRoller
from pincer.core.config import GameConfig
from pincer.core.enums import PlayerId, TurnPhase, UnitType
from pincer.entities.colony import Colony
from pincer.entities.player import Player
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def create_classic_initial_state(
    board: Optional[BoardGraph] = None,
    seed: Optional[int] = 42,
    board_type: str = "synthetic",
) -> GameState:
    """Creates a standard Classic Rules initial game state.
    
    Setup rules:
    - 2 players (P1, P2).
    - Each player starts with 1 Colony and 1 Musketeer.
    - Colonies are placed at distance >= 3 apart, not on edge tiles.
    - If board_type == 'synthetic': 10-tile test board (P1 at T1, P2 at T4).
    - If board_type == 'full_58': Complete 58-tile board (P1 at H14, P2 at H45).
    - Classic rules configuration and costs.
    """
    if board is not None:
        g = board
    elif board_type == "full_58":
        from pincer.board.classic_board import create_full_58_tile_board
        g = create_full_58_tile_board()
    else:
        g = create_synthetic_test_board()

    config = GameConfig.classic()

    players = {
        PlayerId.PLAYER_1: Player(player_id=PlayerId.PLAYER_1),
        PlayerId.PLAYER_2: Player(player_id=PlayerId.PLAYER_2),
    }

    state = GameState(
        board=g,
        players=players,
        current_player=PlayerId.PLAYER_1,
        phase=TurnPhase.HARVEST,
        turn_number=1,
        deck=create_standard_deck(seed=seed),
        dice=DiceRoller(seed=seed),
        config=config,
    )

    # Initial colonies and musketeers
    if board_type == "full_58" or "H14" in g.nodes:
        start_p1_node = "H14"
        start_p2_node = "H45"
    else:
        start_p1_node = "T1"
        start_p2_node = "T4"

    colony_p1 = Colony(colony_id="COL_P1_START", node_id=start_p1_node, original_owner=PlayerId.PLAYER_1)
    colony_p2 = Colony(colony_id="COL_P2_START", node_id=start_p2_node, original_owner=PlayerId.PLAYER_2)
    state.colonies[colony_p1.colony_id] = colony_p1
    state.colonies[colony_p2.colony_id] = colony_p2

    musk_p1 = Unit(unit_id="M_P1_START", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id=start_p1_node, built_turn=0)
    musk_p2 = Unit(unit_id="M_P2_START", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id=start_p2_node, built_turn=0)
    state.units[musk_p1.unit_id] = musk_p1
    state.units[musk_p2.unit_id] = musk_p2

    return state
