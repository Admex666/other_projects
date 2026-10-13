from enum import Enum, auto


class PlayerId(str, Enum):
    PLAYER_1 = "P1"
    PLAYER_2 = "P2"
    PLAYER_3 = "P3"
    PLAYER_4 = "P4"

    def opponent(self) -> "PlayerId":
        if self == PlayerId.PLAYER_1:
            return PlayerId.PLAYER_2
        if self == PlayerId.PLAYER_2:
            return PlayerId.PLAYER_1
        raise ValueError(f"Opponent mapping not uniquely defined for {self}")


class TerrainType(str, Enum):
    LAND = "land"
    WATER = "water"
    MOUNTAIN = "mountain"
    WOODS = "woods"
    HILLS = "hills"
    WHEAT = "wheat"
    STONE = "stone"


class UnitType(str, Enum):
    MUSKETEER = "musketeer"
    CAVALRY = "cavalry"
    CANNON = "cannon"
    FRIGATE = "frigate"


class InfrastructureType(str, Enum):
    COLONY = "colony"
    PORT = "port"
    HARBOR = "harbor"
    FORT = "fort"
    WALL = "wall"
    ROAD = "road"
    BRIDGE = "bridge"


class TurnPhase(str, Enum):
    HARVEST = "harvest"
    MOBILIZATION = "mobilization"
    DEVELOPMENT = "development"


class ManeuverType(str, Enum):
    AMBUSH = "ambush"
    OUTFLANK = "outflank"
    RETREAT = "retreat"
    FORTIFY = "fortify"
    ENCIRCLEMENT = "encirclement"


class ResourceType(str, Enum):
    WOOD = "wood"
    WHEAT = "wheat"
    STONE = "stone"
    IRON_ORE = "iron_ore"
    ORE = "ore"
    GOLD = "gold"
    SHEEP = "sheep"
    FISH = "fish"
    MUSTANG = "mustang"
