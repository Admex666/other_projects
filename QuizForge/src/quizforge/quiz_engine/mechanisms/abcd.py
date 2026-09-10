"""ABCD (Feleletválasztós) mechanizmus implementáció."""

import random
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class ABCDMechanism(BaseMechanism):
    """Klasszikus 4 válaszlehetőséges mechanizmus."""

    mechanism_type = QuestionMechanism.ABCD

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """4 opció összeállítása keverve."""
        # Legfeljebb 3 disztraktor
        selected_distractors = distractors[:3]
        all_options = [correct_value] + selected_distractors
        random.shuffle(all_options)
        return {
            "options": all_options,
            "correct_answer": correct_value
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """Értékelés: pontos egyezés (kis- és nagybetű független)."""
        given_clean = str(given_answer).strip().lower()
        correct_clean = str(correct_answer).strip().lower()

        is_correct = (given_clean == correct_clean)
        score = 1.0 if is_correct else 0.0
        feedback = "Helyes válasz!" if is_correct else f"Helytelen! A helyes válasz: {correct_answer}"
        return is_correct, score, feedback
