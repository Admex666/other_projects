"""Movement validation and pathing for all unit types."""
from typing import List, Optional
from pincer.board.graph import BoardGraph
from pincer.core.enums import TerrainType, UnitType, PlayerId
from pincer.core.errors import IllegalMovementError
from pincer.entities.unit import Unit
from pincer.state.state import GameState


class MovementValidator:
    """Validates movement rules for Musketeers, Cavalry, Cannons, and Frigates."""

    @staticmethod
    def validate_move(state: GameState, unit: Unit, target_node_id: str, path: Optional[List[str]] = None) -> None:
        """Validates whether a unit can move to target_node_id."""
        if not unit.can_act_on_turn(state.turn_number):
            raise IllegalMovementError(f"Unit {unit.unit_id} was recruited this turn and cannot act until next turn.")

        if unit.unit_id in state.units_moved_this_turn or unit.unit_id in state.units_attacked_this_turn:
            raise IllegalMovementError(f"Unit {unit.unit_id} has already moved or attacked this turn.")

        if target_node_id not in state.board.nodes:
            raise IllegalMovementError(f"Target node {target_node_id} does not exist on the board.")

        target_node = state.board.get_node(target_node_id)

        # Destination must be empty for a non-attack move
        existing_unit = state.get_unit_at(target_node_id)
        if existing_unit is not None:
            raise IllegalMovementError(f"Destination {target_node_id} is already occupied by unit {existing_unit.unit_id}.")

        # Mountain restriction: Land units may not enter mountain tiles
        if unit.is_land_unit() and target_node.is_mountain():
            raise IllegalMovementError(f"Land unit {unit.unit_id} cannot enter mountain tile {target_node_id}.")

        # Water restriction: Land units cannot enter water tiles without transport
        if unit.is_land_unit() and target_node.is_water():
            # Check if there is a bridge on the edge, or land unit cannot step into water
            edge = state.board.get_edge(unit.node_id, target_node_id)
            if not (edge and edge.bridge_owner is not None):
                raise IllegalMovementError(f"Land unit {unit.unit_id} cannot enter water tile {target_node_id} without a bridge or transport.")

        # Naval restriction: Frigate cannot enter land or mountain
        if unit.is_naval_unit() and not target_node.is_water():
            raise IllegalMovementError(f"Naval unit {unit.unit_id} cannot enter non-water tile {target_node_id}.")

        # Unit-specific movement range & path rules
        if unit.unit_type == UnitType.MUSKETEER:
            MovementValidator._validate_musketeer_move(state, unit, target_node_id)
        elif unit.unit_type == UnitType.CAVALRY:
            MovementValidator._validate_cavalry_move(state, unit, target_node_id, path)
        elif unit.unit_type == UnitType.CANNON:
            MovementValidator._validate_cannon_move(state, unit, target_node_id)
        elif unit.unit_type == UnitType.FRIGATE:
            MovementValidator._validate_frigate_move(state, unit, target_node_id, path)

    @staticmethod
    def _validate_musketeer_move(state: GameState, unit: Unit, target_node_id: str) -> None:
        neighbors = state.board.get_neighbors(unit.node_id)
        if target_node_id not in neighbors:
            raise IllegalMovementError(f"Musketeer can only move 1 tile. {target_node_id} is not adjacent to {unit.node_id}.")

    @staticmethod
    def _validate_cannon_move(state: GameState, unit: Unit, target_node_id: str) -> None:
        neighbors = state.board.get_neighbors(unit.node_id)
        if target_node_id not in neighbors:
            raise IllegalMovementError(f"Cannon can only move 1 tile. {target_node_id} is not adjacent to {unit.node_id}.")

    @staticmethod
    def _validate_cavalry_move(
        state: GameState,
        unit: Unit,
        target_node_id: str,
        path: Optional[List[str]] = None
    ) -> None:
        """Cavalry moves/attacks only by 2 tiles away. Cannot move through enemy occupied or mountain tiles."""
        dist = state.board.graph_distance(unit.node_id, target_node_id)
        if state.config.cavalry_requires_exact_2_tiles:
            if dist != 2:
                raise IllegalMovementError(f"Cavalry must move exactly 2 tiles away. Target distance is {dist}.")
        else:
            if dist not in (1, 2):
                raise IllegalMovementError(f"Cavalry cannot reach tile at distance {dist}.")

        if dist == 2:
            # Must have at least one valid intermediate step
            neighbors = state.board.get_neighbors(unit.node_id)
            target_neighbors = state.board.get_neighbors(target_node_id)
            common_intermediates = set(neighbors).intersection(target_neighbors)

            valid_intermediate_found = False
            for inter_id in common_intermediates:
                inter_node = state.board.get_node(inter_id)
                if inter_node.is_mountain():
                    continue
                # Cannot cross through water without bridge
                if inter_node.is_water():
                    e1 = state.board.get_edge(unit.node_id, inter_id)
                    e2 = state.board.get_edge(inter_id, target_node_id)
                    if not (e1 and e1.bridge_owner and e2 and e2.bridge_owner):
                        continue
                # Cannot pass through enemy-occupied tile
                inter_unit = state.get_unit_at(inter_id)
                if inter_unit is not None and inter_unit.player_id != unit.player_id:
                    continue
                valid_intermediate_found = True
                break

            if not valid_intermediate_found:
                raise IllegalMovementError(f"Cavalry path to {target_node_id} is blocked by terrain or enemy units.")

    @staticmethod
    def _validate_frigate_move(
        state: GameState,
        unit: Unit,
        target_node_id: str,
        path: Optional[List[str]] = None
    ) -> None:
        """Frigate moves 1 or 2 tiles across water."""
        dist = state.board.graph_distance(unit.node_id, target_node_id)
        if dist not in (1, 2):
            raise IllegalMovementError(f"Frigate move distance must be 1 or 2 tiles. Found: {dist}.")

        if dist == 2:
            # Ensure intermediate tile is water and not blocked by enemy naval unit
            neighbors = state.board.get_neighbors(unit.node_id)
            target_neighbors = state.board.get_neighbors(target_node_id)
            common = set(neighbors).intersection(target_neighbors)
            valid_water_path = False
            for inter_id in common:
                inter_node = state.board.get_node(inter_id)
                if inter_node.is_water():
                    inter_unit = state.get_unit_at(inter_id)
                    if inter_unit is None or inter_unit.player_id == unit.player_id:
                        valid_water_path = True
                        break
            if not valid_water_path:
                raise IllegalMovementError(f"Frigate has no clear water path of distance 2 to {target_node_id}.")
