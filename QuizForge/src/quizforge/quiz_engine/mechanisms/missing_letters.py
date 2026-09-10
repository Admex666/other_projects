"""Betűkiegészítés mechanizmus implementáció (pl. Inquizitor hiányos címek, mondások)."""

from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class MissingLettersMechanism(BaseMechanism):
    """Kihagyott betűkkel megadott cím vagy szólás kitalálása."""

    mechanism_type = QuestionMechanism.MISSING_LETTERS

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
        """Értékelés: szóközök és írásjelek toleranciájával egyezésvizsgálat."""
        given_clean = str(given_answer).strip().lower().replace(",", "").replace(".", "").replace("!", "")
        correct_clean = str(correct_answer).strip().lower().replace(",", "").replace(".", "").replace("!", "")

        # Felesleges többszörös szóközök összevonása
        given_clean = " ".join(given_clean.split())
        correct_clean = " ".join(correct_clean.split())

        # Névelők levágása
        for prefix in ["a ", "az ", "the "]:
            if given_clean.startswith(prefix):
                given_clean = given_clean[len(prefix):].strip()
            if correct_clean.startswith(prefix):
                correct_clean = correct_clean[len(prefix):].strip()

        is_correct = (given_clean == correct_clean) or (len(correct_clean) > 5 and correct_clean in given_clean)
        score = 1.0 if is_correct else 0.0
        feedback = "Telitalálat! Helyesen egészítetted ki." if is_correct else f"Helytelen kiegészítés! A helyes megoldás: {correct_answer}"
        return is_correct, score, feedback
