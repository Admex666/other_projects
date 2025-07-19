# game/engine.py
import random
import uuid
import json
from typing import List, Dict, Optional, Tuple

from game.definitions import Card, Suit, Rank, GameType, Meld, BonusType
from agents.base_agent import PlayerAgent
from agents.human_agent import HumanPlayerAgent # Alapértelmezett ágensnek
from config import BONUS_POINTS, SUIT_ORDER

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
        self.bonus_results = {player: [] for player in self.players}  # To store bonus outcomes
        self.bonus_scores = {player: 0 for player in self.players}
        self.SUIT_ORDER = SUIT_ORDER 
    
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
       decision_context = {
            'bid_context': context_phase1,
            'hand': [str(c) for c in self.hands[non_dealer]],
            'trump_indicator_suit': self.trump_indicator.suit.value if self.trump_indicator else None,
            'trump_cards': sum(1 for c in self.hands[non_dealer] if self.trump_indicator and c.suit == self.trump_indicator.suit),
            'high_cards': sum(1 for c in self.hands[non_dealer] if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
            'hearts_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.HEARTS),
            'bells_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.BELLS),
            'leaves_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.LEAVES),
            'acorns_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.ACORNS),
            'total_points': sum(self._get_card_points(c) for c in self.hands[non_dealer]),
            'options': ['y', 'n'],
            'chosen_option': response
        }
       self.game_log.append({
            'event': 'bidding_decision',
            'player': non_dealer,
            'context': decision_context
        })
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
           decision_context = {
                'bid_context': context_phase2,
                'hand': [str(c) for c in self.hands[non_dealer]],
                'trump_indicator_suit': self.trump_indicator.suit.value if self.trump_indicator else None,
                'trump_cards': sum(1 for c in self.hands[non_dealer] if self.trump_indicator and c.suit == self.trump_indicator.suit),
                'high_cards': sum(1 for c in self.hands[non_dealer] if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
                'hearts_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.HEARTS),
                'bells_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.BELLS),
                'leaves_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.LEAVES),
                'acorns_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.ACORNS),
                'total_points': sum(self._get_card_points(c) for c in self.hands[non_dealer]),
                'options': ['y', 'n'],
                'chosen_option': response
            }
           self.game_log.append({
                'event': 'bidding_decision',
                'player': non_dealer,
                'context': decision_context
            })
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
       decision_context = {
            'bid_context': context_phase3,
            'hand': [str(c) for c in self.hands[non_dealer]],
            'trump_indicator_suit': self.trump_indicator.suit.value if self.trump_indicator else None,
            'trump_cards': sum(1 for c in self.hands[non_dealer] if self.trump_indicator and c.suit == self.trump_indicator.suit),
            'high_cards': sum(1 for c in self.hands[non_dealer] if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
            'hearts_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.HEARTS),
            'bells_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.BELLS),
            'leaves_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.LEAVES),
            'acorns_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.ACORNS),
            'total_points': sum(self._get_card_points(c) for c in self.hands[non_dealer]),
            'options': ['y', 'n'],
            'chosen_option': response
        }
       self.game_log.append({
            'event': 'bidding_decision',
            'player': non_dealer,
            'context': decision_context
        })
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
       decision_context = {
            'bid_context': context_phase4,
            'hand': [str(c) for c in self.hands[non_dealer]],
            'trump_indicator_suit': self.trump_indicator.suit.value if self.trump_indicator else None,
            'trump_cards': sum(1 for c in self.hands[non_dealer] if self.trump_indicator and c.suit == self.trump_indicator.suit),
            'high_cards': sum(1 for c in self.hands[non_dealer] if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
            'hearts_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.HEARTS),
            'bells_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.BELLS),
            'leaves_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.LEAVES),
            'acorns_count': sum(1 for c in self.hands[non_dealer] if c.suit == Suit.ACORNS),
            'total_points': sum(self._get_card_points(c) for c in self.hands[non_dealer]),
            'options': ['y', 'n'],
            'chosen_option': response
        }
       self.game_log.append({
            'event': 'bidding_decision',
            'player': non_dealer,
            'context': decision_context
        })
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
        available_bonuses_info = []
        already_announced = {bt for bt, ph in self.bonus_announcements.get(player, [])}
        
        for i, bonus_type in enumerate(BonusType):
            if bonus_type not in already_announced:  # Only show bonuses not already announced
                available_bonuses_info.append((i+1, (bonus_type, phase)))
    
        # Log the available bonuses before asking for decision
        self.game_log.append({
            "event": "available_bonuses",
            "player": player,
            "phase": phase,
            "available_bonuses": [(num, (bt.value, ph)) for num, (bt, ph) in available_bonuses_info]
        })
    
        self.current_bonus_phase = phase
        choice = self.agents[player].choose_bonus_announcements(self, player, available_bonuses_info).strip()
    
        if choice.lower() == 'pass':
            print(f"{player} passes")
            self.game_log.append({
                "event": "bonus_decision",
                "player": player,
                "choice": "pass"
            })
            return
    
        try:
            choices = [int(c.strip()) for c in choice.split(',')]
            for choice_num in choices:
                if 1 <= choice_num <= len(BonusType):
                    bonus_type = list(BonusType)[choice_num-1]
                    if bonus_type == BonusType.KASSZA and player != self.taker:
                        print("Only taker can announce Kassza!")
                        continue
                    if bonus_type not in already_announced:
                        self.bonus_announcements[player].append((bonus_type, phase))
                        print(f"{player} announces {bonus_type.value} ({phase})")
                        self.game_log.append({
                            "event": "bonus_announced",
                            "player": player,
                            "bonus_type": bonus_type.value,
                            "phase": phase,
                            "choice_num": choice_num
                        })
        except ValueError:
            print("Invalid input for bonus announcement, skipping.")
        
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

        decision_context = {
            "player": current_player,
            "trick_num": trick_num,
            "current_trick": {p: str(c) for p, c in trick_cards.items()},
            "valid_cards": [str(c) for c in valid_cards],
            "chosen_card": str(played_card),
            "hand": [str(c) for c in self.hands[current_player]],
            "game_type": self.game_type.value,
            "trump_suit": self.trump_suit.value if self.trump_suit else None
        }
        self.game_log.append({
            "event": "player_decision",
            "context": decision_context
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
                print(f"{i}: {card}")
        
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
        

        # Calculate game points (card + meld) and bonus points separately
        game_points = {player: 0 for player in self.players}
        bonus_points = {player: 0 for player in self.players}
        
        # First calculate all bonus points from announcements
        for player in self.players:
            bonus_points[player] = self.evaluate_bonuses(player)
        
        # Then calculate game points (card + meld)
        for player in self.players:
            card_pts = self.calculate_game_points(player)
            meld_pts = self.scores[player]  # From evaluate_melds()
            game_points[player] = card_pts + meld_pts
        
        # Add +1 bonus point to player with highest game points
        max_game_points = max(game_points.values())
        winners = [p for p, pts in game_points.items() if pts == max_game_points]
        if len(winners) == 1:  # Only add if there's a clear winner
            bonus_points[winners[0]] += 1
            self.bonus_results[winners[0]].append(("Game points winner", "+1"))
        
        # Display final results
        print("\n=== FINAL RESULTS ===")
        final_scores_data = {}
        for player in self.players:
            print(f"{player}:")
            print(f"  Game points (card + meld): {game_points[player]}")
            
            # Print bonus results
            if self.bonus_results[player]:
                print("  Bonus announcements:")
                for announcement, result in self.bonus_results[player]:
                    print(f"    - {announcement}: {result}")
                print(f"  Total bonus points: {bonus_points[player]:+}")
            
            print("")  # Empty line for separation
            
            final_scores_data[player] = {
                "game_points": game_points[player],
                "bonus_points": bonus_points[player],
                "bonus_results": [f"{announcement}: {result}" 
                                 for announcement, result in self.bonus_results.get(player, [])]
            }
        
        # Determine the actual game winner based on game points
        game_winner_status = "Undetermined"
        if self.game_type == GameType.BETLI:
            game_winner_status = f"{self.taker} wins Betli!" if len(self.tricks[self.taker]) == 0 else f"{self.taker} fails Betli!"
        elif self.game_type == GameType.KLOPITZKY:
            min_tricks = min(len(self.tricks[player]) for player in self.players)
            winners = [player for player in self.players if len(self.tricks[player]) == min_tricks]
            game_winner_status = f"{', '.join(winners)} wins Klopitzky!" if len(winners) > 0 else "Klopitzky is a tie!"
        else: # Trump or No-Trump
            max_points = max(game_points.values())
            winners = [p for p, pts in game_points.items() if pts == max_points]
            if len(winners) == 1:
                game_winner_status = f"{winners[0]} wins the game with {max_points} points!"
            else:
                game_winner_status = f"Tie between {', '.join(winners)} with {max_points} points each!"
    
        self.game_log.append({
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
                self.bonus_results[player].append((f"{bonus_type.value} ({phase})", f"+{points}"))
            else:
                print(f"{player} failed {bonus_type.value} ({phase}) -{points}")
                bonus_points -= points
                self.bonus_results[player].append((f"{bonus_type.value} ({phase})", f"-{points}"))
                    
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