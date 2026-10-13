import pytest
from pincer.board.graph import BoardGraph
from pincer.board.node import BoardNode
from pincer.board.edge import BoardEdge
from pincer.board.synthetic import create_synthetic_test_board
from pincer.core.enums import TerrainType, ResourceType


def test_board_graph_topology():
    g = BoardGraph()
    n1 = BoardNode("N1", TerrainType.LAND)
    n2 = BoardNode("N2", TerrainType.LAND)
    n3 = BoardNode("N3", TerrainType.WATER)
    g.add_node(n1)
    g.add_node(n2)
    g.add_node(n3)

    e1 = BoardEdge("E1", "N1", "N2")
    e2 = BoardEdge("E2", "N2", "N3", is_water_crossing=True)
    g.add_edge(e1)
    g.add_edge(e2)

    assert g.get_neighbors("N1") == ["N2"]
    assert set(g.get_neighbors("N2")) == {"N1", "N3"}
    assert g.graph_distance("N1", "N3") == 2
    assert g.graph_distance("N1", "N1") == 0


def test_synthetic_test_board_composition():
    board = create_synthetic_test_board()
    assert "T1" in board.nodes
    assert "M1" in board.nodes
    assert "W1" in board.nodes
    assert "E1" in board.nodes

    # T1 is interior land
    assert board.get_node("T1").is_land()
    assert not board.get_node("T1").is_edge

    # E1 is edge land
    assert board.get_node("E1").is_edge

    # M1 is mountain
    assert board.get_node("M1").is_mountain()

    # W1 is water
    assert board.get_node("W1").is_water()


def test_colony_site_validity():
    board = create_synthetic_test_board()

    # Edge tile cannot host colony
    assert not board.is_valid_colony_site("E1", existing_colony_nodes=[])

    # Mountain or water cannot host colony
    assert not board.is_valid_colony_site("M1", existing_colony_nodes=[])
    assert not board.is_valid_colony_site("W1", existing_colony_nodes=[])

    # Interior land T1 can host initial colony
    assert board.is_valid_colony_site("T1", existing_colony_nodes=[])

    # If colony exists at T1, T2 (dist 1) and T3 (dist 2) cannot host colony
    assert not board.is_valid_colony_site("T2", existing_colony_nodes=["T1"], min_distance=3)
    assert not board.is_valid_colony_site("T3", existing_colony_nodes=["T1"], min_distance=3)

    # T4 distance from T1: T1 -> T2 -> T3 -> T4 (dist 3) or T1 -> T2 -> W1 -> T4 (dist 3)
    assert board.graph_distance("T1", "T4") == 3
    assert board.is_valid_colony_site("T4", existing_colony_nodes=["T1"], min_distance=3)


def test_full_58_tile_board_topology():
    from pincer.board.classic_board import create_full_58_tile_board
    board = create_full_58_tile_board()

    # Must contain exactly 58 hexagonal tiles
    assert len(board.nodes) == 58
    assert "H01" in board.nodes
    assert "H58" in board.nodes
    assert len(board.edges) == 143

    # Check terrain distribution
    terrains = {n.terrain for n in board.nodes.values()}
    assert TerrainType.WHEAT in terrains
    assert TerrainType.WOODS in terrains
    assert TerrainType.STONE in terrains
    assert TerrainType.HILLS in terrains
    assert TerrainType.MOUNTAIN in terrains
    assert TerrainType.WATER in terrains

    # Perimeter edge tiles vs interior tiles
    edge_nodes = [nid for nid, n in board.nodes.items() if n.is_edge]
    interior_nodes = [nid for nid, n in board.nodes.items() if not n.is_edge]
    assert len(edge_nodes) > 0
    assert len(interior_nodes) > 0

    # Colonies can only be on valid interior non-mountain, non-water land
    assert board.is_valid_colony_site("H14", existing_colony_nodes=[])
    assert board.is_valid_colony_site("H45", existing_colony_nodes=[])


def test_full_58_tile_board_initial_state():
    from pincer.state.setup import create_classic_initial_state
    from pincer.core.enums import PlayerId, TurnPhase
    from pincer.engine.engine import PincerEngine

    state = create_classic_initial_state(board_type="full_58")
    assert len(state.board.nodes) == 58
    assert state.phase == TurnPhase.HARVEST

    # P1 at H14, P2 at H45
    p1_cols = state.get_player_colonies(PlayerId.PLAYER_1)
    p2_cols = state.get_player_colonies(PlayerId.PLAYER_2)
    assert len(p1_cols) == 1
    assert p1_cols[0].node_id == "H14"
    assert len(p2_cols) == 1
    assert p2_cols[0].node_id == "H45"

    # Separation distance >= 3
    assert state.board.graph_distance("H14", "H45") >= 3

    # Starting units
    p1_units = state.get_player_units(PlayerId.PLAYER_1)
    p2_units = state.get_player_units(PlayerId.PLAYER_2)
    assert len(p1_units) == 1
    assert p1_units[0].node_id == "H14"
    assert len(p2_units) == 1
    assert p2_units[0].node_id == "H45"

    # Harvest roll legal action exists
    actions = PincerEngine.get_legal_actions(state)
    assert any(a.__class__.__name__ == "HarvestRollAction" for a in actions)

