"""Dedukció és Sztori-kitalálás mechanizmus implementáció (pl. Inquizitor)."""

from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class DeductionMechanism(BaseMechanism):
    """Műcím vagy fogalom kitalálása cselekmény-összefoglaló vagy nyomok alapján."""

    mechanism_type = QuestionMechanism.DEDUCTION

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        options = [correct_value] + distractors[:3]
        return {
            "options": options,
            "correct_answer": correct_value
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        Értékelés:
        - Ha feleletválasztós (ABCD), pontos egyezés
        - Ha szabad szöveges, kisbetűs vagy részleges címegyezés (pl. 'Tüskevár' vs 'A Tüskevár')
        """
        given_clean = str(given_answer).strip().lower()
        correct_clean = str(correct_answer).strip().lower()

        # Névelők eltávolítása a rugalmas összehasonlításhoz
        for prefix in ["a ", "az ", "the "]:
            if given_clean.startswith(prefix):
                given_clean = given_clean[len(prefix):].strip()
            if correct_clean.startswith(prefix):
                correct_clean = correct_clean[len(prefix):].strip()

        is_correct = (given_clean == correct_clean) or (correct_clean in given_clean and len(correct_clean) > 4)
        score = 1.0 if is_correct else 0.0
        feedback = "Kiváló dedukció, helyes!" if is_correct else f"Sajnos nem! A helyes megoldás: {correct_answer}"
        return is_correct, score, feedback
