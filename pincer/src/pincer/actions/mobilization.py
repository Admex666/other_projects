"""Mobilization phase actions: movement, attacks, reactions, transport."""
from dataclasses import dataclass
from typing import Optional, List
from pincer.actions.base import Action
from pincer.core.enums import PlayerId


@dataclass
class MoveUnitAction(Action):
    """Moves a unit along a path to an empty tile."""
    unit_id: str
    target_node_id: str
    # Optional path nodes (for multi-step moves e.g. cavalry or frigate)
    path: Optional[List[str]] = None


@dataclass
class AttackAction(Action):
    """Attacks an enemy unit stationed on target_node_id."""
    attacker_unit_id: str
    target_node_id: str
    # Cannon tactical choice: return immediately to original tile after attack
    cannon_return: bool = False


@dataclass
class CounterMoveAction(Action):
    """Immediate reaction taken by defender after an attack."""
    defender_unit_id: str
    target_node_id: str
    is_attack: bool = False


@dataclass
class PassCounterMoveAction(Action):
    """Defender chooses to decline/pass their counter-move."""
    pass


@dataclass
class TransferViaRoadAction(Action):
    """Transfer a unit between road-connected friendly colonies in 1 move/turn."""
    unit_id: str
    target_colony_node_id: str


@dataclass
class EmbarkFrigateAction(Action):
    """Embark a land unit onto an adjacent friendly frigate on water."""
    land_unit_id: str
    frigate_unit_id: str


@dataclass
class DisembarkFrigateAction(Action):
    """Disembark transported land unit onto adjacent land tile, moving/attacking by its range."""
    frigate_unit_id: str
    target_node_id: str
    is_attack: bool = False


@dataclass
class EndPhaseAction(Action):
    """Ends current turn phase and advances to next phase."""
    pass
