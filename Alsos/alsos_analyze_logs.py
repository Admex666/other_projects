# alsos_analyze_logs.py

import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

def prepare_training_data(game_data):
    """Játéknaplókból kinyeri a tanító adatokat"""
    samples = []
    
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'player_decision':
                context = event['context']
                
                # Minden érvényes kártyához létrehozunk egy mintát
                for card_str in context['valid_cards']:
                    sample = {
                        'game_type': context['game_type'],
                        'trump_suit': context['trump_suit'],
                        'is_taker': 1 if context['player'].startswith('Player 1') else 0,
                        'trick_num': context['trick_num'],
                        'hand_size': len(context['hand']),
                        'card_played': 1 if card_str == context['chosen_card'] else 0,
                        'card_rank': card_str.split(' of ')[0],
                        'card_suit': card_str.split(' of ')[1].split(' ')[0],
                        'led_suit': context['current_trick'][list(context['current_trick'].keys())[0]].split(' of ')[1].split(' ')[0] 
                                  if context['current_trick'] else 'None'
                    }
                    samples.append(sample)
                    
    return pd.DataFrame(samples)

def prepare_bidding_training_data(game_data):
    """Prepare training data for bidding decisions"""
    samples = []
    
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'bidding_decision':
                context = event['context']
                
                # Calculate hand size if not provided
                hand_size = context.get('hand_size', len(context['hand']) if 'hand' in context else 0)
                
                # Convert options list to a string representation
                options = context['options']
                if isinstance(options, list):
                    options_str = ','.join(options)
                else:
                    options_str = str(options)
                
                features = {
                    'context': context['bid_context'],
                    'hand_size': hand_size,
                    'trump_indicator_suit': context.get('trump_indicator_suit', None),
                    'trump_cards': context.get('trump_cards', 0),
                    'high_cards': context.get('high_cards', 0),
                    'hearts_count': context.get('hearts_count', 0),
                    'bells_count': context.get('bells_count', 0),
                    'leaves_count': context.get('leaves_count', 0),
                    'acorns_count': context.get('acorns_count', 0),
                    'total_points': context.get('total_points', 0),
                    'options': options_str,  # Use string representation instead of list
                    'chosen_option': context['chosen_option']
                }
                samples.append(features)
    
    return pd.DataFrame(samples)

def prepare_bonus_training_data(game_data):
    """Prepare training data with bonus success information"""
    samples = []
    
    for game in game_data:
        # First collect all bonus results
        bonus_results = {}
        for event in game['log']:
            if event.get('event') == 'bonus_announced':
                player = event['player']
                bonus_type = event['bonus_type']
                phase = event['phase']
                key = (player, bonus_type, phase)
                bonus_results[key] = None  # Initialize
                
        # Check final results for each bonus
        final_scores = game['log'][-1].get('final_scores', {})
        for player, data in final_scores.items():
            for result in data.get('bonus_results', []):
                if isinstance(result, str) and ':' in result:
                    try:
                        bonus_str, outcome = result.split(':', 1)
                        bonus_str = bonus_str.strip()
                        outcome = outcome.strip()
                        
                        # Handle different bonus string formats
                        if ' (' in bonus_str:
                            bonus_type = bonus_str.split(' (')[0].strip()
                            phase = bonus_str.split(' (')[1].split(')')[0].strip()
                        else:
                            # Fallback for simpler formats
                            bonus_type = bonus_str
                            phase = 'unknown'
                        
                        key = (player, bonus_type, phase)
                        bonus_results[key] = 1 if '+' in outcome else 0
                    except (IndexError, ValueError):
                        # Skip malformed entries
                        continue
        
        # Then process available bonuses
        for event in game['log']:
            if event.get('event') == 'available_bonuses':
                player = event['player']
                phase = event['phase']
                
                # Get player's hand
                hand = []
                for e in reversed(game['log']):
                    if e.get('event') in ['deal_initial_hands', 'deal_final_hands']:
                        hand = e['hands'].get(player, [])
                        break
                
                # Create features for each available bonus
                for num, (bt, ph) in event['available_bonuses']:
                    features = {
                        'game_type': game['log'][-1].get('game_type', 'Trump'),
                        'trump_suit': game['log'][-1].get('trump_suit', None),
                        'is_taker': int(player == game['log'][-1].get('taker', '')),
                        'phase': phase,
                        'hand_size': len(hand),
                        'high_cards': sum(1 for c_str in hand if any(r in c_str for r in ['ACE', 'X', 'KING'])),
                        'trump_cards': sum(1 for c_str in hand if game['log'][-1].get('trump_suit') and 
                                      game['log'][-1]['trump_suit'] in c_str.split(' of ')[1]),
                        'hearts_count': sum(1 for c_str in hand if 'Hearts' in c_str),
                        'bells_count': sum(1 for c_str in hand if 'Bells' in c_str),
                        'leaves_count': sum(1 for c_str in hand if 'Leaves' in c_str),
                        'acorns_count': sum(1 for c_str in hand if 'Acorns' in c_str),
                        'total_points': sum(10 if any(r in c_str for r in ['ACE', 'X']) else 
                                      (4 if 'KING' in c_str else 3 if 'OVER' in c_str else 2 if 'UNDER' in c_str else 0) 
                                      for c_str in hand),
                        'bonus_type': bt,
                        'bonus_number': num,
                        # Add bonus potential features
                        'has_bela': int(any('KING' in c_str and game['log'][-1].get('trump_suit', '') in c_str for c_str in hand)
                                        and any('OVER' in c_str and game['log'][-1].get('trump_suit', '') in c_str 
                                        for c_str in hand)),
                        'has_ulti': int(any('VII' in c_str and game['log'][-1].get('trump_suit', '') in c_str 
                                          for c_str in hand)),
                        'ace_count': sum(1 for c_str in hand if 'ACE' in c_str),
                        # Target variable: 1 if announced and successful, 0 otherwise
                        'success': bonus_results.get((player, bt, phase), 0)
                    }
                    samples.append(features)
    
    return pd.DataFrame(samples)

def train_model(df):
    """Modell betanítása"""
    # Jellemzők és célváltozó szétválasztása
    X = df.drop('card_played', axis=1)
    y = df['card_played']
    
    # Kategorikus változók kódolása
    encoder = OneHotEncoder(handle_unknown='ignore')
    X_encoded = encoder.fit_transform(X)
    
    # Modell létrehozása és tanítása
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)
    
    return model, encoder

def train_bonus_model(df):
    """Train the bonus model to predict success probability"""
    if len(df) == 0:
        return None, None
        
    X = df.drop('success', axis=1)
    y = df['success']
    
    encoder = OneHotEncoder(handle_unknown='ignore')
    X_encoded = encoder.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)
    
    return model, encoder

def train_bidding_model(df):
    """Train the bidding decision model"""
    if len(df) == 0:
        return None, None
        
    X = df.drop('chosen_option', axis=1)
    y = df['chosen_option']
    
    # Ensure all columns are string type
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = X[col].astype(str)
    
    encoder = OneHotEncoder(handle_unknown='ignore')
    X_encoded = encoder.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)
    
    return model, encoder

def analyze_opening_plays(game_data):
    """Analyze what cards agents play as opening moves"""
    opening_plays = defaultdict(list)
    suit_openings = defaultdict(list)
    
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'player_decision' and event['context']['trick_num'] == 1:
                player = event['context']['player']
                card = event['context']['chosen_card']
                
                # Extract card rank and suit
                rank = card.split(' of ')[0]
                suit = card.split(' of ')[1].split(' ')[0]
                
                opening_plays[player].append({
                    'card': card,
                    'rank': rank,
                    'suit': suit,
                    'game_type': event['context']['game_type'],
                    'trump_suit': event['context']['trump_suit'],
                    'hand_size': len(event['context']['hand'])
                })
    
    print("=== OPENING PLAY ANALYSIS ===")
    for player, plays in opening_plays.items():
        print(f"\n{player} Opening Plays:")
        
        # Most common opening cards
        card_counts = Counter([play['card'] for play in plays])
        print(f"Most common opening cards:")
        for card, count in card_counts.most_common(5):
            print(f"  {card}: {count} times")
        
        # Most common opening suits
        suit_counts = Counter([play['suit'] for play in plays])
        print(f"Most common opening suits:")
        for suit, count in suit_counts.most_common():
            print(f"  {suit}: {count} times ({count/len(plays)*100:.1f}%)")
        
        # Most common opening ranks
        rank_counts = Counter([play['rank'] for play in plays])
        print(f"Most common opening ranks:")
        for rank, count in rank_counts.most_common(5):
            print(f"  {rank}: {count} times")

def analyze_suit_length_strategy(game_data):
    """Analyze how suit length affects play strategy"""
    suit_strategies = defaultdict(list)
    
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'player_decision':
                player = event['context']['player']
                hand = event['context']['hand']
                chosen_card = event['context']['chosen_card']
                
                # Count cards by suit in hand
                suit_counts = defaultdict(int)
                for card in hand:
                    suit = card.split(' of ')[1].split(' ')[0]
                    suit_counts[suit] += 1
                
                chosen_suit = chosen_card.split(' of ')[1].split(' ')[0]
                suit_length = suit_counts[chosen_suit]
                
                suit_strategies[player].append({
                    'suit': chosen_suit,
                    'suit_length': suit_length,
                    'trick_num': event['context']['trick_num'],
                    'is_trump': chosen_suit == event['context']['trump_suit'],
                    'hand_size': len(hand)
                })
    
    print("\n=== SUIT LENGTH STRATEGY ANALYSIS ===")
    for player, strategies in suit_strategies.items():
        print(f"\n{player} Suit Length Preferences:")
        
        # Average suit length when playing each suit
        suit_avg_length = defaultdict(list)
        for strategy in strategies:
            suit_avg_length[strategy['suit']].append(strategy['suit_length'])
        
        for suit, lengths in suit_avg_length.items():
            avg_length = sum(lengths) / len(lengths)
            print(f"  {suit}: avg length {avg_length:.1f} (played {len(lengths)} times)")

def analyze_trump_usage(game_data):
    """Analyze how and when players use trump cards"""
    trump_usage = defaultdict(list)
    
    for game in game_data:
        trump_suit = None
        for event in game['log']:
            if event.get('event') == 'bidding_result':
                trump_suit = event.get('trump_suit')
            elif event.get('event') == 'player_decision' and trump_suit:
                player = event['context']['player']
                chosen_card = event['context']['chosen_card']
                current_trick = event['context']['current_trick']
                
                chosen_suit = chosen_card.split(' of ')[1].split(' ')[0]
                is_trump_played = trump_suit in chosen_suit
                
                # Determine if trump was led or played to follow
                led_suit = None
                if current_trick:
                    first_card = list(current_trick.values())[0]
                    led_suit = first_card.split(' of ')[1].split(' ')[0]
                
                trump_usage[player].append({
                    'is_trump': is_trump_played,
                    'trick_num': event['context']['trick_num'],
                    'led_suit': led_suit,
                    'is_leading': led_suit is None or player == list(current_trick.keys())[0],
                    'hand_size': len(event['context']['hand'])
                })
    
    print("\n=== TRUMP USAGE ANALYSIS ===")
    for player, usage in trump_usage.items():
        trump_plays = [u for u in usage if u['is_trump']]
        total_plays = len(usage)
        trump_count = len(trump_plays)
        
        print(f"\n{player} Trump Usage:")
        print(f"  Trump played: {trump_count}/{total_plays} times ({trump_count/total_plays*100:.1f}%)")
        
        if trump_plays:
            # When do they lead trump?
            trump_leads = [t for t in trump_plays if t['is_leading']]
            print(f"  Trump leads: {len(trump_leads)}/{trump_count} trump plays ({len(trump_leads)/trump_count*100:.1f}%)")
            
            # At what hand sizes do they play trump?
            hand_sizes = [t['hand_size'] for t in trump_plays]
            print(f"  Avg hand size when playing trump: {sum(hand_sizes)/len(hand_sizes):.1f}")

def analyze_card_sequence_patterns(game_data):
    """Analyze patterns in card play sequences"""
    sequences = defaultdict(list)
    
    for game in game_data:
        player_sequences = defaultdict(list)
        
        for event in game['log']:
            if event.get('event') == 'player_decision':
                player = event['context']['player']
                card = event['context']['chosen_card']
                rank = card.split(' of ')[0]
                suit = card.split(' of ')[1].split(' ')[0]
                
                player_sequences[player].append({
                    'rank': rank,
                    'suit': suit,
                    'trick_num': event['context']['trick_num']
                })
        
        # Store sequences for each player
        for player, seq in player_sequences.items():
            sequences[player].append(seq)
    
    print("\n=== CARD SEQUENCE PATTERNS ===")
    for player, player_sequences in sequences.items():
        print(f"\n{player} Sequence Analysis:")
        
        # Analyze rank progression patterns
        rank_transitions = defaultdict(int)
        suit_switches = 0
        total_transitions = 0
        
        for sequence in player_sequences:
            for i in range(len(sequence) - 1):
                current = sequence[i]
                next_card = sequence[i + 1]
                
                rank_transitions[f"{current['rank']} -> {next_card['rank']}"] += 1
                if current['suit'] != next_card['suit']:
                    suit_switches += 1
                total_transitions += 1
        
        print(f"  Suit switches: {suit_switches}/{total_transitions} transitions ({suit_switches/total_transitions*100:.1f}%)")
        
        # Most common rank transitions
        print(f"  Most common rank transitions:")
        for transition, count in sorted(rank_transitions.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {transition}: {count} times")

def create_visualizations(game_data):
    """Create visualizations for the analysis"""
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Opening suit distribution
    opening_suits = defaultdict(list)
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'player_decision' and event['context']['trick_num'] == 1:
                player = event['context']['player']
                suit = event['context']['chosen_card'].split(' of ')[1].split(' ')[0]
                opening_suits[player].append(suit)
    
    # Plot opening suits
    ax1 = axes[0, 0]
    for player, suits in opening_suits.items():
        suit_counts = Counter(suits)
        ax1.bar(suit_counts.keys(), suit_counts.values(), alpha=0.7, label=player)
    ax1.set_title('Opening Suit Distribution')
    ax1.set_xlabel('Suit')
    ax1.set_ylabel('Count')
    ax1.legend()
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Trump usage over time
    trump_usage_by_trick = defaultdict(lambda: defaultdict(int))
    for game in game_data:
        trump_suit = None
        for event in game['log']:
            if event.get('event') == 'bidding_result':
                trump_suit = event.get('trump_suit')
            elif event.get('event') == 'player_decision' and trump_suit:
                player = event['context']['player']
                trick_num = event['context']['trick_num']
                chosen_suit = event['context']['chosen_card'].split(' of ')[1].split(' ')[0]
                
                if trump_suit in chosen_suit:
                    trump_usage_by_trick[player][trick_num] += 1
    
    ax2 = axes[0, 1]
    for player, usage in trump_usage_by_trick.items():
        tricks = sorted(usage.keys())
        counts = [usage[trick] for trick in tricks]
        ax2.plot(tricks, counts, marker='o', label=player)
    ax2.set_title('Trump Usage by Trick Number')
    ax2.set_xlabel('Trick Number')
    ax2.set_ylabel('Trump Cards Played')
    ax2.legend()
    
    # 3. Hand size when playing high cards
    high_card_hand_sizes = defaultdict(list)
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'player_decision':
                player = event['context']['player']
                card = event['context']['chosen_card']
                hand_size = len(event['context']['hand'])
                
                if any(rank in card for rank in ['ACE', 'X', 'KING']):
                    high_card_hand_sizes[player].append(hand_size)
    
    ax3 = axes[1, 0]
    for player, sizes in high_card_hand_sizes.items():
        ax3.hist(sizes, alpha=0.7, label=player, bins=range(1, 13))
    ax3.set_title('Hand Size When Playing High Cards')
    ax3.set_xlabel('Hand Size')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    
    # 4. Win rate by opening suit
    opening_wins = defaultdict(lambda: defaultdict(int))
    opening_total = defaultdict(lambda: defaultdict(int))
    
    for game in game_data:
        winner = None
        opening_suit_by_player = {}
        
        # Find game winner
        for event in game['log']:
            if event.get('event') == 'game_end':
                final_scores = event['final_scores']
                winner = max(final_scores.keys(), key=lambda x: final_scores[x]['game_points'])
            elif event.get('event') == 'player_decision' and event['context']['trick_num'] == 1:
                player = event['context']['player']
                suit = event['context']['chosen_card'].split(' of ')[1].split(' ')[0]
                opening_suit_by_player[player] = suit
        
        # Record wins/losses for each opening suit
        for player, suit in opening_suit_by_player.items():
            opening_total[player][suit] += 1
            if player == winner:
                opening_wins[player][suit] += 1
    
    ax4 = axes[1, 1]
    for player in opening_wins.keys():
        suits = list(opening_total[player].keys())
        win_rates = [opening_wins[player][suit] / opening_total[player][suit] * 100 
                    for suit in suits]
        ax4.bar(suits, win_rates, alpha=0.7, label=player)
    ax4.set_title('Win Rate by Opening Suit')
    ax4.set_xlabel('Opening Suit')
    ax4.set_ylabel('Win Rate (%)')
    ax4.legend()
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('alsos_agent_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_game_logs(filename="simulated_game_logs.jsonl"):
    game_data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                game_data.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return

    print(f"Successfully loaded {len(game_data)} game logs from '{filename}'.\n")
    
    # EDA Analysis
    print("=" * 50)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 50)
    
    analyze_opening_plays(game_data)
    analyze_suit_length_strategy(game_data)
    analyze_trump_usage(game_data)
    analyze_card_sequence_patterns(game_data)
    
    # Create visualizations
    create_visualizations(game_data)
    
    # Modell tanítása
    print("\nPreparing training data...")
    df = prepare_training_data(game_data)
    print(f"Prepared {len(df)} training samples")
    
    if len(df) > 100:
        print("Training card play model...")
        model, encoder = train_model(df)
        joblib.dump({'model': model, 'encoder': encoder}, 'alsos_agent_model.pkl')
        print("Card play model trained and saved to alsos_agent_model.pkl")
        
        # Print feature importances
        feature_importances = pd.Series(model.feature_importances_,
                                      index=encoder.get_feature_names_out())
        print("\nCard play feature importances:")
        print(feature_importances.sort_values(ascending=False).head(10))
        
        # Train bonus model
        print("\nPreparing bonus training data...")
        bonus_df = prepare_bonus_training_data(game_data)
        print(f"Prepared {len(bonus_df)} bonus training samples")
        
        if len(bonus_df) > 50:
            print("Training bonus model...")
            bonus_model, bonus_encoder = train_bonus_model(bonus_df)
            joblib.dump({'model': bonus_model, 'encoder': bonus_encoder}, 'alsos_bonus_model.pkl')
            print("Bonus model trained and saved to alsos_bonus_model.pkl")
            
            # Print feature importances
            feature_importances = pd.Series(bonus_model.feature_importances_,
                                          index=bonus_encoder.get_feature_names_out())
            print("\nBonus feature importances:")
            print(feature_importances.sort_values(ascending=False).head(10))
        
# To run the analysis:
if __name__ == "__main__":
    filename = "simulated_game_logs.jsonl" # simulate_game_logs OR human_vs_ai_game_logs
    analyze_game_logs(filename)
