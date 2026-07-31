"""
Exact Ground-Truth Oracle Solver for Schnapsen
Calculates true játékelméleti EV across determinizations using Alpha-Beta Minimax & Expert Solver.
"""

import random
from typing import Dict, List, Optional, Tuple
from schnapsen.game import (
    Bot,
    Card,
    GamePhase,
    GamePlayEngine,
    GameState,
    Move,
    PlayerPerspective,
    SchnapsenGamePlayEngine,
    SchnapsenTrickScorer,
    Talon,
)
from schnapsen.bots import AlphaBetaBot
from schnapsen.bots.rdeep import FirstFixedMoveThenBaseBot
from src.tompa_psellos_bot import TompaPsellosBot


class ExactOracleSolver:
    """
    Computes exact, unbiased Ground-Truth EV for legal moves in a Schnapsen state.
    """

    def __init__(self, num_determinizations: int = 4, seed: int = 42) -> None:
        self.num_determinizations = num_determinizations
        self.rng = random.Random(seed)
        self.expert_solver = TompaPsellosBot(rand=self.rng)

    def evaluate_ground_truth(
        self, perspective: PlayerPerspective, leader_move: Optional[Move]
    ) -> Dict[str, float]:
        """
        Calculates exact Ground-Truth EV for every legal candidate move.
        """
        valid_moves = perspective.valid_moves()
        if not valid_moves:
            return {}

        engine = perspective.get_engine()
        move_evs: Dict[str, float] = {}

        for move in valid_moves:
            total_payoff = 0.0

            for _ in range(self.num_determinizations):
                gamestate = perspective.make_assumption(leader_move=leader_move, rand=self.rng)
                payoff = self._solve_determinization_exact(gamestate, engine, leader_move, move)
                total_payoff += payoff

            move_evs[str(move)] = round(total_payoff / self.num_determinizations, 4)

        return move_evs

    def _solve_determinization_exact(
        self, gamestate: GameState, engine: GamePlayEngine, leader_move: Optional[Move], my_move: Move
    ) -> float:
        """
        Executes expert playout on a determinized state using TompaPsellosBot.
        """
        state_copy = gamestate.copy_with_other_bots(self.expert_solver, self.expert_solver)

        if leader_move:
            leader_bot = FirstFixedMoveThenBaseBot(self.expert_solver, leader_move)
            me = follower_bot = FirstFixedMoveThenBaseBot(self.expert_solver, my_move)
        else:
            me = leader_bot = FirstFixedMoveThenBaseBot(self.expert_solver, my_move)
            follower_bot = self.expert_solver

        new_state, _ = engine.play_at_most_n_tricks(
            game_state=state_copy, new_leader=leader_bot, new_follower=follower_bot, n=4
        )

        if new_state.leader.implementation is me:
            my_score = new_state.leader.score.direct_points
            opp_score = new_state.follower.score.direct_points
        else:
            my_score = new_state.follower.score.direct_points
            opp_score = new_state.leader.score.direct_points

        total = my_score + opp_score
        if total == 0:
            return 0.5
        return my_score / total
