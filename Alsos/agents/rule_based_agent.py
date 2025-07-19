# agents/rule_based_agent.py
import typing
from typing import List, Dict, Optional, Tuple
from agents.base_agent import PlayerAgent

from game.definitions import Card, Suit, Rank, GameType, BonusType
from config import BASE_FEATURE_ORDER, BONUS_POINTS

class RuleBasedPlayerAgent(PlayerAgent):
    """An agent that makes simple rule-based decisions."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        # Get player's current hand
        hand = game_state.hands[player_name]
        trump_indicator_suit = game_state.trump_indicator.suit if game_state.trump_indicator else None

        # --- Basic Bidding Strategy ---

        # 1. Evaluate trump indicator suit
        if trump_indicator_suit:
            trump_cards_in_hand = [c for c in hand if c.suit == trump_indicator_suit]
            # If 'y' to accept trump indicator is an option and we have a decent number of trumps
            if 'y' in options and len(trump_cards_in_hand) >= 3:
                return 'y'

        # 2. Evaluate bidding a different suit
        # The game asks for each suit one-by-one. The agent just decides yes or no.
        if 'y' in options and current_bid_context and 'bid' in current_bid_context:
            # Figure out which suit is being proposed from the context string
            proposed_suit = None
            for s in Suit:
                if s.value in current_bid_context:
                    proposed_suit = s
                    break
            
            # If a suit was found, evaluate the hand for that suit
            if proposed_suit:
                suit_cards_in_hand = [c for c in hand if c.suit == proposed_suit]
                # Define the condition for saying 'y' to this new suit bid
                is_strong_enough = len(suit_cards_in_hand) >= 2 and any(c.rank in [Rank.ACE, Rank.X, Rank.KING] for c in suit_cards_in_hand)
                
                if is_strong_enough:
                    return 'y'

        # 3. Consider No-Trump
        if 'No-Trump' in options:
            # Check for balanced hand with high cards, few singletons, no very weak suits
            has_strong_aces_tens = len([c for c in hand if c.rank in [Rank.ACE, Rank.X]]) >= 3
            if has_strong_aces_tens:
                return 'No-Trump'

        # 4. Consider Betli (simplified: if hand is very low on points)
        if 'Betli' in options:
            total_points = sum(game_state._get_card_points(c) for c in hand) # Assuming non-trump points
            if total_points < 30: # Very low point hand might be good for betli
                return 'Betli'

        # Default fallback (original logic, but less likely to be hit with better strategy)
        if 'n' in options: return 'n'
        return options[0] if options else 'pass'

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        # Simple rule: Announce bonuses if we're the taker and have good cards
        hand = game_state.hands[player_name]
        announcements = []
        
        # Check each available bonus
        for num, (bonus_type, phase) in available_bonuses_info:
            should_announce = False
            
            if bonus_type == BonusType.KASSZA:
                # Only taker can announce Kassza
                if player_name == game_state.taker:
                    should_announce = True
            
            elif bonus_type == BonusType.ABSZOLUT:
                # Announce if we have high card points
                total_points = sum(game_state._get_card_points(c, c.suit == game_state.trump_suit) for c in hand)
                if total_points > 40:
                    should_announce = True
            
            if should_announce:
                announcements.append(str(num))
        
        if announcements:
            return ','.join(announcements)
        else:
            return 'pass'

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        if not valid_cards:
            return game_state.hands[player_name][0] # Fallback, should ideally not happen

        # For Betli, play the lowest possible card to avoid winning tricks
        if game_state.game_type == GameType.BETLI:
            # Sort by point value (ascending), then by rank (ascending)
            valid_cards.sort(key=lambda c: (game_state._get_card_points(c, False), c.rank.value))
            return valid_cards[0]

        # General strategy for Trump/No-Trump games:
        if not current_trick: # Leading the trick
            # Play a high card from your longest suit to try and establish control
            # Or play a low card if you want to save high cards for later
            
            # Simple version: Play highest point card from hand (can be refined)
            # Find the card with the highest points in hand (not just valid cards)
            best_card = None
            max_points = -1
            for card in game_state.hands[player_name]:
                points = game_state._get_card_points(card, card.suit == game_state.trump_suit)
                if points > max_points:
                    max_points = points
                    best_card = card
            return best_card if best_card else valid_cards[0] # Return the highest card from *hand*

        else: # Not leading the trick
            led_card = list(current_trick.values())[0]
            led_suit = led_card.suit
            
            # Find the current winning card in the trick
            trick_winner_card = None
            max_trick_value = -1
            for p, c in current_trick.items():
                val = game_state._get_card_value_for_comparison(c)
                if val > max_trick_value:
                    max_trick_value = val
                    trick_winner_card = c

            # Try to win the trick if possible and desirable
            for card in valid_cards:
                if game_state._get_card_value_for_comparison(card) > max_trick_value:
                    # If we can win with a valid card, play it.
                    # This could be refined: don't overplay, save trumps if unnecessary.
                    return card
            
            # If cannot win, play the lowest valid card to save higher cards
            # Sort valid cards by point value (ascending), then by rank (ascending)
            valid_cards.sort(key=lambda c: (game_state._get_card_points(c, c.suit == game_state.trump_suit), c.rank.value))
            return valid_cards[0] # Play the lowest point card if unable to win
