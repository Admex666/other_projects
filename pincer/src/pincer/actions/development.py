"""Development phase actions: trading, construction, recruitment."""
from dataclasses import dataclass
from pincer.actions.base import Action
from pincer.core.enums import PlayerId, ResourceType, UnitType


@dataclass
class TradeWithBankAction(Action):
    """Trades identical resources with the bank for a resource of choice."""
    offered_resource: ResourceType
    requested_resource: ResourceType


@dataclass
class BuildColonyAction(Action):
    """Builds a new colony on a tile occupied by a friendly unit."""
    node_id: str


@dataclass
class BuildPortAction(Action):
    """Builds a port on a water tile adjacent to a friendly colony."""
    node_id: str
    adjacent_colony_id: str


@dataclass
class BuildFortAction(Action):
    """Builds a fort around a friendly colony."""
    colony_id: str


@dataclass
class BuildRoadAction(Action):
    """Builds a road on a board edge connecting tiles."""
    edge_id: str


@dataclass
class BuildBridgeAction(Action):
    """Builds a bridge on a water crossing edge touching land on both sides."""
    edge_id: str


@dataclass
class RecruitUnitAction(Action):
    """Recruits a new unit placing it in an eligible colony or port.
    
    *New units may not be used until next turn!*
    """
    unit_type: UnitType
    target_node_id: str
