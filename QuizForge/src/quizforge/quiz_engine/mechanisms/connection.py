"""Kapcsolat / Mi a közös bennük? (Connection) mechanizmus implementáció."""

from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class ConnectionMechanism(BaseMechanism):
    """Mi a közös a felsorolt elemekben? / Kakukktojás mechanizmus."""

    mechanism_type = QuestionMechanism.CONNECTION

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        meta = metadata or {}
        return {
            "entities": meta.get("entities", []),
            "common_property": correct_value,
            "distractor_properties": distractors
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        Kapcsolat értékelése:
        Kulcsszó- és kifejezés-egyezés vizsgálata a helyes magyarázattal.
        """
        given_clean = str(given_answer).strip().lower()
        correct_clean = str(correct_answer).strip().lower()

        # Teljes egyezés vagy lényegi kulcsszavak jelenléte
        if given_clean == correct_clean:
            return True, 1.0, "Pontos válasz!"

        # Kulcsszavak arányos átfedése (3 betűnél hosszabb szavak)
        correct_keywords = {w for w in correct_clean.replace(",", " ").replace(".", " ").split() if len(w) > 3}
        given_keywords = {w for w in given_clean.replace(",", " ").replace(".", " ").split() if len(w) > 3}

        overlap = correct_keywords.intersection(given_keywords)
        overlap_ratio = len(overlap) / len(correct_keywords) if correct_keywords else 0.0

        if overlap_ratio >= 0.5:
            score = round(min(1.0, 0.6 + overlap_ratio * 0.4), 2)
            return True, score, f"Helyes felismerés! Megtalált kulcsfogalmak: {', '.join(overlap)}"
        elif overlap_ratio > 0.2:
            return False, 0.3, f"Részben eltaláltad, de nem elég pontos. A helyes összefüggés: {correct_answer}"
        else:
            return False, 0.0, f"Nem talált. A helyes összefüggés: {correct_answer}"
