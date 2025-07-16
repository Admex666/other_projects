# agents/base_agent.py
import typing
from typing import List, Dict, Optional, Tuple

# Előre deklarálás a típusannotációhoz, hogy elkerüljük a körkörös importot
if typing.TYPE_CHECKING:
    from game.engine import AlsosGame
    from game.definitions import Card, BonusType

class PlayerAgent:
    """Base class for player agents, defining decision-making methods."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        raise NotImplementedError

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        """Decide which bonuses to announce. Returns a comma-separated string of bonus numbers or 'pass'."""
        raise NotImplementedError

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        raise NotImplementedError