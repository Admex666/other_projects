import typing
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import joblib

from agents.base_agent import PlayerAgent
from agents.rule_based_agent import RuleBasedPlayerAgent
from game.definitions import Card, Suit, Rank, GameType, BonusType
from config import BASE_FEATURE_ORDER, BONUS_POINTS

class LearningPlayerAgent(PlayerAgent):
    def __init__(self, model_path=None):
        self.model = RandomForestClassifier(n_estimators=100)
        self.encoder = OneHotEncoder(handle_unknown='ignore')
        self.bidding_model = RandomForestClassifier(n_estimators=100)
        self.bidding_encoder = OneHotEncoder(handle_unknown='ignore')
        self.bonus_model = RandomForestClassifier(n_estimators=100)  
        self.bonus_encoder = OneHotEncoder(handle_unknown='ignore')
        self.model_path = "alsos_agent_model.pkl"
        self.bidding_model_path = "alsos_bidding_model.pkl"
        self.bonus_model_path = "alsos_bonus_model.pkl"
        self.initialize_encoders()
        self.load_models()
    
    def initialize_encoders(self):
        """Initialize encoders with expected feature names for all models"""
        # Card play encoder
        card_features = {
            'game_type': 'Trump',
            'trump_suit': 'Hearts ❤️',
            'is_taker': 0,
            'trick_num': 1,
            'hand_size': 8,
            'card_rank': 'ACE',
            'card_suit': 'Hearts ❤️',
            'led_suit': 'Hearts ❤️'
        }
        df = pd.DataFrame([card_features])
        self.encoder.fit(df)
        
        # Bidding encoder
        bid_features = {
            'context': 'initial',
            'hand_size': 8,
            'trump_indicator_suit': 'Hearts ❤️',
            'trump_cards': 2,
            'high_cards': 3,
            'hearts_count': 2,
            'bells_count': 2,
            'leaves_count': 2,
            'acorns_count': 2,
            'total_points': 30,
            'options': 'y,n'
        }
        bid_df = pd.DataFrame([bid_features])
        self.bidding_encoder.fit(bid_df)
        
        # Bonus encoder
        bonus_features = {
            'game_type': 'Trump',
            'trump_suit': 'Hearts ❤️',
            'is_taker': 1,
            'phase': 'back',
            'hand_size': 8,
            'high_cards': 3,
            'trump_cards': 2,
            'hearts_count': 2,
            'bells_count': 2,
            'leaves_count': 2,
            'acorns_count': 2,
            'total_points': 30,
            'bonus_type': 'Kassza',
            'bonus_number': 1,
            'has_bela': 1,
            'has_ulti': 0,
            'ace_count': 1
        }
        bonus_df = pd.DataFrame([bonus_features])[BASE_FEATURE_ORDER]
        self.bonus_encoder.fit(bonus_df)
    
    def load_models(self):
        # Load card play model
        try:
            loaded = joblib.load(self.model_path)
            self.model = loaded['model']
            self.encoder = loaded['encoder']
        except:
            print("Card play model not found or invalid, initializing new one")
        
        # Load bidding model
        try:
            loaded = joblib.load(self.bidding_model_path)
            self.bidding_model = loaded['model']
            self.bidding_encoder = loaded['encoder']
        except:
            print("Bidding model not found or invalid, initializing new one")
        
        # Load bonus model
        try:
            loaded = joblib.load(self.bonus_model_path)
            self.bonus_model = loaded['model']
            self.bonus_encoder = loaded['encoder']
        except:
            print("Bonus model not found or invalid, initializing new one")
    
    def save_models(self):
        # Save card play model
        if hasattr(self.model, 'estimators_'):
            joblib.dump({'model': self.model, 'encoder': self.encoder}, self.model_path)
        
        # Save bidding model
        if hasattr(self.bidding_model, 'estimators_'):
            joblib.dump({'model': self.bidding_model, 'encoder': self.bidding_encoder}, self.bidding_model_path)
        
        # Save bonus model
        if hasattr(self.bonus_model, 'estimators_'):
            joblib.dump({'model': self.bonus_model, 'encoder': self.bonus_encoder}, self.bonus_model_path)
                
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        # Extract features for bidding decision
        features = self.extract_bid_features(game_state, player_name, options, current_bid_context)
        
        # If we have a trained bidding model, use it
        if hasattr(self.bidding_model, 'estimators_'):
            try:
                # Convert features to DataFrame and encode
                df = pd.DataFrame([features])
                X = self.bidding_encoder.transform(df)
                
                # Predict probabilities for each option
                probas = self.bidding_model.predict_proba(X)[0]
                best_option_idx = np.argmax(probas)
                best_option = options[best_option_idx]
                return best_option
            except Exception as e:
                print(f"Bid model prediction failed: {e}")
        
        # Fallback to rule-based bidding
        rule_based_agent = RuleBasedPlayerAgent()
        return rule_based_agent.choose_bid(game_state, player_name, options, current_bid_context)
        
    def extract_card_features(self, game_state, player_name, current_trick, valid_cards):
        """Extract features consistent with training data format"""
        hand = game_state.hands[player_name]
        context = {
            'game_type': game_state.game_type.value,
            'trump_suit': game_state.trump_suit.value if game_state.trump_suit else 'None',
            'is_taker': int(player_name == game_state.taker),
            'trick_num': len(game_state.tricks[player_name]) + 1,
            'hand_size': len(hand),
            'card_rank': valid_cards[0].rank.name if valid_cards else 'None',
            'card_suit': valid_cards[0].suit.value if valid_cards else 'None',
            'led_suit': list(current_trick.values())[0].suit.value if current_trick else 'None'
        }
        return context
    
    def extract_bid_features(self, game_state, player_name, options, current_bid_context):
        """Extract features for bidding decisions"""
        hand = game_state.hands[player_name]
        trump_indicator_suit = game_state.trump_indicator.suit if game_state.trump_indicator else None
        
        features = {
            'context': current_bid_context or 'initial',
            'hand_size': len(hand),
            'trump_indicator_suit': trump_indicator_suit.value if trump_indicator_suit else 'None',
            'trump_cards': sum(1 for c in hand if trump_indicator_suit and c.suit == trump_indicator_suit),
            'high_cards': sum(1 for c in hand if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
            'hearts_count': sum(1 for c in hand if c.suit == Suit.HEARTS),
            'bells_count': sum(1 for c in hand if c.suit == Suit.BELLS),
            'leaves_count': sum(1 for c in hand if c.suit == Suit.LEAVES),
            'acorns_count': sum(1 for c in hand if c.suit == Suit.ACORNS),
            'total_points': sum(game_state._get_card_points(c) for c in hand),
            'options': ','.join(options)
        }
        
        return features
    
    def extract_bonus_features(self, game_state, player_name, available_bonuses_info):
        """Extract features with added bonus potential information"""
        hand = game_state.hands[player_name]
        
        features = {
            'game_type': game_state.game_type.value,
            'trump_suit': game_state.trump_suit.value if game_state.trump_suit else 'None',
            'is_taker': int(player_name == game_state.taker),
            'phase': game_state.current_bonus_phase,
            'hand_size': len(hand),
            'high_cards': sum(1 for c in hand if c.rank in [Rank.ACE, Rank.X, Rank.KING]),
            'trump_cards': sum(1 for c in hand if game_state.trump_suit and c.suit == game_state.trump_suit),
            'hearts_count': sum(1 for c in hand if c.suit == Suit.HEARTS),
            'bells_count': sum(1 for c in hand if c.suit == Suit.BELLS),
            'leaves_count': sum(1 for c in hand if c.suit == Suit.LEAVES),
            'acorns_count': sum(1 for c in hand if c.suit == Suit.ACORNS),
            'total_points': sum(game_state._get_card_points(c) for c in hand),
             # Add bonus potential metrics
            'has_bela': int(any(c.rank == Rank.KING and c.suit == game_state.trump_suit for c in hand) and 
                       any(c.rank == Rank.OVER and c.suit == game_state.trump_suit for c in hand)),
            'has_ulti': int(any(c.rank == Rank.VII and c.suit == game_state.trump_suit for c in hand)),
            'ace_count': sum(1 for c in hand if c.rank == Rank.ACE)
            }
        
        return features
    
    def evaluate_suit_strength(self, hand: List[Card], trump_suit: Optional[Suit] = None) -> Dict[Suit, Dict[str, float]]:
        """Evaluate the strength of each suit considering card distribution and trick-taking potential"""
        suit_strength = {}
        
        for card in hand:
            suit = card.suit
            if suit not in suit_strength:
                suit_strength[suit] = {
                    'count': 0,
                    'total_points': 0,
                    'high_cards': 0,
                    'is_trump': (suit == trump_suit),
                    'cards': []
                }
            
            suit_strength[suit]['count'] += 1
            suit_strength[suit]['cards'].append(card)
            
            # Calculate points based on trump/non-trump
            if trump_suit and suit == trump_suit:
                if card.rank == Rank.UNDER: points = 20
                elif card.rank == Rank.IX: points = 14
                elif card.rank == Rank.ACE: points = 11
                elif card.rank == Rank.X: points = 10
                elif card.rank == Rank.KING: points = 4
                elif card.rank == Rank.OVER: points = 3
                else: points = 0
            else:
                if card.rank == Rank.ACE: points = 11
                elif card.rank == Rank.X: points = 10
                elif card.rank == Rank.KING: points = 4
                elif card.rank == Rank.OVER: points = 3
                elif card.rank == Rank.UNDER: points = 2
                else: points = 0
                
            suit_strength[suit]['total_points'] += points
            
            if card.rank in [Rank.ACE, Rank.X, Rank.KING]:
                suit_strength[suit]['high_cards'] += 1
        
        # Calculate advanced strength scores
        for suit in suit_strength:
            info = suit_strength[suit]
            
            # Base strength from points and high cards
            base_strength = info['total_points'] * 0.4 + info['high_cards'] * 5
            
            # Length bonus/penalty
            if info['count'] >= 3:
                length_bonus = info['count'] * 1.5  # Long suits are safer to lead
            elif info['count'] == 2:
                length_bonus = 0  # Neutral
            else:
                length_bonus = -2  # Short suits risky to lead
            
            # Trump bonus
            trump_bonus = 8 if info['is_trump'] else 0
            
            # Concentration bonus - prefer suits with multiple high cards
            concentration_bonus = (info['high_cards'] ** 2) * 2 if info['high_cards'] > 1 else 0
            
            # Calculate trick-taking potential
            trick_potential = self._calculate_trick_potential(info['cards'], suit, trump_suit)
            
            final_strength = base_strength + length_bonus + trump_bonus + concentration_bonus + trick_potential
            suit_strength[suit]['strength_score'] = final_strength
        
        return suit_strength
    
    def _calculate_trick_potential(self, cards: List[Card], suit: Suit, trump_suit: Optional[Suit]) -> float:
        """Calculate the potential of cards in this suit to win tricks"""
        if not cards:
            return 0
        
        potential = 0
        
        # Sort cards by power (highest first)
        if suit == trump_suit:
            # Trump order: J, 9, A, 10, K, Q, 8, 7
            trump_order = {Rank.UNDER: 8, Rank.IX: 7, Rank.ACE: 6, Rank.X: 5, 
                          Rank.KING: 4, Rank.OVER: 3, Rank.VIII: 2, Rank.VII: 1}
            sorted_cards = sorted(cards, key=lambda c: trump_order.get(c.rank, 0), reverse=True)
        else:
            # Non-trump order: A, 10, K, Q, J, 9, 8, 7
            normal_order = {Rank.ACE: 8, Rank.X: 7, Rank.KING: 6, Rank.OVER: 5,
                           Rank.UNDER: 4, Rank.IX: 3, Rank.VIII: 2, Rank.VII: 1}
            sorted_cards = sorted(cards, key=lambda c: normal_order.get(c.rank, 0), reverse=True)
        
        # Higher cards have better trick-taking potential
        for i, card in enumerate(sorted_cards):
            if suit == trump_suit:
                # Trump cards have higher base potential
                base_potential = 10 - i * 1.5
            else:
                # Non-trump potential depends on card rank
                if card.rank == Rank.ACE:
                    base_potential = 8 - i * 1.5
                elif card.rank == Rank.X:
                    base_potential = 6 - i * 1.5
                elif card.rank == Rank.KING:
                    base_potential = 4 - i * 1.5
                else:
                    base_potential = max(0, 2 - i * 1.5)
            
            potential += max(0, base_potential)
        
        return potential
    
    def _choose_leading_card(self, game_state, player_name: str, valid_cards: List['Card']) -> 'Card':
        """Choose the best card to lead with considering multiple factors"""
        hand = game_state.hands[player_name]
        suit_strength = self.evaluate_suit_strength(hand, game_state.trump_suit)
        
        # Score each valid card for leading
        card_scores = []
        
        for card in valid_cards:
            suit = card.suit
            suit_info = suit_strength[suit]
            
            # Base score from suit strength
            base_score = suit_info['strength_score']
            
            # Card rank bonus
            if suit == game_state.trump_suit:
                rank_bonus = {Rank.UNDER: 20, Rank.IX: 15, Rank.ACE: 12, Rank.X: 10, 
                             Rank.KING: 5, Rank.OVER: 3, Rank.VIII: 1, Rank.VII: 0}.get(card.rank, 0)
            else:
                rank_bonus = {Rank.ACE: 15, Rank.X: 12, Rank.KING: 8, Rank.OVER: 5,
                             Rank.UNDER: 3, Rank.IX: 2, Rank.VIII: 1, Rank.VII: 0}.get(card.rank, 0)
            
            # Length-based strategy
            if suit_info['count'] >= 4:
                # Long suit - prefer lower cards to establish suit
                length_bonus = -rank_bonus * 0.3
            elif suit_info['count'] == 1:
                # Singleton - prefer high cards
                length_bonus = rank_bonus * 0.5
            else:
                # Medium length - neutral
                length_bonus = 0
            
            # Trump considerations
            if suit == game_state.trump_suit:
                # Leading trump is powerful but depletes trump holding
                trump_bonus = 5 if suit_info['count'] >= 3 else -2
            else:
                trump_bonus = 0
            
            # Safety consideration - avoid leading weak suits if opponents likely have trump
            if suit_info['count'] <= 2 and suit != game_state.trump_suit:
                safety_penalty = -5
            else:
                safety_penalty = 0
            
            total_score = base_score + rank_bonus + length_bonus + trump_bonus + safety_penalty
            card_scores.append((card, total_score))
        
        # Select the highest scoring card
        best_card = max(card_scores, key=lambda x: x[1])[0]
        return best_card
    
    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, 
                                 available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        if hasattr(self.bonus_model, 'estimators_'):
            try:
                bonus_scores = []
                base_features = self.extract_bonus_features(game_state, player_name, available_bonuses_info)
                
                for num, (bonus_type, phase) in available_bonuses_info:
                    features = base_features.copy()
                    features.update({
                        'bonus_type': bonus_type.value,
                        'bonus_number': num,
                        'phase': phase
                    })
                    
                    # Create DataFrame with consistent column order
                    df = pd.DataFrame([features])[BASE_FEATURE_ORDER]
                    X = self.bonus_encoder.transform(df)
                    
                    prob_success = self.bonus_model.predict_proba(X)[0][1]
                    potential_points = BONUS_POINTS[bonus_type][phase] * prob_success
                    
                    # Subtract potential loss if failed
                    potential_loss = BONUS_POINTS[bonus_type][phase] * (1 - prob_success)
                    net_value = potential_points - potential_loss
                    
                    bonus_scores.append((num, net_value))
                
                # Select all bonuses with positive expected value, sorted by value
                good_bonuses = [str(num) for num, value in bonus_scores if value > 0]
                good_bonuses.sort(key=lambda x: -[v for n, v in bonus_scores if str(n) == x][0])
                
                if good_bonuses:
                    return ','.join(good_bonuses)
            except Exception as e:
                print(f"Bonus model prediction failed: {e}")
        
        # Fallback: Aggressive bonus claiming when we're the taker
        if player_name == game_state.taker and available_bonuses_info:
            return str(available_bonuses_info[0][0])
        
        return 'pass'
    
    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        # If leading (first to play in trick)
        if not current_trick:
            return self._choose_leading_card(game_state, player_name, valid_cards)
        
        # Fall back to original model-based or rule-based strategy for non-leading plays
        if hasattr(self.model, 'estimators_'):
            try:
                features = self.extract_card_features(game_state, player_name, current_trick, valid_cards)
                df = pd.DataFrame([features])
                X = self.encoder.transform(df)
                probas = self.model.predict_proba(X)[0]
                best_card_idx = np.argmax(probas)
                return valid_cards[best_card_idx]
            except Exception as e:
                print(f"Card play model prediction failed: {e}")
        
        # Fallback to rule-based strategy
        rule_based_agent = RuleBasedPlayerAgent()
        return rule_based_agent.choose_card_to_play(game_state, player_name, current_trick, valid_cards)