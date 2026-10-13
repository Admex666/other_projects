import pytest
from pincer.actions.mobilization import MoveUnitAction, AttackAction
from pincer.actions.development import RecruitUnitAction, BuildColonyAction
from pincer.core.enums import PlayerId, TurnPhase, UnitType, ResourceType
from pincer.core.errors import (
    IllegalMovementError,
    IllegalPlacementError,
    PhaseOrderError,
    ResourceDeficitError,
    RuleViolationError,
)
from pincer.engine.engine import PincerEngine
from pincer.state.setup import create_classic_initial_state


def test_invalid_phase_action_preserves_state():
    state = create_classic_initial_state(seed=42)
    state.phase = TurnPhase.HARVEST

    # Attempting to move unit during Harvest phase
    unit = state.get_player_units(PlayerId.PLAYER_1)[0]
    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id=unit.unit_id, target_node_id="T2")

    clone_before = state.clone()
    with pytest.raises(PhaseOrderError):
        PincerEngine.apply_action(state, action)

    assert state.phase == clone_before.phase
    assert state.current_player == clone_before.current_player
    assert state.turn_number == clone_before.turn_number
    assert unit.node_id == "T1"


def test_invalid_movement_preserves_state():
    state = create_classic_initial_state(seed=42)
    state.phase = TurnPhase.MOBILIZATION
    unit = state.get_player_units(PlayerId.PLAYER_1)[0]

    # Attempting to move into mountain M1
    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id=unit.unit_id, target_node_id="M1")
    with pytest.raises(IllegalMovementError):
        PincerEngine.apply_action(state, action)

    assert unit.node_id == "T1"
    assert unit.unit_id not in state.units_moved_this_turn


def test_deficit_recruitment_preserves_state():
    state = create_classic_initial_state(seed=42)
    state.phase = TurnPhase.DEVELOPMENT
    # P1 has 0 wheat, cannon costs 4 iron ore
    action = RecruitUnitAction(player_id=PlayerId.PLAYER_1, unit_type=UnitType.CANNON, target_node_id="T1")

    with pytest.raises(ResourceDeficitError):
        PincerEngine.apply_action(state, action)

    assert len(state.units) == 2
    assert state.get_unit_at("T1").unit_type == UnitType.MUSKETEER


def test_state_cloning_isolation():
    state = create_classic_initial_state(seed=42)
    cloned = state.clone()

    # Mutate cloned
    cloned.players[PlayerId.PLAYER_1].add_resource(ResourceType.WOOD, 10)
    cloned.units["M_P1_START"].node_id = "T2"

    # Original remains untouched
    assert state.players[PlayerId.PLAYER_1].resources[ResourceType.WOOD] == 0
    assert state.units["M_P1_START"].node_id == "T1"
