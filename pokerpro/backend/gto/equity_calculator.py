"""
Equity Calculator for poker hands

Uses Monte Carlo simulation to calculate hand equity
"""

import random
from typing import List, Tuple, Optional
from itertools import combinations


# Card representations
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades

RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}


class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]
    
    def __repr__(self):
        return f"{self.rank}{self.suit}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))


def create_deck() -> List[Card]:
    """Create a standard 52-card deck"""
    return [Card(rank, suit) for rank in RANKS for suit in SUITS]


def parse_hand(hand_str: str) -> List[Card]:
    """
    Parse hand string to Card objects
    Example: "AhKd" -> [Card('A', 'h'), Card('K', 'd')]
    """
    cards = []
    i = 0
    while i < len(hand_str):
        if i + 1 < len(hand_str):
            rank = hand_str[i]
            suit = hand_str[i + 1]
            if rank in RANKS and suit in SUITS:
                cards.append(Card(rank, suit))
                i += 2
            else:
                i += 1
        else:
            i += 1
    return cards


def evaluate_hand(cards: List[Card]) -> Tuple[int, List[int]]:
    """
    Evaluate 5-card poker hand
    
    Returns:
        (hand_rank, tiebreakers)
        hand_rank: 0=high card, 1=pair, 2=two pair, ..., 8=straight flush
    """
    
    if len(cards) != 5:
        return (0, [])
    
    # Sort by value
    sorted_cards = sorted(cards, key=lambda c: c.value, reverse=True)
    values = [c.value for c in sorted_cards]
    suits = [c.suit for c in sorted_cards]
    
    # Check flush
    is_flush = len(set(suits)) == 1
    
    # Check straight
    is_straight = False
    if values == list(range(values[0], values[0] - 5, -1)):
        is_straight = True
    # Check wheel (A-2-3-4-5)
    elif values == [12, 3, 2, 1, 0]:  # A-5-4-3-2
        is_straight = True
        values = [3, 2, 1, 0, 12]  # Reorder for proper evaluation
    
    # Count ranks
    rank_counts = {}
    for v in values:
        rank_counts[v] = rank_counts.get(v, 0) + 1
    
    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(rank_counts.keys(), key=lambda x: (rank_counts[x], x), reverse=True)
    
    # Determine hand rank
    if is_straight and is_flush:
        return (8, values[:1])  # Straight flush
    elif counts == [4, 1]:
        return (7, unique_ranks)  # Four of a kind
    elif counts == [3, 2]:
        return (6, unique_ranks)  # Full house
    elif is_flush:
        return (5, values)  # Flush
    elif is_straight:
        return (4, values[:1])  # Straight
    elif counts == [3, 1, 1]:
        return (3, unique_ranks)  # Three of a kind
    elif counts == [2, 2, 1]:
        return (2, unique_ranks)  # Two pair
    elif counts == [2, 1, 1, 1]:
        return (1, unique_ranks)  # Pair
    else:
        return (0, values)  # High card


def best_hand(cards: List[Card]) -> Tuple[int, List[int]]:
    """Find best 5-card hand from 7 cards"""
    
    if len(cards) < 5:
        return (0, [])
    
    best = (0, [])
    for combo in combinations(cards, 5):
        hand_value = evaluate_hand(list(combo))
        if hand_value > best:
            best = hand_value
    
    return best


def calculate_equity(
    hero_hand: str,
    villain_hand: str = None,
    board: str = "",
    simulations: int = 10000
) -> float:
    """
    Calculate equity using Monte Carlo simulation
    
    Args:
        hero_hand: Hero's hand (e.g., "AhKd")
        villain_hand: Villain's hand or None for random
        board: Current board cards (e.g., "Qh Jd 7s")
        simulations: Number of simulations to run
    
    Returns:
        Equity as percentage (0-100)
    """
    
    hero_cards = parse_hand(hero_hand.replace(" ", ""))
    board_cards = parse_hand(board.replace(" ", "")) if board else []
    villain_cards = parse_hand(villain_hand.replace(" ", "")) if villain_hand else None
    
    # Remove known cards from deck
    deck = create_deck()
    known_cards = set(hero_cards + board_cards)
    if villain_cards:
        known_cards.update(villain_cards)
    
    available_deck = [c for c in deck if c not in known_cards]
    
    wins = 0
    ties = 0
    
    for _ in range(simulations):
        sim_deck = available_deck.copy()
        random.shuffle(sim_deck)
        
        # Deal villain hand if not specified
        if villain_cards is None:
            sim_villain = sim_deck[:2]
            remaining = sim_deck[2:]
        else:
            sim_villain = villain_cards
            remaining = sim_deck
        
        # Complete the board
        cards_needed = 5 - len(board_cards)
        sim_board = board_cards + remaining[:cards_needed]
        
        # Evaluate hands
        hero_best = best_hand(hero_cards + sim_board)
        villain_best = best_hand(sim_villain + sim_board)
        
        if hero_best > villain_best:
            wins += 1
        elif hero_best == villain_best:
            ties += 1
    
    equity = ((wins + ties / 2) / simulations) * 100
    return round(equity, 2)


def calculate_outs(hero_hand: str, board: str, target: str = "any") -> int:
    """
    Calculate number of outs
    
    Args:
        hero_hand: Hero's hand
        board: Current board
        target: Type of draw ("flush", "straight", "any")
    
    Returns:
        Number of outs
    """
    
    # Simplified out counting
    hero_cards = parse_hand(hero_hand.replace(" ", ""))
    board_cards = parse_hand(board.replace(" ", ""))
    
    all_cards = hero_cards + board_cards
    suits = [c.suit for c in all_cards]
    
    outs = 0
    
    # Flush draw
    if target in ["flush", "any"]:
        for suit in SUITS:
            if suits.count(suit) == 4:
                outs += 9  # 13 cards in suit - 4 we have
    
    # Straight draw (simplified)
    if target in ["straight", "any"]:
        values = sorted([c.value for c in all_cards])
        # Check for open-ended
        if len(values) >= 4:
            gaps = [values[i+1] - values[i] for i in range(len(values)-1)]
            if 1 in gaps:
                outs += 8  # Simplified
    
    return outs
