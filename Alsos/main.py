# main.py
from game.engine import AlsosGame
from agents.human_agent import HumanPlayerAgent
from agents.rule_based_agent import RuleBasedPlayerAgent
from agents.learning_agent import LearningPlayerAgent
from utils.logger import save_game_log

def main():
    print("Welcome to Alsós!")
    
    game_mode = "human_vs_ai"  # "human_vs_ai" vagy "simulation"
    num_simulations = 100

    if game_mode == "simulation":
        sim_agents = {
            "Player 1": RuleBasedPlayerAgent(),
            "Player 2": LearningPlayerAgent()
        }
        for i in range(num_simulations):
            print(f"\n--- Simulating Game {i+1} of {num_simulations} ---")
            game = AlsosGame(num_players=2, agents=sim_agents)
            game.play_game()
            # A logika a main.py-ba kerül
            save_game_log(game.game_id, game.game_log, filename="simulated_game_logs.jsonl")

    elif game_mode == 'human_vs_ai':
        human_vs_ai_agents = {
            "Player 1": HumanPlayerAgent(),
            "Player 2": LearningPlayerAgent()
        }
        game = AlsosGame(num_players=2, agents=human_vs_ai_agents)
        game.play_game()
        save_game_log(game.game_id, game.game_log, filename="human_vs_ai_game_logs.jsonl")

if __name__ == "__main__":
    main()