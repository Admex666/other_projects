"""Domination victory condition evaluator."""
from typing import Optional
from pincer.core.enums import PlayerId
from pincer.state.state import GameState


class VictoryEvaluator:
    """Evaluates endgame conditions according to Pincer rules."""

    @staticmethod
    def is_board_fully_colonized(state: GameState) -> bool:
        """Returns True if no legal space remains for any new colony on the board."""
        existing_nodes = [c.node_id for c in state.colonies.values()]
        return not state.board.any_valid_colony_site_remaining(
            existing_colony_nodes=existing_nodes,
            min_distance=state.config.min_colony_distance,
        )

    @classmethod
    def check_domination_winner(cls, state: GameState) -> Optional[PlayerId]:
        """Checks if any player satisfies the victory condition.
        
        Evaluates both:
        1. Classic Rules target: controlling 4 colonies (or configured threshold).
        2. Domination Rules: controlling >= 75% of colonies when board is fully colonized.
        """
        total_colonies = len(state.colonies)
        if total_colonies == 0:
            return None

        # Check Classic target colonies threshold first if configured
        if state.config.classic_target_colonies is not None:
            for player_id in state.players:
                controlled = state.get_player_colonies(player_id)
                if len(controlled) >= state.config.classic_target_colonies:
                    return player_id

        # Check board completion if configured
        if state.config.domination_requires_board_completion:
            if not cls.is_board_fully_colonized(state):
                return None

        threshold = state.config.domination_control_fraction
        for player_id in state.players:
            controlled = state.get_player_colonies(player_id)
            if (len(controlled) / total_colonies) >= threshold:
                return player_id

        return None
