import pytest
from pincer.actions.mobilization import TransferViaRoadAction, EndPhaseAction
from pincer.actions.development import (
    BuildColonyAction,
    BuildFortAction,
    BuildPortAction,
    BuildRoadAction,
    BuildBridgeAction,
    RecruitUnitAction,
)
from pincer.board.synthetic import create_synthetic_test_board
from pincer.core.config import GameConfig
from pincer.core.enums import PlayerId, TurnPhase, ResourceType, UnitType, InfrastructureType
from pincer.core.errors import RuleViolationError, ResourceDeficitError
from pincer.engine.engine import PincerEngine
from pincer.entities.colony import Colony
from pincer.entities.infrastructure import Road
from pincer.entities.unit import Unit
from pincer.state.setup import create_classic_initial_state
from pincer.state.state import GameState
from pincer.victory.domination import VictoryEvaluator


def test_classic_setup_components():
    state = create_classic_initial_state()
    assert len(state.players) == 2
    assert PlayerId.PLAYER_1 in state.players
    assert PlayerId.PLAYER_2 in state.players

    # Each player has 1 colony and 1 musketeer
    p1_colonies = state.get_player_colonies(PlayerId.PLAYER_1)
    p2_colonies = state.get_player_colonies(PlayerId.PLAYER_2)
    assert len(p1_colonies) == 1
    assert len(p2_colonies) == 1

    p1_units = state.get_player_units(PlayerId.PLAYER_1)
    p2_units = state.get_player_units(PlayerId.PLAYER_2)
    assert len(p1_units) == 1
    assert len(p2_units) == 1
    assert p1_units[0].unit_type == UnitType.MUSKETEER
    assert p2_units[0].unit_type == UnitType.MUSKETEER

    # Initial colonies must be at least 3 tiles apart
    dist = state.board.graph_distance(p1_colonies[0].node_id, p2_colonies[0].node_id)
    assert dist is not None and dist >= 3


def test_classic_construction_costs():
    state = create_classic_initial_state()
    state.phase = TurnPhase.DEVELOPMENT
    p1 = state.players[PlayerId.PLAYER_1]

    # Colony classic cost: 2 wood, 2 wheat, 1 stone, 1 iron ore
    expected_colony_cost = {
        ResourceType.WOOD: 2,
        ResourceType.WHEAT: 2,
        ResourceType.STONE: 1,
        ResourceType.IRON_ORE: 1,
    }
    assert state.config.construction_costs[InfrastructureType.COLONY] == expected_colony_cost

    # Wall classic cost: 3 stone
    assert state.config.construction_costs[InfrastructureType.WALL] == {ResourceType.STONE: 3}

    # Harbor classic cost: 2 wood, 1 iron ore
    assert state.config.construction_costs[InfrastructureType.HARBOR] == {
        ResourceType.WOOD: 2,
        ResourceType.IRON_ORE: 1,
    }

    # Bridge classic cost: 1 stone
    assert state.config.construction_costs[InfrastructureType.BRIDGE] == {ResourceType.STONE: 1}


def test_classic_unit_costs():
    cfg = GameConfig.classic()
    assert cfg.unit_costs[UnitType.MUSKETEER] == {ResourceType.WHEAT: 2}
    assert cfg.unit_costs[UnitType.CAVALRY] == {ResourceType.WHEAT: 2, ResourceType.MUSTANG: 1}
    assert cfg.unit_costs[UnitType.CANNON] == {ResourceType.IRON_ORE: 4}
    assert cfg.unit_costs[UnitType.FRIGATE] == {ResourceType.WOOD: 2, ResourceType.IRON_ORE: 2}


def test_road_connected_movement():
    state = create_classic_initial_state()
    p1 = PlayerId.PLAYER_1
    # Replace P2 starting colony/unit at T4 with friendly P1 colony
    del state.colonies["COL_P2_START"]
    del state.units["M_P2_START"]

    col_t4 = Colony(colony_id="COL_P1_T4", node_id="T4", original_owner=p1)
    state.colonies[col_t4.colony_id] = col_t4

    # Build road network: E_T1_T2, E_T2_T3, E_T3_T4
    state.board.get_edge("T1", "T2").road_owner = p1
    state.board.get_edge("T2", "T3").road_owner = p1
    state.board.get_edge("T3", "T4").road_owner = p1

    state.phase = TurnPhase.MOBILIZATION
    # Move musketeer from T1 to T4 in 1 move via connected colonies
    unit = state.get_unit_at("T1")
    assert unit is not None

    action = TransferViaRoadAction(player_id=p1, unit_id=unit.unit_id, target_colony_node_id="T4")
    PincerEngine.apply_action(state, action)

    assert unit.node_id == "T4"
    assert unit.unit_id in state.units_moved_this_turn


def test_classic_victory_detection_4_colonies():
    state = create_classic_initial_state()
    # Configure classic target colonies = 4
    assert state.config.classic_target_colonies == 4

    p1 = PlayerId.PLAYER_1
    # Add 3 additional colonies controlled by P1 (total 4)
    state.colonies["C2"] = Colony(colony_id="C2", node_id="T2", original_owner=p1)
    state.colonies["C3"] = Colony(colony_id="C3", node_id="T3", original_owner=p1)
    state.colonies["C4"] = Colony(colony_id="C4", node_id="E2", original_owner=p1)

    winner = VictoryEvaluator.check_domination_winner(state)
    assert winner == p1
