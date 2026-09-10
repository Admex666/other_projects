"""Párosító (Matching) mechanizmus implementáció."""

import random
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class MatchingMechanism(BaseMechanism):
    """Két halmaz elemeinek összerendelése (pl. író - mű, város - vármegye)."""

    mechanism_type = QuestionMechanism.MATCHING

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        metadata: dict formátumú párok, pl. {"Petőfi": "János vitéz", "Arany": "Toldi"}
        vagy vesszős stringből elemzés.
        """
        meta = metadata or {}
        pairs: Dict[str, str] = meta.get("pairs", {})

        if not pairs and ":" in str(correct_value):
            # Formátum: "A: 1, B: 2, C: 3"
            for part in str(correct_value).split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    pairs[k.strip()] = v.strip()

        left_items = list(pairs.keys())
        right_items = list(pairs.values())
        random.shuffle(right_items)

        return {
            "left_items": left_items,
            "shuffled_right_items": right_items,
            "correct_pairs": pairs
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        given_answer: dict (pl. {"Petőfi": "János vitéz", ...}) vagy formázott string.
        """
        meta = metadata or {}
        correct_pairs = meta.get("pairs", {})
        if not correct_pairs and isinstance(correct_answer, dict):
            correct_pairs = correct_answer
        elif not correct_pairs and ":" in str(correct_answer):
            correct_pairs = {}
            for part in str(correct_answer).split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    correct_pairs[k.strip().lower()] = v.strip().lower()

        user_pairs = {}
        if isinstance(given_answer, dict):
            user_pairs = {str(k).strip().lower(): str(v).strip().lower() for k, v in given_answer.items()}
        elif ":" in str(given_answer):
            for part in str(given_answer).split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    user_pairs[k.strip().lower()] = v.strip().lower()

        if not correct_pairs:
            return True, 1.0, "Nincs megadott ellenőrző párhalmaz."

        correct_count = sum(1 for k, v in user_pairs.items() if correct_pairs.get(k) == v)
        total = len(correct_pairs)
        score = correct_count / total if total > 0 else 0.0

        if score == 1.0:
            return True, 1.0, f"Minden pár helyes! ({total}/{total})"
        elif score > 0.0:
            return False, round(score, 2), f"Részleges párosítás: {correct_count}/{total} helyes pár."
        else:
            return False, 0.0, "Egyetlen pár sem lett helyesen párosítva."
