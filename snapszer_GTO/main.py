"""
Main Entry Point - Benchmarking GTOExploitBot against Expert Bot & Human Archetypes.
Includes Decision Logging and Net Game Point Difference per deal metrics.
"""

import os
import pathlib
import random
import time
from typing import Optional

from schnapsen.game import Bot, GamePhase, Move, PlayerPerspective, SchnapsenGamePlayEngine
from schnapsen.bots import (
    RandBot,
    BullyBot,
    RdeepBot,
    MiniMaxBot,
    MLPlayingBot,
    MLDataBot,
    train_ML_model,
)
from src.bot import GTOExploitBot
from src.expert_bot import ExpertBot
from src.archetypes import (
    CallingStationBot,
    OverfolderBot,
    AggressiveCloserBot,
    MarriageHunterBot,
    PointCounterFishBot,
)
from src.decision_logger import DecisionLogger
from src.benchmark import BenchmarkSuite


class RandMiniMaxBot(Bot):
    def __init__(self, rng: random.Random, name: Optional[str] = "RandMiniMaxBot") -> None:
        super().__init__(name)
        self.phase1_bot = RandBot(rng)
        self.phase2_bot = MiniMaxBot()

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        if perspective.get_phase() == GamePhase.TWO:
            return self.phase2_bot.get_move(perspective, leader_move)
        return self.phase1_bot.get_move(perspective, leader_move)


def get_or_create_ml_bot(seed: int = 42) -> MLPlayingBot:
    model_dir = pathlib.Path("ML_models")
    model_path = model_dir / "ml_bot_model.joblib"
    replay_path = pathlib.Path("ML_replay_memories") / "training_data.txt"

    if not model_path.exists():
        print("   Generating ML dataset & training ML model...")
        model_dir.mkdir(parents=True, exist_ok=True)
        replay_path.parent.mkdir(parents=True, exist_ok=True)

        if replay_path.exists():
            os.remove(replay_path)

        rng = random.Random(seed)
        engine = SchnapsenGamePlayEngine()
        data_bot1 = MLDataBot(RandBot(rng, "DataRand1"), replay_path)
        data_bot2 = MLDataBot(RandBot(rng, "DataRand2"), replay_path)

        for _ in range(300):
            engine.play_game(data_bot1, data_bot2, rng)

        train_ML_model(replay_path, model_path, model_class="LR")

    return MLPlayingBot(model_path, name="MLPlayingBot")


def main():
    print("=" * 70)
    print("      SCHNAPSEN GTO + EXPLOIT LEAGUE: EXPERT & HUMAN ARCHETYPES     ")
    print("=" * 70)

    seed = 42
    logger = DecisionLogger("logs/decisions.jsonl")
    logger.clear()

    print("\n[1/3] Initializing GTOExploitBot with Decision Logger & League...")
    gto_bot = GTOExploitBot(
        name="GTOExploitBot",
        num_samples=12,
        depth=4,
        rand=random.Random(seed),
        logger=logger,
    )
    ml_bot = get_or_create_ml_bot(seed=seed)

    opponents = [
        ExpertBot(rand=random.Random(201), name="ExpertBot (Tompa)"),
        CallingStationBot(rand=random.Random(202), name="CallingStationBot"),
        OverfolderBot(rand=random.Random(203), name="OverfolderBot"),
        AggressiveCloserBot(rand=random.Random(204), name="AggressiveCloserBot"),
        MarriageHunterBot(rand=random.Random(205), name="MarriageHunterBot"),
        PointCounterFishBot(rand=random.Random(206), name="PointCounterFishBot"),
        RdeepBot(num_samples=6, depth=3, rand=random.Random(207), name="RdeepBot"),
        ml_bot,
        RandMiniMaxBot(rng=random.Random(208), name="RandMiniMaxBot"),
    ]

    games_per_matchup = 500
    suite = BenchmarkSuite(seed=seed)

    print(f"\n[2/3] Running League Tournament ({games_per_matchup} games per opponent)...")
    start_time = time.time()

    for opp in opponents:
        print(f"\n--- Benchmark Matchup: {gto_bot} vs {opp} ---")
        res = suite.run_matchup(gto_bot, opp, num_games=games_per_matchup)
        print(res.summary_table())

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[3/3] Benchmarking completed in {elapsed:.2f} seconds.")
    print(f"      Decision log saved to: {logger.log_filepath} ({len(logger.entries)} decisions logged)")
    print("=" * 70)


if __name__ == "__main__":
    main()
