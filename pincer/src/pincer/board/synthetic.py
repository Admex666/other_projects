"""Synthetic test board topology for rule verification and testing."""
from pincer.board.node import BoardNode
from pincer.board.edge import BoardEdge
from pincer.board.graph import BoardGraph
from pincer.core.enums import TerrainType, ResourceType


def create_synthetic_test_board() -> BoardGraph:
    """Creates a small, fully deterministic synthetic test board.
    
    Layout overview (10 nodes):
    - Interior Land nodes: T1, T2, T3, T4 (can host colonies if dist >= 3)
    - Edge Land nodes: E1, E2, E3 (cannot host colonies)
    - Mountain node: M1 (land units cannot enter)
    - Water nodes: W1, W2 (for naval frigates, ports, bridges)
    
    Graph connectivity:
      E1 (edge land) <-> T1 (land, val 1) <-> T2 (land, val 2) <-> T3 (land, val 3) <-> E2 (edge land)
      T1 <-> M1 (mountain)
      T2 <-> W1 (water) <-> W2 (water)
      W1 <-> T4 (land, val 4)
      T3 <-> T4
      T4 <-> E3 (edge land)
    """
    g = BoardGraph()

    # Edge land nodes
    g.add_node(BoardNode(node_id="E1", terrain=TerrainType.LAND, harvest_value=1, resource_type=ResourceType.WOOD, is_edge=True))
    g.add_node(BoardNode(node_id="E2", terrain=TerrainType.LAND, harvest_value=2, resource_type=ResourceType.WHEAT, is_edge=True))
    g.add_node(BoardNode(node_id="E3", terrain=TerrainType.LAND, harvest_value=3, resource_type=ResourceType.ORE, is_edge=True))

    # Interior land nodes
    g.add_node(BoardNode(node_id="T1", terrain=TerrainType.LAND, harvest_value=1, resource_type=ResourceType.WOOD, is_edge=False))
    g.add_node(BoardNode(node_id="T2", terrain=TerrainType.LAND, harvest_value=2, resource_type=ResourceType.WHEAT, is_edge=False))
    g.add_node(BoardNode(node_id="T3", terrain=TerrainType.LAND, harvest_value=3, resource_type=ResourceType.ORE, is_edge=False))
    g.add_node(BoardNode(node_id="T4", terrain=TerrainType.LAND, harvest_value=4, resource_type=ResourceType.GOLD, is_edge=False))

    # Mountain node
    g.add_node(BoardNode(node_id="M1", terrain=TerrainType.MOUNTAIN, harvest_value=None, resource_type=None, is_edge=False))

    # Water nodes
    g.add_node(BoardNode(node_id="W1", terrain=TerrainType.WATER, harvest_value=None, resource_type=None, is_edge=False))
    g.add_node(BoardNode(node_id="W2", terrain=TerrainType.WATER, harvest_value=None, resource_type=None, is_edge=True))

    # Connect edges
    edges = [
        BoardEdge(edge_id="E_E1_T1", node_a="E1", node_b="T1"),
        BoardEdge(edge_id="E_T1_T2", node_a="T1", node_b="T2"),
        BoardEdge(edge_id="E_T2_T3", node_a="T2", node_b="T3"),
        BoardEdge(edge_id="E_T3_E2", node_a="T3", node_b="E2"),
        BoardEdge(edge_id="E_T1_M1", node_a="T1", node_b="M1"),
        BoardEdge(edge_id="E_T2_W1", node_a="T2", node_b="W1", is_water_crossing=True),
        BoardEdge(edge_id="E_W1_W2", node_a="W1", node_b="W2"),
        BoardEdge(edge_id="E_W1_T4", node_a="W1", node_b="T4", is_water_crossing=True),
        BoardEdge(edge_id="E_T3_T4", node_a="T3", node_b="T4"),
        BoardEdge(edge_id="E_T4_E3", node_a="T4", node_b="E3"),
    ]
    for edge in edges:
        g.add_edge(edge)

    return g
