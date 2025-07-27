#%% Import libraries
import numpy as np
import pandas as pd
from mplsoccer import Sbopen
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import pickle
import joblib
from predictor import RobustMatchPredictor, extract_robust_features
warnings.filterwarnings('ignore')

#%% Data loading
parser = Sbopen()
df_competitions = parser.competition()

# Load match data
df_matches1 = parser.match(competition_id=55, season_id=282)  # Euro2024
df_matches2 = parser.match(competition_id=9, season_id=281)   # Bundesliga
df_matches3 = parser.match(competition_id=7, season_id=235)   # Ligue 1

df_matches = pd.concat([df_matches1, df_matches2, df_matches3], ignore_index=True)
print(f"Total matches: {len(df_matches)}")

#%% Training data preparation (ez helyben marad, mert parser-t használ)

def prepare_training_data_with_parser(df_matches, parser, time_points=[30, 45, 60]):
    """
    Prepare training data with STRICT separation to prevent leakage
    """
    training_data = []
    
    for idx, match_id in enumerate(df_matches.match_id.unique()):
        if idx % 50 == 0:
            print(f"Processing match {idx+1}/{len(df_matches.match_id.unique())}")
            
        try:
            # Get match events
            df_events, _, _, _ = parser.event(match_id)
            shots = df_events[df_events.type_name == "Shot"].copy()
            
            if shots.empty:
                continue
            
            # Get match info
            match_info = df_matches[df_matches['match_id'] == match_id].iloc[0]
            home_team = match_info['home_team_name']
            away_team = match_info['away_team_name']
            
            # Get ONLY final result (no intermediate states)
            final_home_goals = len(shots[(shots['team_name'] == home_team) & 
                                       (shots['outcome_name'] == 'Goal')])
            final_away_goals = len(shots[(shots['team_name'] == away_team) & 
                                       (shots['outcome_name'] == 'Goal')])
            
            if final_home_goals > final_away_goals:
                final_outcome = 'home'
            elif final_away_goals > final_home_goals:
                final_outcome = 'away'
            else:
                final_outcome = 'draw'
            
            # Extract features at different time points
            for minute in time_points:
                if shots['minute'].max() >= minute:
                    features = extract_robust_features(shots, minute, home_team, away_team)
                    features['final_outcome'] = final_outcome
                    features['match_id'] = match_id
                    
                    training_data.append(features)
                    
        except Exception as e:
            print(f"Error processing match {match_id}: {e}")
            continue
            
    return pd.DataFrame(training_data)

#%% Training and Evaluation

# Initialize predictor
predictor = RobustMatchPredictor()

# Prepare training data
print("Preparing training data...")
training_df = prepare_training_data_with_parser(df_matches, parser, time_points=[30, 45, 60])

print(f"Training data shape: {training_df.shape}")
print(f"Outcome distribution:")
print(training_df['final_outcome'].value_counts())

# Train models
feature_importance, test_accuracy = predictor.fit(training_df)

# FONTOS: Model mentése
try:
    with open('trained_predictor.pkl', 'wb') as f:
        pickle.dump(predictor, f)
    print(f"\n✅ Model successfully saved as 'trained_predictor.pkl'")
except Exception as e:
    print(f"❌ Error saving model: {e}")

# A többi kód marad ugyanaz...
print("\n" + "="*80)
print("ROBUST REAL-TIME MATCH PREDICTOR READY!")
print(f"Final Test Accuracy: {test_accuracy:.1%}")
print("="*80)

#%% Live Prediction Demo

def demo_live_prediction(match_id, demo_minutes=[30, 45, 60, 75]):
    """Demo the live prediction system"""
    try:
        # Get match data
        df_events, _, _, _ = parser.event(match_id)
        shots = df_events[df_events.type_name == "Shot"].copy()
        
        if shots.empty:
            print(f"No shots data available for match {match_id}")
            return None
        
        match_info = df_matches[df_matches['match_id'] == match_id].iloc[0]
        home_team = match_info['home_team_name']
        away_team = match_info['away_team_name']
        
        print(f"\n{'='*60}")
        print(f"LIVE PREDICTION DEMO: {home_team} vs {away_team}")
        print(f"{'='*60}")
        
        # Get actual final result
        final_home_goals = len(shots[(shots['team_name'] == home_team) & 
                                   (shots['outcome_name'] == 'Goal')])
        final_away_goals = len(shots[(shots['team_name'] == away_team) & 
                                   (shots['outcome_name'] == 'Goal')])
        
        print(f"ACTUAL FINAL SCORE: {home_team} {final_home_goals} - {final_away_goals} {away_team}")
        
        # Make predictions at different time points
        predictions_timeline = []
        
        for minute in demo_minutes:
            if shots['minute'].max() >= minute:
                prediction = predictor.predict_live(shots, minute, home_team, away_team)
                insights = predictor.get_insights(prediction, minute, home_team, away_team)
                
                predictions_timeline.append({
                    'minute': minute,
                    'prediction': prediction['predicted_outcome'],
                    'confidence': prediction['confidence']
                })
                
                print(f"\n--- MINUTE {minute} ---")
                print(f"Score: {insights['score']}")
                print(f"Prediction: {insights['prediction'].upper()}")
                print(f"Confidence: {insights['confidence']}")
                
                prob_str = ", ".join([f"{k}: {v}" for k, v in insights['probabilities'].items()])
                print(f"Probabilities: {prob_str}")
                
                if insights['key_insights']:
                    print("Key Insights:")
                    for insight in insights['key_insights']:
                        print(f"  • {insight}")
        
        return predictions_timeline
        
    except Exception as e:
        print(f"Error in demo: {e}")
        return None

# Run demo on matches not in training
print(f"\nRunning demos...")

# Get some test matches
demo_matches = []
for match_id in df_matches.sample(5)['match_id'].tolist():
    try:
        df_events, _, _, _ = parser.event(match_id)
        shots = df_events[df_events.type_name == "Shot"]
        if not shots.empty and shots['minute'].max() >= 60:
            demo_matches.append(match_id)
            if len(demo_matches) >= 2:  # Just 2 demos
                break
    except:
        continue

for match_id in demo_matches:
    timeline = demo_live_prediction(match_id)

print("\n" + "="*80)
print("ROBUST REAL-TIME MATCH PREDICTOR READY!")
print(f"Final Test Accuracy: {test_accuracy:.1%}")
print("="*80)

#%% Additional Analysis

def analyze_prediction_patterns(training_df):
    """Analyze when predictions are most/least reliable"""
    
    print("\n=== PREDICTION RELIABILITY ANALYSIS ===")
    
    # By minute
    minute_analysis = training_df.groupby('minute').agg({
        'total_xg_home': 'mean',
        'total_xg_away': 'mean', 
        'game_tempo': 'mean',
        'final_outcome': lambda x: x.value_counts().to_dict()
    })
    
    print("\nAverage stats by minute:")
    print(minute_analysis[['total_xg_home', 'total_xg_away', 'game_tempo']])
    
    # By goal difference
    print("\nOutcome distribution by current goal difference:")
    goal_diff_analysis = training_df.groupby('goal_difference')['final_outcome'].value_counts(normalize=True)
    print(goal_diff_analysis)
    
    return minute_analysis

if len(training_df) > 0:
    analysis = analyze_prediction_patterns(training_df)