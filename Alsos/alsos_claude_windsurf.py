import random
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import uuid

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

# Define an interface or base class for player agents
class PlayerAgent:
    """Base class for player agents, defining decision-making methods."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        raise NotImplementedError

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        """Decide which bonuses to announce. Returns a comma-separated string of bonus numbers or 'pass'."""
        raise NotImplementedError

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        """Decide which card to play in a trick. Returns the Card object to play."""
        raise NotImplementedError

# A simple HumanPlayerAgent for interactive play
class HumanPlayerAgent(PlayerAgent):
    """An agent that prompts a human for input."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        # Determine the relevant context for the prompt based on what's passed
        if current_bid_context:
            prompt_context = f"for '{current_bid_context}'"
        else:
            # Fallback for initial trump indicator phase if context isn't explicitly passed
            trump_card_str = str(game_state.trump_indicator) if game_state.trump_indicator else "No indicator"
            prompt_context = f"accepting indicator '{trump_card_str}'"

        prompt = (f"{player_name}, {prompt_context}, "
                  f"do you accept/bid? ({'/'.join(options)}): ")
        
        while True:
            response = input(prompt).strip()
            if response in options:
                return response
            else:
                print(f"Invalid input. Please choose from: {', '.join(options)}")

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        print(f"\n{player_name}'s turn to announce bonuses ({game_state.current_bonus_phase})")
        print(f"Available bonuses:")
        for num, (bonus_type, phase) in available_bonuses_info:
            print(f"{num}: {bonus_type.value}")
        print("Enter bonus numbers to announce (comma separated), or 'pass' to skip:")
        return input().strip()

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        print(f"\n{player_name}'s turn")
        print(f"Hand:")
        current_hand = game_state.hands[player_name]
        for j, card in enumerate(current_hand):
            print(f"{j}: {game_state._format_card_with_points(card)}")
        
        # Display valid cards with their original indices from player's hand for human input
        valid_card_indices = []
        for card in valid_cards:
            try:
                valid_card_indices.append(current_hand.index(card))
            except ValueError:
                # Should not happen if valid_cards truly comes from current_hand
                pass 
        
        print(f"Valid cards (indices from hand): {[f'{idx}: {current_hand[idx]}' for idx in valid_card_indices]}")
        
        print("Choose a card to play (enter number): ")
        try:
            choice_idx = int(input())
            if choice_idx in valid_card_indices:
                return current_hand[choice_idx]
            else:
                print("Invalid choice, playing first valid card.")
                return valid_cards[0]
        except (ValueError, IndexError):
            print("Invalid input, playing first valid card.")
            return valid_cards[0]

# A simple RuleBasedPlayerAgent for simulation
class RuleBasedPlayerAgent(PlayerAgent):
    """An agent that makes simple rule-based decisions."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        # Get player's current hand
        hand = game_state.hands[player_name]
        trump_indicator_suit = game_state.trump_indicator.suit if game_state.trump_indicator else None

        # --- Basic Bidding Strategy ---

        # 1. Evaluate trump indicator suit
        if trump_indicator_suit:
            trump_cards_in_hand = [c for c in hand if c.suit == trump_indicator_suit]
            # If 'y' to accept trump indicator is an option and we have a decent number of trumps
            if 'y' in options and len(trump_cards_in_hand) >= 3:
                return 'y'

        # 2. Consider bidding other suits (simplified example, could be more complex)
        # For demonstration, let's say it prefers Hearts, then Bells, etc., if it has a strong hand in that suit
        preferred_suits_for_bidding = [Suit.HEARTS, Suit.BELLS, Suit.LEAVES, Suit.ACORNS]
        for suit in preferred_suits_for_bidding:
            if suit != trump_indicator_suit and suit.value in options:
                suit_cards_in_hand = [c for c in hand if c.suit == suit]
                # If we have X+ cards of a potential trump suit and high cards
                if len(suit_cards_in_hand) >= 2 and any(c.rank in [Rank.ACE, Rank.X, Rank.KING] for c in suit_cards_in_hand):
                    return suit.value # Bid this suit

        # 3. Consider No-Trump
        if 'No-Trump' in options:
            # Check for balanced hand with high cards, few singletons, no very weak suits
            has_strong_aces_tens = len([c for c in hand if c.rank in [Rank.ACE, Rank.X]]) >= 3
            if has_strong_aces_tens:
                return 'No-Trump'

        # 4. Consider Betli (simplified: if hand is very low on points)
        if 'Betli' in options:
            total_points = sum(game_state._get_card_points(c) for c in hand) # Assuming non-trump points
            if total_points < 30: # Very low point hand might be good for betli
                return 'Betli'

        # Default fallback (original logic, but less likely to be hit with better strategy)
        if 'n' in options: return 'n'
        return options[0] if options else 'pass'

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        # Simple rule: Announce any bonus available. For real ML, this would be a more complex decision.
        #if available_bonuses_info:
            # Example: Announce the first available bonus
        #    return str(available_bonuses_info[0][0])
        return 'pass'

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        if not valid_cards:
            return game_state.hands[player_name][0] # Fallback, should ideally not happen

        # For Betli, play the lowest possible card to avoid winning tricks
        if game_state.game_type == GameType.BETLI:
            # Sort by point value (ascending), then by rank (ascending)
            valid_cards.sort(key=lambda c: (game_state._get_card_points(c, False), c.rank.value))
            return valid_cards[0]

        # General strategy for Trump/No-Trump games:
        if not current_trick: # Leading the trick
            # Play a high card from your longest suit to try and establish control
            # Or play a low card if you want to save high cards for later
            
            # Simple version: Play highest point card from hand (can be refined)
            # Find the card with the highest points in hand (not just valid cards)
            best_card = None
            max_points = -1
            for card in game_state.hands[player_name]:
                points = game_state._get_card_points(card, card.suit == game_state.trump_suit)
                if points > max_points:
                    max_points = points
                    best_card = card
            return best_card if best_card else valid_cards[0] # Return the highest card from *hand*

        else: # Not leading the trick
            led_card = list(current_trick.values())[0]
            led_suit = led_card.suit
            
            # Find the current winning card in the trick
            trick_winner_card = None
            max_trick_value = -1
            for p, c in current_trick.items():
                val = game_state._get_card_value_for_comparison(c)
                if val > max_trick_value:
                    max_trick_value = val
                    trick_winner_card = c

            # Try to win the trick if possible and desirable
            for card in valid_cards:
                if game_state._get_card_value_for_comparison(card) > max_trick_value:
                    # If we can win with a valid card, play it.
                    # This could be refined: don't overplay, save trumps if unnecessary.
                    return card
            
            # If cannot win, play the lowest valid card to save higher cards
            # Sort valid cards by point value (ascending), then by rank (ascending)
            valid_cards.sort(key=lambda c: (game_state._get_card_points(c, c.suit == game_state.trump_suit), c.rank.value))
            return valid_cards[0] # Play the lowest point card if unable to win

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
    def __init__(self, num_players: int = 2, agents: Optional[Dict[str, 'PlayerAgent']] = None): # MODIFIED
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
        self.bonus_announcements = {player: [] for player in self.players}
        #  Store player agents. Default to HumanPlayerAgent if not provided.
        self.agents = agents if agents else {player: HumanPlayerAgent() for player in self.players} 
        self.current_bonus_phase = "" # New: To pass to bonus agent for context
        self.game_log = [] # New: To store game data for database
        self.game_id = None # New: To identify each game session
    
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
       """Conduct the bidding phase using player agents."""
       non_dealer_idx = (self.current_dealer + 1) % len(self.players)
       non_dealer = self.players[non_dealer_idx]
       dealer = self.players[self.current_dealer]

       print(f"Trump indicator: {self.trump_indicator}")
       print(f"Indicated trump suit: {self.trump_indicator.suit.value}")

       # Phase 1: Accept indicated trump
       # Pass the initial trump indicator as context for the 'y/n' question
       context_phase1 = f"accept {self.trump_indicator}"
       response = self.agents[non_dealer].choose_bid(self, non_dealer, ['y', 'n'], current_bid_context=context_phase1)
       print(f"{non_dealer} chose: {response}")
       if response.lower() == 'y':
           self.trump_suit = self.trump_indicator.suit
           self.game_type = GameType.TRUMP
           self.taker = non_dealer
           return True

       response = self.agents[dealer].choose_bid(self, dealer, ['y', 'n'], current_bid_context=context_phase1)
       print(f"{dealer} chose: {response}")
       if response.lower() == 'y':
           self.trump_suit = self.trump_indicator.suit
           self.game_type = GameType.TRUMP
           self.taker = dealer
           return True

       # Phase 2: Bid different trump suits
       suit_priority = [Suit.ACORNS, Suit.LEAVES, Suit.BELLS, Suit.HEARTS]
       available_bid_suits = [s for s in suit_priority if s != self.trump_indicator.suit]

       # For this phase, the prompt should indicate which *new* suit is being proposed
       for suit in available_bid_suits:
           context_phase2 = f"bid {suit.value} as trump" # NEW CONTEXT
           response = self.agents[non_dealer].choose_bid(self, non_dealer, ['y', 'n'], current_bid_context=context_phase2)
           print(f"{non_dealer} chose: {response}")
           if response.lower() == 'y':
               self.trump_suit = suit
               self.game_type = GameType.TRUMP
               self.taker = non_dealer
               return True

           response = self.agents[dealer].choose_bid(self, dealer, ['y', 'n'], current_bid_context=context_phase2)
           print(f"{dealer} chose: {response}")
           if response.lower() == 'y':
               self.trump_suit = suit
               self.game_type = GameType.TRUMP
               self.taker = dealer
               return True

       # Phase 3: No-trump
       context_phase3 = "bid No-Trump" # NEW CONTEXT
       response = self.agents[non_dealer].choose_bid(self, non_dealer, ['y', 'n'], current_bid_context=context_phase3)
       print(f"{non_dealer} chose: {response}")
       if response.lower() == 'y':
           self.game_type = GameType.NO_TRUMP
           self.taker = non_dealer
           return True

       response = self.agents[dealer].choose_bid(self, dealer, ['y', 'n'], current_bid_context=context_phase3)
       print(f"{dealer} chose: {response}")
       if response.lower() == 'y':
           self.game_type = GameType.NO_TRUMP
           self.taker = dealer
           return True

       # Phase 4: Betli (after picking up final 4 cards)
       print("\nPicking up final 4 cards for Betli bidding...")

       context_phase4 = "bid Betli" # NEW CONTEXT
       response = self.agents[non_dealer].choose_bid(self, non_dealer, ['y', 'n'], current_bid_context=context_phase4)
       print(f"{non_dealer} chose: {response}")
       if response.lower() == 'y':
           self.game_type = GameType.BETLI
           self.taker = non_dealer
           return True

       response = self.agents[dealer].choose_bid(self, dealer, ['y', 'n'], current_bid_context=context_phase4)
       print(f"{dealer} chose: {response}")
       if response.lower() == 'y':
           self.game_type = GameType.BETLI
           self.taker = dealer
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
        """Handle bonus announcements for a player in a specific phase using agents."""
        # print(f"Available bonuses:") # Keep for human, but not strictly needed for agents
        available_bonuses_info = []
        for i, bonus_type in enumerate(BonusType):
            # print(f"{i+1}: {bonus_type.value}") # Keep for human
            available_bonuses_info.append((i+1, (bonus_type, phase))) # Store (num, (BonusType, phase))

        self.current_bonus_phase = phase # Set this for agent to use
        choice = self.agents[player].choose_bonus_announcements(self, player, available_bonuses_info).strip() # MODIFIED

        if choice.lower() == 'pass':
            print(f"{player} passes")
            return

        try:
            choices = [int(c.strip()) for c in choice.split(',')]
            for choice_num in choices: # Renamed 'choice' to 'choice_num' to avoid conflict
                if 1 <= choice_num <= len(BonusType):
                    bonus_type = list(BonusType)[choice_num-1]
                    if bonus_type == BonusType.KASSZA and player != self.taker:
                        print("Only taker can announce Kassza!")
                        continue

                    self.bonus_announcements[player].append((bonus_type, phase))
                    print(f"{player} announces {bonus_type.value} ({phase})")
                    # Log bonus announcement
                    self.game_log.append({ # NEW
                        "event": "bonus_announced",
                        "player": player,
                        "bonus_type": bonus_type.value,
                        "phase": phase
                    })
        except ValueError:
            print("Invalid input for bonus announcement, skipping.") # MODIFIED print message
    
    def play_trick(self, lead_player: str, trick_num: int) -> str:
        """Play a single trick using player agents."""
        trick_cards = {}
        current_player = lead_player

        print(f"\n--- Trick {trick_num} ---")
        print(f"{lead_player} leads")

        for i in range(len(self.players)):
            if not self.hands[current_player]:
                break

            # print(f"\n{current_player}'s turn") # Keep for human, but not essential for headless
            # print(f"Hand:") # Keep for human
            # for j, card in enumerate(self.hands[current_player]): # Keep for human
            #     print(f"{j}: {self._format_card_with_points(card)}") # Keep for human

            if i == 0:  # First card played
                # Agent chooses a card directly
                played_card = self.agents[current_player].choose_card_to_play(self, current_player, trick_cards, self.hands[current_player]) # MODIFIED
                if played_card not in self.hands[current_player]: # Basic validation for agent output
                    print(f"Warning: Agent for {current_player} chose a card not in hand. Playing first card.")
                    played_card = self.hands[current_player][0]

                self.hands[current_player].remove(played_card)
                trick_cards[current_player] = played_card
                print(f"{current_player} plays {played_card}")
                self.game_log.append({ 
                    "event": "card_played",
                    "trick_num": trick_num,
                    "player": current_player,
                    "card": str(played_card),
                    "suit": played_card.suit.value,
                    "rank": played_card.rank.name
                })
            else:
                led_suit = list(trick_cards.values())[0].suit
                valid_cards = [card for card in self.hands[current_player] if card.suit == led_suit]

                if not valid_cards:
                    if self.trump_suit and self.game_type == GameType.TRUMP:
                        trump_cards = [card for card in self.hands[current_player] if card.suit == self.trump_suit]
                        if trump_cards:
                            valid_cards = trump_cards
                            print(f"Cannot follow {led_suit.value} - must play trump!")
                        else:
                            valid_cards = self.hands[current_player]
                            print(f"Cannot follow {led_suit.value} and no trumps - can play any card")
                    else:
                        valid_cards = self.hands[current_player]
                        print(f"Cannot follow {led_suit.value} - can play any card")
                else:
                    print(f"Must follow {led_suit.value}")

                valid_cards = self._sort_cards(valid_cards) # Ensure sorted for agent consistency
                # print(f"Valid cards: {[f'{j}: {card}' for j, card in enumerate(valid_cards)]}") # Keep for human

                # Agent chooses a card directly
                played_card = self.agents[current_player].choose_card_to_play(self, current_player, trick_cards, valid_cards) # MODIFIED
                if played_card not in valid_cards: # Basic validation for agent output
                    print(f"Warning: Agent for {current_player} chose an invalid card. Playing first valid card.")
                    played_card = valid_cards[0]

                self.hands[current_player].remove(played_card)
                trick_cards[current_player] = played_card
                print(f"{current_player} plays {played_card}")

            current_player = self.players[(self.players.index(current_player) + 1) % len(self.players)]

        winner = self._determine_trick_winner(trick_cards, list(trick_cards.values())[0].suit)
        self.tricks[winner].extend(list(trick_cards.values())) # Ensure it's a list for extend
        print(f"\n{winner} wins the trick!")

        # Log trick winner and contents
        self.game_log.append({ # NEW
            "event": "trick_completed",
            "trick_num": trick_num,
            "leader": lead_player,
            "played_cards": {p: str(c) for p, c in trick_cards.items()},
            "winner": winner
        })

        return winner
    
    def _determine_trick_winner(self, trick_cards: Dict[str, Card], led_suit: Suit) -> str:
        """Determine the winner of a trick"""
        winner = None
        best_value = -1
        
        # Iterate through all cards played in the trick to find the true winner
        for player, card in trick_cards.items():
            card_value = self._get_card_value_for_comparison(card)
            
            # Cards that do not follow suit and are not trump cannot win unless no one can follow suit or trump
            # This logic needs to prioritize following suit, then trumping, then discarding
            
            # Rule 1: Must follow suit if possible
            # Rule 2: If cannot follow suit, must play trump if possible (and trump is active)
            # Rule 3: If cannot follow suit or trump, can play any card (discard)

            # Determine if the current card is a potential winner
            is_following_suit = (card.suit == led_suit)
            is_trump_card = (self.trump_suit and card.suit == self.trump_suit)

            # Only consider cards that follow suit, or are trumps if suit was not followed
            if winner is None: # For the first card, just set it as the current best
                best_value = card_value
                winner = player
            else:
                winning_card = trick_cards[winner]
                winning_card_value = self._get_card_value_for_comparison(winning_card)

                # Case 1: Current winning card is following suit
                if winning_card.suit == led_suit:
                    if is_following_suit and card_value > winning_card_value:
                        best_value = card_value
                        winner = player
                    elif is_trump_card and not (winning_card.suit == self.trump_suit): # New card is trump and current winning is not trump
                        best_value = card_value
                        winner = player
                # Case 2: Current winning card is a trump (and not following suit)
                elif winning_card.suit == self.trump_suit:
                    if is_trump_card and card_value > winning_card_value:
                        best_value = card_value
                        winner = player
                # Case 3: Current winning card is a discard (neither suit nor trump)
                else:
                    if is_following_suit or is_trump_card: # New card is better than a discard
                        best_value = card_value
                        winner = player
                    elif card_value > winning_card_value: # Both are discards, highest discard wins
                         best_value = card_value
                         winner = player
        
        # This part executes ONLY after all cards in the trick have been evaluated
        print(f"\n{winner} wins the trick!")

        # Log trick winner and contents
        self.game_log.append({
            "event": "trick_completed",
            "trick_num": len(self.tricks[winner]) // len(trick_cards), # Approx trick num
            "leader": list(trick_cards.keys())[0], # The player who led the trick
            "played_cards": {p: str(c) for p, c in trick_cards.items()},
            "winner": winner
        })

        return winner
    
    def calculate_game_points(self, player: str) -> Tuple[int, int, int]:
        """Calculate points for a player and return (card_points, meld_points, bonus_points)"""
        # Calculate card points
        card_points = sum(self._get_card_points(c, c.suit == self.trump_suit) for c in self.tricks[player])
        
        return card_points
    
    def play_game(self):
        """Play a complete game"""
        self.game_id = str(uuid.uuid4()) # Assign a unique ID for this game instance
        self.game_log.append({"event": "game_start", "game_id": self.game_id})

        print("=== ALSÓS CARD GAME ===")
        print(f"Playing with {self.num_players} players")

        self.shuffle_and_deal()
        # Log initial hands and trump indicator
        initial_hands_data = {p: [str(c) for c in self.hands[p]] for p in self.players}
        self.game_log.append({"event": "deal_initial_hands", "hands": initial_hands_data, "trump_indicator": str(self.trump_indicator)})
        
        # Show hands
        for player in self.players:
            print(f"\n{player}'s hand:")
            for i, card in enumerate(self.hands[player]):
                print(f"{i}: {card}")
        
        # Bidding
        if not self.conduct_bidding():
            print("Bidding failed")
            self.game_log.append({"event": "bidding_failed"})
            return

        print(f"\nGame type: {self.game_type.value}")
        if self.trump_suit:
            print(f"Trump suit: {self.trump_suit.value}")
        if self.taker:
            print(f"Taker: {self.taker}")

        # Log bidding result
        self.game_log.append({
            "event": "bidding_result",
            "game_type": self.game_type.value,
            "trump_suit": self.trump_suit.value if self.trump_suit else None,
            "taker": self.taker
        })
        
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
        
        # Log hands after dealing remaining cards (12 cards total)
        final_hands_data = {p: [str(c) for c in self.hands[p]] for p in self.players}
        self.game_log.append({"event": "deal_final_hands", "hands": final_hands_data})
        
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
        final_scores_data = {}
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
        
            final_scores_data[player] = {
                "card_points": card_pts,
                "meld_points_awarded": self.scores[player], # Points added by evaluate_melds
                "total_score": card_pts + self.scores[player]
            }

        # Determine the actual game winner based on the complex logic
        game_winner_status = "Undetermined"
        if self.game_type == GameType.BETLI:
            game_winner_status = f"{self.taker} wins Betli!" if len(self.tricks[self.taker]) == 0 else f"{self.taker} fails Betli!"
        elif self.game_type == GameType.KLOPITZKY:
            min_tricks = min(len(self.tricks[player]) for player in self.players)
            winners = [player for player in self.players if len(self.tricks[player]) == min_tricks]
            game_winner_status = f"{', '.join(winners)} wins Klopitzky!" if len(winners) > 0 else "Klopitzky is a tie!"
        else: # Trump or No-Trump
            if self.taker:
                taker_total_score = final_scores_data[self.taker]["total_score"]
                opponent_total_scores = [final_scores_data[p]["total_score"] for p in self.players if p != self.taker]
                # Assuming a simple comparison for now, detailed win conditions might apply
                if taker_total_score > max(opponent_total_scores): # Simplified example
                     game_winner_status = f"{self.taker} wins the game!"
                else:
                    game_winner_status = f"{self.taker} fails to make the game!"
            else: # Should not happen if taker is always set
                game_winner_status = "No taker specified, game winner undetermined."


        self.game_log.append({ # NEW
            "event": "game_end",
            "final_scores": final_scores_data,
            "game_outcome": game_winner_status
        })
        
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
    
    def save_game_log(self, filename: str = "game_logs.jsonl"): # Changed to .jsonl for JSON Lines
        """Saves the game log for a single game to a JSON Lines file."""
        with open(filename, 'a') as f: # 'a' for append mode
            json.dump({"game_id": self.game_id, "log": self.game_log}, f)
            f.write('\n') # Each game log on a new line
            
# alsos_claude_windsurf.py

def main():
    print("Welcome to Alsós!")
    
    # Configuration for simulation vs. human play
    game_type = "human_vs_ai" # simulation, human_vs_ai, human_solo
    num_simulations = 1000

    if game_type == "simulation":
        num_players_sim = 2 # Fixed for simulation, adjust as needed
        
        # Define agents for simulation
        # For simple simulation, use RuleBasedPlayerAgent for all players
        sim_agents = {f"Player {i+1}": RuleBasedPlayerAgent() for i in range(num_players_sim)}

        for i in range(num_simulations):
            print(f"\n--- Simulating Game {i+1} of {num_simulations} ---")
            game = AlsosGame(num_players=num_players_sim, agents=sim_agents)
            game.play_game()
            game.save_game_log(filename="simulated_game_logs.jsonl") # Save each game's log
            print(f"Game {i+1} log saved.")
    elif game_type == 'human_solo':
        print("Choose number of players (2-4): ")
        try:
            num_players_human = int(input())
            if num_players_human < 2 or num_players_human > 4:
                num_players_human = 2
        except ValueError:
            num_players_human = 2
        
        # For human play, agents default to HumanPlayerAgent
        game = AlsosGame(num_players=num_players_human)
        game.play_game()
        # You might want to save human games too
        game.save_game_log(filename="human_game_logs.jsonl")
    elif game_type == "human_vs_ai":
        num_players_human = 2 # Fixed to 2 players for human vs AI scenario
        print(f"Setting up a 2-player game: Player 1 (You) vs Player 2 (AI)")

        # Define agents for human vs. AI play
        human_vs_ai_agents = {
            "Player 1": HumanPlayerAgent(),     # Player 1 is controlled by a human
            "Player 2": RuleBasedPlayerAgent()  # Player 2 is controlled by the RuleBasedPlayerAgent
        }
        
        # Create the game instance with the specified agents
        game = AlsosGame(num_players=num_players_human, agents=human_vs_ai_agents) # MODIFIED LINE
        game.play_game()
        game.save_game_log(filename="human_vs_ai_game_logs.jsonl") # Optional: save to a different log file

if __name__ == "__main__":
    main()

