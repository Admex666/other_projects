# predictor.py
# Közös fájl a RobustMatchPredictor osztályhoz

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_selection import SelectKBest, f_classif

def extract_robust_features(shots_df, current_minute, home_team, away_team):
    """
    Extract ONLY robust, predictive features to prevent overfitting
    """
    shots = shots_df[shots_df['minute'] <= current_minute].copy()
    
    features = {}
    features['minute'] = current_minute
    
    if shots.empty:
        # Return minimal features with default values
        return {
            'minute': current_minute,
            'total_xg_home': 0.0,
            'total_xg_away': 0.0,
            'total_shots_home': 0,
            'total_shots_away': 0,
            'total_goals_home': 0,
            'total_goals_away': 0,
            'xg_per_minute_home': 0.0,
            'xg_per_minute_away': 0.0,
            'shots_per_minute_home': 0.0,
            'shots_per_minute_away': 0.0,
            'goal_difference': 0,
            'xg_difference': 0.0,
            'home_xg_ratio': 0.5,
            'minutes_since_last_goal': current_minute,
            'game_tempo': 0.0
        }
    
    # === Core Features Only ===
    for team, team_name in [('home', home_team), ('away', away_team)]:
        team_shots = shots[shots['team_name'] == team_name]
        
        # Basic aggregates
        features[f'total_xg_{team}'] = float(team_shots['shot_statsbomb_xg'].sum())
        features[f'total_shots_{team}'] = int(len(team_shots))
        features[f'total_goals_{team}'] = int(len(team_shots[team_shots['outcome_name'] == 'Goal']))
        
        # Rate features (more robust than totals)
        features[f'xg_per_minute_{team}'] = features[f'total_xg_{team}'] / max(current_minute, 1)
        features[f'shots_per_minute_{team}'] = features[f'total_shots_{team}'] / max(current_minute, 1)
    
    # === Match State Features ===
    features['goal_difference'] = features['total_goals_home'] - features['total_goals_away']
    features['xg_difference'] = features['total_xg_home'] - features['total_xg_away']
    
    # Home xG dominance (normalized)
    total_xg = features['total_xg_home'] + features['total_xg_away']
    features['home_xg_ratio'] = features['total_xg_home'] / max(total_xg, 0.001)
    
    # === Temporal Features ===
    # Minutes since last goal (any team)
    all_goals = shots[shots['outcome_name'] == 'Goal']
    if not all_goals.empty:
        last_goal_minute = all_goals['minute'].max()
        features['minutes_since_last_goal'] = current_minute - last_goal_minute
    else:
        features['minutes_since_last_goal'] = current_minute
    
    # Game tempo
    total_events = features['total_shots_home'] + features['total_shots_away']
    features['game_tempo'] = total_events / max(current_minute, 1)
    
    return features


class RobustMatchPredictor:
    def __init__(self):
        # Simpler models to prevent overfitting
        self.model = RandomForestClassifier(
            n_estimators=50,  # Reduced from 200
            max_depth=4,      # Limited depth
            min_samples_split=10,  # Higher threshold
            min_samples_leaf=5,    # Higher threshold
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_selector = SelectKBest(f_classif, k=10)  # Select only top 10 features
        self.feature_names = None
        self.selected_features = None
        self.is_fitted = False
        
    def prepare_training_data(self, df_matches, time_points=[30, 45, 60]):
        """
        Prepare training data with STRICT separation to prevent leakage
        """
        training_data = []
        
        # Ez a rész függ a parser-től, ezért a training scriptben kell maradnia
        # Ez csak a placeholder
        return pd.DataFrame(training_data)
    
    def fit(self, training_df):
        """Train with proper validation"""
        print("Training robust model...")
        
        # Prepare features
        exclude_cols = ['final_outcome', 'match_id']
        feature_cols = [col for col in training_df.columns if col not in exclude_cols]
        
        X = training_df[feature_cols].fillna(0)
        y = training_df['final_outcome']
        
        print(f"Training with {len(feature_cols)} features on {len(X)} samples")
        print(f"Class distribution: {y.value_counts().to_dict()}")
        
        # Split data by MATCHES (not by rows) to prevent leakage
        unique_matches = training_df['match_id'].unique()
        train_matches, test_matches = train_test_split(
            unique_matches, test_size=0.2, random_state=42
        )
        
        train_mask = training_df['match_id'].isin(train_matches)
        test_mask = training_df['match_id'].isin(test_matches)
        
        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]
        
        print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Feature selection on training data only
        self.feature_selector.fit(X_train_scaled, y_train)
        X_train_selected = self.feature_selector.transform(X_train_scaled)
        X_test_selected = self.feature_selector.transform(X_test_scaled)
        
        # Get selected feature names
        selected_indices = self.feature_selector.get_support()
        self.selected_features = [feature_cols[i] for i, selected in enumerate(selected_indices) if selected]
        self.feature_names = feature_cols
        
        print(f"Selected features: {self.selected_features}")
        
        # Train model
        self.model.fit(X_train_selected, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test_selected)
        test_accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Test Accuracy: {test_accuracy:.2%}")
        print("\nTest Set Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Cross-validation on training set
        cv_scores = cross_val_score(
            self.model, X_train_selected, y_train, 
            cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
            scoring='accuracy'
        )
        print(f"Cross-validation scores: {cv_scores}")
        print(f"CV Mean: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
        
        self.is_fitted = True
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.selected_features,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nFeature Importance:")
        print(feature_importance)
        
        return feature_importance, test_accuracy
    
    def predict_live(self, shots_df, current_minute, home_team, away_team):
        """Make real-time predictions"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Extract features
        features = extract_robust_features(shots_df, current_minute, home_team, away_team)
        
        # Convert to DataFrame
        feature_df = pd.DataFrame([features])
        
        # Ensure all training features are present
        for feature_name in self.feature_names:
            if feature_name not in feature_df.columns:
                feature_df[feature_name] = 0.0
        
        # Select and scale features
        X = feature_df[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        X_selected = self.feature_selector.transform(X_scaled)
        
        # Get predictions
        outcome_pred = self.model.predict(X_selected)[0]
        outcome_proba = self.model.predict_proba(X_selected)[0]
        
        return {
            'predicted_outcome': outcome_pred,
            'probabilities': dict(zip(self.model.classes_, outcome_proba)),
            'current_features': features,
            'confidence': max(outcome_proba)
        }
    
    def get_insights(self, prediction_result, current_minute, home_team, away_team):
        """Generate actionable insights"""
        features = prediction_result['current_features']
        probs = prediction_result['probabilities']
        
        insights = {
            'minute': current_minute,
            'score': f"{features['total_goals_home']}-{features['total_goals_away']}",
            'prediction': prediction_result['predicted_outcome'],
            'confidence': f"{prediction_result['confidence']:.1%}",
            'probabilities': {
                f'{outcome.title()} Win' if outcome != 'draw' else 'Draw': f"{prob:.1%}"
                for outcome, prob in probs.items()
            }
        }
        
        # Key insights based on robust features
        key_insights = []
        
        # xG advantage
        if abs(features['xg_difference']) > 0.3:
            leading_team = "Home" if features['xg_difference'] > 0 else "Away"
            key_insights.append(f"{leading_team} team creating better chances (xG diff: {abs(features['xg_difference']):.2f})")
        
        # Tempo analysis
        if features['game_tempo'] > 0.4:
            key_insights.append("High-intensity match with frequent attacks")
        elif features['game_tempo'] < 0.15 and current_minute > 20:
            key_insights.append("Cagey affair with few clear chances")
        
        # Recent activity
        if features['minutes_since_last_goal'] > 30:
            key_insights.append("Long period without goals - due for action")
        elif features['minutes_since_last_goal'] < 5:
            key_insights.append("Recent goal could shift momentum")
        
        # xG efficiency
        home_xg_ratio = features['home_xg_ratio']
        if home_xg_ratio > 0.7:
            key_insights.append("Home team dominating chances")
        elif home_xg_ratio < 0.3:
            key_insights.append("Away team controlling the game")
        
        insights['key_insights'] = key_insights
        return insights