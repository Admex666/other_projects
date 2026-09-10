"""Alapvető absztrakt mechanizmus osztály a kérdésmechanizmusokhoz."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism


class BaseMechanism(ABC):
    """Minden kérdésmechanizmus közös interfésze."""

    mechanism_type: QuestionMechanism

    @abstractmethod
    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        Kiértékeli a felhasználó válaszát.
        Visszatérési érték: (is_correct: bool, score: float [0.0 - 1.0], feedback: str)
        """
        pass

    @abstractmethod
    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Előkészíti a kérdéshez tartozó opciókat vagy válaszstruktúrát."""
        pass
