"""Base action class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pincer.core.enums import PlayerId


@dataclass
class Action(ABC):
    """Abstract base class for all player actions."""
    player_id: PlayerId
