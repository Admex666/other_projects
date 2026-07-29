"""
Structured Decision Logger for Schnapsen AI Analysis
Logs state, chosen action, alternative legal actions, and estimated EVs.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from schnapsen.game import Move, PlayerPerspective, GamePhase


class DecisionLogger:
    """
    Logs structured decision entries for offline analysis, debugging, and EV comparisons.
    """

    def __init__(self, log_filepath: str = "logs/decisions.jsonl") -> None:
        self.log_filepath = log_filepath
        os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
        self.entries: List[Dict[str, Any]] = []

    def log_decision(
        self,
        game_id: str,
        trick_num: int,
        perspective: PlayerPerspective,
        leader_move: Optional[Move],
        chosen_move: Move,
        chosen_ev: float,
        alternative_evs: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Creates and writes a structured decision record.
        """
        hand = [str(c) for c in perspective.get_hand()]
        trump = str(perspective.get_trump_card()) if perspective.get_trump_card() else None

        entry = {
            "timestamp": time.time(),
            "game_id": game_id,
            "trick_number": trick_num,
            "phase": "TWO" if perspective.get_phase() == GamePhase.TWO else "ONE",
            "am_i_leader": perspective.am_i_leader(),
            "leader_move": str(leader_move) if leader_move else None,
            "own_hand": hand,
            "trump_card": trump,
            "own_won_cards_count": len(perspective.get_won_cards()),
            "opp_won_cards_count": len(perspective.get_opponent_won_cards()),
            "chosen_action": str(chosen_move),
            "chosen_EV": round(chosen_ev, 4),
            "alternative_EVs": {k: round(v, 4) for k, v in alternative_evs.items()},
        }

        self.entries.append(entry)
        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def clear(self) -> None:
        self.entries.clear()
        if os.path.exists(self.log_filepath):
            os.remove(self.log_filepath)
