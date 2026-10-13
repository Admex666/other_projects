"""Cards, deck, and maneuver management."""
from dataclasses import dataclass
import random
from typing import List, Optional
from pincer.core.enums import ResourceType, ManeuverType


@dataclass
class ResourceCard:
    """A resource card, optionally bearing a tactical maneuver."""
    card_id: str
    resource: ResourceType
    maneuver: Optional[ManeuverType] = None


class Deck:
    """Deck of resource and maneuver cards with deterministic shuffling."""

    def __init__(self, cards: Optional[List[ResourceCard]] = None, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.draw_pile: List[ResourceCard] = list(cards) if cards else []
        self.discard_pile: List[ResourceCard] = []

    def shuffle(self) -> None:
        self.rng.shuffle(self.draw_pile)

    def draw(self) -> Optional[ResourceCard]:
        if not self.draw_pile:
            if not self.discard_pile:
                return None
            self.draw_pile = list(self.discard_pile)
            self.discard_pile.clear()
            self.shuffle()
        return self.draw_pile.pop()

    def discard(self, card: ResourceCard) -> None:
        self.discard_pile.append(card)

    def count(self) -> int:
        return len(self.draw_pile)


def create_standard_deck(seed: Optional[int] = None) -> Deck:
    """Creates a standard deck of resource cards with maneuvers."""
    cards: List[ResourceCard] = []
    card_idx = 1
    # Distribute standard resource cards (e.g. 5 of each resource)
    for res in ResourceType:
        for _ in range(5):
            cards.append(ResourceCard(card_id=f"CARD_{card_idx}", resource=res, maneuver=None))
            card_idx += 1

    # Add cards bearing maneuvers
    maneuvers_map = [
        (ResourceType.ORE, ManeuverType.AMBUSH),
        (ResourceType.WOOD, ManeuverType.OUTFLANK),
        (ResourceType.SHEEP, ManeuverType.RETREAT),
        (ResourceType.ORE, ManeuverType.FORTIFY),
        (ResourceType.WHEAT, ManeuverType.ENCIRCLEMENT),
    ]
    for res, man in maneuvers_map:
        for _ in range(2):
            cards.append(ResourceCard(card_id=f"CARD_{card_idx}", resource=res, maneuver=man))
            card_idx += 1

    deck = Deck(cards=cards, seed=seed)
    deck.shuffle()
    return deck
