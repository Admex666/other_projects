import pytest
from pincer.actions.development import (
    TradeWithBankAction,
    BuildColonyAction,
    BuildPortAction,
    BuildFortAction,
    BuildRoadAction,
    BuildBridgeAction,
    RecruitUnitAction,
)
from pincer.core.enums import PlayerId, TurnPhase, ResourceType, UnitType, InfrastructureType
from pincer.core.errors import IllegalPlacementError, ResourceDeficitError, RuleViolationError
from pincer.engine.engine import PincerEngine
from pincer.entities.colony import Colony
from pincer.entities.infrastructure import Port
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def test_bank_trade_base_rate(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    p1 = base_state.players[PlayerId.PLAYER_1]
    p1.add_resource(ResourceType.WOOD, 5)

    assert base_state.calculate_exchange_rate(PlayerId.PLAYER_1) == 5

    action = TradeWithBankAction(player_id=PlayerId.PLAYER_1, offered_resource=ResourceType.WOOD, requested_resource=ResourceType.GOLD)
    PincerEngine.apply_action(base_state, action)

    assert p1.resources[ResourceType.WOOD] == 0
    assert p1.resources[ResourceType.GOLD] == 1


def test_bank_trade_port_discount_and_enemy_naval_block(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    # Add friendly colony at T2 and port at W1
    colony = Colony(colony_id="COL_T2", node_id="T2", original_owner=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony
    port = Port(port_id="PORT_W1", node_id="W1", owner_id=PlayerId.PLAYER_1, colony_id="COL_T2")
    base_state.ports[port.port_id] = port

    # Port reduces rate by 1 (5 -> 4)
    assert base_state.calculate_exchange_rate(PlayerId.PLAYER_1) == 4

    # Enemy naval unit occupies port tile W1
    enemy_frigate = Unit(unit_id="F_P2", unit_type=UnitType.FRIGATE, player_id=PlayerId.PLAYER_2, node_id="W1", built_turn=0)
    base_state.units[enemy_frigate.unit_id] = enemy_frigate

    # Bonus is blocked while occupied by enemy naval unit!
    assert base_state.calculate_exchange_rate(PlayerId.PLAYER_1) == 5


def test_build_colony_validation(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    p1 = base_state.players[PlayerId.PLAYER_1]

    # Give resources for Colony
    for res in (ResourceType.WOOD, ResourceType.WHEAT, ResourceType.ORE, ResourceType.SHEEP):
        p1.add_resource(res, 2)

    # Friendly unit on T1
    unit = Unit(unit_id="U1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T1", built_turn=0)
    base_state.units["U1"] = unit

    # Build colony on T1 succeeds
    colony = PincerEngine.apply_action(base_state, BuildColonyAction(player_id=PlayerId.PLAYER_1, node_id="T1"))
    assert colony.get_colony_at("T1") is not None

    # Edge tile E1 rejected
    e_unit = Unit(unit_id="U_E1", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="E1", built_turn=0)
    base_state.units["U_E1"] = e_unit
    with pytest.raises(IllegalPlacementError, match="edge tile"):
        PincerEngine.apply_action(base_state, BuildColonyAction(player_id=PlayerId.PLAYER_1, node_id="E1"))

    # Tile T2 is only 1 tile away from T1 -> rejected
    t2_unit = Unit(unit_id="U_T2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_1, node_id="T2", built_turn=0)
    base_state.units["U_T2"] = t2_unit
    with pytest.raises(IllegalPlacementError, match="minimum required"):
        PincerEngine.apply_action(base_state, BuildColonyAction(player_id=PlayerId.PLAYER_1, node_id="T2"))


def test_build_port_validation(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    p1 = base_state.players[PlayerId.PLAYER_1]
    p1.add_resource(ResourceType.WOOD, 5)
    p1.add_resource(ResourceType.ORE, 5)

    colony = Colony(colony_id="COL_T2", node_id="T2", original_owner=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony

    # W1 is water adjacent to T2 -> succeeds
    action = BuildPortAction(player_id=PlayerId.PLAYER_1, node_id="W1", adjacent_colony_id="COL_T2")
    PincerEngine.apply_action(base_state, action)
    assert base_state.get_port_at("W1") is not None

    # Trying to build port on land tile T3 -> rejected
    with pytest.raises(IllegalPlacementError, match="water tile"):
        PincerEngine.apply_action(base_state, BuildPortAction(player_id=PlayerId.PLAYER_1, node_id="T3", adjacent_colony_id="COL_T2"))


def test_recruit_musketeer_and_activation_delay(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    base_state.turn_number = 1
    p1 = base_state.players[PlayerId.PLAYER_1]
    p1.add_resource(ResourceType.WHEAT, 2)
    p1.add_resource(ResourceType.SHEEP, 2)

    colony = Colony(colony_id="COL_T1", node_id="T1", original_owner=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony

    # Recruit Musketeer in empty colony T1
    action = RecruitUnitAction(player_id=PlayerId.PLAYER_1, unit_type=UnitType.MUSKETEER, target_node_id="T1")
    PincerEngine.apply_action(base_state, action)

    recruited_unit = base_state.get_unit_at("T1")
    assert recruited_unit is not None
    assert recruited_unit.built_turn == 1
    # Cannot act in turn 1!
    assert not recruited_unit.can_act_on_turn(1)
    # Can act in turn 2!
    assert recruited_unit.can_act_on_turn(2)


def test_recruit_cannon_requires_fort(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    p1 = base_state.players[PlayerId.PLAYER_1]
    p1.add_resource(ResourceType.ORE, 5)
    p1.add_resource(ResourceType.WOOD, 5)

    colony = Colony(colony_id="COL_T1", node_id="T1", original_owner=PlayerId.PLAYER_1, has_fort=False)
    base_state.colonies[colony.colony_id] = colony

    action = RecruitUnitAction(player_id=PlayerId.PLAYER_1, unit_type=UnitType.CANNON, target_node_id="T1")
    with pytest.raises(RuleViolationError, match="colony with a fort"):
        PincerEngine.apply_action(base_state, action)

    # Now add fort
    colony.has_fort = True
    colony.fort_owner = PlayerId.PLAYER_1
    PincerEngine.apply_action(base_state, action)
    assert base_state.get_unit_at("T1").unit_type == UnitType.CANNON


def test_recruit_frigate_requires_port(base_state: GameState):
    base_state.phase = TurnPhase.DEVELOPMENT
    p1 = base_state.players[PlayerId.PLAYER_1]
    p1.add_resource(ResourceType.WOOD, 5)
    p1.add_resource(ResourceType.ORE, 5)
    p1.add_resource(ResourceType.SHEEP, 5)

    # No port on W1 -> rejected
    action = RecruitUnitAction(player_id=PlayerId.PLAYER_1, unit_type=UnitType.FRIGATE, target_node_id="W1")
    with pytest.raises(IllegalPlacementError, match="friendly port"):
        PincerEngine.apply_action(base_state, action)

    # Add friendly port on W1
    port = Port(port_id="PORT_W1", node_id="W1", owner_id=PlayerId.PLAYER_1, colony_id="COL_T2")
    base_state.ports[port.port_id] = port
    PincerEngine.apply_action(base_state, action)
    assert base_state.get_unit_at("W1").unit_type == UnitType.FRIGATE
