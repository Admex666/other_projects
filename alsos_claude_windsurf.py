import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

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

@dataclass
class Card:
    suit: Suit
    rank: Rank
    
    def __str__(self):
        return f"{self.rank.name} of {self.suit.value}"
    
    def __repr__(self):
        return self.__str__()

class GameType(Enum):
    TRUMP = "Trump"
    NO_TRUMP = "No Trump"
    BETLI = "Betli"
    KLOPITZKY = "Klopitzky"

class Meld:
    def __init__(self, name: str, cards: List[Card], points: int):
        self.name = name
        self.cards = cards
        self.points = points
    
    def __str__(self):
        return f"{self.name} ({self.points} points): {self.cards}"

# Add this enum class
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

# Add this dictionary for bonus points
BONUS_POINTS = {
    BonusType.KASSZA: {'back': 4, 'front': 2},
    BonusType.ABSZOLUT: {'back': 6, 'front': 3},
    BonusType.HUNDRED_EIGHTY: {'back': 8, 'front': 4},
    BonusType.TWO_HUNDRED: {'back': 8, 'front': 4},
    BonusType.FOUR_ACES: {'back': 8, 'front': 4},
    BonusType.TRULL: {'back': 4, 'front': 2},
    BonusType.ULTIMATE: {'back': 10, 'front': 5},
    BonusType.FAMILY: {'back': 4, 'front': 2},
    BonusType.ALL_TRUMPS: {'back': 12, 'front': 6},
    BonusType.VOLAT: {'back': 20, 'front': 10},
}

class AlsosGame:
    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self.deck = self._create_deck()
        self.players = [f"Player {i+1}" for i in range(num_players)]
        self.hands = {player: [] for player in self.players}
        self.talon = []
        self.trump_suit = None
        self.trump_indicator = None
        self.game_type = None
        self.taker = None
        self.current_dealer = 0
        self.tricks = {player: [] for player in self.players}
        self.scores = {player: 0 for player in self.players}
        self.bonus_announcements = {}
    
    SUIT_ORDER = {
        Suit.HEARTS: 4,
        Suit.BELLS: 3,
        Suit.LEAVES: 2,
        Suit.ACORNS: 1
    }    
    
    def _create_deck(self) -> List[Card]:
        """Create a 32-card Hungarian deck"""
        deck = []
        for suit in Suit:
            for rank in [Rank.VII, Rank.VIII, Rank.IX, Rank.X, 
                        Rank.UNDER, Rank.OVER, Rank.KING, Rank.ACE]:
                deck.append(Card(suit, rank))
        return deck
    
    def _get_card_points(self, card: Card, is_trump: bool = False) -> int:
        """Get points for a card based on trump status"""
        if self.game_type == GameType.TRUMP and is_trump:
            trump_points = {
                Rank.UNDER: 20, Rank.IX: 14, Rank.ACE: 11, Rank.X: 10,
                Rank.KING: 4, Rank.OVER: 3, Rank.VIII: 0, Rank.VII: 0
            }
            return trump_points.get(card.rank, 0)
        else:
            regular_points = {
                Rank.ACE: 11, Rank.X: 10, Rank.KING: 4, Rank.OVER: 3,
                Rank.UNDER: 2, Rank.IX: 0, Rank.VIII: 0, Rank.VII: 0
            }
            return regular_points.get(card.rank, 0)
    
    def _format_card_with_points(self, card: Card) -> str:
        """Format a card with its point value"""
        is_trump = (self.game_type == GameType.TRUMP and card.suit == self.trump_suit)
        points = self._get_card_points(card, is_trump)
        return f"{card} ({points} points)"
    
    def _get_card_value_for_comparison(self, card: Card) -> int:
        """Get card value for trick comparison"""
        if self.game_type == GameType.TRUMP and card.suit == self.trump_suit:
            trump_order = {
                Rank.UNDER: 8, Rank.IX: 7, Rank.ACE: 6, Rank.X: 5,
                Rank.KING: 4, Rank.OVER: 3, Rank.VIII: 2, Rank.VII: 1
            }
            return trump_order.get(card.rank, 0) + 100  # Trump bonus
        else:
            regular_order = {
                Rank.ACE: 8, Rank.X: 7, Rank.KING: 6, Rank.OVER: 5,
                Rank.UNDER: 4, Rank.IX: 3, Rank.VIII: 2, Rank.VII: 1
            }
            return regular_order.get(card.rank, 0)
    
    def shuffle_and_deal(self):
        """Shuffle deck and deal initial cards"""
        random.shuffle(self.deck)
        
        if self.num_players == 2:
            # Deal exactly 8 cards to each player initially
            for _ in range(2):  # Deal in 2 rounds of 4 cards each
                for player in self.players:
                    for _ in range(4):
                        if self.deck:
                            self.hands[player].append(self.deck.pop())
            
            # Sort hands after initial deal
            for player in self.players:
                self.hands[player] = self._sort_cards(self.hands[player])
            
            # Trump indicator
            self.trump_indicator = self.deck.pop()
            
            # Remaining cards form talon
            self.talon = self.deck[:]
            
        else:  # 3-4 players
            # Deal exactly 6 cards to each active player initially
            active_players = self.players[:3] if self.num_players == 4 else self.players
            for player in active_players:
                for _ in range(6):
                    if self.deck:
                        self.hands[player].append(self.deck.pop())
            
            # Sort hands after initial deal
            for player in active_players:
                self.hands[player] = self._sort_cards(self.hands[player])
            
            # Trump indicator
            self.trump_indicator = self.deck.pop()
            
            # Remaining cards form talon
            self.talon = self.deck[:]
    
    def conduct_bidding(self) -> bool:
        """Conduct the bidding phase"""
        non_dealer = (self.current_dealer + 1) % len(self.players)
        
        # Phase 1: Accept indicated trump
        print(f"Trump indicator: {self.trump_indicator}")
        print(f"Indicated trump suit: {self.trump_indicator.suit.value}")
        
        print(f"\n{self.players[non_dealer]}, do you accept {self.trump_indicator.suit.value} as trump? (y/n)")
        response = input().lower()
        if response == 'y':
            self.trump_suit = self.trump_indicator.suit
            self.game_type = GameType.TRUMP
            self.taker = self.players[non_dealer]
            return True
        
        print(f"{self.players[self.current_dealer]}, do you accept {self.trump_indicator.suit.value} as trump? (y/n)")
        response = input().lower()
        if response == 'y':
            self.trump_suit = self.trump_indicator.suit
            self.game_type = GameType.TRUMP
            self.taker = self.players[self.current_dealer]
            return True
        
        # Phase 2: Bid different trump suits
        suit_priority = [Suit.ACORNS, Suit.LEAVES, Suit.BELLS, Suit.HEARTS]
        available_suits = [s for s in suit_priority if s != self.trump_indicator.suit]
        
        for suit in available_suits:
            print(f"\n{self.players[non_dealer]}, bid {suit.value} as trump? (y/n)")
            response = input().lower()
            if response == 'y':
                self.trump_suit = suit
                self.game_type = GameType.TRUMP
                self.taker = self.players[non_dealer]
                return True
            
            print(f"{self.players[self.current_dealer]}, bid {suit.value} as trump? (y/n)")
            response = input().lower()
            if response == 'y':
                self.trump_suit = suit
                self.game_type = GameType.TRUMP
                self.taker = self.players[self.current_dealer]
                return True
        
        # Phase 3: No-trump
        print(f"\n{self.players[non_dealer]}, bid No-Trump? (y/n)")
        response = input().lower()
        if response == 'y':
            self.game_type = GameType.NO_TRUMP
            self.taker = self.players[non_dealer]
            return True
        
        print(f"{self.players[self.current_dealer]}, bid No-Trump? (y/n)")
        response = input().lower()
        if response == 'y':
            self.game_type = GameType.NO_TRUMP
            self.taker = self.players[self.current_dealer]
            return True
        
        # Phase 4: Betli (after picking up final 4 cards)
        print("\nPicking up final 4 cards for Betli bidding...")
        
        print(f"\n{self.players[non_dealer]}, bid Betli? (y/n)")
        response = input().lower()
        if response == 'y':
            self.game_type = GameType.BETLI
            self.taker = self.players[non_dealer]
            return True
        
        print(f"{self.players[self.current_dealer]}, bid Betli? (y/n)")
        response = input().lower()
        if response == 'y':
            self.game_type = GameType.BETLI
            self.taker = self.players[self.current_dealer]
            return True
        
        # Phase 5: Klopitzky
        print("\nNo bids made. Playing Klopitzky.")
        self.game_type = GameType.KLOPITZKY
        return True
    
    def _deal_remaining_cards(self):
        """Deal remaining cards to players after trump suit is decided"""
        if self.num_players == 2:
            # Deal 4 more cards to each player (total 12)
            for player in self.players:
                remaining_cards = 4
                for _ in range(remaining_cards):
                    if self.talon:  # Check if there are cards left
                        self.hands[player].append(self.talon.pop())
                # Sort hand after adding cards
                self.hands[player] = self._sort_cards(self.hands[player])
        else:  # 3-4 players
            # Deal 3 more cards to each active player (total 9)
            active_players = self.players[:3] if self.num_players == 4 else self.players
            for player in active_players:
                remaining_cards = 3
                for _ in range(remaining_cards):
                    if self.talon:  # Check if there are cards left
                        self.hands[player].append(self.talon.pop())
                # Sort hand after adding cards
                self.hands[player] = self._sort_cards(self.hands[player])
    
    def find_sequences(self, cards: List[Card]) -> List[Meld]:
        """Find all sequences in a hand where cards of same suit have consecutive ranks"""
        sequences = []
        suits = {}
        
        # Group cards by suit
        for card in cards:
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        # Sort cards in each suit by rank value
        for suit in suits:
            suits[suit].sort(key=lambda c: c.rank.value)
            
            # Find consecutive sequences
            current_seq = [suits[suit][0]]
            for i in range(1, len(suits[suit])):
                if suits[suit][i].rank.value == current_seq[-1].rank.value + 1:
                    current_seq.append(suits[suit][i])
                else:
                    if len(current_seq) >= 3:
                        sequences.append(self._create_sequence_meld(current_seq))
                    current_seq = [suits[suit][i]]
            
            if len(current_seq) >= 3:
                sequences.append(self._create_sequence_meld(current_seq))
        
        return sequences
    
    def _create_sequence_meld(self, cards: List[Card]) -> Meld:
        """Create a sequence meld from cards"""
        length = len(cards)
        if length == 3:
            return Meld("Terc", cards, 20)
        elif length == 4:
            return Meld("Kvart", cards, 50)
        else:
            return Meld("Long Sequence", cards, 100)
    
    def find_vannaks(self, cards: List[Card]) -> List[Meld]:
        """Find all four-of-a-kind (vannak) melds"""
        vannaks = []
        ranks = {}
        
        for card in cards:
            if card.rank not in ranks:
                ranks[card.rank] = []
            ranks[card.rank].append(card)
        
        for rank, rank_cards in ranks.items():
            if len(rank_cards) == 4:
                vannaks.append(Meld("Vannak", rank_cards, 80))
        
        return vannaks
    
    def conduct_back_announcements(self):
        """Handle bonus announcements after bidding but before dealing remaining cards"""
        print("\n=== BACK ANNOUNCEMENTS (Double Value) ===")
        self.bonus_announcements = {player: [] for player in self.players}
        
        # Start with taker
        for player in [self.taker] + [p for p in self.players if p != self.taker]:
            print(f"\n{player}'s turn to announce bonuses (back announcements)")
            self.announce_bonuses(player, 'back')
    
    def conduct_front_announcements(self):
        """Handle bonus announcements after dealing remaining cards"""
        print("\n=== FRONT ANNOUNCEMENTS ===")
        
        # Start with taker
        for player in [self.taker] + [p for p in self.players if p != self.taker]:
            print(f"\n{player}'s turn to announce bonuses (front announcements)")
            self.announce_bonuses(player, 'front')
    
    def announce_bonuses(self, player: str, phase: str):
        """Handle bonus announcements for a player in a specific phase"""
        print(f"Available bonuses:")
        for i, bonus in enumerate(BonusType):
            print(f"{i+1}: {bonus.value}")
        
        print("Enter bonus numbers to announce (comma separated), or 'pass' to skip:")
        choice = input().strip()
        
        if choice.lower() == 'pass':
            print(f"{player} passes")
            return
        
        try:
            choices = [int(c.strip()) for c in choice.split(',')]
            for choice in choices:
                if 1 <= choice <= len(BonusType):
                    bonus_type = list(BonusType)[choice-1]
                    # Kassza can only be announced by taker
                    if bonus_type == BonusType.KASSZA and player != self.taker:
                        print("Only taker can announce Kassza!")
                        continue
                    
                    self.bonus_announcements[player].append((bonus_type, phase))
                    print(f"{player} announces {bonus_type.value} ({phase})")
        except ValueError:
            print("Invalid input, skipping bonuses")
    
    def play_trick(self, lead_player: str, trick_num: int) -> str:
        """Play a single trick"""
        trick_cards = {}
        current_player = lead_player
        
        print(f"\n--- Trick {trick_num} ---")
        print(f"{lead_player} leads")
        
        for i in range(len(self.players)):
            if not self.hands[current_player]:
                break
                
            print(f"\n{current_player}'s turn")
            print(f"Hand:")
            for j, card in enumerate(self.hands[current_player]):
                print(f"{j}: {self._format_card_with_points(card)}")
            
            if i == 0:  # First card played
                print("Choose a card to play (enter number): ")
                try:
                    choice = int(input())
                    played_card = self.hands[current_player].pop(choice)
                    trick_cards[current_player] = played_card
                    print(f"{current_player} plays {played_card}")
                except (ValueError, IndexError):
                    print("Invalid choice, playing first card")
                    played_card = self.hands[current_player].pop(0)
                    trick_cards[current_player] = played_card
                    print(f"{current_player} plays {played_card}")
            else:
                # Must follow suit if possible, otherwise must play trump if available
                led_suit = list(trick_cards.values())[0].suit
                valid_cards = [card for card in self.hands[current_player] if card.suit == led_suit]
                
                if not valid_cards:
                    # Cannot follow suit - must play trump if available
                    if self.trump_suit and self.game_type == GameType.TRUMP:
                        trump_cards = [card for card in self.hands[current_player] if card.suit == self.trump_suit]
                        if trump_cards:
                            valid_cards = trump_cards
                            print(f"Cannot follow {led_suit.value} - must play trump!")
                        else:
                            valid_cards = self.hands[current_player]  # No trumps, can play any card
                            print(f"Cannot follow {led_suit.value} and no trumps - can play any card")
                    else:
                        valid_cards = self.hands[current_player]  # No trump suit in game, can play any card
                        print(f"Cannot follow {led_suit.value} - can play any card")
                else:
                    print(f"Must follow {led_suit.value}")
                
                # Show valid cards in sorted order
                valid_cards = self._sort_cards(valid_cards)
                print(f"Valid cards: {[f'{j}: {card}' for j, card in enumerate(valid_cards)]}")
                print("Choose a card to play (enter number): ")
                
                try:
                    choice = int(input())
                    if choice < len(valid_cards):
                        played_card = valid_cards[choice]
                        self.hands[current_player].remove(played_card)
                        trick_cards[current_player] = played_card
                        print(f"{current_player} plays {played_card}")
                    else:
                        played_card = valid_cards[0]
                        self.hands[current_player].remove(played_card)
                        trick_cards[current_player] = played_card
                        print(f"Invalid choice, playing {played_card}")
                except (ValueError, IndexError):
                    played_card = valid_cards[0]
                    self.hands[current_player].remove(played_card)
                    trick_cards[current_player] = played_card
                    print(f"Invalid choice, playing {played_card}")
            
            # Next player
            current_player = self.players[(self.players.index(current_player) + 1) % len(self.players)]
        
        # Determine winner
        winner = self._determine_trick_winner(trick_cards, list(trick_cards.values())[0].suit)
        self.tricks[winner].extend(trick_cards.values())
        print(f"\n{winner} wins the trick!")
        
        return winner
    
    def _determine_trick_winner(self, trick_cards: Dict[str, Card], led_suit: Suit) -> str:
        """Determine the winner of a trick"""
        best_player = None
        best_value = -1
        
        for player, card in trick_cards.items():
            card_value = self._get_card_value_for_comparison(card)
            
            # If card doesn't follow suit and isn't trump, it can't win
            if card.suit != led_suit and (self.trump_suit is None or card.suit != self.trump_suit):
                card_value = -1
            
            if card_value > best_value:
                best_value = card_value
                best_player = player
        
        return best_player
    
    def calculate_game_points(self, player: str) -> Tuple[int, int, int]:
        """Calculate points for a player and return (card_points, meld_points, bonus_points)"""
        # Calculate card points
        card_points = sum(self._get_card_points(c, c.suit == self.trump_suit) for c in self.tricks[player])
        
        return card_points
    
    def play_game(self):
        """Play a complete game"""
        print("=== ALSÓS CARD GAME ===")
        print(f"Playing with {self.num_players} players")
        
        # Deal cards
        self.shuffle_and_deal()
        
        # Show hands
        for player in self.players:
            print(f"\n{player}'s hand:")
            for i, card in enumerate(self.hands[player]):
                print(f"{i}: {self._format_card_with_points(card)}")
        
        # Bidding
        if not self.conduct_bidding():
            print("Bidding failed")
            return
        
        print(f"\nGame type: {self.game_type.value}")
        if self.trump_suit:
            print(f"Trump suit: {self.trump_suit.value}")
        if self.taker:
            print(f"Taker: {self.taker}")
        
        # Back announcements (before dealing remaining cards)
        if self.game_type not in [GameType.BETLI, GameType.KLOPITZKY]:
            self.conduct_back_announcements()
        
        # Deal remaining cards
        self._deal_remaining_cards()
        
        # Show updated hands
        for player in self.players:
            print(f"\n{player}'s hand after dealing:")
            for i, card in enumerate(self.hands[player]):
                print(f"{i}: {self._format_card_with_points(card)}")
        
        # Front announcements (after dealing remaining cards)
        if self.game_type not in [GameType.BETLI, GameType.KLOPITZKY]:
            self.conduct_front_announcements()
        
        # Initialize current_leader - in Klopitzky it's the dealer's right, otherwise non-dealer
        if self.game_type == GameType.KLOPITZKY:
            current_leader = self.players[(self.current_dealer + 1) % len(self.players)]
        else:
            current_leader = self.players[(self.current_dealer + 1) % len(self.players)]  # Same for now, adjust if needed
        
        # Evaluate melds before playing any tricks (based on initial hand)
        self.evaluate_melds()

        # Play first trick
        current_leader = self.play_trick(current_leader, 1)
        
        # Continue with remaining tricks
        for trick_num in range(2, 13):
            if any(self.hands[player] for player in self.players):
                current_leader = self.play_trick(current_leader, trick_num)
        
        # Calculate final scores
        print("\n=== FINAL RESULTS ===")
        for player in self.players:
            # Get card points for the tricks won
            card_pts = self.calculate_game_points(player)

            # self.scores[player] already contains the meld points (Vannak, Sequences)
            # that were added in the evaluate_melds method.
            total_score = card_pts + self.scores[player]

            print(f"{player}:")
            print(f"  Card points from tricks: {card_pts}")
            print(f"  Meld points from declarations: {self.scores[player]}") # This includes Vannak and Sequence points
            print(f"  TOTAL: {total_score}")
        
        # Determine winner based on game type
        if self.game_type == GameType.BETLI:
            if len(self.tricks[self.taker]) == 0:
                print(f"{self.taker} wins Betli!")
            else:
                print(f"{self.taker} fails Betli!")
        elif self.game_type == GameType.KLOPITZKY:
            min_tricks = min(len(self.tricks[player]) for player in self.players)
            winners = [player for player in self.players if len(self.tricks[player]) == min_tricks]
            if len(winners) == 1:
                print(f"{winners[0]} wins Klopitzky with {min_tricks} tricks!")
            else:
                print("Klopitzky is a tie!")
        else:
            if self.taker:
                taker_points = self.scores[self.taker]
                opponent_points = max(self.scores[player] for player in self.players if player != self.taker)
                if taker_points > opponent_points:
                    print(f"{self.taker} wins the game!")
                else:
                    print(f"{self.taker} fails to make the game!")
        
    def evaluate_bonuses(self, player: str) -> int:
        """Evaluate bonus announcements for a player and return points"""
        bonus_points = 0
        player_tricks = self.tricks[player]
        
        for bonus_type, phase in self.bonus_announcements.get(player, []):
            points = BONUS_POINTS[bonus_type][phase]
            success = False
            
            # Check bonus conditions
            if bonus_type == BonusType.KASSZA:
                # Kassza: Winning game with Béla meld (King and Over of trumps)
                if self.game_type == GameType.TRUMP:
                    has_bela = (any(c.rank == Rank.KING and c.suit == self.trump_suit for c in player_tricks) and
                               any(c.rank == Rank.OVER and c.suit == self.trump_suit for c in player_tricks))
                    taker_points = self.calculate_game_points(self.taker)
                    opponent_points = max(self.calculate_game_points(p) for p in self.players if p != self.taker)
                    success = has_bela and (taker_points > opponent_points)
            
            elif bonus_type == BonusType.ABSZOLUT:
                # Abszolút: 82/66 card points (trump/no trump)
                card_points = sum(self._get_card_points(c, c.suit == self.trump_suit) for c in player_tricks)
                if self.game_type == GameType.TRUMP:
                    success = card_points >= 82
                else:  # No Trump
                    success = card_points >= 66
                    
            elif bonus_type == BonusType.HUNDRED_EIGHTY:
                # 100/80 card points (trump/no trump)
                card_points = sum(self._get_card_points(c, c.suit == self.trump_suit) for c in player_tricks)
                if self.game_type == GameType.TRUMP:
                    success = card_points >= 100
                else:  # No Trump
                    success = card_points >= 80
                    
            elif bonus_type == BonusType.TWO_HUNDRED:
                # 200/180 game points (trump/no trump)
                game_points = self.calculate_game_points(player)
                if self.game_type == GameType.TRUMP:
                    success = game_points >= 200
                else:  # No Trump
                    success = game_points >= 180
                    
            elif bonus_type == BonusType.FOUR_ACES:
                # Four Aces: Win all 4 Aces
                aces = [c for c in player_tricks if c.rank == Rank.ACE]
                success = len(aces) == 4
                    
            elif bonus_type == BonusType.TRULL:
                # Trull: Under, IX and VII of trumps won
                if self.game_type == GameType.TRUMP:
                    has_under = any(c.rank == Rank.UNDER and c.suit == self.trump_suit for c in player_tricks)
                    has_ix = any(c.rank == Rank.IX and c.suit == self.trump_suit for c in player_tricks)
                    has_vii = any(c.rank == Rank.VII and c.suit == self.trump_suit for c in player_tricks)
                    success = has_under and has_ix and has_vii
                    
            elif bonus_type == BonusType.ULTIMATE:
                # Ulti: Last trick won by VII of trumps
                if player_tricks and self.game_type == GameType.TRUMP:
                    last_card = player_tricks[-1]  # Last card won in last trick
                    success = (last_card.rank == Rank.VII and last_card.suit == self.trump_suit)
                    
            elif bonus_type == BonusType.FAMILY:
                # Family: Ace, King and Over trumps won
                if self.game_type == GameType.TRUMP:
                    has_ace = any(c.rank == Rank.ACE and c.suit == self.trump_suit for c in player_tricks)
                    has_king = any(c.rank == Rank.KING and c.suit == self.trump_suit for c in player_tricks)
                    has_over = any(c.rank == Rank.OVER and c.suit == self.trump_suit for c in player_tricks)
                    success = has_ace and has_king and has_over
                    
            elif bonus_type == BonusType.ALL_TRUMPS:
                # All trumps: Under, IX, Ace, X, King, Over of trumps won
                if self.game_type == GameType.TRUMP:
                    required_ranks = {Rank.UNDER, Rank.IX, Rank.ACE, Rank.X, Rank.KING, Rank.OVER}
                    trump_cards = [c for c in player_tricks if c.suit == self.trump_suit]
                    collected_ranks = {c.rank for c in trump_cards}
                    success = required_ranks.issubset(collected_ranks)
                    
            elif bonus_type == BonusType.VOLAT:
                # Volát: Win all tricks
                total_tricks = sum(len(t) for t in self.tricks.values())
                success = len(player_tricks) == total_tricks
                
            if success:
                print(f"{player} succeeded {bonus_type.value} ({phase}) +{points}")
                bonus_points += points
            else:
                print(f"{player} failed {bonus_type.value} ({phase}) -{points}")
                bonus_points -= points
                    
        return bonus_points
    
    def evaluate_melds(self):
        """Evaluate all melds after first trick to determine which players score points"""
        # Collect all sequences and vannaks from all players
        all_sequences = []
        all_vannaks = []
        
        for player in self.players:
            # Find sequences and vannaks in player's hand + won tricks
            player_cards = self.hands[player] + self.tricks[player]
            sequences = self.find_sequences(player_cards)
            vannaks = self.find_vannaks(player_cards)
            
            # Add player info to melds
            for seq in sequences:
                all_sequences.append((player, seq))
            for vannak in vannaks:
                all_vannaks.append((player, vannak))
        
        # Evaluate sequences - only the strongest sequence scores points
        if all_sequences:
            # Find all sequences and sort them by length (descending), then by highest card
            all_sequences.sort(key=lambda x: (
                -len(x[1].cards),  # Longer sequences first
                -x[1].cards[-1].rank.value,  # Higher rank first
                -self.SUIT_ORDER[x[1].cards[-1].suit]  # Higher suit first
            ))
            
            # The first sequence in the sorted list is the winner
            winner, winning_seq = all_sequences[0]
            self.scores[winner] += winning_seq.points
            print(f"{winner} wins sequence contest with {winning_seq.name} (+{winning_seq.points})")
        
        # Evaluate vannaks - same logic as before
        if all_vannaks:
            # Find highest rank vannak
            highest_rank = None
            winning_vannak = None
            winner = None
            
            for player, vannak in all_vannaks:
                # Vannak cards are all same rank, just check first one
                card_rank = vannak.cards[0].rank
                
                if highest_rank is None:
                    highest_rank = card_rank
                    winning_vannak = vannak
                    winner = player
                else:
                    if self._get_card_value_for_comparison(vannak.cards[0]) > self._get_card_value_for_comparison(winning_vannak.cards[0]):
                        highest_rank = card_rank
                        winning_vannak = vannak
                        winner = player
            
            if winner:
                self.scores[winner] += winning_vannak.points
                print(f"{winner} wins vannak contest with {winning_vannak.name} (+{winning_vannak.points})")
            
    def _sort_cards(self, cards: List[Card]) -> List[Card]:
        """Sort cards by suit (hearts > bells > leaves > acorns) and point value (high to low)"""
        return sorted(cards, 
                     key=lambda c: (
                         -self.SUIT_ORDER[c.suit],  # Higher suit value first
                         -self._get_card_points(c, c.suit == self.trump_suit)  # Higher points first
                     ))
            
def main():
    print("Welcome to Alsós!")
    print("Choose number of players (2-4): ")
    try:
        num_players = int(input())
        if num_players < 2 or num_players > 4:
            num_players = 2
    except ValueError:
        num_players = 2
    
    game = AlsosGame(num_players)
    game.play_game()

if __name__ == "__main__":
    main()

