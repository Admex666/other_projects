"""Board edge representing an adjacency boundary or crossing between tiles."""
from dataclasses import dataclass
from typing import Optional
from pincer.core.enums import PlayerId


@dataclass
class BoardEdge:
    """Represents an edge connecting two adjacent tile nodes."""
    edge_id: str
    node_a: str
    node_b: str
    is_water_crossing: bool = False
    road_owner: Optional[PlayerId] = None
    bridge_owner: Optional[PlayerId] = None

    def connects(self, u: str, v: str) -> bool:
        return (self.node_a == u and self.node_b == v) or (self.node_a == v and self.node_b == u)

    def other_node(self, node: str) -> str:
        if node == self.node_a:
            return self.node_b
        if node == self.node_b:
            return self.node_a
        raise ValueError(f"Node {node} is not part of edge {self.edge_id}")
