# utils/logger.py
import json

def save_game_log(game_id: str, game_log: list, filename: str = "game_logs.jsonl"):
    """Saves the game log for a single game to a JSON Lines file."""
    with open(filename, 'a') as f:
        json.dump({"game_id": game_id, "log": game_log}, f)
        f.write('\n')