"""Infrastructure entity definitions (Port, Fort, Road, Bridge)."""
from dataclasses import dataclass
from typing import Optional
from pincer.core.enums import PlayerId


@dataclass
class Port:
    """A port built on a water tile adjacent to a colony."""
    port_id: str
    node_id: str
    owner_id: PlayerId
    colony_id: str


@dataclass
class Road:
    """A road built along an edge connecting tiles."""
    edge_id: str
    owner_id: PlayerId


@dataclass
class Bridge:
    """A bridge built on a water edge crossing touching land on both sides."""
    edge_id: str
    owner_id: PlayerId
