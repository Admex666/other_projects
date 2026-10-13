"""Harvest phase execution and resource distribution."""
from typing import Dict, List, Optional
from pincer.core.enums import PlayerId, ResourceType
from pincer.state.state import GameState


class HarvestResolver:
    """Resolves resource die rolling and colony harvest collection."""

    @staticmethod
    def execute_harvest(state: GameState, roll_override: Optional[int] = None) -> Dict[PlayerId, List[ResourceType]]:
        """Rolls resource die and awards cards to all players based on colonies.
        
        Rule: "Roll resource die. All players collect one resource card per colony,
        if die matches adjacent tile (Unless occupied by enemy unit)."
        Occupied/annexed colonies yield resources to the occupying player.
        """
        roll = roll_override if roll_override is not None else state.dice.roll()
        state.last_harvest_roll = roll

        collected: Dict[PlayerId, List[ResourceType]] = {p: [] for p in state.players}

        for colony in state.colonies.values():
            controller_id = colony.controller
            adj_nodes = state.board.get_neighbors(colony.node_id)

            for adj_id in adj_nodes:
                adj_node = state.board.get_node(adj_id)
                if adj_node.harvest_value == roll and adj_node.resource_type is not None:
                    # Check if adjacent tile is occupied by enemy of the colony controller
                    unit_on_tile = state.get_unit_at(adj_id)
                    if unit_on_tile is not None and unit_on_tile.player_id != controller_id:
                        # Blocked: "Unless occupied by enemy unit"
                        continue

                    # Award resource
                    res = adj_node.resource_type
                    state.players[controller_id].add_resource(res, 1)
                    collected[controller_id].append(res)

        return collected
