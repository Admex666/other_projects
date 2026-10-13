"""Combat resolution, counter-move reactions, and fort defense."""
from typing import Optional, List
from pincer.core.enums import UnitType, PlayerId, TerrainType
from pincer.core.errors import RuleViolationError, IllegalMovementError
from pincer.entities.unit import Unit
from pincer.state.counter_move import CounterMoveState
from pincer.state.state import GameState
from pincer.engine.movement import MovementValidator


class CombatResolver:
    """Handles attacks, cannon retreat, fort defense checks, and counter-moves."""

    @staticmethod
    def validate_attack(
        state: GameState,
        attacker: Unit,
        target_node_id: str,
        cannon_return: bool = False
    ) -> None:
        """Validates that attacker can attack target_node_id."""
        if not attacker.can_act_on_turn(state.turn_number):
            raise RuleViolationError(f"Unit {attacker.unit_id} was recruited this turn and cannot attack.")

        if attacker.unit_id in state.units_attacked_this_turn or attacker.unit_id in state.units_moved_this_turn:
            raise RuleViolationError(f"Unit {attacker.unit_id} has already moved or attacked this turn.")

        defender_unit = state.get_unit_at(target_node_id)
        if defender_unit is None:
            raise RuleViolationError(f"No unit found at target tile {target_node_id} to attack.")

        if defender_unit.player_id == attacker.player_id:
            raise RuleViolationError("Cannot attack a friendly unit.")

        target_node = state.board.get_node(target_node_id)

        # Fort siege validation
        colony = state.get_colony_at(target_node_id)
        if colony and colony.has_fort and colony.fort_owner == defender_unit.player_id:
            # Must satisfy fort siege condition
            CombatResolver._validate_fort_siege_condition(state, attacker.player_id, colony.colony_id)

        # Check unit attack reach & constraints
        if attacker.unit_type == UnitType.MUSKETEER:
            if target_node_id not in state.board.get_neighbors(attacker.node_id):
                raise IllegalMovementError(f"Musketeer cannot attack non-adjacent tile {target_node_id}.")
            if target_node.is_mountain():
                raise IllegalMovementError("Musketeer cannot attack into mountain.")
            if target_node.is_water():
                raise IllegalMovementError("Musketeer cannot attack naval units in water.")

        elif attacker.unit_type == UnitType.CAVALRY:
            dist = state.board.graph_distance(attacker.node_id, target_node_id)
            if state.config.cavalry_requires_exact_2_tiles:
                if dist != 2:
                    raise IllegalMovementError(f"Cavalry must attack exactly 2 tiles away. Target distance is {dist}.")
            else:
                if dist not in (1, 2):
                    raise IllegalMovementError(f"Cavalry cannot attack target at distance {dist}.")
            if target_node.is_mountain() or target_node.is_water():
                raise IllegalMovementError(f"Cavalry cannot attack into {target_node.terrain}.")

        elif attacker.unit_type == UnitType.CANNON:
            if target_node_id not in state.board.get_neighbors(attacker.node_id):
                raise IllegalMovementError(f"Cannon cannot attack non-adjacent tile {target_node_id}.")
            # If attacking naval unit, MUST return to original tile
            if defender_unit.is_naval_unit() and not cannon_return:
                raise RuleViolationError("Cannon MUST return to original tile after attacking naval units.")

        elif attacker.unit_type == UnitType.FRIGATE:
            dist = state.board.graph_distance(attacker.node_id, target_node_id)
            if dist not in (1, 2):
                raise IllegalMovementError(f"Frigate attack distance must be 1 or 2. Found {dist}.")
            # Frigate attacks naval or coastal units

    @staticmethod
    def _validate_fort_siege_condition(state: GameState, attacker_player_id: PlayerId, colony_id: str) -> None:
        """Fort Rule: forces enemies to have either a cannon or frigate,
        plus additional land unit adjacent to the colony for a whole turn before attacking.
        """
        siege_turns = state.consecutive_siege_turns.get(colony_id, 0)
        if siege_turns < 1:
            raise RuleViolationError(
                f"Fortified colony {colony_id} cannot be attacked until besieged by a cannon/frigate "
                f"and an additional land unit for a full turn."
            )

    @staticmethod
    def execute_attack(
        state: GameState,
        attacker: Unit,
        target_node_id: str,
        cannon_return: bool = False
    ) -> None:
        """Executes an attack:
        1. Destroys fort if present.
        2. Removes defending unit (and any cargo if frigate).
        3. Moves attacker to target node (unless cannon returns).
        4. Updates colony annexation if applicable.
        5. Sets up CounterMoveState for defending player.
        """
        origin_node_id = attacker.node_id
        defender_unit = state.get_unit_at(target_node_id)
        assert defender_unit is not None
        defender_player_id = defender_unit.player_id

        # Destroy fort if present
        colony = state.get_colony_at(target_node_id)
        if colony and colony.has_fort and colony.fort_owner == defender_player_id:
            colony.has_fort = False
            colony.fort_owner = None
            colony.fort_built_turn = None

        # Defending unit is removed
        del state.units[defender_unit.unit_id]

        # Handle attacker movement
        if attacker.unit_type == UnitType.CANNON and (cannon_return or defender_unit.is_naval_unit()):
            # Cannon stays at / returns to origin node
            attacker.node_id = origin_node_id
        else:
            attacker.node_id = target_node_id

        # Update colony occupation if colony exists on target_node_id and attacker occupies it
        if colony and attacker.node_id == target_node_id:
            colony.occupy(attacker.player_id, state.turn_number)

        # Track attacker usage
        state.units_attacked_this_turn.add(attacker.unit_id)

        # Set up counter-move reaction window for defender
        existing_used = state.counter_move_state.used_counter_unit_ids if state.counter_move_state else set()
        state.counter_move_state = CounterMoveState(
            attacker_unit_id=attacker.unit_id,
            defender_player_id=defender_player_id,
            attacked_node_id=target_node_id,
            used_counter_unit_ids=existing_used,
            is_active=True,
        )

    @staticmethod
    def validate_counter_move(
        state: GameState,
        unit: Unit,
        target_node_id: str,
        is_attack: bool = False
    ) -> None:
        """Validates counter-move reaction."""
        if state.counter_move_state is None or not state.counter_move_state.is_active:
            raise RuleViolationError("No counter-move reaction is currently active.")

        if unit.player_id != state.counter_move_state.defender_player_id:
            raise RuleViolationError("Only the attacked player can execute a counter-move.")

        # Check unit reuse constraint:
        # "Opponent must use a separate piece for each counter attack before reusing the same one, until the offensive player's turn ends."
        defender_units = [u for u in state.units.values() if u.player_id == unit.player_id]
        used_units = state.counter_move_state.used_counter_unit_ids

        # If not all units have been used, this unit must not have been used yet
        if len(used_units) < len(defender_units) and unit.unit_id in used_units:
            raise RuleViolationError(
                f"Unit {unit.unit_id} has already performed a counter-move this turn. "
                f"Must use a separate unit before reusing."
            )

        if is_attack:
            CombatResolver.validate_attack(state, unit, target_node_id)
        else:
            MovementValidator.validate_move(state, unit, target_node_id)

    @staticmethod
    def execute_counter_move(
        state: GameState,
        unit: Unit,
        target_node_id: str,
        is_attack: bool = False
    ) -> None:
        """Executes counter move/attack and concludes the counter-move window."""
        assert state.counter_move_state is not None

        if is_attack:
            # Resolve attack without triggering a secondary counter-move
            CombatResolver._execute_counter_attack(state, unit, target_node_id)
        else:
            unit.node_id = target_node_id
            col = state.get_colony_at(target_node_id)
            if col:
                col.occupy(unit.player_id, state.turn_number)

        state.counter_move_state.record_counter_move(unit.unit_id)

    @staticmethod
    def _execute_counter_attack(state: GameState, attacker: Unit, target_node_id: str) -> None:
        """Executes counter-attack by removing target piece."""
        defender_unit = state.get_unit_at(target_node_id)
        assert defender_unit is not None

        del state.units[defender_unit.unit_id]
        attacker.node_id = target_node_id

        col = state.get_colony_at(target_node_id)
        if col:
            col.occupy(attacker.player_id, state.turn_number)
