import json

def analyze_game_logs(filename="simulated_game_logs.jsonl"):
    """
    Opens a .jsonl file, reads game logs, and performs a basic analysis.
    """
    game_data = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                game_data.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return

    print(f"Successfully loaded {len(game_data)} game logs from '{filename}'.\n")

    # --- Example Analysis ---

    # 1. Count game outcomes
    game_outcomes = {}
    for game_log in game_data:
        if 'game_outcome' in game_log['log'][-1]: # Assuming game_outcome is in the last event
            outcome = game_log['log'][-1]['game_outcome']
            game_outcomes[outcome] = game_outcomes.get(outcome, 0) + 1

    print("Game Outcomes Summary:")
    for outcome, count in game_outcomes.items():
        print(f"- {outcome}: {count} times")
    print("-" * 30)

# To run the analysis:
if __name__ == "__main__":
    filename = "simulated_game_logs.jsonl" # simulate_game_logs OR human_vs_ai_game_logs
    analyze_game_logs(filename)
