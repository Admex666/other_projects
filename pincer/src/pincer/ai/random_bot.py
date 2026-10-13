"""Random bot and headless simulation loop for Pincer."""
from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional
from pincer.actions.base import Action
from pincer.core.enums import PlayerId
from pincer.engine.engine import PincerEngine
from pincer.state.state import GameState


class RandomBot:
    """A baseline bot that samples uniformly from legal actions."""

    def __init__(self, player_id: PlayerId, seed: Optional[int] = None) -> None:
        self.player_id = player_id
        self.rng = random.Random(seed)

    def select_action(self, state: GameState) -> Action:
        """Selects a legal action for this bot from the game state."""
        legal_actions = PincerEngine.get_legal_actions(state)
        # Filter actions belonging to this bot
        bot_actions = [a for a in legal_actions if a.player_id == self.player_id]
        if not bot_actions:
            raise RuntimeError(f"No legal actions available for bot {self.player_id}")
        return self.rng.choice(bot_actions)


@dataclass
class SimulationResult:
    """Outcome of an automated game simulation."""
    winner: Optional[PlayerId]
    total_turns: int
    total_actions: int
    final_colony_counts: Dict[PlayerId, int] = field(default_factory=dict)
    terminated_by_limit: bool = False


class SimulationRunner:
    """Executes headless simulations between bots."""

    @staticmethod
    def run_match(
        initial_state: GameState,
        max_turns: int = 150,
        seed: Optional[int] = None
    ) -> SimulationResult:
        """Runs a complete headless simulation match until victory or turn limit."""
        state = initial_state.clone()
        bots = {
            p: RandomBot(player_id=p, seed=(seed + i if seed is not None else None))
            for i, p in enumerate(state.players)
        }

        action_count = 0
        while state.winner is None and state.turn_number <= max_turns:
            # Determine active player (counter-move vs normal phase)
            if state.counter_move_state and state.counter_move_state.is_active:
                acting_player = state.counter_move_state.defender_player_id
            else:
                acting_player = state.current_player

            bot = bots[acting_player]
            action = bot.select_action(state)
            PincerEngine.apply_action(state, action)
            action_count += 1

        colony_counts = {
            p: len(state.get_player_colonies(p)) for p in state.players
        }

        return SimulationResult(
            winner=state.winner,
            total_turns=state.turn_number,
            total_actions=action_count,
            final_colony_counts=colony_counts,
            terminated_by_limit=(state.winner is None),
        )
