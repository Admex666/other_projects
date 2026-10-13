"""Graph topology and navigation for the Pincer board."""
from collections import deque
from copy import deepcopy
from typing import Dict, List, Optional, Set, Tuple, Iterable
from pincer.board.node import BoardNode
from pincer.board.edge import BoardEdge
from pincer.core.enums import TerrainType


class BoardGraph:
    """Topology graph representing tiles (nodes) and connections (edges)."""

    def __init__(self) -> None:
        self.nodes: Dict[str, BoardNode] = {}
        self.edges: Dict[str, BoardEdge] = {}
        self._adjacency: Dict[str, List[str]] = {}
        self._edge_lookup: Dict[Tuple[str, str], str] = {}

    def add_node(self, node: BoardNode) -> None:
        self.nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = []

    def add_edge(self, edge: BoardEdge) -> None:
        if edge.node_a not in self.nodes or edge.node_b not in self.nodes:
            raise ValueError(f"Edge {edge.edge_id} connects non-existent nodes {edge.node_a}, {edge.node_b}")
        self.edges[edge.edge_id] = edge
        self._adjacency[edge.node_a].append(edge.node_b)
        self._adjacency[edge.node_b].append(edge.node_a)
        self._edge_lookup[(edge.node_a, edge.node_b)] = edge.edge_id
        self._edge_lookup[(edge.node_b, edge.node_a)] = edge.edge_id

    def get_node(self, node_id: str) -> BoardNode:
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} does not exist on board")
        return self.nodes[node_id]

    def get_neighbors(self, node_id: str) -> List[str]:
        return list(self._adjacency.get(node_id, []))

    def get_edge(self, node_a: str, node_b: str) -> Optional[BoardEdge]:
        edge_id = self._edge_lookup.get((node_a, node_b))
        return self.edges[edge_id] if edge_id else None

    def graph_distance(self, start_node: str, end_node: str) -> Optional[int]:
        """Calculates topological graph distance (unweighted shortest path)."""
        if start_node == end_node:
            return 0
        if start_node not in self.nodes or end_node not in self.nodes:
            return None

        visited: Set[str] = {start_node}
        queue: deque[Tuple[str, int]] = deque([(start_node, 0)])

        while queue:
            curr, dist = queue.popleft()
            for neighbor in self._adjacency.get(curr, []):
                if neighbor == end_node:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        return None

    def distance_matrix(self) -> Dict[str, Dict[str, int]]:
        """Precomputes all-pairs shortest path distances."""
        distances: Dict[str, Dict[str, int]] = {}
        for src in self.nodes:
            distances[src] = {}
            visited: Set[str] = {src}
            queue: deque[Tuple[str, int]] = deque([(src, 0)])
            distances[src][src] = 0
            while queue:
                curr, d = queue.popleft()
                for nxt in self._adjacency.get(curr, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        distances[src][nxt] = d + 1
                        queue.append((nxt, d + 1))
        return distances

    def is_valid_colony_site(
        self,
        node_id: str,
        existing_colony_nodes: Iterable[str],
        min_distance: int = 3
    ) -> bool:
        """Validates topological criteria for colony placement:
        1. Node must exist.
        2. Node must NOT be an edge tile.
        3. Node must be at least min_distance (e.g. 3) away from all existing colonies.
        """
        if node_id not in self.nodes:
            return False
        node = self.nodes[node_id]
        if node.is_edge:
            return False
        # Must be land to build a colony
        if not node.is_land():
            return False

        for existing_id in existing_colony_nodes:
            dist = self.graph_distance(node_id, existing_id)
            if dist is not None and dist < min_distance:
                return False
        return True

    def any_valid_colony_site_remaining(
        self,
        existing_colony_nodes: Iterable[str],
        min_distance: int = 3
    ) -> bool:
        """Returns True if any unoccupied valid colony site remains on the board."""
        existing_set = set(existing_colony_nodes)
        for node_id in self.nodes:
            if node_id in existing_set:
                continue
            if self.is_valid_colony_site(node_id, existing_set, min_distance):
                return True
        return False

    def clone(self) -> "BoardGraph":
        """Returns a deep copy of the board graph."""
        return deepcopy(self)
