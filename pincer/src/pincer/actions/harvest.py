"""Harvest phase action."""
from dataclasses import dataclass
from typing import Optional
from pincer.actions.base import Action
from pincer.core.enums import PlayerId


@dataclass
class HarvestRollAction(Action):
    """Action to roll the resource die during the Harvest phase."""
    override_roll: Optional[int] = None  # Allows deterministic testing
