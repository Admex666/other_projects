"""Player state representation."""
from dataclasses import dataclass, field
from typing import Dict, List
from pincer.core.enums import PlayerId, ResourceType


@dataclass
class Player:
    """Represents a player in the game."""
    player_id: PlayerId
    resources: Dict[ResourceType, int] = field(default_factory=lambda: {r: 0 for r in ResourceType})
    maneuvers: List[str] = field(default_factory=list)

    def total_resources(self) -> int:
        return sum(self.resources.values())

    def add_resource(self, resource: ResourceType, count: int = 1) -> None:
        self.resources[resource] = self.resources.get(resource, 0) + count

    def remove_resource(self, resource: ResourceType, count: int = 1) -> bool:
        if self.resources.get(resource, 0) >= count:
            self.resources[resource] -= count
            return True
        return False

    def has_resources(self, cost: Dict[ResourceType, int]) -> bool:
        return all(self.resources.get(r, 0) >= qty for r, qty in cost.items())

    def deduct_resources(self, cost: Dict[ResourceType, int]) -> None:
        if not self.has_resources(cost):
            raise ValueError(f"Player {self.player_id} lacks resources to pay cost {cost}")
        for r, qty in cost.items():
            self.resources[r] -= qty
