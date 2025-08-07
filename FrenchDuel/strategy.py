import random
from cards import Card

class BaseStrategy:
    """
    Base class for all bot strategies.
    Defines the standard API for decision-making.
    """
    def choose_draft_card(self, available_cards: list[Card], hand_type: str) -> Card:
        raise NotImplementedError
    
    def choose_defense_card(self, hand: list[Card]) -> Card:
        raise NotImplementedError
    
    def choose_attack_order(self, hand: list[Card]) -> list[Card]:  # Új metódus
        raise NotImplementedError
    
    def discard_draft_card(self, hand: list[Card], hand_type: str) -> Card:
        raise NotImplementedError

class RandomStrategy(BaseStrategy):
    """
    A strategy that makes completely random choices.
    """
    def choose_draft_card(self, available_cards: list[Card], hand_type: str) -> Card:
        return random.choice(available_cards)
    
    def choose_defense_card(self, hand: list[Card]) -> Card:
        return random.choice(hand)

    def choose_attack_order(self, hand: list[Card]) -> list[Card]:  # Új metódus
        ordered_hand = list(hand)
        random.shuffle(ordered_hand)
        return ordered_hand
    
    def discard_draft_card(self, hand: list[Card], hand_type: str) -> Card:
        return random.choice(hand)

class GreedyHighestValueStrategy(BaseStrategy):
    """
    A greedy strategy that always picks/plays the highest value card.
    """
    def choose_draft_card(self, available_cards: list[Card], hand_type: str) -> Card:
        return max(available_cards, key=lambda card: card.get_score_value())
    
    def choose_defense_card(self, hand: list[Card]) -> Card:
        return max(hand, key=lambda card: card.get_score_value())

    def choose_attack_order(self, hand: list[Card]) -> list[Card]:  # Új metódus
        return sorted(hand, key=lambda card: card.get_score_value(), reverse=True)
    
    def discard_draft_card(self, hand: list[Card], hand_type: str) -> Card:
        return min(hand, key=lambda card: card.get_score_value())