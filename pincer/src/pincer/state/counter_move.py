"""Counter-move reaction state tracking."""
from dataclasses import dataclass, field
from typing import Set
from pincer.core.enums import PlayerId


@dataclass
class CounterMoveState:
    """Explicitly models the combat counter-move reaction window.
    
    After attacking, the opponent makes one immediate counter move/attack
    with any unit before the offensive player's turn resumes.
    The opponent must use a separate piece for each counter attack before
    reusing the same one, until the offensive player's turn ends.
    """
    attacker_unit_id: str
    defender_player_id: PlayerId
    attacked_node_id: str
    # Units of the defender that have already performed a counter-move this turn
    used_counter_unit_ids: Set[str] = field(default_factory=set)
    # Is counter-move currently pending resolution?
    is_active: bool = True

    def record_counter_move(self, unit_id: str) -> None:
        self.used_counter_unit_ids.add(unit_id)
        self.is_active = False

    def pass_counter_move(self) -> None:
        self.is_active = False

    def reset_for_new_turn(self) -> None:
        self.used_counter_unit_ids.clear()
        self.is_active = False
