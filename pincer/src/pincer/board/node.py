"""Board node representing a tile in the board graph."""
from dataclasses import dataclass
from typing import Optional
from pincer.core.enums import TerrainType, ResourceType


@dataclass
class BoardNode:
    """Represents a single tile on the game board."""
    node_id: str
    terrain: TerrainType
    harvest_value: Optional[int] = None
    resource_type: Optional[ResourceType] = None
    is_edge: bool = False

    def is_land(self) -> bool:
        return self.terrain in (
            TerrainType.LAND,
            TerrainType.WOODS,
            TerrainType.HILLS,
            TerrainType.WHEAT,
            TerrainType.STONE,
        )

    def is_water(self) -> bool:
        return self.terrain == TerrainType.WATER

    def is_mountain(self) -> bool:
        return self.terrain == TerrainType.MOUNTAIN
