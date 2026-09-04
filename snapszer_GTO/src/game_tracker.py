"""
Schnapsen Match State Tracker & Rule Evaluator
Tracks cards seen, scores, unseen deck cards, and trick history.
"""

from typing import List, Dict, Set, Optional, Tuple
from schnapsen.game import Suit, Rank

CARD_POINTS = {
    "ACE": 11,
    "TEN": 10,
    "KING": 4,
    "QUEEN": 3,
    "JACK": 2,
}

ALL_20_CARDS = [
    f"{suit}_{rank}"
    for suit in ["HEARTS", "DIAMONDS", "SPADES", "CLUBS"]
    for rank in ["ACE", "TEN", "KING", "QUEEN", "JACK"]
]

SUIT_HU = {"HEARTS": "Piros", "DIAMONDS": "Tök", "SPADES": "Zöld", "CLUBS": "Makk"}
RANK_HU = {"ACE": "Ász", "TEN": "Tízes", "KING": "Király", "QUEEN": "Felső", "JACK": "Alsó"}


def to_hu(card_name: Optional[str]) -> str:
    if not card_name:
        return "Ismeretlen"
    parts = card_name.split("_")
    if len(parts) == 2 and parts[0] in SUIT_HU and parts[1] in RANK_HU:
        return f"{SUIT_HU[parts[0]]} {RANK_HU[parts[1]]}"
    return card_name


def get_card_value(card_name: Optional[str]) -> int:
    if not card_name:
        return 0
    parts = card_name.split("_")
    if len(parts) == 2:
        return CARD_POINTS.get(parts[1], 0)
    return 0


def determine_trick_winner(leader_card: str, follower_card: str, trump_suit: str) -> str:
    """
    Returns 'LEADER' or 'FOLLOWER' based on standard Schnapsen trick rules.
    """
    l_suit, l_rank = leader_card.split("_")
    f_suit, f_rank = follower_card.split("_")

    l_val = CARD_POINTS[l_rank]
    f_val = CARD_POINTS[f_rank]

    # If follower plays trump and leader didn't play trump -> Follower wins
    if f_suit == trump_suit and l_suit != trump_suit:
        return "FOLLOWER"

    # If both played same suit -> higher point value wins
    if f_suit == l_suit:
        return "FOLLOWER" if f_val > l_val else "LEADER"

    # Follower played different non-trump suit -> Leader wins
    return "LEADER"


class SchnapsenTracker:
    """
    Maintains the persistent game state across tricks in a Schnapsen match.
    """

    def __init__(self):
        self.reset_match()

    def reset_match(self):
        self.trump_card: Optional[str] = None
        self.trump_suit: Optional[str] = None
        self.my_score: int = 0
        self.opp_score: int = 0
        self.my_tricks_count: int = 0
        self.opp_tricks_count: int = 0
        self.played_cards: Set[str] = set()
        self.my_current_hand: List[str] = []
        self.trick_history: List[Dict] = []
        self.talon_closed: bool = False

    def set_trump(self, card_name: str):
        if not self.trump_card and card_name:
            self.trump_card = card_name
            self.trump_suit = card_name.split("_")[0]

    def update_my_hand(self, detected_cards: List[str]):
        self.my_current_hand = [c for c in detected_cards if c]

    def record_trick(self, leader: str, leader_card: str, follower_card: str):
        """
        Records a completed trick, awards points, and marks cards as played.
        leader: 'ME' or 'OPP'
        """
        if not leader_card or not follower_card or not self.trump_suit:
            return

        self.played_cards.add(leader_card)
        self.played_cards.add(follower_card)

        winner_side = determine_trick_winner(leader_card, follower_card, self.trump_suit)
        actual_winner = leader if winner_side == "LEADER" else ("OPP" if leader == "ME" else "ME")

        trick_pts = get_card_value(leader_card) + get_card_value(follower_card)

        if actual_winner == "ME":
            self.my_score += trick_pts
            self.my_tricks_count += 1
        else:
            self.opp_score += trick_pts
            self.opp_tricks_count += 1

        self.trick_history.append({
            "leader": leader,
            "leader_card": leader_card,
            "follower_card": follower_card,
            "winner": actual_winner,
            "points": trick_pts
        })

    def get_unseen_cards(self) -> List[str]:
        """
        Returns cards that are still in the deck or in the opponent's hand.
        """
        known = set(self.my_current_hand) | self.played_cards
        if self.trump_card:
            known.add(self.trump_card)
        unseen = [c for c in ALL_20_CARDS if c not in known]
        return sorted(unseen, key=lambda c: (c.split("_")[0], -get_card_value(c)))

    def print_dashboard(self, opp_lead_card: Optional[str] = None):
        """
        Prints a beautiful, comprehensive terminal dashboard.
        """
        trump_str = f"{SUIT_HU.get(self.trump_suit, self.trump_suit)} ({to_hu(self.trump_card)})" if self.trump_card else "Keresés..."
        unseen = self.get_unseen_cards()

        print("\n" + "=" * 68)
        print("  ♣️ ♦️ ♥️ ♠️   SCHNAPSEN MECCS ÉLŐ KÖVETŐ & GTO AGY   ♠️ ♥️ ♦️ ♣️")
        print("=" * 68)
        print(f"ADU SZÍN: {trump_str.upper()} | Állapot: {'ZÁRT TALON (2. fázis)' if self.talon_closed else 'NYITOTT TALON (1. fázis)'}")
        print("-" * 68)
        print(f"PONTÁLLÁS (66-ig):")
        print(f"  🟢 TE:       {self.my_score:2d} pont | {self.my_tricks_count} ütés")
        print(f"  🔴 ELLENFÉL: {self.opp_score:2d} pont | {self.opp_tricks_count} ütés")
        print("-" * 68)
        print(f"KEZEDBEN LÉVŐ LAPOK ({len(self.my_current_hand)} db):")
        for idx, c in enumerate(self.my_current_hand, 1):
            val = get_card_value(c)
            is_trump = " [ADU]" if self.trump_suit and c.startswith(self.trump_suit) else ""
            print(f"  {idx}. {to_hu(c):15} ({val:2d} pont){is_trump}")

        print("-" * 68)
        if opp_lead_card:
            print(f"⚡ ELLENFÉL HÍVÁSA AZ ASZTALON: {to_hu(opp_lead_card)} ({get_card_value(opp_lead_card)} pont)")
        else:
            print("⚡ TE HÍVSZ AZ ASZTALRA (Nincs még kijátszott lap)")

        print("-" * 68)
        unseen_hu = [f"{to_hu(c)} ({get_card_value(c)}p)" for c in unseen]
        print(f"ISMERETLEN LAPOK (Pakliban vagy ellenfélnél - {len(unseen)} db):")
        # Print nicely wrapped
        for i in range(0, len(unseen_hu), 4):
            print("   " + ", ".join(unseen_hu[i:i+4]))
        print("=" * 68 + "\n")
