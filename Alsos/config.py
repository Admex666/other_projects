# config.py
from game.definitions import Suit, BonusType # Majdani import, ha a definíciók külön fájlban lesznek

BASE_FEATURE_ORDER = [
    'game_type', 'trump_suit', 'is_taker', 'phase', 'hand_size',
    'high_cards', 'trump_cards', 'hearts_count', 'bells_count',
    'leaves_count', 'acorns_count', 'total_points', 'bonus_type',
    'bonus_number', 'has_bela', 'has_ulti', 'ace_count'
]

BONUS_POINTS = {
    BonusType.KASSZA: {'back': 4, 'front': 2},
    BonusType.ABSZOLUT: {'back': 6, 'front': 3},
    # ... a többi bónuszpont
}

SUIT_ORDER = {
    Suit.HEARTS: 4,
    Suit.BELLS: 3,
    Suit.LEAVES: 2,
    Suit.ACORNS: 1
}