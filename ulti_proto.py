import random

# Constants
SUITS = ['Piros', 'Zöld', 'Makk', 'Tök']
RANKS = ['VII', 'VIII', 'IX', 'X', 'Alsó', 'Felső', 'Király', 'Ász']
PLAYERS = ['Player1', 'Player2', 'Player3', 'Player4']
BID_POINTS = {
    'Passz': {'success': 1, 'fail': 2},
    '40-100': {'success': 4, 'fail': 8},
    '20-100': {'success': 8, 'fail': 16},
    'Ulti': {'success': 5, 'fail': 9},
    'Betli': {'success': 5, 'fail': 5},
    'Durchmars': {'success': 6, 'fail': 12},
    # ... További licitek hozzáadása itt
}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.suit}_{self.rank}"

class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        random.shuffle(self.cards)

    def deal(self, num_players):
        if num_players == 3:
            return [self.cards[:12], self.cards[12:22], self.cards[22:32]]
        elif num_players == 4:
            return [self.cards[:12], self.cards[12:22], self.cards[22:32], []]

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.tricks = []
        self.points = 0
        self.melds = {'20': 0, '40': 0}

    def declare_melds(self):
        print(f"{self.name}, declare melds (20/40 points):")
        # ... Meldek deklarálásának implementációja
        
    def __repr__(self):
        return f"{self.name} with {len(self.hand)} cards"

    def discard_to_talon(self, num_cards=2):
        print(f"{self.name}, choose {num_cards} cards to discard to the talon:")
        for i, card in enumerate(self.hand):
            print(f"{i + 1}: {card}")
        choices = list(map(int, input("Enter card numbers (e.g., 1 2): ").split()))
        talon = [self.hand.pop(choice - 1) for choice in choices]
        return talon

    def bid(self, current_bid):
        print(f"{self.name}, your hand: {self.hand}")
        print(f"Current bid is {current_bid}. Do you want to bid higher? (yes/no)")
        choice = input().strip().lower()
        if choice == 'yes':
            new_bid = input("Enter your bid (e.g., 'Parti', '40-100'): ").strip()
            return new_bid
        return None

    def play_card(self, lead_suit, trump_suit):
        print(f"{self.name}, your hand: {self.hand}")
        print(f"Lead suit is {lead_suit}, trump suit is {trump_suit}.")
        valid_cards = [card for card in self.hand if card.suit == lead_suit]
        if not valid_cards:
            valid_cards = [card for card in self.hand if card.suit == trump_suit]
        if not valid_cards:
            valid_cards = self.hand
        print("Choose a card to play:")
        for i, card in enumerate(valid_cards):
            print(f"{i + 1}: {card}")
        choice = int(input("Enter card number: "))
        return valid_cards.pop(choice - 1)

class Game:
    def __init__(self, num_players):
        self.num_players = num_players
        self.deck = Deck()
        self.players = [Player(name) for name in PLAYERS[:num_players]]
        self.talon = []
        self.declarer = None
        self.trump_suit = None
        self.current_bid = None
        self.passes = 0

    def setup_round(self):
        hands = self.deck.deal(self.num_players)
        for player, hand in zip(self.players, hands):
            player.hand = hand
        self.talon = self.players[0].discard_to_talon()

    def play_phase(self):
        leader = self.players[0]  # First player leads
        for trick in range(10):
            print(f"\nTrick {trick + 1}:")
            cards_played = []
            lead_card = leader.play_card(None, self.trump_suit)
            cards_played.append((leader, lead_card))
            for player in self.players:
                if player != leader:
                    card = player.play_card(lead_card.suit, self.trump_suit)
                    cards_played.append((player, card))
            winner = self.determine_trick_winner(cards_played, lead_card.suit, self.trump_suit)
            print(f"{winner[0].name} wins the trick with {winner[1]}!")
            winner[0].tricks.append(cards_played)
            leader = winner[0]

    def determine_trick_winner(self, cards_played, lead_suit, trump_suit):
        trump_cards = [card for card in cards_played if card[1].suit == trump_suit]
        if trump_cards:
            return max(trump_cards, key=lambda x: RANKS.index(x[1].rank))
        lead_cards = [card for card in cards_played if card[1].suit == lead_suit]
        return max(lead_cards, key=lambda x: RANKS.index(x[1].rank))

    def bidding_phase(self):
        current_bid = "Passz"
        bidder_index = 0
        self.passes = 0
        
        while self.passes < 3:
            player = self.players[bidder_index % self.num_players]
            print(f"\nCurrent bid: {current_bid}")
            print(f"{player.name}'s turn to bid:")
            
            if player == self.declarer:
                action = input("Passzol? (igen/nem): ").lower()
                if action == 'igen':
                    self.passes += 1
                    bidder_index += 1
                    continue
                else:
                    self.passes = 0
                    
            new_bid = player.bid(current_bid)
            
            if new_bid:
                self.declarer = player
                current_bid = new_bid
                self.passes = 0
                # Talon kezelés
                if input("Take talon? (igen/nem): ") == 'igen':
                    player.hand += self.talon
                    self.talon = player.discard_to_talon()
            else:
                self.passes += 1
                
            bidder_index += 1
        
        print(f"Final bid: {current_bid} by {self.declarer.name}")

    def calculate_trick_points(self, tricks):
        points = 0
        for trick in tricks:
            for card in trick:
                if card.rank in ['Ász', 'X']:
                    points += 10
        # Utolsó ütés pontja
        if tricks:
            points += 10
        return points

    def check_bid_success(self, bid_type):
        # Egyszerűsített ellenőrzés
        total_points = self.calculate_trick_points(self.declarer.tricks)
        
        if bid_type == '40-100':
            required_points = 60
            if self.declarer.melds['40'] >= 40 and total_points >= required_points:
                return True
            return False
            
        elif bid_type == '20-100':
            required_points = 80
            if self.declarer.melds['20'] >= 20 and total_points >= required_points:
                return True
            return False
        
        # ... További licit típusok ellenőrzése
        
        return False

    def scoring_phase(self):
        bid_type = self.current_bid.split()[0]  # Egyszerűsítve
        success = self.check_bid_success(bid_type)
        
        base_points = BID_POINTS.get(bid_type, {'success': 0, 'fail': 0})
        multiplier = 1
        
        # Szín és terített szorzók
        if 'Piros' in self.current_bid:
            multiplier *= 2
        if 'Terített' in self.current_bid:
            multiplier *= 2
            
        if success:
            points = base_points['success'] * multiplier
            self.declarer.points += points
            for player in self.players:
                if player != self.declarer:
                    player.points -= points
        else:
            points = base_points['fail'] * multiplier
            self.declarer.points -= points
            for player in self.players:
                if player != self.declarer:
                    player.points += points

        # ... Egyéb speciális esetek kezelése

    def play_game(self):
        print("Starting Ulti Game!")
        self.setup_round()
        self.bidding_phase()
        self.declarer.declare_melds()
        self.play_phase()
        self.scoring_phase()
        print("\nFinal Scores:")
        for player in self.players:
            print(f"{player.name}: {player.points} points")
        print("Game Over!")

# Main
if __name__ == "__main__":
    num_players = int(input("Enter number of players (3 or 4): "))
    game = Game(num_players)
    game.play_game()