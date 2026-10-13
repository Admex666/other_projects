from dataclasses import dataclass, field
from typing import Dict, Optional
from pincer.core.enums import InfrastructureType, UnitType, ResourceType


@dataclass(frozen=True)
class GameConfig:
    """Game rules configuration.
    
    Unstated or ambiguous values in the player card reference are parameterized here
    so they can be configured or tuned without modifying rule enforcement code.
    """
    # Colony placement rule: minimum graph distance between colonies
    min_colony_distance: int = 3

    # Cavalry movement: player card specifies "move/attack only by 2 tiles away per turn"
    # If True, cavalry must move exactly 2 tiles. If False, cavalry can move 1 or 2 tiles.
    cavalry_requires_exact_2_tiles: bool = True

    # Base exchange rate: 5:1 trade (5 of same resource for 1 of choice)
    base_exchange_rate: int = 5
    # Minimum exchange rate limit (limit 2:1)
    min_exchange_rate: int = 2

    # Domination victory requirement: controlling fraction of colonies
    domination_control_fraction: float = 0.75
    # Does domination require board completion (no legal room left for colonies)?
    domination_requires_board_completion: bool = True
    # Classic Rules victory: target number of controlled colonies (video describes 4)
    classic_target_colonies: Optional[int] = None

    # Default configurable resource costs for infrastructure
    construction_costs: Dict[InfrastructureType, Dict[ResourceType, int]] = field(
        default_factory=lambda: {
            InfrastructureType.COLONY: {ResourceType.WOOD: 1, ResourceType.WHEAT: 1, ResourceType.ORE: 1, ResourceType.SHEEP: 1},
            InfrastructureType.PORT: {ResourceType.WOOD: 2, ResourceType.ORE: 1},
            InfrastructureType.HARBOR: {ResourceType.WOOD: 2, ResourceType.ORE: 1},
            InfrastructureType.FORT: {ResourceType.ORE: 2, ResourceType.WOOD: 1},
            InfrastructureType.WALL: {ResourceType.STONE: 3},
            InfrastructureType.ROAD: {ResourceType.WOOD: 1, ResourceType.ORE: 1},
            InfrastructureType.BRIDGE: {ResourceType.WOOD: 2, ResourceType.ORE: 2},
        }
    )

    # Default configurable resource costs for units
    unit_costs: Dict[UnitType, Dict[ResourceType, int]] = field(
        default_factory=lambda: {
            UnitType.MUSKETEER: {ResourceType.WHEAT: 1, ResourceType.SHEEP: 1},
            UnitType.CAVALRY: {ResourceType.WHEAT: 1, ResourceType.SHEEP: 1, ResourceType.ORE: 1},
            UnitType.CANNON: {ResourceType.ORE: 2, ResourceType.WOOD: 1},
            UnitType.FRIGATE: {ResourceType.WOOD: 2, ResourceType.ORE: 1, ResourceType.SHEEP: 1},
        }
    )

    @classmethod
    def classic(cls) -> "GameConfig":
        """Returns GameConfig initialized with documented Classic Rules values."""
        classic_construction = {
            InfrastructureType.COLONY: {ResourceType.WOOD: 2, ResourceType.WHEAT: 2, ResourceType.STONE: 1, ResourceType.IRON_ORE: 1},
            InfrastructureType.PORT: {ResourceType.WOOD: 2, ResourceType.IRON_ORE: 1},
            InfrastructureType.HARBOR: {ResourceType.WOOD: 2, ResourceType.IRON_ORE: 1},
            InfrastructureType.FORT: {ResourceType.STONE: 3},
            InfrastructureType.WALL: {ResourceType.STONE: 3},
            InfrastructureType.ROAD: {ResourceType.WOOD: 1, ResourceType.STONE: 1},
            InfrastructureType.BRIDGE: {ResourceType.STONE: 1},
        }
        classic_units = {
            UnitType.MUSKETEER: {ResourceType.WHEAT: 2},
            UnitType.CAVALRY: {ResourceType.WHEAT: 2, ResourceType.MUSTANG: 1},
            UnitType.CANNON: {ResourceType.IRON_ORE: 4},
            UnitType.FRIGATE: {ResourceType.WOOD: 2, ResourceType.IRON_ORE: 2},
        }
        return cls(
            classic_target_colonies=4,
            domination_requires_board_completion=False,
            construction_costs=classic_construction,
            unit_costs=classic_units,
        )
