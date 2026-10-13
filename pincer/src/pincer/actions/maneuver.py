"""Tactical maneuver card actions."""
from dataclasses import dataclass
from typing import Optional
from pincer.actions.base import Action
from pincer.core.enums import ManeuverType, PlayerId


@dataclass
class PlayManeuverAction(Action):
    """Plays a tactical maneuver card during combat or movement."""
    maneuver_type: ManeuverType
    card_id: str
    unit_id: str
    tile_id: str
    target_node_id: Optional[str] = None
