"""Core game engine orchestrator for Pincer."""
from typing import List, Optional
from pincer.actions.base import Action
from pincer.actions.harvest import HarvestRollAction
from pincer.actions.mobilization import (
    MoveUnitAction,
    AttackAction,
    CounterMoveAction,
    PassCounterMoveAction,
    TransferViaRoadAction,
    EmbarkFrigateAction,
    DisembarkFrigateAction,
    EndPhaseAction,
)
from pincer.actions.development import (
    TradeWithBankAction,
    BuildColonyAction,
    BuildPortAction,
    BuildFortAction,
    BuildRoadAction,
    BuildBridgeAction,
    RecruitUnitAction,
)
from pincer.core.enums import TurnPhase, PlayerId, UnitType, InfrastructureType
from pincer.core.errors import InvalidActionError, PhaseOrderError, RuleViolationError
from pincer.engine.combat import CombatResolver
from pincer.engine.development import DevelopmentResolver
from pincer.engine.harvest import HarvestResolver
from pincer.engine.movement import MovementValidator
from pincer.state.state import GameState
from pincer.victory.domination import VictoryEvaluator


class PincerEngine:
    """The central state transition and rule enforcement engine."""

    @staticmethod
    def validate_action(state: GameState, action: Action) -> None:
        """Validates that an action is strictly legal under the current state.
        
        Raises an exception (InvalidActionError or subclass) if illegal.
        """
        if state.winner is not None:
            raise RuleViolationError(f"Game has already ended. Winner is {state.winner}.")

        # Check counter-move state precedence
        if state.counter_move_state and state.counter_move_state.is_active:
            if not isinstance(action, (CounterMoveAction, PassCounterMoveAction)):
                raise RuleViolationError("Must resolve pending counter-move reaction before other actions.")
            if action.player_id != state.counter_move_state.defender_player_id:
                raise RuleViolationError("Only the defending player may act during counter-move reaction.")
            return

        # Normal phase: active player check
        if action.player_id != state.current_player:
            raise RuleViolationError(f"It is Player {state.current_player}'s turn, not {action.player_id}.")

        # Phase-specific action validation
        if state.phase == TurnPhase.HARVEST:
            if not isinstance(action, HarvestRollAction):
                raise PhaseOrderError("Only HarvestRollAction is allowed during Harvest phase.")

        elif state.phase == TurnPhase.MOBILIZATION:
            if isinstance(action, HarvestRollAction):
                raise PhaseOrderError("Harvest action cannot be performed during Mobilization phase.")
            if isinstance(action, (TradeWithBankAction, BuildColonyAction, BuildPortAction,
                                   BuildFortAction, BuildRoadAction, BuildBridgeAction, RecruitUnitAction)):
                raise PhaseOrderError("Development actions are only allowed during Development phase.")

            if isinstance(action, MoveUnitAction):
                unit = state.units.get(action.unit_id)
                if unit is None:
                    raise InvalidActionError(f"Unit {action.unit_id} does not exist.")
                if unit.player_id != action.player_id:
                    raise RuleViolationError("Cannot move an opponent's unit.")
                MovementValidator.validate_move(state, unit, action.target_node_id, action.path)

            elif isinstance(action, AttackAction):
                unit = state.units.get(action.attacker_unit_id)
                if unit is None:
                    raise InvalidActionError(f"Unit {action.attacker_unit_id} does not exist.")
                if unit.player_id != action.player_id:
                    raise RuleViolationError("Cannot attack with an opponent's unit.")
                CombatResolver.validate_attack(state, unit, action.target_node_id, action.cannon_return)

            elif isinstance(action, TransferViaRoadAction):
                PincerEngine._validate_road_transfer(state, action)

            elif isinstance(action, EndPhaseAction):
                pass  # Legal to conclude Mobilization

        elif state.phase == TurnPhase.DEVELOPMENT:
            if isinstance(action, (MoveUnitAction, AttackAction, TransferViaRoadAction)):
                raise PhaseOrderError("Movement and attacks are not allowed during Development phase.")
            if isinstance(action, HarvestRollAction):
                raise PhaseOrderError("Harvest action cannot be performed during Development phase.")

            if isinstance(action, TradeWithBankAction):
                rate = state.calculate_exchange_rate(action.player_id)
                if state.players[action.player_id].resources.get(action.offered_resource, 0) < rate:
                    raise RuleViolationError("Insufficient resources to trade with bank.")

            elif isinstance(action, EndPhaseAction):
                pass

    @staticmethod
    def apply_action(state: GameState, action: Action) -> GameState:
        """Applies an action to produce the next state.
        
        Validates before mutation; if invalid, state is guaranteed uncorrupted.
        """
        # Validate first
        PincerEngine.validate_action(state, action)

        # Counter-move execution
        if isinstance(action, CounterMoveAction):
            unit = state.units[action.defender_unit_id]
            CombatResolver.execute_counter_move(state, unit, action.target_node_id, action.is_attack)
            return state

        if isinstance(action, PassCounterMoveAction):
            assert state.counter_move_state is not None
            state.counter_move_state.pass_counter_move()
            return state

        # Phase execution
        if isinstance(action, HarvestRollAction):
            HarvestResolver.execute_harvest(state, action.override_roll)
            state.phase = TurnPhase.MOBILIZATION
            return state

        if isinstance(action, MoveUnitAction):
            unit = state.units[action.unit_id]
            unit.node_id = action.target_node_id
            state.units_moved_this_turn.add(unit.unit_id)
            # If unit moved into a friendly or enemy colony tile, check annexation
            col = state.get_colony_at(action.target_node_id)
            if col:
                col.occupy(unit.player_id, state.turn_number)
            return state

        if isinstance(action, AttackAction):
            unit = state.units[action.attacker_unit_id]
            CombatResolver.execute_attack(state, unit, action.target_node_id, action.cannon_return)
            return state

        if isinstance(action, TransferViaRoadAction):
            unit = state.units[action.unit_id]
            unit.node_id = action.target_colony_node_id
            state.units_moved_this_turn.add(unit.unit_id)
            return state

        if isinstance(action, TradeWithBankAction):
            DevelopmentResolver.execute_trade(state, action.player_id, action.offered_resource, action.requested_resource)
            return state

        if isinstance(action, BuildColonyAction):
            DevelopmentResolver.validate_and_build_colony(state, action.player_id, action.node_id)
            return state

        if isinstance(action, BuildPortAction):
            DevelopmentResolver.validate_and_build_port(state, action.player_id, action.node_id, action.adjacent_colony_id)
            return state

        if isinstance(action, BuildFortAction):
            DevelopmentResolver.validate_and_build_fort(state, action.player_id, action.colony_id)
            return state

        if isinstance(action, BuildRoadAction):
            DevelopmentResolver.validate_and_build_road(state, action.player_id, action.edge_id)
            return state

        if isinstance(action, BuildBridgeAction):
            DevelopmentResolver.validate_and_build_bridge(state, action.player_id, action.edge_id)
            return state

        if isinstance(action, RecruitUnitAction):
            DevelopmentResolver.validate_and_recruit_unit(state, action.player_id, action.unit_type, action.target_node_id)
            return state

        if isinstance(action, EndPhaseAction):
            PincerEngine._advance_phase(state)
            return state

        return state

    @staticmethod
    def _validate_road_transfer(state: GameState, action: TransferViaRoadAction) -> None:
        """Rule: units may transfer between connected colonies in 1 move/turn."""
        unit = state.units.get(action.unit_id)
        if unit is None or unit.player_id != action.player_id:
            raise InvalidActionError("Invalid unit for road transfer.")
        if unit.unit_id in state.units_moved_this_turn or unit.unit_id in state.units_attacked_this_turn:
            raise RuleViolationError("Unit has already acted this turn.")

        curr_colony = state.get_colony_at(unit.node_id)
        target_colony = state.get_colony_at(action.target_colony_node_id)
        if not curr_colony or not target_colony:
            raise RuleViolationError("Road transfer must start and end at friendly colonies.")

        if curr_colony.controller != action.player_id or target_colony.controller != action.player_id:
            raise RuleViolationError("Road transfer only valid between friendly controlled colonies.")

        if curr_colony.is_annexed or target_colony.is_annexed:
            raise RuleViolationError("Road bonuses lost while colony is annexed.")

        # Check target tile has no unit
        if state.get_unit_at(action.target_colony_node_id) is not None:
            raise RuleViolationError("Destination colony is already occupied.")

    @staticmethod
    def _advance_phase(state: GameState) -> None:
        """Transitions between Harvest -> Mobilization -> Development -> Next Player Harvest."""
        if state.phase == TurnPhase.HARVEST:
            state.phase = TurnPhase.MOBILIZATION
        elif state.phase == TurnPhase.MOBILIZATION:
            state.phase = TurnPhase.DEVELOPMENT
        elif state.phase == TurnPhase.DEVELOPMENT:
            # End of active player's turn: advance turn
            PincerEngine._end_turn_and_advance(state)

    @staticmethod
    def _end_turn_and_advance(state: GameState) -> None:
        """Ends current turn, checks victory, updates fort siege, reverts annexed colonies if vacated."""
        # Update siege turns for fortified colonies
        PincerEngine._update_siege_status(state)

        # Clear per-turn tracking
        state.units_moved_this_turn.clear()
        state.units_attacked_this_turn.clear()
        if state.counter_move_state:
            state.counter_move_state.reset_for_new_turn()

        # Advance player
        player_list = list(state.players.keys())
        idx = player_list.index(state.current_player)
        next_player = player_list[(idx + 1) % len(player_list)]
        state.current_player = next_player

        if next_player == player_list[0]:
            state.turn_number += 1

        state.phase = TurnPhase.HARVEST

        # Check colony vacancy reversion on original owner's turn:
        # "Once your unit no longer occupies the colonies' tile, ownership is immediately transferred
        # back to the original owner (on their turn), at which point any fort built will be destroyed."
        for col in state.colonies.values():
            if col.is_annexed and col.original_owner == state.current_player:
                unit_on_tile = state.get_unit_at(col.node_id)
                if unit_on_tile is None or unit_on_tile.player_id == col.original_owner:
                    col.vacate()

        # Check victory after state updates and reversion
        winner = VictoryEvaluator.check_domination_winner(state)
        if winner is not None:
            state.winner = winner
            return

    @staticmethod
    def _update_siege_status(state: GameState) -> None:
        """Updates consecutive siege count for fortified colonies."""
        for colony in state.colonies.values():
            if not colony.has_fort:
                state.consecutive_siege_turns[colony.colony_id] = 0
                continue

            owner = colony.fort_owner or colony.controller
            # Check if any enemy has (cannon or frigate) AND additional land unit adjacent
            adjacent_nodes = state.board.get_neighbors(colony.node_id)
            enemy_cannons_or_frigates = 0
            enemy_other_land_units = 0

            for adj_id in adjacent_nodes:
                unit = state.get_unit_at(adj_id)
                if unit and unit.player_id != owner:
                    if unit.unit_type in (UnitType.CANNON, UnitType.FRIGATE):
                        enemy_cannons_or_frigates += 1
                    elif unit.is_land_unit():
                        enemy_other_land_units += 1

            if enemy_cannons_or_frigates >= 1 and enemy_other_land_units >= 1:
                state.consecutive_siege_turns[colony.colony_id] = (
                    state.consecutive_siege_turns.get(colony.colony_id, 0) + 1
                )
            else:
                state.consecutive_siege_turns[colony.colony_id] = 0

    @staticmethod
    def get_legal_actions(state: GameState) -> List[Action]:
        """Generates all legal actions available in the current state."""
        actions: List[Action] = []
        if state.winner is not None:
            return actions

        # Counter-move reaction window
        if state.counter_move_state and state.counter_move_state.is_active:
            def_player = state.counter_move_state.defender_player_id
            actions.append(PassCounterMoveAction(player_id=def_player))

            # Defending units that can counter-move
            def_units = [u for u in state.units.values() if u.player_id == def_player]
            used_units = state.counter_move_state.used_counter_unit_ids
            eligible_units = [
                u for u in def_units
                if len(used_units) == len(def_units) or u.unit_id not in used_units
            ]

            for unit in eligible_units:
                # Potential moves
                neighbors = state.board.get_neighbors(unit.node_id)
                for n_id in neighbors:
                    target_unit = state.get_unit_at(n_id)
                    if target_unit is None:
                        # Test if move is valid
                        try:
                            MovementValidator.validate_move(state, unit, n_id)
                            actions.append(CounterMoveAction(player_id=def_player, defender_unit_id=unit.unit_id, target_node_id=n_id, is_attack=False))
                        except Exception:
                            pass
                    elif target_unit.player_id != def_player:
                        # Test if attack is valid
                        try:
                            CombatResolver.validate_attack(state, unit, n_id)
                            actions.append(CounterMoveAction(player_id=def_player, defender_unit_id=unit.unit_id, target_node_id=n_id, is_attack=True))
                        except Exception:
                            pass
            return actions

        curr_p = state.current_player

        if state.phase == TurnPhase.HARVEST:
            actions.append(HarvestRollAction(player_id=curr_p))
            return actions

        if state.phase == TurnPhase.MOBILIZATION:
            actions.append(EndPhaseAction(player_id=curr_p))
            p_units = [
                u for u in state.units.values()
                if u.player_id == curr_p
                and u.can_act_on_turn(state.turn_number)
                and u.unit_id not in state.units_moved_this_turn
                and u.unit_id not in state.units_attacked_this_turn
            ]

            for unit in p_units:
                # Basic 1-step moves / attacks
                neighbors = state.board.get_neighbors(unit.node_id)
                for n_id in neighbors:
                    target_unit = state.get_unit_at(n_id)
                    if target_unit is None:
                        try:
                            MovementValidator.validate_move(state, unit, n_id)
                            actions.append(MoveUnitAction(player_id=curr_p, unit_id=unit.unit_id, target_node_id=n_id))
                        except Exception:
                            pass
                    elif target_unit.player_id != curr_p:
                        try:
                            CombatResolver.validate_attack(state, unit, n_id)
                            actions.append(AttackAction(player_id=curr_p, attacker_unit_id=unit.unit_id, target_node_id=n_id))
                        except Exception:
                            pass

                # Cannon attack option to return immediately
                if unit.unit_type == UnitType.CANNON:
                    for n_id in neighbors:
                        target_unit = state.get_unit_at(n_id)
                        if target_unit and target_unit.player_id != curr_p:
                            try:
                                CombatResolver.validate_attack(state, unit, n_id, cannon_return=True)
                                actions.append(AttackAction(player_id=curr_p, attacker_unit_id=unit.unit_id, target_node_id=n_id, cannon_return=True))
                            except Exception:
                                pass

                # Cavalry distance 2 moves/attacks
                if unit.unit_type == UnitType.CAVALRY:
                    for dest_id in state.board.nodes:
                        if state.board.graph_distance(unit.node_id, dest_id) == 2:
                            target_unit = state.get_unit_at(dest_id)
                            if target_unit is None:
                                try:
                                    MovementValidator.validate_move(state, unit, dest_id)
                                    actions.append(MoveUnitAction(player_id=curr_p, unit_id=unit.unit_id, target_node_id=dest_id))
                                except Exception:
                                    pass
                            elif target_unit.player_id != curr_p:
                                try:
                                    CombatResolver.validate_attack(state, unit, dest_id)
                                    actions.append(AttackAction(player_id=curr_p, attacker_unit_id=unit.unit_id, target_node_id=dest_id))
                                except Exception:
                                    pass

                # Frigate distance 2 moves/attacks on water
                if unit.unit_type == UnitType.FRIGATE:
                    for dest_id in state.board.nodes:
                        if state.board.graph_distance(unit.node_id, dest_id) == 2:
                            target_unit = state.get_unit_at(dest_id)
                            if target_unit is None:
                                try:
                                    MovementValidator.validate_move(state, unit, dest_id)
                                    actions.append(MoveUnitAction(player_id=curr_p, unit_id=unit.unit_id, target_node_id=dest_id))
                                except Exception:
                                    pass
                            elif target_unit.player_id != curr_p:
                                try:
                                    CombatResolver.validate_attack(state, unit, dest_id)
                                    actions.append(AttackAction(player_id=curr_p, attacker_unit_id=unit.unit_id, target_node_id=dest_id))
                                except Exception:
                                    pass

            return actions

        if state.phase == TurnPhase.DEVELOPMENT:
            actions.append(EndPhaseAction(player_id=curr_p))
            player = state.players[curr_p]

            # Trade actions
            rate = state.calculate_exchange_rate(curr_p)
            for offered in player.resources:
                if player.resources[offered] >= rate:
                    for req in player.resources:
                        if req != offered:
                            actions.append(TradeWithBankAction(player_id=curr_p, offered_resource=offered, requested_resource=req))

            # Build colony actions
            colony_cost = state.config.construction_costs.get(InfrastructureType.COLONY, {})
            if player.has_resources(colony_cost):
                for unit in state.get_player_units(curr_p):
                    try:
                        DevelopmentResolver.validate_and_build_colony(state.clone(), curr_p, unit.node_id)
                        actions.append(BuildColonyAction(player_id=curr_p, node_id=unit.node_id))
                    except Exception:
                        pass

            # Build port actions
            port_cost = (
                state.config.construction_costs.get(InfrastructureType.PORT)
                or state.config.construction_costs.get(InfrastructureType.HARBOR, {})
            )
            if player.has_resources(port_cost):
                for col in state.get_player_colonies(curr_p):
                    for n_id in state.board.get_neighbors(col.node_id):
                        try:
                            DevelopmentResolver.validate_and_build_port(state.clone(), curr_p, n_id, col.colony_id)
                            actions.append(BuildPortAction(player_id=curr_p, node_id=n_id, adjacent_colony_id=col.colony_id))
                        except Exception:
                            pass

            # Build fort actions
            fort_cost = (
                state.config.construction_costs.get(InfrastructureType.FORT)
                or state.config.construction_costs.get(InfrastructureType.WALL, {})
            )
            if player.has_resources(fort_cost):
                for col in state.get_player_colonies(curr_p):
                    try:
                        DevelopmentResolver.validate_and_build_fort(state.clone(), curr_p, col.colony_id)
                        actions.append(BuildFortAction(player_id=curr_p, colony_id=col.colony_id))
                    except Exception:
                        pass

            # Build road actions
            road_cost = state.config.construction_costs.get(InfrastructureType.ROAD, {})
            if player.has_resources(road_cost):
                for edge_id in state.board.edges:
                    try:
                        DevelopmentResolver.validate_and_build_road(state.clone(), curr_p, edge_id)
                        actions.append(BuildRoadAction(player_id=curr_p, edge_id=edge_id))
                    except Exception:
                        pass

            # Build bridge actions
            bridge_cost = state.config.construction_costs.get(InfrastructureType.BRIDGE, {})
            if player.has_resources(bridge_cost):
                for edge_id in state.board.edges:
                    try:
                        DevelopmentResolver.validate_and_build_bridge(state.clone(), curr_p, edge_id)
                        actions.append(BuildBridgeAction(player_id=curr_p, edge_id=edge_id))
                    except Exception:
                        pass

            # Unit recruitment actions
            for u_type in UnitType:
                cost = state.config.unit_costs.get(u_type, {})
                if player.has_resources(cost):
                    if u_type in (UnitType.MUSKETEER, UnitType.CAVALRY, UnitType.CANNON):
                        for col in state.get_player_colonies(curr_p):
                            try:
                                DevelopmentResolver.validate_and_recruit_unit(state.clone(), curr_p, u_type, col.node_id)
                                actions.append(RecruitUnitAction(player_id=curr_p, unit_type=u_type, target_node_id=col.node_id))
                            except Exception:
                                pass
                    elif u_type == UnitType.FRIGATE:
                        for port in state.ports.values():
                            if port.owner_id == curr_p:
                                try:
                                    DevelopmentResolver.validate_and_recruit_unit(state.clone(), curr_p, u_type, port.node_id)
                                    actions.append(RecruitUnitAction(player_id=curr_p, unit_type=u_type, target_node_id=port.node_id))
                                except Exception:
                                    pass

            return actions

        return actions
