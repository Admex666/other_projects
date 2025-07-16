# game/definitions.py
from enum import Enum
from dataclasses import dataclass
from typing import List

class Suit(Enum):
    ACORNS = "Acorns 🌰"
    LEAVES = "Leaves 🌿" 
    BELLS = "Bells 🔔"
    HEARTS = "Hearts ❤️"

class Rank(Enum):
    VII = 7
    VIII = 8
    IX = 9
    X = 10
    UNDER = 11  # Jack
    OVER = 12   # Queen
    KING = 13
    ACE = 14

class GameType(Enum):
    TRUMP = "Trump"
    NO_TRUMP = "No Trump"
    BETLI = "Betli"
    KLOPITZKY = "Klopitzky"

class BonusType(Enum):
    KASSZA = "Kassza"
    ABSZOLUT = "Abszolút"
    HUNDRED_EIGHTY = "100/80"
    TWO_HUNDRED = "200/180"
    FOUR_ACES = "Four Aces"
    TRULL = "Trull"
    ULTIMATE = "Ulti"
    FAMILY = "Family"
    ALL_TRUMPS = "All trumps"
    VOLAT = "Volát"

@dataclass
class Card:
    suit: Suit
    rank: Rank
    
    def __str__(self):
        return f"{self.rank.name} of {self.suit.value}"
    
    def __repr__(self):
        return self.__str__()

class Meld:
    def __init__(self, name: str, cards: List[Card], points: int):
        self.name = name
        self.cards = cards
        self.points = points
    
    def __str__(self):
        return f"{self.name} ({self.points} points): {self.cards}"