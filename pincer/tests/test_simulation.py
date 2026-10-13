import pytest
from pincer.ai.random_bot import RandomBot, SimulationRunner
from pincer.core.enums import PlayerId, TurnPhase
from pincer.engine.engine import PincerEngine
from pincer.state.setup import create_classic_initial_state


def test_random_bot_selects_legal_actions():
    state = create_classic_initial_state(seed=42)
    bot = RandomBot(player_id=PlayerId.PLAYER_1, seed=42)

    # In Harvest phase, bot chooses HarvestRollAction
    action = bot.select_action(state)
    assert action.player_id == PlayerId.PLAYER_1
    assert type(action).__name__ == "HarvestRollAction"


def test_headless_simulation_run():
    state = create_classic_initial_state(seed=10)
    result = SimulationRunner.run_match(state, max_turns=40, seed=10)

    assert result.total_turns > 0
    assert result.total_actions > 0
    # Both players have colony count tracked
    assert PlayerId.PLAYER_1 in result.final_colony_counts
    assert PlayerId.PLAYER_2 in result.final_colony_counts


def test_deterministic_simulation_reproducibility():
    state1 = create_classic_initial_state(seed=99)
    state2 = create_classic_initial_state(seed=99)

    res1 = SimulationRunner.run_match(state1, max_turns=30, seed=99)
    res2 = SimulationRunner.run_match(state2, max_turns=30, seed=99)

    assert res1.total_turns == res2.total_turns
    assert res1.total_actions == res2.total_actions
    assert res1.winner == res2.winner
    assert res1.final_colony_counts == res2.final_colony_counts
