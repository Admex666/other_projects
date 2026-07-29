"""
GTO & Exploit Bot Implementation for Schnapsen with Decision Logging & CFR Hooks
"""

import random
from typing import Optional, List, Dict
from schnapsen.game import (
    Bot,
    GamePhase,
    GamePlayEngine,
    GameState,
    Move,
    PlayerPerspective,
    Marriage,
    TrumpExchange,
)
from schnapsen.bots import AlphaBetaBot, RandBot
from schnapsen.bots.rdeep import FirstFixedMoveThenBaseBot
from src.belief_state import BeliefStateModel
from src.closing import TalonClosingEvaluator
from src.decision_logger import DecisionLogger


class GTOExploitBot(Bot):
    """
    Schnapsen bot combining:
    - Phase 1 (Hidden Info): Monte Carlo belief-state rollouts + Talon closing heuristics + Marriage & Exchange priority
    - Phase 2 (Perfect Info): Exact Alpha-Beta Minimax Solver
    - Decision Logger integration for EV tree analysis
    """

    def __init__(
        self,
        name: Optional[str] = "GTOExploitBot",
        num_samples: int = 16,
        depth: int = 4,
        rand: Optional[random.Random] = None,
        logger: Optional[DecisionLogger] = None,
    ) -> None:
        super().__init__(name)
        self.num_samples = max(1, num_samples)
        self.depth = max(1, depth)
        self.rng = rand or random.Random()

        self.delegate_phase2 = AlphaBetaBot()
        self.closing_evaluator = TalonClosingEvaluator()
        self.belief_model = BeliefStateModel(self.rng)
        self.logger = logger

        self.current_game_id = "game_0"
        self.trick_counter = 0

    def get_move(
        self,
        perspective: PlayerPerspective,
        leader_move: Optional[Move],
    ) -> Move:
        self.trick_counter += 1

        # Phase 2: Perfect information -> Exact AlphaBeta Minimax search
        if perspective.get_phase() == GamePhase.TWO:
            move = self.delegate_phase2.get_move(perspective, leader_move)
            if self.logger:
                self.logger.log_decision(
                    game_id=self.current_game_id,
                    trick_num=self.trick_counter,
                    perspective=perspective,
                    leader_move=leader_move,
                    chosen_move=move,
                    chosen_ev=1.0,
                    alternative_evs={str(m): 0.0 for m in perspective.valid_moves() if m != move},
                )
            return move

        # Phase 1: Imperfect information -> Monte Carlo rollout + heuristic evaluation
        valid_moves: List[Move] = perspective.valid_moves()
        if len(valid_moves) == 1:
            return valid_moves[0]

        # Evaluate closing potential
        closing_eval = self.closing_evaluator.evaluate_closing(perspective)

        moves = list(valid_moves)
        self.rng.shuffle(moves)

        best_score = float("-inf")
        best_move = moves[0]
        alternative_evs: Dict[str, float] = {}

        for move in moves:
            total_score = 0.0

            heuristic_boost = 0.0
            if move.is_marriage():
                heuristic_boost += 0.25
            elif move.is_trump_exchange():
                heuristic_boost += 0.20

            if closing_eval.should_close:
                heuristic_boost += closing_eval.confidence * 0.15

            for _ in range(self.num_samples):
                gamestate = self.belief_model.sample_determinization(
                    perspective=perspective, leader_move=leader_move
                )
                eval_score = self._evaluate_rollout(
                    gamestate=gamestate,
                    engine=perspective.get_engine(),
                    leader_move=leader_move,
                    my_move=move,
                )
                total_score += eval_score

            average_score = (total_score / self.num_samples) + heuristic_boost
            alternative_evs[str(move)] = average_score

            if average_score > best_score:
                best_score = average_score
                best_move = move

        if self.logger:
            self.logger.log_decision(
                game_id=self.current_game_id,
                trick_num=self.trick_counter,
                perspective=perspective,
                leader_move=leader_move,
                chosen_move=best_move,
                chosen_ev=best_score,
                alternative_evs=alternative_evs,
            )

        return best_move

    def _evaluate_rollout(
        self,
        gamestate: GameState,
        engine: GamePlayEngine,
        leader_move: Optional[Move],
        my_move: Move,
    ) -> float:
        """
        Simulates playout starting with my_move and returns normalized state score.
        """
        if leader_move:
            leader_bot = FirstFixedMoveThenBaseBot(RandBot(rand=self.rng), leader_move)
            me = follower_bot = FirstFixedMoveThenBaseBot(RandBot(rand=self.rng), my_move)
        else:
            me = leader_bot = FirstFixedMoveThenBaseBot(RandBot(rand=self.rng), my_move)
            follower_bot = RandBot(rand=self.rng)

        new_game_state, _ = engine.play_at_most_n_tricks(
            game_state=gamestate,
            new_leader=leader_bot,
            new_follower=follower_bot,
            n=self.depth,
        )

        if new_game_state.leader.implementation is me:
            my_score = new_game_state.leader.score.direct_points
            opponent_score = new_game_state.follower.score.direct_points
        else:
            my_score = new_game_state.follower.score.direct_points
            opponent_score = new_game_state.leader.score.direct_points

        total = my_score + opponent_score
        if total == 0:
            return 0.5
        return my_score / total

    def notify_trump_exchange(self, move: TrumpExchange) -> None:
        self.belief_model.opponent_profile.total_trump_exchanges += 1

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        self.belief_model.opponent_profile.update_game_end(won)
        self.trick_counter = 0
