import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz
from normalization import normalize_text, extract_year, extract_card_number
from aliases import apply_aliases

class MatchingEngine:
    def __init__(self, confidence_threshold: float = 0.85, review_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.review_threshold = review_threshold
        
    def jaccard_similarity(self, set1: set, set2: set) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def score_match(self, ebay_title: str, card_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Scores a match between an eBay title and TCDB card data.
        card_data keys: player_name, card_number, set_name, year, is_auto, is_memo
        """
        ebay_tokens = set(apply_aliases(normalize_text(ebay_title)))
        
        # 1. Player Match (Critical)
        player_tokens = set(apply_aliases(normalize_text(card_data['player_name'])))
        # We check if most of player tokens are in ebay title
        player_score = 0.0
        if player_tokens:
            matched_player_tokens = player_tokens.intersection(ebay_tokens)
            player_score = len(matched_player_tokens) / len(player_tokens)
            
        # 2. Card Number Match (Critical)
        ebay_card_num = extract_card_number(ebay_title)
        card_num_score = 1.0 if (ebay_card_num and ebay_card_num == str(card_data.get('card_number', '')).lower()) else 0.0
        
        # 3. Set Name Match (Medium)
        set_tokens = set(apply_aliases(normalize_text(card_data['set_name'])))
        set_score = self.jaccard_similarity(set_tokens, ebay_tokens)
        
        # 4. Year Match (Medium)
        ebay_year = extract_year(ebay_title)
        year_score = 1.0 if (ebay_year and ebay_year == card_data.get('year')) else 0.0
        
        # 5. Attributes (Auto/Memo)
        auto_match = 1.0 if (card_data.get('is_auto') and 'auto' in ebay_title.lower()) else 1.0 if not card_data.get('is_auto') else 0.0
        
        # Weighted Final Score
        individual_scores = {
            'player': player_score,
            'number': card_num_score,
            'set': set_score,
            'year': year_score,
            'auto': auto_match
        }
        
        # Weights: Player=0.4, Number=0.3, Set=0.15, Year=0.1, Auto=0.05
        final_score = (
            0.4 * player_score +
            0.3 * card_num_score +
            0.15 * set_score +
            0.1 * year_score +
            0.05 * auto_match
        )
        
        # Boost if player and number match perfectly
        if player_score > 0.9 and card_num_score > 0.9:
            final_score = max(final_score, 0.95)
            
        return final_score, individual_scores

    def filter_candidates(self, ebay_title: str, all_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 1: Fast filtering by Year and Player Name presence."""
        ebay_year = extract_year(ebay_title)
        ebay_title_lower = ebay_title.lower()
        
        candidates = []
        for card in all_cards:
            # Must match year if year is in title
            if ebay_year and card.get('year') != ebay_year:
                continue
            
            # Simple substring check for player last name (usually unique enough for a first pass)
            player_last_name = card['player_name'].split()[-1].lower()
            if player_last_name not in ebay_title_lower:
                continue
                
            candidates.append(card)
            
        return candidates

    def get_best_match(self, ebay_title: str, all_cards: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        candidates = self.filter_candidates(ebay_title, all_cards)
        
        best_match = None
        best_score = 0.0
        
        for cand in candidates:
            score, _ = self.score_match(ebay_title, cand)
            if score > best_score:
                best_score = score
                best_match = cand
                
        if best_score >= self.review_threshold:
            best_match['match_score'] = best_score
            best_match['needs_review'] = best_score < self.confidence_threshold
            return best_match
            
        return None
