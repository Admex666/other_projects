from cards import Deck, Hand, DiscardPile, Card
from player import Player, BotPlayer
from rules_engine import RulesEngine
import random

class Match:
    """
    Simulates a single duel phase between two players in FrenchDuel.
    Handles card drafting, action phase (6 rounds), and phase end conditions.
    """
    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.deck = Deck()
        self.discard_pile = DiscardPile()
        self.rules_engine = RulesEngine()
        self.attacker = None
        self.defender = None
        self.round_logs = [] # To store details of each round

    def _assign_roles(self, starting_attacker_name):
        """Assigns attacker and defender roles based on the starting attacker."""
        if self.player1.name == starting_attacker_name:
            self.attacker = self.player1
            self.defender = self.player2
        else:
            self.attacker = self.player2
            self.defender = self.player1

        self.attacker.is_attacker = True
        self.defender.is_attacker = False
        print(f"\n--- Roles Assigned ---")
        print(f"Attacker: {self.attacker.name}")
        print(f"Defender: {self.defender.name}")

    def _draft_attack_cards(self):
        """
        Each player drafts 7 attack cards.
        Felváltva húznak 2-2 lapot a pakliból. Ebből 1 lapot nyíltan eldobnak, 1 lapot rejtve megtartanak.
        """
        print("\n--- Attack Card Draft Phase ---")
        for player in [self.player1, self.player2]:
            print(f"\n{player.name}'s Attack Draft:")
            for i in range(7): # Repeat 7 times to get 7 cards
                # Draw 2 cards
                drawn_cards = self.deck.draw(2)
                print(f"  Drawn cards: {[str(c) for c in drawn_cards]}")

                # Player chooses 1 to keep, 1 to discard
                # For bot, it will just keep 1 and discard 1 randomly
                card_to_keep = player.choose_draft_card(drawn_cards, 'attack')
                # Find the card to discard (the one not chosen to keep)
                card_to_discard = [c for c in drawn_cards if c != card_to_keep][0] 

                player.add_attack_card(card_to_keep)
                self.discard_pile.add_card(card_to_discard)
                print(f"  Kept: {card_to_keep}. Discarded: {card_to_discard}")
            print(f"{player.name}'s final attack hand ({len(player.attack_hand)} cards): {player.attack_hand}")


    def _draft_defense_cards(self):
        """
        Each player draws 3 cards, keeps 2 hidden, discards 1. Repeats until 6 defense cards.
        """
        print("\n--- Defense Card Draft Phase ---")
        for player in [self.player1, self.player2]:
            print(f"\n{player.name}'s Defense Draft:")
            for i in range(3): # Repeat 3 times to get 6 cards
                drawn_cards = self.deck.draw(3)
                print(f"  Drawn cards: {[str(c) for c in drawn_cards]}")

                # For bot, it will just keep 2 and discard 1 randomly
                # In a real game, player would choose which 2 to keep
                cards_to_keep = random.sample(drawn_cards, 2)
                card_to_discard = [c for c in drawn_cards if c not in cards_to_keep][0]

                player.add_defense_card(cards_to_keep[0])
                player.add_defense_card(cards_to_keep[1])
                self.discard_pile.add_card(card_to_discard)
                print(f"  Kept: {cards_to_keep[0]}, {cards_to_keep[1]}. Discarded: {card_to_discard}")
            print(f"{player.name}'s final defense hand ({len(player.defense_hand)} cards): {player.defense_hand}")


    def _action_phase(self):
        """
        Simulates the 6 rounds of attack and defense.
        """
        print("\n--- Action Phase (6 Rounds) ---")
        self.round_logs = []
        rounds_played = 0
        attacker_card_history = [] # To keep track of attacker's played cards for combo bonuses

        # Attacker pre-determines attack order (módosítottuk, hogy a támadó állítsa előre a sorrendet)
        attacker_ordered_cards = self.attacker.choose_attack_order()
        print(f"{self.attacker.name} pre-determined attack order: {[str(c) for c in attacker_ordered_cards]}")

        while rounds_played < 6:
            # Check for phase end conditions before starting a new round
            if self.rules_engine.check_phase_end(self.attacker.serious_injuries, rounds_played):
                break

            rounds_played += 1
            print(f"\n--- Round {rounds_played} ---")

            # Védő kezdeményez (a védő választ kártyát a saját kezéből)
            defender_played_card = self.defender.choose_defense_card()
            if not defender_played_card:
                print(f"{self.defender.name} has no cards left to defend with. Phase ends early.")
                break

            # Támadó válaszol (a előre meghatározott sorrendből veszi a következő kártyát)
            attacker_played_card = attacker_ordered_cards.pop(0)
            if not attacker_played_card:
                print(f"{self.attacker.name} has no cards left to attack with. Phase ends early.")
                break

            print(f"{self.defender.name} (Defender) plays: {defender_played_card}")
            print(f"{self.attacker.name} (Attacker) responds with: {attacker_played_card}")

            # Eredmény számítás (itt felcseréljük a támadó és védő szerepét a számításnál)
            initial_damage, serious_injury_to_defender, two_vs_figure_bonus_applied = \
                self.rules_engine.calculate_round_outcome(defender_played_card, attacker_played_card)

            # A támadó kártyatörténetéhez hozzáadjuk a kártyát
            attacker_card_history.append(attacker_played_card)

            # Bónuszok alkalmazása
            damage_breakdown = self.rules_engine.apply_bonuses(
                attacker_card_history, attacker_played_card, initial_damage, serious_injury_to_defender, two_vs_figure_bonus_applied
            )
            final_damage = damage_breakdown['final_damage']

            if serious_injury_to_defender:
                self.defender.suffer_serious_injury()
                print(f"  {self.defender.name} suffered a serious injury.")
                final_damage = 0
            elif final_damage > 0:
                self.attacker.take_damage(final_damage)
                print(f"  {self.defender.name} dealt {final_damage} damage to {self.attacker.name}.")
            else:
                print("  Round neutralized. No damage, no injury.")

            self.round_logs.append({
                'round': rounds_played,
                'defender': self.defender.name,
                'attacker': self.attacker.name,
                'defender_card': str(defender_played_card),
                'attacker_card': str(attacker_played_card),
                'damage_dealt': final_damage,
                'defender_serious_injury': serious_injury_to_defender,
                'defender_total_injuries': self.defender.serious_injuries,
                'attacker_total_damage': self.attacker.damage,
                'damage_breakdown': damage_breakdown
            })

            self.discard_pile.add_card(defender_played_card)
            self.discard_pile.add_card(attacker_played_card)

        print("\n--- Action Phase End ---")
        print(f"Defender ({self.defender.name}) serious injuries: {self.defender.serious_injuries}")
        print(f"Attacker ({self.attacker.name}) total damage: {self.attacker.damage}")

    def play_duel_phase(self, starting_attacker_name):
        """
        Orchestrates a full duel phase.
        Returns a dictionary with phase results.
        """
        print(f"\n--- Starting New Duel Phase ---")
        self.player1.reset_for_new_phase()
        self.player2.reset_for_new_phase()
        self.deck = Deck() # New shuffled deck for each phase
        self.discard_pile = DiscardPile() # New discard pile for each phase

        self._assign_roles(starting_attacker_name)

        self._draft_attack_cards()
        self._draft_defense_cards()
        
        initial_attacker_hand_cards = [repr(card) for card in self.attacker.attack_hand.cards] 
        initial_defender_hand_cards = [repr(card) for card in self.defender.defense_hand.cards]

        self._action_phase()

        # Determine phase winner
        phase_winner = None
        if self.attacker.serious_injuries >= 3:
            phase_winner = self.defender.name
        else:
            phase_winner = self.attacker.name

        return {
            'attacker_name': self.attacker.name,
            'defender_name': self.defender.name,
            'attacker_final_injuries': self.attacker.serious_injuries,
            'defender_final_damage': self.defender.damage,
            'phase_winner': phase_winner,
            'round_logs': self.round_logs,
            'initial_attacker_hand': initial_attacker_hand_cards, # Log initial hand
            'initial_defender_hand': initial_defender_hand_cards  # Log initial hand
        }

if __name__ == '__main__':
    # Simple test for match.py
    print("Testing match.py...")
    bot1 = BotPlayer("Bot_Alpha")
    bot2 = BotPlayer("Bot_Beta")

    match = Match(bot1, bot2)
    phase_results = match.play_duel_phase(bot1.name) # Bot_Alpha starts as attacker

    print("\n--- Duel Phase Results ---\n")
    print(f"Attacker: {phase_results['attacker_name']}")
    print(f"Defender: {phase_results['defender_name']}")
    print(f"Attacker Final Serious Injuries: {phase_results['attacker_final_injuries']}")
    print(f"Defender Final Damage: {phase_results['defender_final_damage']}")
    print(f"Phase Winner: {phase_results['phase_winner']}")

    print("\n--- Round Logs ---")
    for log in phase_results['round_logs']:
        print(f"Round {log['round']}: {log['attacker_card']} (Attacker) vs {log['defender_card']} (Defender)")
        print(f"    Damage Dealt: {log['damage_dealt']}, Attacker Serious Injury: {log['attacker_serious_injury']}")
        print(f"    Attacker Total Injuries: {log['attacker_total_injuries']}, Defender Total Damage: {log['defender_total_damage']}")
        print(f"    Damage Breakdown: {log['damage_breakdown']}")
