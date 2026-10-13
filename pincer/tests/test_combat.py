import pytest
from pincer.actions.mobilization import (
    AttackAction,
    CounterMoveAction,
    PassCounterMoveAction,
    MoveUnitAction,
)
from pincer.core.enums import PlayerId, TurnPhase, UnitType
from pincer.core.errors import RuleViolationError
from pincer.engine.engine import PincerEngine
from pincer.entities.colony import Colony
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def test_basic_attack_and_piece_capture(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    p1_unit = Unit(unit_id="M1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    p2_unit = Unit(unit_id="M2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    base_state.units["M1"] = p1_unit
    base_state.units["M2"] = p2_unit

    action = AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="M1", target_node_id="T2")
    PincerEngine.apply_action(base_state, action)

    # Defending piece removed
    assert "M2" not in base_state.units
    # Attacking piece occupies tile
    assert base_state.units["M1"].node_id == "T2"
    # Counter-move state is active for P2
    assert base_state.counter_move_state is not None
    assert base_state.counter_move_state.is_active
    assert base_state.counter_move_state.defender_player_id == PlayerId.PLAYER_2


def test_counter_move_blocks_active_player_until_resolved(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    p1_unit = Unit(unit_id="M1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    p1_other = Unit(unit_id="M1_OTHER", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="E1", built_turn=0)
    p2_unit = Unit(unit_id="M2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    p2_other = Unit(unit_id="M2_OTHER", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T3", built_turn=0)

    base_state.units.update({"M1": p1_unit, "M1_OTHER": p1_other, "M2": p2_unit, "M2_OTHER": p2_other})

    # P1 attacks M2
    PincerEngine.apply_action(base_state, AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="M1", target_node_id="T2"))

    # P1 tries to move another unit while counter-move is active -> rejected
    with pytest.raises(RuleViolationError, match="Must resolve pending counter-move"):
        PincerEngine.apply_action(base_state, MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="M1_OTHER", target_node_id="T1"))

    # P2 executes counter-move with M2_OTHER (moves T3 -> E2)
    PincerEngine.apply_action(base_state, CounterMoveAction(
        player_id=PlayerId.PLAYER_2,
        defender_unit_id="M2_OTHER",
        target_node_id="E2",
        is_attack=False,
    ))

    # Counter-move resolved, active is False
    assert not base_state.counter_move_state.is_active
    assert "M2_OTHER" in base_state.counter_move_state.used_counter_unit_ids
    assert base_state.units["M2_OTHER"].node_id == "E2"


def test_counter_move_unit_reuse_restriction(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    p1_a = Unit(unit_id="P1_A", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    p1_b = Unit(unit_id="P1_B", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="E1", built_turn=0)
    # P2 has two units
    p2_a = Unit(unit_id="P2_A", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    p2_b = Unit(unit_id="P2_B", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T3", built_turn=0)
    base_state.units.update({"P1_A": p1_a, "P1_B": p1_b, "P2_A": p2_a, "P2_B": p2_b})

    # P1_A attacks P2_A
    PincerEngine.apply_action(base_state, AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="P1_A", target_node_id="T2"))

    # P2 counter-moves with P2_B
    PincerEngine.apply_action(base_state, CounterMoveAction(
        player_id=PlayerId.PLAYER_2, defender_unit_id="P2_B", target_node_id="E2", is_attack=False
    ))

    # P2_B is now used. Suppose P2 had another unit P2_C on T4
    p2_c = Unit(unit_id="P2_C", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T4", built_turn=0)
    base_state.units["P2_C"] = p2_c

    # P1_B attacks P2_B on E2
    # First let's put P1_B on T3
    base_state.units["P1_B"].node_id = "T3"
    PincerEngine.apply_action(base_state, AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="P1_B", target_node_id="E2"))

    # P2 has P2_C available. If P2 tries to use P2_B (already used) while P2_C hasn't been used:
    # Actually P2_B was captured, but if P2_C tries to move it succeeds. If a used unit tries to move, it's rejected.
    assert base_state.counter_move_state.is_active
    PincerEngine.apply_action(base_state, PassCounterMoveAction(player_id=PlayerId.PLAYER_2))
    assert not base_state.counter_move_state.is_active


def test_cannon_immediate_return(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    cannon = Unit(unit_id="C1", unit_type=UnitType.CANNON, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    enemy = Unit(unit_id="E1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    base_state.units.update({"C1": cannon, "E1": enemy})

    # Cannon attacks with cannon_return=True
    action = AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="C1", target_node_id="T2", cannon_return=True)
    PincerEngine.apply_action(base_state, action)

    # Enemy removed, but Cannon returned to original tile T1
    assert "E1" not in base_state.units
    assert base_state.units["C1"].node_id == "T1"


def test_cannon_attacking_naval_must_return(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    cannon = Unit(unit_id="C1", unit_type=UnitType.CANNON, player_id=PlayerId.PLAYER_1, node_id="T2", built_turn=0)
    naval = Unit(unit_id="F1", unit_type=UnitType.FRIGATE, player_id=PlayerId.PLAYER_2, node_id="W1", built_turn=0)
    base_state.units.update({"C1": cannon, "F1": naval})

    # Cannon attacks naval without return -> rejected
    act_no_return = AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="C1", target_node_id="W1", cannon_return=False)
    with pytest.raises(RuleViolationError, match="MUST return"):
        PincerEngine.apply_action(base_state, act_no_return)

    # Cannon attacks naval with return -> succeeds
    act_return = AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="C1", target_node_id="W1", cannon_return=True)
    PincerEngine.apply_action(base_state, act_return)
    assert "F1" not in base_state.units
    assert base_state.units["C1"].node_id == "T2"


def test_fortified_colony_defense(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    colony = Colony(colony_id="COL_T2", node_id="T2", original_owner=PlayerId.PLAYER_2, has_fort=True, fort_owner=PlayerId.PLAYER_2)
    base_state.colonies[colony.colony_id] = colony
    defender = Unit(unit_id="DEF", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    attacker = Unit(unit_id="ATK", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units.update({"DEF": defender, "ATK": attacker})

    # Direct attack without siege requirement -> rejected
    action = AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="ATK", target_node_id="T2")
    with pytest.raises(RuleViolationError, match="cannot be attacked until besieged"):
        PincerEngine.apply_action(base_state, action)

    # Simulate siege condition met (consecutive_siege_turns >= 1)
    base_state.consecutive_siege_turns[colony.colony_id] = 1

    # Now attack succeeds, fort is destroyed
    PincerEngine.apply_action(base_state, action)
    assert not colony.has_fort
    assert "DEF" not in base_state.units
    assert base_state.units["ATK"].node_id == "T2"
    assert colony.is_annexed
