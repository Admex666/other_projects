from player import BotPlayer
from match import Match
from strategy import BaseStrategy
import json

class Simulation:
    """
    Runs multiple matches between two bots with given strategies.
    """
    def __init__(self, strategy_a: BaseStrategy, strategy_b: BaseStrategy):
        self.strategy_a = strategy_a
        self.strategy_b = strategy_b
        self.player_a_name = "Player_A"
        self.player_b_name = "Player_B"
        self.log = []

    def run_simulation(self, num_matches):
        print(f"Running {num_matches} matches...")
        
        player_a_wins = 0
        player_b_wins = 0
        total_damage_a = 0
        total_damage_b = 0
        total_serious_injuries_a = 0
        total_serious_injuries_b = 0
        
        for i in range(num_matches):
            # Alternate who is the starting attacker to make it fair
            starting_attacker = self.player_a_name if i % 2 == 0 else self.player_b_name
            
            player_a = BotPlayer(self.player_a_name, self.strategy_a)
            player_b = BotPlayer(self.player_b_name, self.strategy_b)
            
            current_match = Match(player_a, player_b)
            phase_results = current_match.play_duel_phase(starting_attacker)
            
            if phase_results['phase_winner'] == self.player_a_name:
                player_a_wins += 1
            else:
                player_b_wins += 1

            total_damage_a += player_a.damage
            total_damage_b += player_b.damage
            total_serious_injuries_a += player_a.serious_injuries
            total_serious_injuries_b += player_b.serious_injuries

            # Save full log for later analysis
            self.log.append(phase_results)

            if (i + 1) % 100 == 0:
                print(f"  Completed {i + 1} matches.")

        print("\n--- Simulation Complete ---")
        print(f"Strategy A ({self.strategy_a.__class__.__name__}) vs Strategy B ({self.strategy_b.__class__.__name__})")
        print(f"Total Matches: {num_matches}")
        print(f"Player A Wins: {player_a_wins} ({player_a_wins / num_matches * 100:.2f}%)")
        print(f"Player B Wins: {player_b_wins} ({player_b_wins / num_matches * 100:.2f}%)")
        print(f"Average Damage dealt by A: {total_damage_b / num_matches:.2f}")
        print(f"Average Damage dealt by B: {total_damage_a / num_matches:.2f}")
        print(f"Average Serious Injuries received by A: {total_serious_injuries_a / num_matches:.2f}")
        print(f"Average Serious Injuries received by B: {total_serious_injuries_b / num_matches:.2f}")

    def save_log_to_file(self, filename="simulation_log.json"):
        """Saves the simulation log to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=4, ensure_ascii=False)
        print(f"Simulation log saved to {filename}")
