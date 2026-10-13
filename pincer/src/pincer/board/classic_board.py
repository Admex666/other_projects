"""Full 58-tile board generator based on the Classic Rules component count."""
from typing import Dict, List, Set, Tuple
from pincer.board.edge import BoardEdge
from pincer.board.graph import BoardGraph
from pincer.board.node import BoardNode
from pincer.core.enums import TerrainType, ResourceType


def create_full_58_tile_board() -> BoardGraph:
    """Creates a full 58-tile hexagonal board representing the physical game board.
    
    Layout:
    - 58 terrain tiles arranged on a contiguous hexagonal grid.
    - 6 official terrain types:
        - Wheat (Fields, harvest value 1-6) -> ResourceType.WHEAT
        - Woods (Forest, harvest value 1-6) -> ResourceType.WOOD
        - Stone (Quarry, harvest value 1-6) -> ResourceType.STONE
        - Hills (harvest value 1-6) -> ResourceType.IRON_ORE
        - Mountains (impassable)
        - Water (lakes/bays for naval frigates, ports, bridges)
    - Perimeter tiles marked as is_edge=True (colonies cannot be built on edges).
    """
    g = BoardGraph()

    # Hex rows definition: list of (row_index, start_col, end_col_exclusive)
    # Sum of counts = 5 + 6 + 7 + 8 + 9 + 8 + 7 + 5 + 3 = 58 hexes!
    row_specs = [
        (0, 2, 7),  # 5 hexes: cols 2..6
        (1, 1, 7),  # 6 hexes: cols 1..6
        (2, 1, 8),  # 7 hexes: cols 1..7
        (3, 0, 8),  # 8 hexes: cols 0..7
        (4, 0, 9),  # 9 hexes: cols 0..8 (center row)
        (5, 0, 8),  # 8 hexes: cols 0..7
        (6, 1, 8),  # 7 hexes: cols 1..7
        (7, 2, 7),  # 5 hexes: cols 2..6
        (8, 3, 6),  # 3 hexes: cols 3..5
    ]

    # Pre-planned terrain distribution across 58 tiles:
    # 12 wheat, 12 woods, 10 stone, 10 hills, 6 mountain, 8 water = 58
    terrain_pattern = [
        # Row 0 (5): edge tiles
        (TerrainType.WOODS, ResourceType.WOOD, 1),
        (TerrainType.WHEAT, ResourceType.WHEAT, 2),
        (TerrainType.WATER, None, None),
        (TerrainType.STONE, ResourceType.STONE, 3),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 4),
        # Row 1 (6)
        (TerrainType.STONE, ResourceType.STONE, 5),
        (TerrainType.WOODS, ResourceType.WOOD, 6),
        (TerrainType.WHEAT, ResourceType.WHEAT, 1),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 2),
        (TerrainType.WOODS, ResourceType.WOOD, 3),
        # Row 2 (7)
        (TerrainType.WHEAT, ResourceType.WHEAT, 4),
        (TerrainType.WATER, None, None),
        (TerrainType.STONE, ResourceType.STONE, 5),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 6),
        (TerrainType.WHEAT, ResourceType.WHEAT, 1),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.STONE, ResourceType.STONE, 2),
        # Row 3 (8)
        (TerrainType.HILLS, ResourceType.IRON_ORE, 3),
        (TerrainType.WOODS, ResourceType.WOOD, 4),
        (TerrainType.WHEAT, ResourceType.WHEAT, 5),
        (TerrainType.WATER, None, None),
        (TerrainType.STONE, ResourceType.STONE, 6),
        (TerrainType.WOODS, ResourceType.WOOD, 1),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 2),
        (TerrainType.WATER, None, None),
        # Row 4 (9) center
        (TerrainType.STONE, ResourceType.STONE, 3),
        (TerrainType.WHEAT, ResourceType.WHEAT, 4),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.WOODS, ResourceType.WOOD, 5),
        (TerrainType.WATER, None, None),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 6),
        (TerrainType.STONE, ResourceType.STONE, 1),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.WOODS, ResourceType.WOOD, 2),
        # Row 5 (8)
        (TerrainType.WATER, None, None),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 3),
        (TerrainType.WHEAT, ResourceType.WHEAT, 4),
        (TerrainType.STONE, ResourceType.STONE, 5),
        (TerrainType.WOODS, ResourceType.WOOD, 6),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.WHEAT, ResourceType.WHEAT, 1),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 2),
        # Row 6 (7)
        (TerrainType.WOODS, ResourceType.WOOD, 3),
        (TerrainType.STONE, ResourceType.STONE, 4),
        (TerrainType.WATER, None, None),
        (TerrainType.WHEAT, ResourceType.WHEAT, 5),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 6),
        (TerrainType.WOODS, ResourceType.WOOD, 1),
        (TerrainType.STONE, ResourceType.STONE, 2),
        # Row 7 (5)
        (TerrainType.HILLS, ResourceType.IRON_ORE, 3),
        (TerrainType.WHEAT, ResourceType.WHEAT, 4),
        (TerrainType.MOUNTAIN, None, None),
        (TerrainType.WATER, None, None),
        (TerrainType.WOODS, ResourceType.WOOD, 5),
        # Row 8 (3)
        (TerrainType.STONE, ResourceType.STONE, 6),
        (TerrainType.WHEAT, ResourceType.WHEAT, 1),
        (TerrainType.HILLS, ResourceType.IRON_ORE, 2),
    ]

    tile_coords: Dict[str, Tuple[int, int]] = {}
    idx = 1
    t_idx = 0

    # Step 1: Create nodes
    for r, c_start, c_end in row_specs:
        for c in range(c_start, c_end):
            node_id = f"H{idx:02d}"
            terrain, res_type, val = terrain_pattern[t_idx]

            # Determine if node is on the boundary (perimeter edge tile)
            is_edge = (
                r == 0 or r == len(row_specs) - 1 or
                c == c_start or c == c_end - 1
            )

            node = BoardNode(
                node_id=node_id,
                terrain=terrain,
                harvest_value=val,
                resource_type=res_type,
                is_edge=is_edge,
            )
            g.add_node(node)
            tile_coords[node_id] = (c, r)
            idx += 1
            t_idx += 1

    # Step 2: Connect adjacent hexes
    # In flat-topped hex grid with even-col vertical offset:
    # Neighbor offsets from (c, r):
    # Same col: (c, r-1), (c, r+1)
    # If c is even: (c-1, r-1), (c-1, r), (c+1, r-1), (c+1, r)
    # If c is odd:  (c-1, r), (c-1, r+1), (c+1, r), (c+1, r+1)
    coord_to_id = {pos: nid for nid, pos in tile_coords.items()}

    def get_hex_neighbors(c: int, r: int) -> List[Tuple[int, int]]:
        offsets_same = [(c, r - 1), (c, r + 1)]
        if c % 2 == 0:
            offsets_diag = [(c - 1, r - 1), (c - 1, r), (c + 1, r - 1), (c + 1, r)]
        else:
            offsets_diag = [(c - 1, r), (c - 1, r + 1), (c + 1, r), (c + 1, r + 1)]
        return offsets_same + offsets_diag

    connected_pairs: Set[Tuple[str, str]] = set()
    edge_idx = 1

    for nid, (c, r) in tile_coords.items():
        node_a = g.get_node(nid)
        for nc, nr in get_hex_neighbors(c, r):
            neighbor_id = coord_to_id.get((nc, nr))
            if neighbor_id:
                pair = tuple(sorted([nid, neighbor_id]))
                if pair not in connected_pairs:
                    connected_pairs.add(pair)
                    node_b = g.get_node(neighbor_id)
                    is_water_crossing = (node_a.is_water() or node_b.is_water())
                    edge = BoardEdge(
                        edge_id=f"E_{nid}_{neighbor_id}",
                        node_a=nid,
                        node_b=neighbor_id,
                        is_water_crossing=is_water_crossing,
                    )
                    g.add_edge(edge)
                    edge_idx += 1

    return g
