"""Development phase actions: construction, trading, recruitment."""
from typing import Dict, List, Optional, Set
from pincer.core.enums import (
    InfrastructureType,
    PlayerId,
    ResourceType,
    UnitType,
)
from pincer.core.errors import (
    IllegalPlacementError,
    ResourceDeficitError,
    RuleViolationError,
)
from pincer.entities.colony import Colony
from pincer.entities.infrastructure import Port, Road, Bridge
from pincer.entities.unit import Unit
from pincer.state.state import GameState


class DevelopmentResolver:
    """Handles trading, construction validation, and unit recruitment."""

    @staticmethod
    def execute_trade(
        state: GameState,
        player_id: PlayerId,
        offered: ResourceType,
        requested: ResourceType
    ) -> None:
        """Executes a bank trade at player's current exchange rate."""
        rate = state.calculate_exchange_rate(player_id)
        player = state.players[player_id]

        if player.resources.get(offered, 0) < rate:
            raise ResourceDeficitError(
                f"Player {player_id} has {player.resources.get(offered, 0)} {offered.value}, "
                f"needs {rate} to trade at current rate."
            )

        player.remove_resource(offered, rate)
        player.add_resource(requested, 1)

    @staticmethod
    def validate_and_build_colony(state: GameState, player_id: PlayerId, node_id: str) -> Colony:
        """Validates and constructs a new Colony.
        
        Rules:
        - Must be built at least 3 tiles apart from any existing colony.
        - Must be built on a tile occupied by a friendly unit.
        - May not be built on edge tiles of the board.
        - Costs resources defined in config.
        """
        player = state.players[player_id]
        cost = state.config.construction_costs[InfrastructureType.COLONY]
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to build Colony. Required: {cost}")

        if node_id not in state.board.nodes:
            raise IllegalPlacementError(f"Node {node_id} does not exist.")

        node = state.board.get_node(node_id)
        if node.is_edge:
            raise IllegalPlacementError(f"Colony cannot be built on edge tile {node_id}.")

        if not node.is_land():
            raise IllegalPlacementError(f"Colony must be built on land, not {node.terrain}.")

        if state.get_colony_at(node_id) is not None:
            raise IllegalPlacementError(f"Colony already exists on tile {node_id}.")

        occupying_unit = state.get_unit_at(node_id)
        if occupying_unit is None or occupying_unit.player_id != player_id:
            raise IllegalPlacementError(f"Colony must be built on a tile occupied by a friendly unit.")

        # Check distance constraint to all existing colonies
        existing_nodes = [c.node_id for c in state.colonies.values()]
        for ex_node in existing_nodes:
            dist = state.board.graph_distance(node_id, ex_node)
            if dist is not None and dist < state.config.min_colony_distance:
                raise IllegalPlacementError(
                    f"Colony at {node_id} is only {dist} tiles away from {ex_node} "
                    f"(minimum required: {state.config.min_colony_distance})."
                )

        # Deduct resources & build
        player.deduct_resources(cost)
        colony_id = f"COLONY_{node_id}_{player_id.value}"
        colony = Colony(colony_id=colony_id, node_id=node_id, original_owner=player_id)
        state.colonies[colony_id] = colony
        return colony

    @staticmethod
    def validate_and_build_port(
        state: GameState,
        player_id: PlayerId,
        node_id: str,
        adjacent_colony_id: str
    ) -> Port:
        """Validates and constructs a Port.
        
        Rules:
        - Must be built on a water tile adjacent to an existing colony.
        """
        player = state.players[player_id]
        cost = (
            state.config.construction_costs.get(InfrastructureType.PORT)
            or state.config.construction_costs.get(InfrastructureType.HARBOR, {})
        )
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to build Port/Harbor. Required: {cost}")

        colony = state.colonies.get(adjacent_colony_id)
        if colony is None or colony.controller != player_id:
            raise IllegalPlacementError(f"Must build port adjacent to a friendly colony.")

        if node_id not in state.board.nodes:
            raise IllegalPlacementError(f"Node {node_id} does not exist.")

        node = state.board.get_node(node_id)
        if not node.is_water():
            raise IllegalPlacementError(f"Port must be built on a water tile.")

        if node_id not in state.board.get_neighbors(colony.node_id):
            raise IllegalPlacementError(f"Water tile {node_id} is not adjacent to colony {colony.colony_id}.")

        if state.get_port_at(node_id) is not None:
            raise IllegalPlacementError(f"Port already exists on tile {node_id}.")

        player.deduct_resources(cost)
        port_id = f"PORT_{node_id}"
        port = Port(port_id=port_id, node_id=node_id, owner_id=player_id, colony_id=adjacent_colony_id)
        state.ports[port_id] = port
        return port

    @staticmethod
    def validate_and_build_fort(state: GameState, player_id: PlayerId, colony_id: str) -> None:
        """Validates and constructs a Fort on a colony.
        
        Rules:
        - Must be built around a friendly colony.
        - If annexed: "You may also build a fort turn after annexing (in your own color)."
        """
        player = state.players[player_id]
        cost = (
            state.config.construction_costs.get(InfrastructureType.FORT)
            or state.config.construction_costs.get(InfrastructureType.WALL, {})
        )
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to build Fort/Wall. Required: {cost}")

        colony = state.colonies.get(colony_id)
        if colony is None or colony.controller != player_id:
            raise IllegalPlacementError(f"Colony {colony_id} is not controlled by player {player_id}.")

        if colony.has_fort:
            raise IllegalPlacementError(f"Colony {colony_id} already has a fort.")

        if colony.is_annexed:
            if colony.annexed_turn is not None and state.turn_number <= colony.annexed_turn:
                raise RuleViolationError("Can only build a fort a turn after annexing.")

        player.deduct_resources(cost)
        colony.has_fort = True
        colony.fort_owner = player_id
        colony.fort_built_turn = state.turn_number

    @staticmethod
    def validate_and_build_road(state: GameState, player_id: PlayerId, edge_id: str) -> Road:
        """Validates and builds a Road on an edge."""
        player = state.players[player_id]
        cost = state.config.construction_costs[InfrastructureType.ROAD]
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to build Road. Required: {cost}")

        if edge_id not in state.board.edges:
            raise IllegalPlacementError(f"Edge {edge_id} does not exist.")

        edge = state.board.edges[edge_id]
        if edge.road_owner is not None or edge.bridge_owner is not None:
            raise IllegalPlacementError(f"Edge {edge_id} already has a road or bridge.")

        # Must be built upon an existing colony or road
        connected = DevelopmentResolver._is_edge_connected_to_network(state, player_id, edge)
        if not connected:
            raise IllegalPlacementError(f"Road must connect to an existing friendly colony or road.")

        player.deduct_resources(cost)
        edge.road_owner = player_id
        road = Road(edge_id=edge_id, owner_id=player_id)
        state.roads[edge_id] = road
        return road

    @staticmethod
    def validate_and_build_bridge(state: GameState, player_id: PlayerId, edge_id: str) -> Bridge:
        """Validates and builds a Bridge on a water crossing edge touching land on either side."""
        player = state.players[player_id]
        cost = state.config.construction_costs[InfrastructureType.BRIDGE]
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to build Bridge. Required: {cost}")

        if edge_id not in state.board.edges:
            raise IllegalPlacementError(f"Edge {edge_id} does not exist.")

        edge = state.board.edges[edge_id]
        if edge.bridge_owner is not None or edge.road_owner is not None:
            raise IllegalPlacementError(f"Edge {edge_id} already has infrastructure.")

        # Must cross water and touch land on either side
        node_a = state.board.get_node(edge.node_a)
        node_b = state.board.get_node(edge.node_b)
        has_land = node_a.is_land() or node_b.is_land()
        has_water = node_a.is_water() or node_b.is_water() or edge.is_water_crossing

        if not (has_land and has_water):
            raise IllegalPlacementError(f"Bridge must be on a water crossing touching land.")

        # Must connect to player network
        connected = DevelopmentResolver._is_edge_connected_to_network(state, player_id, edge)
        if not connected:
            raise IllegalPlacementError(f"Bridge must connect to existing friendly colony or road.")

        player.deduct_resources(cost)
        edge.bridge_owner = player_id
        bridge = Bridge(edge_id=edge_id, owner_id=player_id)
        state.bridges[edge_id] = bridge
        return bridge

    @staticmethod
    def _is_edge_connected_to_network(state: GameState, player_id: PlayerId, edge) -> bool:
        """Checks if edge touches a friendly colony or friendly road/bridge."""
        nodes = (edge.node_a, edge.node_b)
        for nid in nodes:
            col = state.get_colony_at(nid)
            if col and col.controller == player_id:
                return True
            # Check adjacent edges for friendly road
            for other_eid in state.board.edges:
                other_edge = state.board.edges[other_eid]
                if other_edge.edge_id != edge.edge_id and (other_edge.node_a == nid or other_edge.node_b == nid):
                    if other_edge.road_owner == player_id or other_edge.bridge_owner == player_id:
                        return True
        return False

    @staticmethod
    def validate_and_recruit_unit(
        state: GameState,
        player_id: PlayerId,
        unit_type: UnitType,
        target_node_id: str
    ) -> Unit:
        """Validates recruitment prerequisites and spawns a new unit.
        
        Prerequisites:
        - Musketeer: placed in an empty, friendly colony.
        - Cavalry: placed in a colony connected to another by roads (bridges also allow cavalry).
        - Cannon: placed in a colony with a fort.
        - Frigate: placed in an empty, friendly, unoccupied port.
        - In all cases: cannot recruit land/naval units from an annexed colony!
        - Newly built units have built_turn == state.turn_number (cannot act until next turn).
        """
        player = state.players[player_id]
        cost = state.config.unit_costs[unit_type]
        if not player.has_resources(cost):
            raise ResourceDeficitError(f"Insufficient resources to recruit {unit_type.value}. Required: {cost}")

        if unit_type in (UnitType.MUSKETEER, UnitType.CAVALRY, UnitType.CANNON):
            colony = state.get_colony_at(target_node_id)
            if colony is None:
                raise IllegalPlacementError(f"Land units must be placed in a colony. Tile {target_node_id} has none.")
            if colony.controller != player_id:
                raise IllegalPlacementError(f"Colony {colony.colony_id} is not controlled by player {player_id}.")
            if colony.is_annexed:
                raise RuleViolationError("Cannot recruit units from an annexed colony.")

            # Must be empty
            if state.get_unit_at(target_node_id) is not None:
                raise IllegalPlacementError(f"Colony tile {target_node_id} is already occupied by a unit.")

            if unit_type == UnitType.CAVALRY:
                # Must be connected to another colony by roads or bridges
                player_colonies = [c for c in state.colonies.values() if c.controller == player_id and not c.is_annexed]
                if state._count_road_connected_colonies(player_id, player_colonies) < 2:
                    raise RuleViolationError("Cavalry requires placement in a colony connected to another by roads.")

            elif unit_type == UnitType.CANNON:
                # Must have a fort
                if not colony.has_fort:
                    raise RuleViolationError("Cannons must be placed in a colony with a fort.")

        elif unit_type == UnitType.FRIGATE:
            port = state.get_port_at(target_node_id)
            if port is None or port.owner_id != player_id:
                raise IllegalPlacementError(f"Frigates must be placed in a friendly port. No port found at {target_node_id}.")
            if state.get_unit_at(target_node_id) is not None:
                raise IllegalPlacementError(f"Port tile {target_node_id} is already occupied by a unit.")

        player.deduct_resources(cost)
        unit_id = f"UNIT_{unit_type.value.upper()}_{len(state.units) + 1}_{player_id.value}"
        new_unit = Unit(
            unit_id=unit_id,
            unit_type=unit_type,
            player_id=player_id,
            node_id=target_node_id,
            built_turn=state.turn_number,
        )
        state.units[unit_id] = new_unit
        return new_unit
