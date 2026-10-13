import pytest
from pincer.actions.mobilization import MoveUnitAction
from pincer.core.enums import PlayerId, TurnPhase, UnitType
from pincer.core.errors import IllegalMovementError
from pincer.engine.engine import PincerEngine
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def test_musketeer_valid_move(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    unit = Unit(unit_id="M_P1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units[unit.unit_id] = unit

    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="T2")
    next_state = PincerEngine.apply_action(base_state, action)

    assert next_state.units["M_P1"].node_id == "T2"
    assert "M_P1" in next_state.units_moved_this_turn


def test_land_unit_cannot_enter_mountain(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    # T1 is adjacent to M1 (mountain)
    unit = Unit(unit_id="M_P1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units[unit.unit_id] = unit

    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="M1")
    with pytest.raises(IllegalMovementError, match="cannot enter mountain"):
        PincerEngine.apply_action(base_state, action)

    # Ensure state was not corrupted
    assert base_state.units["M_P1"].node_id == "T1"
    assert "M_P1" not in base_state.units_moved_this_turn


def test_land_unit_cannot_enter_water_without_bridge(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    # T2 is adjacent to W1 (water)
    unit = Unit(unit_id="M_P1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T2", built_turn=0)
    base_state.units[unit.unit_id] = unit

    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="W1")
    with pytest.raises(IllegalMovementError, match="cannot enter water"):
        PincerEngine.apply_action(base_state, action)


def test_newly_built_unit_cannot_move_until_next_turn(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    base_state.turn_number = 1
    # Unit built on current turn (turn 1)
    unit = Unit(unit_id="M_P1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=1)
    base_state.units[unit.unit_id] = unit

    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="T2")
    with pytest.raises(IllegalMovementError, match="cannot act until next turn"):
        PincerEngine.apply_action(base_state, action)


def test_unit_cannot_move_twice_in_same_turn(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    unit = Unit(unit_id="M_P1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units[unit.unit_id] = unit

    action1 = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="T2")
    PincerEngine.apply_action(base_state, action1)

    action2 = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M_P1", target_node_id="T3")
    with pytest.raises(IllegalMovementError, match="already moved"):
        PincerEngine.apply_action(base_state, action2)


def test_cavalry_movement_rules(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    # Path: T1 -> T2 -> T3 (distance 2)
    cav = Unit(unit_id="C_P1", unit_type=UnitType.CAVALRY, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units[cav.unit_id] = cav

    # Distance 1 is rejected when cavalry_requires_exact_2_tiles is True
    act_dist_1 = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="C_P1", target_node_id="T2")
    with pytest.raises(IllegalMovementError, match="must move exactly 2 tiles"):
        PincerEngine.apply_action(base_state, act_dist_1)

    # Distance 2 succeeds
    act_dist_2 = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="C_P1", target_node_id="T3")
    PincerEngine.apply_action(base_state, act_dist_2)
    assert base_state.units["C_P1"].node_id == "T3"


def test_cavalry_blocked_by_enemy_intermediate(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    cav = Unit(unit_id="C_P1", unit_type=UnitType.CAVALRY, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    # Enemy unit stationed on intermediate T2
    enemy = Unit(unit_id="M_P2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    base_state.units[cav.unit_id] = cav
    base_state.units[enemy.unit_id] = enemy

    # Target is T3 (dist 2 from T1, intermediate is T2)
    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="C_P1", target_node_id="T3")
    with pytest.raises(IllegalMovementError, match="blocked"):
        PincerEngine.apply_action(base_state, action)


def test_frigate_movement_on_water(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    # W1 and W2 are water nodes
    frig = Unit(unit_id="F_P1", unit_type=UnitType.FRIGATE, player_id=PlayerId.PLAYER_1, node_id="W1", built_turn=0)
    base_state.units[frig.unit_id] = frig

    # Frigate moves to W2 (water)
    action = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="F_P1", target_node_id="W2")
    PincerEngine.apply_action(base_state, action)
    assert base_state.units["F_P1"].node_id == "W2"

    # Frigate cannot move to land (e.g. T2)
    base_state.units_moved_this_turn.clear()
    action_land = MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="F_P1", target_node_id="T2")
    with pytest.raises(IllegalMovementError, match="cannot enter non-water"):
        PincerEngine.apply_action(base_state, action_land)
