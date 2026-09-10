"""Sorrendező (Ordering) mechanizmus implementáció."""

import random
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class OrderingMechanism(BaseMechanism):
    """Elemek helyes sorrendbe állítása (időrend, nagyságrend stb.)."""

    mechanism_type = QuestionMechanism.ORDERING

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        correct_value: vesszővel elválasztott helyes sorrend vagy lista
        """
        if isinstance(correct_value, list):
            items = list(correct_value)
        else:
            items = [s.strip() for s in str(correct_value).split(",") if s.strip()]

        shuffled = list(items)
        # Addig keverjük, amíg nem különbözik az eredetitől (ha van legalább 2 elem)
        if len(shuffled) > 1:
            while shuffled == items:
                random.shuffle(shuffled)

        return {
            "shuffled_items": shuffled,
            "correct_order": items
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        Sorrend értékelése:
        - Ha pontos a sorrend: 1.0 pont
        - Részpontszám a helyes pozícióban lévő elemek aránya alapján
        """
        if isinstance(given_answer, list):
            given_items = [str(x).strip().lower() for x in given_answer]
        else:
            given_items = [str(x).strip().lower() for x in str(given_answer).split(",") if str(x).strip()]

        if isinstance(correct_answer, list):
            correct_items = [str(x).strip().lower() for x in correct_answer]
        else:
            correct_items = [str(x).strip().lower() for x in str(correct_answer).split(",") if str(x).strip()]

        if len(given_items) != len(correct_items):
            return False, 0.0, f"A megadott elemek száma ({len(given_items)}) eltér a várttól ({len(correct_items)})."

        correct_positions = sum(1 for g, c in zip(given_items, correct_items) if g == c)
        score = correct_positions / len(correct_items)

        if score == 1.0:
            return True, 1.0, "Tökéletes sorrend!"
        elif score >= 0.5:
            return False, round(score, 2), f"Részben helyes sorrend ({int(score * 100)}%). Helyes: {', '.join(correct_items)}"
        else:
            return False, round(score, 2), f"Helytelen sorrend. Helyes: {', '.join(correct_items)}"
