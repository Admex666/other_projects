"""Central GameState data model and state accessors."""
from copy import deepcopy
from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Set
from pincer.board.graph import BoardGraph
from pincer.cards.cards import Deck, create_standard_deck
from pincer.cards.dice import DiceRoller
from pincer.core.config import GameConfig
from pincer.core.enums import PlayerId, TurnPhase, UnitType, InfrastructureType
from pincer.entities.colony import Colony
from pincer.entities.infrastructure import Port, Road, Bridge
from pincer.entities.player import Player
from pincer.entities.unit import Unit
from pincer.state.counter_move import CounterMoveState


@dataclass
class GameState:
    """Full snapshot of the Pincer board game state."""
    board: BoardGraph
    players: Dict[PlayerId, Player]
    current_player: PlayerId
    phase: TurnPhase = TurnPhase.HARVEST
    turn_number: int = 1

    colonies: Dict[str, Colony] = field(default_factory=dict)
    units: Dict[str, Unit] = field(default_factory=dict)
    ports: Dict[str, Port] = field(default_factory=dict)
    roads: Dict[str, Road] = field(default_factory=dict)
    bridges: Dict[str, Bridge] = field(default_factory=dict)

    # Unit action tracking per turn
    units_moved_this_turn: Set[str] = field(default_factory=set)
    units_attacked_this_turn: Set[str] = field(default_factory=set)

    # Combat counter-move reaction window
    counter_move_state: Optional[CounterMoveState] = None

    # Decks & dice
    deck: Deck = field(default_factory=create_standard_deck)
    dice: DiceRoller = field(default_factory=DiceRoller)
    last_harvest_roll: Optional[int] = None

    # Config
    config: GameConfig = field(default_factory=GameConfig)

    # Endgame
    winner: Optional[PlayerId] = None

    # Fort siege tracking: colony_id -> count of consecutive player turns besieged
    consecutive_siege_turns: Dict[str, int] = field(default_factory=dict)

    def clone(self) -> "GameState":
        """Performs a deep copy of the complete game state."""
        return deepcopy(self)

    def get_unit_at(self, node_id: str) -> Optional[Unit]:
        """Returns the unit currently stationed on the specified tile, if any."""
        for u in self.units.values():
            if u.node_id == node_id:
                return u
        return None

    def get_units_at(self, node_id: str) -> List[Unit]:
        """Returns all units at the specified tile."""
        return [u for u in self.units.values() if u.node_id == node_id]

    def get_colony_at(self, node_id: str) -> Optional[Colony]:
        """Returns the colony on the specified tile, if any."""
        for c in self.colonies.values():
            if c.node_id == node_id:
                return c
        return None

    def get_port_at(self, node_id: str) -> Optional[Port]:
        """Returns the port at the specified water tile, if any."""
        for p in self.ports.values():
            if p.node_id == node_id:
                return p
        return None

    def get_player_colonies(self, player_id: PlayerId) -> List[Colony]:
        """Returns colonies currently controlled by the player (including annexed)."""
        return [c for c in self.colonies.values() if c.controller == player_id]

    def get_player_units(self, player_id: PlayerId) -> List[Unit]:
        """Returns all units belonging to the player."""
        return [u for u in self.units.values() if u.player_id == player_id]

    def calculate_exchange_rate(self, player_id: PlayerId) -> int:
        """Calculates current exchange rate for a player (5:1 base down to min 2:1).
        
        Rule: "5:1 trade ... Minus 1 for every port OR new colony connected by a road. (limit 2:1)."
        - Port: decreases rate by 1, unless occupied by enemy naval unit.
        - Connected colony: each new colony connected reduces rate by 1 (unless annexed).
        """
        rate = self.config.base_exchange_rate
        discounts = 0

        # Port discount:
        for port in self.ports.values():
            # Check ownership or annexation bonus
            colony = self.colonies.get(port.colony_id)
            if colony and colony.controller == player_id:
                # Unless occupied by an enemy naval unit
                occupying_unit = self.get_unit_at(port.node_id)
                if occupying_unit and occupying_unit.player_id != player_id and occupying_unit.is_naval_unit():
                    continue  # Blocked by enemy naval unit
                discounts += 1

        # Connected colonies by road:
        # A road network between colonies owned by player that are not annexed
        # Count connected pairs or connected colonies beyond the first
        player_colonies = [c for c in self.colonies.values() if c.controller == player_id and not c.is_annexed]
        if len(player_colonies) >= 2:
            # Check graph connectivity via player roads
            connected_colonies = self._count_road_connected_colonies(player_id, player_colonies)
            if connected_colonies > 1:
                # Each NEW colony connected beyond the first reduces exchange rate by 1
                discounts += (connected_colonies - 1)

        rate = max(self.config.min_exchange_rate, rate - discounts)
        return rate

    def _count_road_connected_colonies(self, player_id: PlayerId, player_colonies: List[Colony]) -> int:
        """Counts colonies in the largest connected component of player's road network."""
        colony_nodes = {c.node_id for c in player_colonies}
        player_road_edges = {
            e.edge_id for e in self.board.edges.values()
            if (e.road_owner == player_id or e.bridge_owner == player_id)
        }

        # Build adjacency over player roads
        adj: Dict[str, Set[str]] = {}
        for edge_id in player_road_edges:
            edge = self.board.edges[edge_id]
            adj.setdefault(edge.node_a, set()).add(edge.node_b)
            adj.setdefault(edge.node_b, set()).add(edge.node_a)

        # Find connected components of colony_nodes
        visited_nodes: Set[str] = set()
        max_connected = 0

        for col_node in colony_nodes:
            if col_node not in visited_nodes:
                comp_colonies = 0
                q = [col_node]
                visited_nodes.add(col_node)
                while q:
                    curr = q.pop(0)
                    if curr in colony_nodes:
                        comp_colonies += 1
                    for nxt in adj.get(curr, set()):
                        if nxt not in visited_nodes:
                            visited_nodes.add(nxt)
                            q.append(nxt)
                max_connected = max(max_connected, comp_colonies)

        return max_connected
