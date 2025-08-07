import json
import pandas as pd
import numpy as np # For standard deviation
import re # For regex to parse card repr

class Analyzer:
    """
    Handles loading and analyzing simulation data.
    """
    def __init__(self, log_file="simulation_log.json"):
        self.log_file = log_file
        self.data = self._load_data()
        self.df = self._create_dataframe() # Create DataFrame once

    def _load_data(self):
        """Loads simulation data from a JSON file."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Log file '{self.log_file}' not found.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{self.log_file}'.")
            return []

    def _extract_card_value_from_repr(self, card_repr: str):
        """Extracts the card value from its __repr__ string (e.g., "Card('A', 'Spades')" -> "A")."""
        match = re.search(r"Card\('([^']+)',", card_repr)
        if match:
            return match.group(1)
        return None

    def _extract_card_suit_from_repr(self, card_repr: str):
        """Extracts the card suit from its __repr__ string (e.g., "Card('A', 'Spades')" -> "Spades")."""
        match = re.search(r", '([^']+)'\)", card_repr)
        if match:
            return match.group(1)
        return None

    def _get_card_score_value(self, value_str):
        """Returns the numerical score value for a card value string."""
        if value_str.isdigit():
            return int(value_str)
        if value_str == 'J': return 11
        if value_str == 'Q': return 12
        if value_str == 'K': return 13
        if value_str == 'A': return 14
        return 0 # Should not happen

    def _get_card_color_group(self, suit_str):
        """Determines if the card is Red or Black based on suit string."""
        if suit_str in ['Hearts', 'Diamonds']:
            return 'Red'
        return 'Black'

    def _get_hand_features(self, hand_cards_repr: list[str]) -> dict:
        """
        Analyzes a hand of cards (represented as __repr__ strings) and returns key features.
        """
        features = {
            'has_3_same_suit': False,
            'num_figures_aces': 0,
            'has_9': False,
            'has_2': False,
            'average_hand_value': 0.0,
            'num_red_cards': 0,
            'num_black_cards': 0
        }

        if not hand_cards_repr:
            return features

        card_values = [self._extract_card_value_from_repr(c) for c in hand_cards_repr]
        card_suits = [self._extract_card_suit_from_repr(c) for c in hand_cards_repr]
        
        # Count suits for 'has_3_same_suit'
        suit_counts = {}
        for suit in card_suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
            if suit_counts[suit] >= 3:
                features['has_3_same_suit'] = True

        # Count figures/aces, 9s, 2s, and calculate average value
        total_value = 0
        for val_str, suit_str in zip(card_values, card_suits):
            if val_str in ['J', 'Q', 'K', 'A']:
                features['num_figures_aces'] += 1
            if val_str == '9':
                features['has_9'] = True
            if val_str == '2':
                features['has_2'] = True
            
            total_value += self._get_card_score_value(val_str)

            if self._get_card_color_group(suit_str) == 'Red':
                features['num_red_cards'] += 1
            else:
                features['num_black_cards'] += 1

        features['average_hand_value'] = total_value / len(hand_cards_repr)

        return features


    def _create_dataframe(self):
        """Converts the raw log data into a pandas DataFrame for easier analysis."""
        if not self.data:
            return pd.DataFrame()
        
        flattened_data = []
        for match_idx, match in enumerate(self.data):
            # Extract drafted cards for this match
            initial_attacker_hand_repr = match.get('initial_attacker_hand', [])
            initial_defender_hand_repr = match.get('initial_defender_hand', [])

            # Generate hand features
            attacker_hand_features = self._get_hand_features(initial_attacker_hand_repr)
            defender_hand_features = self._get_hand_features(initial_defender_hand_repr)

            # Extract final match results (these are constant for all rounds within a match)
            match_final_damage_defender = match['defender_final_damage']
            match_final_injuries_attacker = match['attacker_final_injuries']
            match_phase_winner = match['phase_winner']

            for round_log_idx, round_log in enumerate(match['round_logs']):
                round_data = {
                    'match_id': match_idx,
                    'round': round_log['round'],
                    'attacker_name': round_log['attacker'],
                    'defender_name': round_log['defender'],
                    'attacker_card': round_log['attacker_card'],
                    'defender_card': round_log['defender_card'],
                    'damage_dealt_round': round_log['damage_dealt'], # Final damage for the round
                    'attacker_serious_injury_round': round_log['attacker_serious_injury'],
                    
                    # Store match-level final results for each round row
                    'defender_final_damage_match': match_final_damage_defender,
                    'attacker_final_injuries_match': match_final_injuries_attacker,
                    'phase_winner': match_phase_winner, # Add phase winner to each round for easier filtering

                    'initial_attacker_hand_repr': initial_attacker_hand_repr, # Raw hand repr for later parsing
                    'initial_defender_hand_repr': initial_defender_hand_repr, # Raw hand repr for later parsing

                    # Add hand features to each round row
                    **{f'attacker_hand_{k}': v for k, v in attacker_hand_features.items()},
                    **{f'defender_hand_{k}': v for k, v in defender_hand_features.items()},

                    # Detailed breakdown from rules_engine
                    'base_hit_damage': round_log['damage_breakdown'].get('base_hit_damage', 0),
                    'suit_bonus': round_log['damage_breakdown'].get('suit_bonus', 0),
                    'color_group_bonus': round_log['damage_breakdown'].get('color_group_bonus', 0),
                    'range_5_8_bonus': round_log['damage_breakdown'].get('range_5_8_bonus', 0),
                    'nine_multiplier_bonus': round_log['damage_breakdown'].get('nine_multiplier_bonus', 0),
                    'two_vs_figure_bonus': round_log['damage_breakdown'].get('two_vs_figure_bonus', 0),
                    'consecutive_low_bonus': round_log['damage_breakdown'].get('consecutive_low_bonus', 0),
                    'total_bonus_damage_round': round_log['damage_breakdown'].get('total_bonus_damage', 0),
                }
                flattened_data.append(round_data)
        
        return pd.DataFrame(flattened_data)

    def get_dataframe(self):
        """Returns the prepared pandas DataFrame."""
        return self.df

    def analyze_win_rates(self):
        """Calculates and prints win rates for each player/strategy."""
        df_matches = self.df.drop_duplicates(subset=['match_id']) # Get one row per match
        if df_matches.empty:
            print("No data to analyze win rates.")
            return

        total_matches = len(df_matches)
        if total_matches == 0:
            print("No matches played.")
            return

        # Assuming Player_A and Player_B are consistent names for strategies
        player_a_name = df_matches['attacker_name'].iloc[0] if not df_matches.empty else "Player_A"
        player_b_name = df_matches['defender_name'].iloc[0] if not df_matches.empty else "Player_B"

        player_a_wins = df_matches[df_matches['phase_winner'] == player_a_name].shape[0]
        player_b_wins = df_matches[df_matches['phase_winner'] == player_b_name].shape[0]

        print("\n--- Win Rate Analysis ---")
        print(f"{player_a_name} Wins: {player_a_wins} ({player_a_wins / total_matches * 100:.2f}%)")
        print(f"{player_b_name} Wins: {player_b_wins} ({player_b_wins / total_matches * 100:.2f}%)")

    def analyze_damage_and_injuries(self):
        """Calculates and prints average damage and injuries."""
        df_matches = self.df.drop_duplicates(subset=['match_id']) # Get one row per match
        if df_matches.empty:
            print("No data to analyze damage and injuries.")
            return

        print("\n--- Damage and Injury Analysis ---")
        
        # Get actual player names from the first match log
        player_a_name = self.data[0]['attacker_name']
        player_b_name = self.data[0]['defender_name']

        # Average Damage taken by each player (when they were the defender)
        # Use the new columns which explicitly store the final match results
        player_a_damage_taken_when_defender = df_matches[df_matches['defender_name'] == player_a_name]['defender_final_damage_match'].mean()
        player_b_damage_taken_when_defender = df_matches[df_matches['defender_name'] == player_b_name]['defender_final_damage_match'].mean()

        # Average Serious Injuries taken by each player (when they were the attacker)
        # Use the new columns for final match results
        player_a_injuries_taken_when_attacker = df_matches[df_matches['attacker_name'] == player_a_name]['attacker_final_injuries_match'].mean()
        player_b_injuries_taken_when_attacker = df_matches[df_matches['attacker_name'] == player_b_name]['attacker_final_injuries_match'].mean()

        print(f"Average Damage taken by {player_a_name} (when Defender): {player_a_damage_taken_when_defender:.2f}")
        print(f"Average Serious Injuries taken by {player_a_name} (when Attacker): {player_a_injuries_taken_when_attacker:.2f}")
        print(f"Average Damage taken by {player_b_name} (when Defender): {player_b_damage_taken_when_defender:.2f}")
        print(f"Average Serious Injuries taken by {player_b_name} (when Attacker): {player_b_injuries_taken_when_attacker:.2f}")


    def analyze_damage_per_rank(self):
        """
        Analyzes which cards (rank) deal how much damage on average.
        Only considers rounds where damage was dealt.
        """
        df_rounds = self.df[self.df['damage_dealt_round'] > 0].copy() # Only winning hits
        if df_rounds.empty:
            print("\nNo winning hits to analyze damage per rank.")
            return

        # Extract card rank (value)
        # Assuming card string format like '♥️A', '♣️10', '♦️K'
        df_rounds['attacker_card_rank'] = df_rounds['attacker_card'].apply(lambda x: x[1:] if len(x) > 1 else x[0])

        damage_by_rank = df_rounds.groupby('attacker_card_rank')['damage_dealt_round'].mean().sort_values(ascending=False)
        
        print("\n--- Average Damage Dealt Per Attacker Card Rank (Winning Hits) ---")
        print(damage_by_rank)

    def analyze_injury_rate_per_rank(self):
        """
        Analyzes which cards (rank) lead to serious injuries for the attacker.
        """
        df_rounds = self.df.copy()
        if df_rounds.empty:
            print("\nNo data to analyze injury rate per rank.")
            return

        df_rounds['attacker_card_rank'] = df_rounds['attacker_card'].apply(lambda x: x[1:] if len(x) > 1 else x[0])

        # Calculate total rounds played with each card rank
        total_plays_by_rank = df_rounds.groupby('attacker_card_rank').size()
        
        # Calculate serious injuries suffered with each card rank
        injuries_by_rank = df_rounds[df_rounds['attacker_serious_injury_round']].groupby('attacker_card_rank').size()

        # Calculate injury rate
        injury_rate_by_rank = (injuries_by_rank / total_plays_by_rank * 100).fillna(0).sort_values(ascending=False)

        print("\n--- Attacker Serious Injury Rate Per Attacker Card Rank ---")
        print(injury_rate_by_rank)

    def analyze_damage_source_breakdown(self):
        """
        Analyzes the percentage of total damage coming from different sources.
        """
        df_rounds = self.df.copy()
        if df_rounds.empty:
            print("\nNo data to analyze damage source breakdown.")
            return

        # Sum up each bonus component across all rounds where damage was dealt
        total_damage_dealt_across_rounds = df_rounds['damage_dealt_round'].sum()

        if total_damage_dealt_across_rounds == 0:
            print("\nTotal damage dealt is zero, cannot break down sources.")
            return

        # Sum up each bonus component
        base_hit_total = df_rounds['base_hit_damage'].sum()
        suit_bonus_total = df_rounds['suit_bonus'].sum()
        color_group_bonus_total = df_rounds['color_group_bonus'].sum()
        range_5_8_bonus_total = df_rounds['range_5_8_bonus'].sum()
        nine_multiplier_bonus_total = df_rounds['nine_multiplier_bonus'].sum()
        two_vs_figure_bonus_total = df_rounds['two_vs_figure_bonus'].sum()
        consecutive_low_bonus_total = df_rounds['consecutive_low_bonus'].sum()

        # Calculate percentages
        breakdown = {
            'Base Hit Damage': base_hit_total,
            'Suit Bonus': suit_bonus_total,
            'Color Group Bonus': color_group_bonus_total,
            '5-8 Range Bonus': range_5_8_bonus_total,
            '9-Multiplier Bonus': nine_multiplier_bonus_total,
            '2 vs Figure Bonus': two_vs_figure_bonus_total,
            'Consecutive Low Bonus': consecutive_low_bonus_total
        }

        print("\n--- Damage Source Breakdown ---")
        for source, amount in breakdown.items():
            percentage = (amount / total_damage_dealt_across_rounds) * 100
            print(f"{source}: {amount:.2f} ({percentage:.2f}%)")
        print(f"Total Damage Accounted For: {sum(breakdown.values()):.2f} (Should match Total Damage Dealt: {total_damage_dealt_across_rounds:.2f})")


    def analyze_win_rate_by_drafted_cards(self):
        """
        Analyzes the win rate associated with specific drafted cards (for the attacker).
        """
        df_matches = self.df.drop_duplicates(subset=['match_id']).copy()
        if df_matches.empty:
            print("\nNo data to analyze win rate by drafted cards.")
            return

        print("\n--- Win Rate by Drafted Cards (Attacker's Initial Hand) ---")
        
        # Get all unique card ranks from the initial attacker hands across all matches
        all_card_ranks = sorted(list(set([self._extract_card_value_from_repr(card_repr) 
                                           for match_data in self.data 
                                           for card_repr in match_data['initial_attacker_hand']])))
        
        results = {}
        for rank in all_card_ranks:
            matches_with_card = 0
            wins_with_card = 0
            
            for match_data in self.data:
                # Check if the card rank is in the initial attacker's hand
                attacker_initial_hand_ranks = [self._extract_card_value_from_repr(card_repr) 
                                               for card_repr in match_data['initial_attacker_hand']]
                
                if rank in attacker_initial_hand_ranks:
                    matches_with_card += 1
                    if match_data['phase_winner'] == match_data['attacker_name']:
                        wins_with_card += 1
            
            if matches_with_card > 0:
                win_rate = (wins_with_card / matches_with_card) * 100
                results[rank] = {'matches': matches_with_card, 'wins': wins_with_card, 'win_rate': win_rate}
            else:
                results[rank] = {'matches': 0, 'wins': 0, 'win_rate': 0.0}

        sorted_results = sorted(results.items(), key=lambda item: item[1]['win_rate'], reverse=True)

        for rank, stats in sorted_results:
            print(f"Card Rank {rank}: Matches: {stats['matches']}, Wins: {stats['wins']}, Win Rate: {stats['win_rate']:.2f}%")

    def analyze_draft_rate_vs_win_rate(self):
        """
        Analyzes draft frequency of specific card types and their correlation with win rates.
        (Figures, 10, 9, 2)
        """
        if not self.data:
            print("\nNo data to analyze draft rate vs. win rate.")
            return

        print("\n--- Draft Rate vs. Win Rate (Specific Card Types for Attacker) ---")

        target_ranks = ['J', 'Q', 'K', 'A', '10', '9', '2']
        
        total_drafted_cards = 0
        for match_data in self.data:
            total_drafted_cards += len(match_data['initial_attacker_hand'])
        
        results = {}
        for rank in target_ranks:
            draft_count = 0
            matches_won_with_card_in_hand = 0
            total_matches_with_card_in_hand = 0

            for match_data in self.data:
                attacker_initial_hand_ranks = [self._extract_card_value_from_repr(card_repr) for card_repr in match_data['initial_attacker_hand']]
                
                # Count draft rate
                draft_count += attacker_initial_hand_ranks.count(rank)

                # Check for win rate when card is in hand
                if rank in attacker_initial_hand_ranks:
                    total_matches_with_card_in_hand += 1
                    if match_data['phase_winner'] == match_data['attacker_name']:
                        matches_won_with_card_in_hand += 1
            
            draft_rate = (draft_count / total_drafted_cards) * 100 if total_drafted_cards > 0 else 0
            win_rate_when_drafted = (matches_won_with_card_in_hand / total_matches_with_card_in_hand) * 100 if total_matches_with_card_in_hand > 0 else 0

            results[rank] = {
                'draft_count': draft_count,
                'draft_rate': draft_rate,
                'win_rate_when_drafted': win_rate_when_drafted
            }

        for rank, stats in sorted(results.items(), key=lambda x: x[1]['draft_rate'], reverse=True):
            print(f"Card Rank {rank}: Draft Count: {stats['draft_count']}, Draft Rate: {stats['draft_rate']:.2f}%, Win Rate (when drafted): {stats['win_rate_when_drafted']:.2f}%")


    def analyze_bot_performance_stability(self):
        """
        Calculates and prints the stability of bot performance (relative standard deviation).
        """
        df_matches = self.df.drop_duplicates(subset=['match_id']).copy()
        if df_matches.empty:
            print("\nNo data to analyze bot performance stability.")
            return

        print("\n--- Bot Performance Stability (Relative Standard Deviation) ---")

        player_a_name = self.data[0]['attacker_name'] # Get actual name from log
        player_b_name = self.data[0]['defender_name']

        # Performance of Player A when they were the attacker
        player_a_as_attacker_df = df_matches[df_matches['attacker_name'] == player_a_name]
        player_a_damage_dealt = player_a_as_attacker_df['defender_final_damage_match']
        player_a_injuries_received = player_a_as_attacker_df['attacker_final_injuries_match']

        # Performance of Player B when they were the attacker
        player_b_as_attacker_df = df_matches[df_matches['attacker_name'] == player_b_name]
        player_b_damage_dealt = player_b_as_attacker_df['defender_final_damage_match']
        player_b_injuries_received = player_b_as_attacker_df['attacker_final_injuries_match']

        def calculate_rsd(data_series):
            if data_series.empty or data_series.mean() == 0:
                return np.nan
            return (data_series.std() / data_series.mean()) * 100

        print(f"\n{player_a_name} Performance Stability (when Attacker):")
        rsd_a_damage = calculate_rsd(player_a_damage_dealt)
        rsd_a_injuries = calculate_rsd(player_a_injuries_received)
        print(f"  Relative Std Dev of Damage Dealt: {rsd_a_damage:.2f}%" if not np.isnan(rsd_a_damage) else "  N/A (Mean Damage is 0)")
        print(f"  Relative Std Dev of Injuries Received: {rsd_a_injuries:.2f}%" if not np.isnan(rsd_a_injuries) else "  N/A (Mean Injuries is 0)")

        print(f"\n{player_b_name} Performance Stability (when Attacker):")
        rsd_b_damage = calculate_rsd(player_b_damage_dealt)
        rsd_b_injuries = calculate_rsd(player_b_injuries_received)
        print(f"  Relative Std Dev of Damage Dealt: {rsd_b_damage:.2f}%" if not np.isnan(rsd_b_damage) else "  N/A (Mean Damage is 0)")
        print(f"  Relative Std Dev of Injuries Received: {rsd_b_injuries:.2f}%" if not np.isnan(rsd_b_injuries) else "  N/A (Mean Injuries is 0)")

    # --- ÚJ ELEMZÉSEK ---

    def analyze_win_rate_by_hand_features(self):
        """
        Analyzes the win rate based on specific features of the attacker's initial hand.
        """
        df_matches = self.df.drop_duplicates(subset=['match_id']).copy()
        if df_matches.empty:
            print("\nNo data to analyze win rate by hand features.")
            return

        print("\n--- Win Rate by Attacker Hand Features ---")

        # Feature: Has 3 or more cards of the same suit
        has_3_same_suit_wins = df_matches[
            (df_matches['attacker_hand_has_3_same_suit'] == True) & 
            (df_matches['phase_winner'] == df_matches['attacker_name'])
        ].shape[0]
        has_3_same_suit_total = df_matches[df_matches['attacker_hand_has_3_same_suit'] == True].shape[0]
        win_rate_3_same_suit = (has_3_same_suit_wins / has_3_same_suit_total * 100) if has_3_same_suit_total > 0 else 0
        print(f"  Hands with 3+ same suit: Total Matches: {has_3_same_suit_total}, Win Rate: {win_rate_3_same_suit:.2f}%")

        # Feature: Number of Figures/Aces
        print("\n  Win Rate by Number of Figures/Aces in Hand:")
        for num_figures in sorted(df_matches['attacker_hand_num_figures_aces'].unique()):
            total_matches = df_matches[df_matches['attacker_hand_num_figures_aces'] == num_figures].shape[0]
            if total_matches > 0:
                wins = df_matches[
                    (df_matches['attacker_hand_num_figures_aces'] == num_figures) & 
                    (df_matches['phase_winner'] == df_matches['attacker_name'])
                ].shape[0]
                win_rate = (wins / total_matches) * 100
                print(f"    {num_figures} Figures/Aces: Total Matches: {total_matches}, Win Rate: {win_rate:.2f}%")

        # Feature: Has a 9
        has_9_wins = df_matches[
            (df_matches['attacker_hand_has_9'] == True) & 
            (df_matches['phase_winner'] == df_matches['attacker_name'])
        ].shape[0]
        has_9_total = df_matches[df_matches['attacker_hand_has_9'] == True].shape[0]
        win_rate_has_9 = (has_9_wins / has_9_total * 100) if has_9_total > 0 else 0
        print(f"\n  Hands with a 9: Total Matches: {has_9_total}, Win Rate: {win_rate_has_9:.2f}%")

        # Feature: Has a 2
        has_2_wins = df_matches[
            (df_matches['attacker_hand_has_2'] == True) & 
            (df_matches['phase_winner'] == df_matches['attacker_name'])
        ].shape[0]
        has_2_total = df_matches[df_matches['attacker_hand_has_2'] == True].shape[0]
        win_rate_has_2 = (has_2_wins / has_2_total * 100) if has_2_total > 0 else 0
        print(f"  Hands with a 2: Total Matches: {has_2_total}, Win Rate: {win_rate_has_2:.2f}%")

        # Feature: Average hand value
        print(f"\n  Average Hand Value (Attacker): {df_matches['attacker_hand_average_hand_value'].mean():.2f}")
        # You could further group by value ranges for more detailed analysis here.


    def analyze_draft_distribution_vs_expected(self):
        """
        Analyzes the actual draft distribution of cards vs. the theoretical expected distribution.
        """
        if not self.data:
            print("\nNo data to analyze draft distribution.")
            return

        print("\n--- Card Draft Distribution vs. Expected (Attacker) ---")

        # Theoretical distribution: 52 cards in a deck, 4 of each rank (A, K, Q, J, 10, ..., 2)
        # Total unique ranks = 13
        # Expected draft rate for any specific rank (e.g., 'A') = (4 cards of that rank / 52 total cards) * 100
        # This is for a single draw. For the draft, it's more complex, but we can look at overall frequency.
        
        # Let's calculate observed draft frequencies first
        observed_draft_counts = {}
        total_drafted_cards = 0
        for match_data in self.data:
            for card_repr in match_data['initial_attacker_hand']:
                card_value = self._extract_card_value_from_repr(card_repr)
                observed_draft_counts[card_value] = observed_draft_counts.get(card_value, 0) + 1
                total_drafted_cards += 1

        if total_drafted_cards == 0:
            print("No cards were drafted.")
            return

        print("Observed Draft Rates:")
        for rank in sorted(observed_draft_counts.keys(), key=lambda x: self._get_card_score_value(x), reverse=True):
            count = observed_draft_counts[rank]
            rate = (count / total_drafted_cards) * 100
            print(f"  Card Rank {rank}: Count: {count}, Rate: {rate:.2f}%")

        # Theoretical expected draft rate for each rank (assuming uniform random draw from a full deck)
        # Each rank has 4 cards. Total cards = 52.
        # So, probability of drawing any specific rank = 4/52 = 1/13
        # Expected rate for each rank = (1/13) * 100 = 7.69%
        print("\nTheoretical Expected Draft Rate for Each Rank (Uniform Distribution): 7.69%")
        print("Note: This is a simplification, as the draft process is not a simple random draw from a full deck each time.")


if __name__ == '__main__':
    # Example usage:
    # 1. Run main.py to generate simulation_log.json
    # 2. Then, run this file to analyze

    analyzer = Analyzer("simulation_log.json")
    analyzer.analyze_win_rates()
    analyzer.analyze_damage_and_injuries()
    analyzer.analyze_damage_per_rank()
    analyzer.analyze_injury_rate_per_rank()
    analyzer.analyze_damage_source_breakdown()
    analyzer.analyze_win_rate_by_drafted_cards()
    analyzer.analyze_draft_rate_vs_win_rate()
    analyzer.analyze_bot_performance_stability()
    
    # --- ÚJ ELEMZÉSEK HÍVÁSA ---
    analyzer.analyze_win_rate_by_hand_features()
    analyzer.analyze_draft_distribution_vs_expected()
