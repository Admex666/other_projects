import random
from cards import Hand, Card, is_figure_or_ace
from strategy import BaseStrategy, RandomStrategy

class Player:
    """
    Base class for a player in the FrenchDuel game.
    Manages player's hand, damage, and serious injuries.
    """
    def __init__(self, name):
        self.name = name
        self.attack_hand = Hand()
        self.defense_hand = Hand()
        self.damage = 0
        self.serious_injuries = 0
        self.is_attacker = False # Role for the current phase

    def reset_for_new_phase(self):
        """Resets player state for a new duel phase."""
        self.attack_hand = Hand()
        self.defense_hand = Hand()
        self.serious_injuries = 0
        self.is_attacker = False

    def add_attack_card(self, card):
        """Adds a card to the player's attack hand."""
        self.attack_hand.add_card(card)

    def add_defense_card(self, card):
        """Adds a card to the player's defense hand."""
        self.defense_hand.add_card(card)

    def take_damage(self, amount):
        """Increases the player's damage."""
        self.damage += amount
        # print(f"{self.name} took {amount} damage. Total damage: {self.damage}")

    def suffer_serious_injury(self):
        """Increases the player's serious injury count."""
        self.serious_injuries += 1
        # print(f"{self.name} suffered a serious injury! Total serious injuries this phase: {self.serious_injuries}")

    def choose_attack_order(self):
        """
        Returns the ordered list of attack cards to be played.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
        
    def choose_defense_card(self):
        """
        Chooses a card to play as defender.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def discard_draft_card(self, hand_type):
        """
        Placeholder for discarding a card during the draft.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def choose_draft_card(self, available_cards, hand_type):
        """
        Placeholder for choosing a card during draft.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def __str__(self):
        return f"{self.name} (Damage: {self.damage}, Injuries: {self.serious_injuries})"

class BotPlayer(Player):
    """
    An AI player that makes decisions based on an assigned strategy object.
    """
    def __init__(self, name="Bot", strategy: BaseStrategy = None):
        super().__init__(name)
        # If no strategy is provided, use the default RandomStrategy
        self.strategy = strategy if strategy else RandomStrategy()

    def choose_attack_order(self):
        """
        Returns the ordered list of attack cards to be played.
        """
        ordered_cards = self.strategy.choose_attack_order(self.attack_hand.cards)
        return ordered_cards
        
    def choose_defense_card(self):
        """
        Chooses a card to play as defender.
        """
        if not self.defense_hand.cards:
            return None
        
        chosen_card = self.strategy.choose_defense_card(self.defense_hand.cards)
        self.defense_hand.remove_card(chosen_card)
        return chosen_card

    def discard_draft_card(self, hand_type):
        if hand_type == 'attack':
            hand_to_discard_from = self.attack_hand
        elif hand_type == 'defense':
            hand_to_discard_from = self.defense_hand
        else:
            raise ValueError("Invalid hand_type for discarding.")

        card_to_discard = self.strategy.discard_draft_card(hand_to_discard_from.cards, hand_type)
        hand_to_discard_from.remove_card(card_to_discard)
        return card_to_discard

    def choose_draft_card(self, available_cards, hand_type):
        chosen_card = self.strategy.choose_draft_card(available_cards, hand_type)
        return chosen_card