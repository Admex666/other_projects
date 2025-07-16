# agents/human_agent.py
from typing import List, Dict, Optional, Tuple
from agents.base_agent import PlayerAgent

from game.definitions import Card, Suit, Rank, GameType, BonusType
from config import BASE_FEATURE_ORDER, BONUS_POINTS

class HumanPlayerAgent(PlayerAgent):
    """An agent that prompts a human for input."""
    def choose_bid(self, game_state: 'AlsosGame', player_name: str, options: List[str], current_bid_context: Optional[str] = None) -> str:
        # Determine the relevant context for the prompt based on what's passed
        if current_bid_context:
            prompt_context = f"for '{current_bid_context}'"
        else:
            # Fallback for initial trump indicator phase if context isn't explicitly passed
            trump_card_str = str(game_state.trump_indicator) if game_state.trump_indicator else "No indicator"
            prompt_context = f"accepting indicator '{trump_card_str}'"

        prompt = (f"{player_name}, {prompt_context}, "
                  f"do you accept/bid? ({'/'.join(options)}): ")
        
        while True:
            response = input(prompt).strip()
            if response in options:
                return response
            else:
                print(f"Invalid input. Please choose from: {', '.join(options)}")

    def choose_bonus_announcements(self, game_state: 'AlsosGame', player_name: str, available_bonuses_info: List[Tuple[int, Tuple['BonusType', str]]]) -> str:
        print(f"\n{player_name}'s turn to announce bonuses ({game_state.current_bonus_phase})")
        print(f"Available bonuses:")
        for num, (bonus_type, phase) in available_bonuses_info:
            print(f"{num}: {bonus_type.value}")
        print("Enter bonus numbers to announce (comma separated), or 'pass' to skip:")
        return input().strip()

    def choose_card_to_play(self, game_state: 'AlsosGame', player_name: str, current_trick: Dict[str, 'Card'], valid_cards: List['Card']) -> 'Card':
        print(f"\n{player_name}'s turn")
        print(f"Hand:")
        current_hand = game_state.hands[player_name]
        for j, card in enumerate(current_hand):
            print(f"{j}: {card}")
        
        # Display valid cards with their original indices from player's hand for human input
        valid_card_indices = []
        for card in valid_cards:
            try:
                valid_card_indices.append(current_hand.index(card))
            except ValueError:
                # Should not happen if valid_cards truly comes from current_hand
                pass 
        
        print(f"Valid cards (indices from hand): {[f'{idx}: {current_hand[idx]}' for idx in valid_card_indices]}")
        
        print("Choose a card to play (enter number): ")
        try:
            choice_idx = int(input())
            if choice_idx in valid_card_indices:
                return current_hand[choice_idx]
            else:
                print("Invalid choice, playing first valid card.")
                return valid_cards[0]
        except (ValueError, IndexError):
            print("Invalid input, playing first valid card.")
            return valid_cards[0]