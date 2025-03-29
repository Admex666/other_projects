import random

# Kártya osztály: tartalmazza a lap színét és értékét.
class Card:
    def __init__(self, suit, rank):
        self.suit = suit      # pl. "piros", "makk", "zöld", "tök"
        self.rank = rank      # pl. "Ász", "10", "Király", "Felső", "Alsó", "9", "8", "7"

    def __repr__(self):
        return f"{self.suit}_{self.rank}"


# Pakli osztály: a 32 lapos magyar kártyapaklit reprezentálja.
class Deck:
    def __init__(self):
        self.cards = []
        suits = ["Piros", "Makk", "Zöld", "Tök"]
        ranks = ["7", "8", "9", "Alsó", "Felső", "Király", "10", "Ász"]
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards


# Játékos osztály: tárolja a játékos nevét, kézét, és egyszerű licit/logikát.
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []  # A játékos kezében lévő lapok
        self.bid = None  # A licit, amit a játékos meghozott

    def receive_cards(self, cards):
        self.hand.extend(cards)

    def show_hand(self):
        return ", ".join(map(str, self.hand))

    def make_bid(self, current_highest_bid):
        """
        A játékos csak akkor licitál, ha a licitje magasabb az aktuális legmagasabbnál.
        Ha nem tud vagy nem akar, akkor passzol (None).
        """
        possible_bids = ["Parti", "40-100", "Ulti", "Betli", "Durchmars", "20-100"]
        higher_bids = [bid for bid in possible_bids if bid not in [None, "Parti"] and 
                       (current_highest_bid is None or possible_bids.index(bid) > possible_bids.index(current_highest_bid))]

        if not higher_bids:
            self.bid = None  # Nincs magasabb licit, passzolunk
        else:
            self.bid = random.choice(higher_bids)  # Véletlenszerűen választunk a magasabb lehetőségek közül
        
        return self.bid

    def select_discard(self):
        """
        A játékos kiválaszt két lapot, amelyet visszatesz a talonba.
        Jelenleg egyszerűsítve: az első két lapot dobja el.
        """
        discard = self.hand[:2]
        self.hand = self.hand[2:]
        return discard

    def play_card(self, leading_suit=None):
        """
        Egyszerű lejátszási logika:
        - Ha meg van a kért szín (leading_suit), az első ilyen lapot játssza.
        - Különben az első lapot.
        """
        if leading_suit:
            valid_cards = [card for card in self.hand if card.suit == leading_suit]
            if valid_cards:
                chosen_card = valid_cards[0]
            else:
                chosen_card = self.hand[0]
        else:
            chosen_card = self.hand[0]
        self.hand.remove(chosen_card)
        return chosen_card


# Ütés osztály: egy ütés lejátszását modellezi.
class Trick:
    def __init__(self, leader_index, players, game_type, adu_szin):
        self.leader_index = leader_index
        self.players = players
        self.cards_played = []
        self.play_order = self.get_play_order()
        self.game_type = game_type
        self.adu_szin = adu_szin

    def get_play_order(self):
        order = []
        n = len(self.players)
        for i in range(n):
            order.append(self.players[(self.leader_index + i) % n])
        return order

    def play(self):
        print("----- Új ütés -----")
        leading_suit = None
        for i, player in enumerate(self.play_order):
            if i == 0:
                card = player.play_card()
                leading_suit = card.suit
                print(f"{player.name} vezet: {card}")
            else:
                card = player.play_card(leading_suit)
                print(f"{player.name} játszik: {card}")
            self.cards_played.append((player, card))
        winner = self.determine_winner(leading_suit)
        print(f"Ütést nyer: {winner.name}\n")
        return winner

    def determine_winner(self, leading_suit):
        """
        Az aduszínt is figyelembe veszi, ha van, egyébként a sima ütésnyerés logikája.
        """
        rank_order = {"7": 0, "8": 1, "9": 2, "Felső": 3, "Alsó": 4,
                      "Király": 5, "10": 6, "Ász": 7}
        winning_player, winning_card = self.cards_played[0]
        
        # Ha van aduszín és egy játékos nem tudott a vezető színben játszani, akkor aduszin kell játszon
        for player, card in self.cards_played[1:]:
            if card.suit == self.adu_szin:  # Ha aduszínt játszottak
                winning_player = player
                winning_card = card
            elif card.suit == leading_suit and rank_order[card.rank] > rank_order[winning_card.rank]:
                winning_player = player
                winning_card = card
        return winning_player


# Game osztály: a játék menetét (kör, licit, lejátszás, pontozás) irányítja.
class Game:
    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.talon = []      
        self.declarer = None  
        self.tricks = []
        self.game_type = None  # A játék típusa (Adus vagy Adu nélküli)

    # Módosítás a setup_round-ban, hogy a talon ne maradjon üres
    def setup_round(self):
        print("=== Kör beállítása ===")
        self.deck.shuffle()
    
        num_players = len(self.players)
        if num_players == 3:
            distribution = [12, 10, 10]
        elif num_players == 4:
            distribution = [12, 10, 10]  
        else:
            raise ValueError("A játékhoz 3 vagy 4 játékos szükséges!")
    
        for i, player in enumerate(self.players):
            cards_to_deal = distribution[i % len(distribution)]
            player.receive_cards(self.deck.deal(cards_to_deal))
            print(f"{player.name} kezében: {player.show_hand()}")
    
        # Csak Játékos1 (első játékos) dob 2 lapot a talonba
        self.talon = []
        first_player = self.players[0]
        if len(first_player.hand) >= 2:
            discarded = first_player.select_discard()
            self.talon.extend(discarded)
            print(f"{first_player.name} dobja a talonba: {discarded}")

    
    # Licitálás, hogy a talon tartalma most már megfelelő
    def bidding_phase(self):
        print("=== Licitálás ===")
        bid_order = {"Parti": 0, "40-100": 1, "Ulti": 2, "Betli": 3, "Durchmars": 4, "20-100": 5}
        current_bid_level = -1
        current_bid = None
        any_bid = False
        
        passes = {player: False for player in self.players}
        bid_history = []
        talon_taken = False  # Nyomon követjük, hogy ki vette fel a talont
        
        round_count = 0
        max_rounds = 10
        
        while round_count < max_rounds:
            round_count += 1
            bid_made_in_round = False
            for i, player in enumerate(self.players):
                if passes[player]:
                    continue
    
                if i > 0 and not talon_taken:  # Ha már volt talonfelvétel, a következő játékos dönthet
                    if random.random() < 0.5:
                        print(f"{player.name} felveszi a talont: {self.talon}")
                        player.hand.extend(self.talon)
                        self.talon = []  
                        talon_taken = True
                        # Kötelezően dobjon el két lapot, miután felvette a talont
                        discarded = player.select_discard()
                        print(f"{player.name} leteszi a talonba: {discarded}")
                    else:
                        passes[player] = True
                        print(f"{player.name} passzol.")
                        continue
    
                # Ellenőrizzük, hogy a licitálás magasabb, mint a korábbi
                possible_bids = [bid for bid, level in bid_order.items() if level > current_bid_level]
                if possible_bids and random.random() < 0.5:
                    chosen_bid = random.choice(possible_bids)
                    player.bid = chosen_bid
                    current_bid_level = bid_order[chosen_bid]
                    current_bid = chosen_bid
                    any_bid = True
                    bid_made_in_round = True
                    bid_history.append((player, chosen_bid))
                    print(f"{player.name} licitál: {chosen_bid}")
                else:
                    passes[player] = True
                    print(f"{player.name} passzol.")
            
            if not bid_made_in_round:
                break
    
        if not any_bid:
            current_bid = "Parti"
            self.declarer = self.players[0]  
            self.declarer.bid = current_bid
            print(f"Senki sem licitált, alapértelmezett licit: {current_bid} a {self.declarer.name} részére.\n")
        else:
            self.declarer = max(bid_history, key=lambda x: bid_order[x[1]])[0]
            self.declarer.bid = current_bid
            print(f"\n{self.declarer.name} a felvevő a {self.declarer.bid} licittel.\n")
    
        return self.declarer
    
    def play_phase(self):
        print("=== Lejátszás ===")
        if self.declarer:
            leader = self.declarer
        else:
            leader = self.players[0]
    
        self.tricks = []  # Ensure this is reset before each round
        for trick_number in range(10):
            print(f"Ütés {trick_number+1}:")
            trick = Trick(self.players.index(leader), self.players, self.game_type, getattr(self.declarer, 'adu_szin', None))
            leader = trick.play()
            self.tricks.append(trick)  # Store the trick for scoring


    def scoring_phase(self):
        """
        Pontozási fázis:
          - Az összes ütésből (self.tricks, melynek eleme egy Trick objektum, amely a
            play_phase során rögzítette a lejátszott lapokat) kiszámoljuk:
             • Minden Ász és 10-es lap 10 pontot ér.
             • Az utolsó ütést nyerő játékos további 10 pontot kap.
          - A felvevő (declarer) összpontja a trükkökből szerzett pontok + a bemondás (meld) pontok.
          - A vállalás sikerességét a licit típusa határozza meg:
             • Parti: a felvevőnek több pontja kell legyen, mint az ellenfelek összesen.
             • 40-100: a felvevőnek legalább 40 pont bemondása (Negyven) mellett 60 ütéspontja.
             • 20-100: a felvevőnek legalább 20 pont bemondása (Húsz) mellett 80 ütéspontja.
             • Ulti: a felvevőnek az utolsó ütést a trump 7-esével kell nyernie.
             • Durchmars: a felvevőnek az összes 10 ütést meg kell nyernie.
             • Betli: a felvevőnek nem szabad ütést nyernie.
             • Négy Ász: a felvevőnek az összes Ászt (mind a négyet) meg kell nyernie a trükkök során.
          - A sikeres vállalás esetén a licithez tartozó pontértéket (pl. Parti: 1, 40-100: 4, 20-100: 8, Ulti: 4, Durchmars: 6, Betli: 5) számoljuk.
          - Ha a felvevő nem teljesítette a vállalását, az ellenfelek pontot kapnak.
        """
        print("=== Pontozás ===")
        if not hasattr(self, 'tricks') or not self.tricks:
            print("Nincsenek ütés adatok, nem lehet pontozni.")
            return
    
        trump = "piros"  # Ugyancsak az adu színe
        declarer = self.declarer
    
        trick_points_declarer = 0
        trick_points_opponents = 0
    
        # Minden ütésből összegezzük az értékes lapok pontjait:
        # Az Ász és 10-es lap 10 pontot ér.
        for trick in self.tricks:
            for player, card in trick.cards_played:
                if card.rank in ["10", "Ász"]:
                    if player == declarer:
                        trick_points_declarer += 10
                    else:
                        trick_points_opponents += 10
    
        # Az utolsó ütést nyerő játékos további 10 pontot kap.
        last_trick = self.tricks[-1]
        # Feltételezzük, hogy a Trick objektum rendelkezik a determine_winner() metódussal,
        # ami a vezető szín alapján meghatározza a nyertest.
        last_trick_winner = last_trick.determine_winner(last_trick.cards_played[0][1].suit)
        if last_trick_winner == declarer:
            trick_points_declarer += 10
        else:
            trick_points_opponents += 10
    
        print(f"Ütéspontok: {declarer.name}: {trick_points_declarer}, ellenfelek: {trick_points_opponents}")
    
        # A felvevő összpontja: ütéspontok + bemondás (meld) pontok
        total_declarer = trick_points_declarer + getattr(declarer, 'meld_points', 0)
        total_opponents = trick_points_opponents
        print(f"{declarer.name} összpontszáma (ütések + bemondások): {total_declarer}")
    
        # Vállalás sikerességének ellenőrzése a licit típusától függően:
        bid = declarer.bid
        contract_success = False
    
        if bid == "Parti":
            if total_declarer > total_opponents:
                contract_success = True
        elif bid == "40-100":
            # Követelmény: legyen Negyven bemondás (legalább 40 pont a meld-ekből) és minimum 60 ütéspont.
            if getattr(declarer, 'meld_points', 0) >= 40 and trick_points_declarer >= 60:
                contract_success = True
        elif bid == "20-100":
            # Követelmény: legyen legalább egy Húsz bemondás (minimum 20 pont) és minimum 80 ütéspont.
            if getattr(declarer, 'meld_points', 0) >= 20 and trick_points_declarer >= 80:
                contract_success = True
        elif bid == "Ulti":
            # A felvevőnek az utolsó ütést a trump 7-esével kell nyernie.
            # Keressük meg az utolsó ütésben a declarer által lejátszott lapot.
            ulti_card = None
            for player, card in last_trick.cards_played:
                if player == declarer:
                    ulti_card = card
                    break
            if ulti_card and ulti_card.suit == trump and ulti_card.rank == "7":
                contract_success = True
        elif bid == "Durchmars":
            # A felvevőnek minden ütést meg kell nyernie.
            if all(trick.determine_winner(trick.cards_played[0][1].suit) == declarer for trick in self.tricks):
                contract_success = True
        elif bid == "Betli":
            # A felvevőnek egyetlen ütést sem szabad nyernie.
            if all(trick.determine_winner(trick.cards_played[0][1].suit) != declarer for trick in self.tricks):
                contract_success = True
        elif bid == "Négy Ász":
            # A felvevőnek az összes (4 db) Ászt kell nyernie a trükkök során.
            ace_wins = 0
            for trick in self.tricks:
                # Számoljuk, hogy a nyertes trükk tartalmaz Ász lapot,
                # és ha igen, azt a felvevő nyerte-e.
                winner = trick.determine_winner(trick.cards_played[0][1].suit)
                if winner == declarer:
                    for _, card in trick.cards_played:
                        if card.rank == "Ász":
                            ace_wins += 1
            if ace_wins >= 4:
                contract_success = True
        else:
            # Egyéb licitek: itt egy alapértelmezett feltétel, vagy egyéb logika is bevezethető.
            print(f"A licit típusa ({bid}) nincs részletesen implementálva, feltételezzük a sikerességet.")
            contract_success = True
    
        # A licithez tartozó pontértékek (egyszerűsítve, a tipikus értékek):
        bid_values = {
            "Parti": 1,
            "40-100": 4,
            "20-100": 8,
            "Ulti": 4,
            "Durchmars": 6,
            "Betli": 5,
            "Négy Ász": 4
        }
        base_points = bid_values.get(bid, 0)
    
        if contract_success:
            print(f"A szerző ({declarer.name}) teljesítette a vállalását. Pontértéke: {base_points}")
        else:
            print(f"A szerző ({declarer.name}) nem teljesítette a vállalását. Elveszíti: {base_points} pontot.")
    
        print("")
    
    def declaration_phase(self):
        """
        A felvevő (declarer) bejelenti, hogy milyen játékot fog játszani.
        Ha van érvényes licit, akkor az lesz a játék típusa.
        """
        if self.declarer and self.declarer.bid:
            self.game_type = self.declarer.bid
        else:
            self.game_type = "Parti"  # Ha valamiért nincs érvényes licit, alapértelmezettként Parti

        print(f"\nA játék típusa: {self.game_type}")
        
        if self.game_type in ["40-100", "Ulti", "Durchmars", "Négy Ász", "20-100"]:
            self.declarer.adu_szin = self.choose_adu_szin()  # Felvevő kiválasztja az aduszínt
    
    def choose_adu_szin(self):
        """
        A felvevő kiválasztja az aduszínt (a legtöbb lapja alapján).
        """
        suits_count = {suit: 0 for suit in ["Piros", "Makk", "Zöld", "Tök"]}
        for card in self.declarer.hand:
            suits_count[card.suit] += 1
        
        # A legnagyobb lapot tartalmazó szín lesz az aduszín
        adu_szin = max(suits_count, key=suits_count.get)
        print(f"{self.declarer.name} kijelöli az aduszínt: {adu_szin}")
        return adu_szin
    
    def play_round(self):
        self.setup_round()
        if self.bidding_phase():
            self.declaration_phase()
            self.play_phase()
            self.scoring_phase()
        else:
            print("Nincs felvevő, új kör kezdődik.")
    

if __name__ == "__main__":
    # Játékosok létrehozása
    player_names = ["Játékos1", "Játékos2", "Játékos3"]
    players = [Player(name) for name in player_names]

    # Játék indítása és egy kör lejátszása
    game = Game(players)
    game.play_round()
