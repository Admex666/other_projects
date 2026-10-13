"""Unit entity definitions."""
from dataclasses import dataclass
from typing import Optional
from pincer.core.enums import PlayerId, UnitType


@dataclass
class Unit:
    """Represents a military piece on the board."""
    unit_id: str
    unit_type: UnitType
    player_id: PlayerId
    node_id: str
    built_turn: int = 0
    # For frigates transporting a land unit:
    cargo: Optional["Unit"] = None

    def can_act_on_turn(self, current_turn: int) -> bool:
        """New units may not be used until next turn."""
        return current_turn > self.built_turn

    def is_land_unit(self) -> bool:
        return self.unit_type in (UnitType.MUSKETEER, UnitType.CAVALRY, UnitType.CANNON)

    def is_naval_unit(self) -> bool:
        return self.unit_type == UnitType.FRIGATE
