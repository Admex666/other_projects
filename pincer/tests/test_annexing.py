import pytest
from pincer.actions.mobilization import AttackAction, MoveUnitAction, PassCounterMoveAction, EndPhaseAction
from pincer.actions.development import RecruitUnitAction, BuildFortAction
from pincer.core.enums import PlayerId, TurnPhase, UnitType, ResourceType
from pincer.core.errors import RuleViolationError
from pincer.engine.engine import PincerEngine
from pincer.entities.colony import Colony
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def test_annexing_colony_and_occupation(base_state: GameState):
    base_state.phase = TurnPhase.MOBILIZATION
    colony = Colony(colony_id="COL_T2", node_id="T2", original_owner=PlayerId.PLAYER_2)
    base_state.colonies[colony.colony_id] = colony

    # P2 unit occupies T2, P1 unit attacks from T1
    p2_unit = Unit(unit_id="U2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    p1_unit = Unit(unit_id="U1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units.update({"U1": p1_unit, "U2": p2_unit})

    # Attack and occupy
    PincerEngine.apply_action(base_state, AttackAction(player_id=PlayerId.PLAYER_1, attacker_unit_id="U1", target_node_id="T2"))

    # Resolve counter move pass
    PincerEngine.apply_action(base_state, PassCounterMoveAction(player_id=PlayerId.PLAYER_2))

    assert colony.is_annexed
    assert colony.controller == PlayerId.PLAYER_1
    assert colony.original_owner == PlayerId.PLAYER_2
    assert colony.current_occupant == PlayerId.PLAYER_1


def test_cannot_recruit_units_from_annexed_colony(base_state: GameState):
    colony = Colony(colony_id="COL_T2", node_id="T2", original_owner=PlayerId.PLAYER_2, current_occupant=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony
    base_state.phase = TurnPhase.DEVELOPMENT
    base_state.current_player = PlayerId.PLAYER_1

    # Give P1 enough resources to buy musketeer
    base_state.players[PlayerId.PLAYER_1].add_resource(ResourceType.WHEAT, 5)
    base_state.players[PlayerId.PLAYER_1].add_resource(ResourceType.SHEEP, 5)

    # Attempt recruit from annexed colony -> rejected
    action = RecruitUnitAction(player_id=PlayerId.PLAYER_1, unit_type=UnitType.MUSKETEER, target_node_id="T2")
    with pytest.raises(RuleViolationError, match="Cannot recruit units from an annexed colony"):
        PincerEngine.apply_action(base_state, action)


def test_build_fort_turn_after_annexing(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    base_state.current_player = PlayerId.PLAYER_1
    base_state.turn_number = 1

    colony = Colony(
        colony_id="COL_T2",
        node_id="T2",
        original_owner=PlayerId.PLAYER_2,
        current_occupant=PlayerId.PLAYER_1,
        annexed_turn=1,  # Annexed on turn 1
    )
    base_state.colonies[colony.colony_id] = colony

    # Give P1 fort resources
    base_state.players[PlayerId.PLAYER_1].add_resource(ResourceType.ORE, 5)
    base_state.players[PlayerId.PLAYER_1].add_resource(ResourceType.WOOD, 5)

    # Building fort on same turn (turn 1) -> rejected
    with pytest.raises(RuleViolationError, match="turn after annexing"):
        PincerEngine.apply_action(base_state, BuildFortAction(player_id=PlayerId.PLAYER_1, colony_id="COL_T2"))

    # On turn 2 -> succeeds
    base_state.turn_number = 2
    PincerEngine.apply_action(base_state, BuildFortAction(player_id=PlayerId.PLAYER_1, colony_id="COL_T2"))
    assert colony.has_fort
    assert colony.fort_owner == PlayerId.PLAYER_1


def test_colony_reversion_and_fort_destruction_when_vacated(base_state: GameState):
    colony = Colony(
        colony_id="COL_T2",
        node_id="T2",
        original_owner=PlayerId.PLAYER_2,
        current_occupant=PlayerId.PLAYER_1,
        has_fort=True,
        fort_owner=PlayerId.PLAYER_1,
    )
    # Add a second colony at T4 owned by P1, so each controls 1 colony (50% < 75%)
    colony_p1 = Colony(
        colony_id="COL_T4",
        node_id="T4",
        original_owner=PlayerId.PLAYER_1,
    )
    base_state.colonies[colony.colony_id] = colony
    base_state.colonies[colony_p1.colony_id] = colony_p1
    base_state.current_player = PlayerId.PLAYER_1
    base_state.phase = TurnPhase.MOBILIZATION

    # P1 unit on T2 moves away to T3
    p1_unit = Unit(unit_id="U1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T2", built_turn=0)
    base_state.units["U1"] = p1_unit

    PincerEngine.apply_action(base_state, MoveUnitAction(player_id=PlayerId.PLAYER_1, unit_id="U1", target_node_id="T3"))
    # Advance to Development
    PincerEngine.apply_action(base_state, EndPhaseAction(player_id=PlayerId.PLAYER_1))
    # End P1 turn -> advances to P2
    PincerEngine.apply_action(base_state, EndPhaseAction(player_id=PlayerId.PLAYER_1))

    # Now it is P2's turn. T2 is vacant of enemy units. Colony should revert, fort should be destroyed!
    assert base_state.current_player == PlayerId.PLAYER_2
    assert not colony.is_annexed
    assert colony.controller == PlayerId.PLAYER_2
    assert not colony.has_fort
    assert colony.fort_owner is None
