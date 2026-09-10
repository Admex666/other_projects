"""Igaz-Hamis mechanizmus implementáció."""

from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class TrueFalseMechanism(BaseMechanism):
    """Kétválasztós Igaz / Hamis kérdésmechanizmus."""

    mechanism_type = QuestionMechanism.TRUE_FALSE

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "options": ["Igaz", "Hamis"],
            "correct_answer": "Igaz" if "igaz" in str(correct_value).lower() else "Hamis"
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """Értékelés: 'igaz' vagy 'hamis' egyezés."""
        given_clean = str(given_answer).strip().lower()
        correct_clean = str(correct_answer).strip().lower()

        # Normalizálás: pl. true/false -> igaz/hamis
        if given_clean in ["true", "i", "1", "igen"]:
            given_clean = "igaz"
        elif given_clean in ["false", "h", "0", "nem"]:
            given_clean = "hamis"

        if correct_clean in ["true", "i", "1", "igen"]:
            correct_clean = "igaz"
        elif correct_clean in ["false", "h", "0", "nem"]:
            correct_clean = "hamis"

        is_correct = (given_clean == correct_clean)
        score = 1.0 if is_correct else 0.0
        feedback = "Helyes válasz!" if is_correct else f"Helytelen! A helyes válasz: {correct_answer}"
        return is_correct, score, feedback
