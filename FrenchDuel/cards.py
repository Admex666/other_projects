import random

class Card:
    """
    Represents a single playing card with its value, suit, color group, and type.
    """
    # New: A dictionary to map suit names to emojis
    SUIT_EMOJIS = {
        'Hearts': '♥️',
        'Diamonds': '♦️',
        'Clubs': '♣️',
        'Spades': '♠️'
    }

    def __init__(self, value, suit):
        self.value = value  # 2-10, J, Q, K, A
        self.suit = suit    # 'Hearts', 'Diamonds', 'Clubs', 'Spades'
        self.color_group = self._get_color_group()
        self.card_type = self._get_card_type()

    def _get_color_group(self):
        """Determines if the card is Red or Black."""
        if self.suit in ['Hearts', 'Diamonds']:
            return 'Red'
        return 'Black'

    def _get_card_type(self):
        """Determines if the card is a number, figure, or ace."""
        if self.value in ['J', 'Q', 'K']:
            return 'figure'
        if self.value == 'A':
            return 'ace'
        return 'number' # 2-10

    def get_score_value(self):
        """Returns the numerical score value of the card for damage calculation."""
        if isinstance(self.value, int):
            return self.value
        if self.value == 'J':
            return 11
        if self.value == 'Q':
            return 12
        if self.value == 'K':
            return 13
        if self.value == 'A':
            return 14 # Ace is high for scoring

    def __str__(self):
        """
        Modified to return a string with a suit emoji and the card value.
        Example: '♥️A' or '♣️10'
        """
        # Get the emoji from our dictionary
        emoji = self.SUIT_EMOJIS.get(self.suit, '')
        return f"{emoji}{self.value}"

    def __repr__(self):
        """
        Kept as is for clear, unambiguous debugging.
        """
        return f"Card('{self.value}', '{self.suit}')"

class Deck:
    """
    Represents a standard 52-card French deck.
    """
    def __init__(self):
        self.cards = self._create_deck()
        self.shuffle()

    def _create_deck(self):
        """Creates a fresh deck of 52 cards."""
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A']
        return [Card(value, suit) for suit in suits for value in values]

    def shuffle(self):
        """Shuffles the deck."""
        random.shuffle(self.cards)

    def draw(self, num_cards=1):
        """Draws a specified number of cards from the top of the deck."""
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards in the deck to draw.")
        drawn_cards = [self.cards.pop() for _ in range(num_cards)]
        return drawn_cards if num_cards > 1 else drawn_cards[0]

    def __len__(self):
        return len(self.cards)

class Hand:
    """
    Represents a player's hand of cards.
    """
    def __init__(self, cards=None):
        self.cards = cards if cards is not None else []

    def add_card(self, card):
        """Adds a card to the hand."""
        self.cards.append(card)

    def remove_card(self, card_to_remove):
        """Removes a specific card from the hand."""
        for i, card in enumerate(self.cards):
            if card.value == card_to_remove.value and card.suit == card_to_remove.suit:
                return self.cards.pop(i)
        raise ValueError(f"Card {card_to_remove} not found in hand.")

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

    def __repr__(self):
        return f"Hand({self.cards})"

class DiscardPile:
    """
    Represents the discard pile.
    """
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        """Adds a card to the discard pile."""
        self.cards.append(card)

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return f"Discard Pile ({len(self.cards)} cards)"

    def __repr__(self):
        return f"DiscardPile({self.cards})"

# Utility functions (can also be methods of Card or RulesEngine later)
def is_figure_or_ace(card):
    """Checks if a card is a figure (J, Q, K) or an Ace."""
    return card.card_type in ['figure', 'ace']

if __name__ == '__main__':
    # Simple test for cards.py
    print("Testing cards.py...")
    deck = Deck()
    print(f"Deck size: {len(deck)}")
    print(f"First 5 cards in shuffled deck: {deck.cards[:5]}")

    drawn_cards = deck.draw(3)
    print(f"Drawn 3 cards: {drawn_cards}")
    print(f"Deck size after drawing: {len(deck)}")

    hand = Hand()
    hand.add_card(drawn_cards[0])
    hand.add_card(deck.draw()) # Draw one more
    print(f"Hand: {hand}")
    print(f"Hand size: {len(hand)}")

    removed_card = hand.remove_card(drawn_cards[0])
    print(f"Removed card: {removed_card}")
    print(f"Hand after removal: {hand}")

    discard_pile = DiscardPile()
    discard_pile.add_card(removed_card)
    print(f"Discard Pile: {discard_pile}")

    test_card = Card('A', 'Spades')
    print(f"Test card: {test_card}, Score value: {test_card.get_score_value()}, Type: {test_card.card_type}")
    print(f"Is figure or ace (Test Card): {is_figure_or_ace(test_card)}")
    test_card_2 = Card(7, 'Diamonds')
    print(f"Test card: {test_card_2}, Score value: {test_card_2.get_score_value()}, Type: {test_card_2.card_type}")
    print(f"Is figure or ace (Test Card 2): {is_figure_or_ace(test_card_2)}")
