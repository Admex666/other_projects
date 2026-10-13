import pytest
from pincer.actions.harvest import HarvestRollAction
from pincer.core.enums import PlayerId, TurnPhase, ResourceType, UnitType
from pincer.engine.engine import PincerEngine
from pincer.entities.colony import Colony
from pincer.entities.unit import Unit
from pincer.state.state import GameState


def test_harvest_awards_resource_to_colony_controller(base_state: GameState):
    # Colony at T1. Neighbors of T1: E1 (val 1, WOOD), T2 (val 2, WHEAT), M1 (None)
    colony = Colony(colony_id="COL_T1", node_id="T1", original_owner=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony
    base_state.phase = TurnPhase.HARVEST

    assert base_state.players[PlayerId.PLAYER_1].resources[ResourceType.WHEAT] == 0

    # Roll 2: matches T2 (WHEAT)
    action = HarvestRollAction(player_id=PlayerId.PLAYER_1, override_roll=2)
    PincerEngine.apply_action(base_state, action)

    assert base_state.players[PlayerId.PLAYER_1].resources[ResourceType.WHEAT] == 1
    # Automatically transitioned to Mobilization
    assert base_state.phase == TurnPhase.MOBILIZATION


def test_harvest_suppressed_if_enemy_occupies_adjacent_producing_tile(base_state: GameState):
    # Colony at T1 (owned by P1). Neighbor T2 produces WHEAT on roll 2.
    colony = Colony(colony_id="COL_T1", node_id="T1", original_owner=PlayerId.PLAYER_1)
    base_state.colonies[colony.colony_id] = colony

    # P2 unit stationed on T2
    enemy_unit = Unit(unit_id="E_T2", unit_type=UnitType.MUSKETEER, player_id=PlayerId.PLAYER_2, node_id="T2", built_turn=0)
    base_state.units[enemy_unit.unit_id] = enemy_unit

    base_state.phase = TurnPhase.HARVEST
    action = HarvestRollAction(player_id=PlayerId.PLAYER_1, override_roll=2)
    PincerEngine.apply_action(base_state, action)

    # Blocked by enemy occupying T2! P1 receives 0 WHEAT
    assert base_state.players[PlayerId.PLAYER_1].resources[ResourceType.WHEAT] == 0


def test_annexed_colony_harvest_goes_to_occupier(base_state: GameState):
    # Colony originally owned by P2, but occupied/annexed by P1
    colony = Colony(
        colony_id="COL_T1",
        node_id="T1",
        original_owner=PlayerId.PLAYER_2,
        current_occupant=PlayerId.PLAYER_1,
    )
    base_state.colonies[colony.colony_id] = colony
    base_state.phase = TurnPhase.HARVEST

    # Roll 2: matches T2 (WHEAT)
    action = HarvestRollAction(player_id=PlayerId.PLAYER_1, override_roll=2)
    PincerEngine.apply_action(base_state, action)

    # Occupier P1 receives harvest, original owner P2 does not
    assert base_state.players[PlayerId.PLAYER_1].resources[ResourceType.WHEAT] == 1
    assert base_state.players[PlayerId.PLAYER_2].resources[ResourceType.WHEAT] == 0
