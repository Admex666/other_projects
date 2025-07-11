import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import joblib

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
            if event.get('event') == 'bidding_decision':  # You'll need to log these events
                context = event['context']
                features = {
                    'context': context['bid_context'],
                    'hand_size': len(context['hand']),
                    'trump_indicator_suit': context['trump_indicator_suit'],
                    'trump_cards': context['trump_cards'],
                    'high_cards': context['high_cards'],
                    'hearts_count': context['hearts_count'],
                    'bells_count': context['bells_count'],
                    'leaves_count': context['leaves_count'],
                    'acorns_count': context['acorns_count'],
                    'total_points': context['total_points'],
                    'options': ','.join(context['options']),
                    'chosen_option': context['chosen_option']
                }
                samples.append(features)
    
    return pd.DataFrame(samples)

def prepare_bonus_training_data(game_data):
    """Prepare training data for bonus announcements"""
    samples = []
    
    for game in game_data:
        for event in game['log']:
            if event.get('event') == 'bonus_announced':
                # Find the corresponding bonus decision in the log
                # We need to look back to find the available bonuses
                for prev_event in reversed(game['log'][:game['log'].index(event)]):
                    if prev_event.get('event') == 'player_decision' and \
                       'available_bonuses_info' in prev_event['context']:
                        # Found the decision point
                        context = prev_event['context']
                        player = event['player']
                        
                        # Create features for all available bonuses
                        base_features = {
                            'game_type': context['game_type'],
                            'trump_suit': context['trump_suit'],
                            'is_taker': 1 if player == context['player'] else 0,
                            'phase': event['phase'],
                            'hand_size': len(context['hand']),
                            'high_card_count': sum(1 for c_str in context['hand'] 
                                               if any(rank in c_str for rank in ['ACE', 'X', 'KING'])),
                            'trump_count': sum(1 for c_str in context['hand'] 
                                         if context['trump_suit'] and 
                                         context['trump_suit'] in c_str.split(' of ')[1]),
                            'announced': 0  # Default to not announced
                        }
                        
                        # Mark which bonuses were actually announced
                        announced_bonuses = [bt for bt, ph in game['log'][-1]['context']['bonus_announcements'].get(player, [])]
                        
                        for num, (bonus_type, phase) in context['available_bonuses_info']:
                            features = base_features.copy()
                            features['bonus_type'] = bonus_type
                            features['bonus_number'] = num
                            features['announced'] = 1 if bonus_type in announced_bonuses else 0
                            samples.append(features)
                        break
                    
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
    """Train the bonus announcement model"""
    if len(df) == 0:
        return None, None
        
    X = df.drop('announced', axis=1)
    y = df['announced']
    
    encoder = OneHotEncoder(handle_unknown='ignore')
    X_encoded = encoder.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)
    
    return model, encoder

def analyze_game_logs(filename="simulated_game_logs.jsonl"):
    """
    Opens a .jsonl file, reads game logs, and performs a basic analysis.
    """
    game_data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                game_data.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return

    print(f"Successfully loaded {len(game_data)} game logs from '{filename}'.\n")

    # --- Example Analysis ---

    # 1. Count game outcomes
    game_outcomes = {}
    for game_log in game_data:
        if 'game_outcome' in game_log['log'][-1]: # Assuming game_outcome is in the last event
            outcome = game_log['log'][-1]['game_outcome']
            game_outcomes[outcome] = game_outcomes.get(outcome, 0) + 1

    print("Game Outcomes Summary:")
    for outcome, count in game_outcomes.items():
        print(f"- {outcome}: {count} times")
    print("-" * 30)
    
    # Új funkció: modell tanítása
    print("\nPreparing training data...")
    df = prepare_training_data(game_data)
    print(f"Prepared {len(df)} training samples")
    
    if len(df) > 100:  # Only if we have enough data
        print("Training card play model...")
        model, encoder = train_model(df)
        joblib.dump({'model': model, 'encoder': encoder}, 'alsos_agent_model.pkl')
        print("Card play model trained and saved to alsos_agent_model.pkl")
        
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
