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
        """Shuffle deck and deal cards"""
        random.shuffle(self.deck)
        
        if self.num_players == 2:
            # Deal 4+4 cards to each player
            for i in range(2):
                for _ in range(4):
                    for player in self.players:
                        self.hands[player].append(self.deck.pop())
            
            # Trump indicator
            self.trump_indicator = self.deck.pop()
            
            # Deal final 4 cards to each player
            for _ in range(4):
                for player in self.players:
                    self.hands[player].append(self.deck.pop())
            
            # Remaining cards form talon
            self.talon = self.deck[:]
            
        else:  # 3-4 players
            # Deal 6 cards to each active player
            active_players = self.players[:3] if self.num_players == 4 else self.players
            for _ in range(6):
                for player in active_players:
                    self.hands[player].append(self.deck.pop())
            
            # Trump indicator
            self.trump_indicator = self.deck.pop()
            
            # Deal final 3 cards
            for _ in range(3):
                for player in active_players:
                    self.hands[player].append(self.deck.pop())
            
            # Remaining cards form talon
            self.talon = self.deck[:]
    
    def conduct_bidding(self) -> bool:
        """Conduct the bidding phase"""
        non_dealer = (self.current_dealer + 1) % len(self.players)
        
        print(f"Trump indicator: {self.trump_indicator}")
        print(f"Indicated trump suit: {self.trump_indicator.suit.value}")
        
        # Phase 1: Accept indicated trump
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
        for player in self.players:
            for _ in range(4):
                if self.talon:
                    self.hands[player].append(self.talon.pop())
        
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
    
    def find_sequences(self, cards: List[Card]) -> List[Meld]:
        """Find all sequences in a hand"""
        sequences = []
        suits = {}
        
        # Group cards by suit
        for card in cards:
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        # Sort cards in each suit
        for suit in suits:
            suits[suit].sort(key=lambda c: c.rank.value)
            
            # Find consecutive sequences
            current_seq = [suits[suit][0]]
            for i in range(1, len(suits[suit])):
                if suits[suit][i].rank.value == suits[suit][i-1].rank.value + 1:
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
            print(f"Hand: {[f'{j}: {card}' for j, card in enumerate(self.hands[current_player])]}")
            
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
    
    def calculate_game_points(self, player: str) -> int:
        """Calculate total game points for a player"""
        card_points = 0
        for card in self.tricks[player]:
            is_trump = (self.trump_suit is not None and card.suit == self.trump_suit)
            card_points += self._get_card_points(card, is_trump)
        
        # Add 10 points for last trick (simplified)
        game_points = card_points
        
        # Add meld points (simplified - would need to track actual melds)
        sequences = self.find_sequences(self.hands[player] + self.tricks[player])
        vannaks = self.find_vannaks(self.hands[player] + self.tricks[player])
        
        for seq in sequences:
            game_points += seq.points
        for vannak in vannaks:
            game_points += vannak.points
        
        return game_points
    
    def play_game(self):
        """Play a complete game"""
        print("=== ALSÓS CARD GAME ===")
        print(f"Playing with {self.num_players} players")
        
        # Deal cards
        self.shuffle_and_deal()
        
        # Show hands
        for player in self.players:
            print(f"\n{player}'s hand: {self.hands[player]}")
        
        # Bidding
        if not self.conduct_bidding():
            print("Bidding failed")
            return
        
        print(f"\nGame type: {self.game_type.value}")
        if self.trump_suit:
            print(f"Trump suit: {self.trump_suit.value}")
        if self.taker:
            print(f"Taker: {self.taker}")
        
        # Play tricks
        current_leader = self.players[(self.current_dealer + 1) % len(self.players)]
        trick_num = 1
        
        while any(self.hands[player] for player in self.players):
            current_leader = self.play_trick(current_leader, trick_num)
            trick_num += 1
        
        # Calculate final scores
        print("\n=== FINAL RESULTS ===")
        for player in self.players:
            points = self.calculate_game_points(player)
            self.scores[player] = points
            print(f"{player}: {points} points")
        
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