"""Colony entity tracking permanent ownership vs temporary occupation."""
from dataclasses import dataclass
from typing import Optional
from pincer.core.enums import PlayerId


@dataclass
class Colony:
    """Represents a colony placed on a board tile."""
    colony_id: str
    node_id: str
    original_owner: PlayerId
    # If occupied by an enemy unit, current_occupant is that enemy's PlayerId
    current_occupant: Optional[PlayerId] = None
    # Fort presence & owner
    has_fort: bool = False
    fort_owner: Optional[PlayerId] = None
    fort_built_turn: Optional[int] = None
    # Turn when annexed
    annexed_turn: Optional[int] = None

    @property
    def controller(self) -> PlayerId:
        """Current controlling player (occupant if annexed, else original owner)."""
        return self.current_occupant if self.current_occupant is not None else self.original_owner

    @property
    def is_annexed(self) -> bool:
        """True if currently occupied by an enemy."""
        return self.current_occupant is not None and self.current_occupant != self.original_owner

    def occupy(self, player_id: PlayerId, turn_number: int) -> None:
        """Unit enters colony tile."""
        if player_id != self.original_owner:
            self.current_occupant = player_id
            self.annexed_turn = turn_number
        else:
            self.current_occupant = None
            self.annexed_turn = None

    def vacate(self) -> None:
        """Occupying unit leaves or is removed."""
        self.current_occupant = None
        self.annexed_turn = None
        # If an occupant had built a fort, it is destroyed upon reversion
        if self.has_fort and self.fort_owner != self.original_owner:
            self.has_fort = False
            self.fort_owner = None
            self.fort_built_turn = None
