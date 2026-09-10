"""Becslés (Numerikus tűréshatár alapú) mechanizmus implementáció."""

import math
from typing import Any, Dict, List, Optional, Tuple
from quizforge.core.constants import QuestionMechanism
from quizforge.quiz_engine.mechanisms.base import BaseMechanism


class EstimationMechanism(BaseMechanism):
    """Numerikus becslés kérdésmechanizmus (pl. évszámok, népesség, távolságok)."""

    mechanism_type = QuestionMechanism.ESTIMATION

    def build_options_or_payload(
        self,
        correct_value: str,
        distractors: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        meta = metadata or {}
        return {
            "correct_answer": correct_value,
            "unit": meta.get("unit", ""),
            "tolerance_percentage": meta.get("tolerance_percentage", 10.0)  # Alapértelmezett 10%
        }

    def evaluate(
        self,
        given_answer: Any,
        correct_answer: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, str]:
        """
        Becslés kiértékelése:
        - Pontos egyezés vagy abszolút különbség (évszámnál pl. ±1 év) = 1.0 pont
        - Tűréshatáron (pl. ±10%) belül: lineárisan arányos pontszám 0.5 és 1.0 között
        - Tűréshatáron kívül: 0.0 pont
        """
        try:
            given_val = float(str(given_answer).replace(" ", "").replace(",", "."))
            correct_val = float(str(correct_answer).replace(" ", "").replace(",", "."))
        except ValueError:
            return False, 0.0, f"Érvénytelen numerikus válasz: {given_answer}"

        meta = metadata or {}
        tol_pct = meta.get("tolerance_percentage", 10.0)

        # Ha évszám (pl. 1000 - 2050 között), konkrét évtűrés érvényesül
        is_year = (1000 <= correct_val <= 2050)
        diff = abs(given_val - correct_val)

        if diff == 0:
            return True, 1.0, f"Tökéletes telitalálat! ({correct_val})"

        if is_year:
            year_tol = meta.get("year_tolerance", 5)  # 5 év alapértelmezett tűrés évszámokra
            if diff <= year_tol:
                score = round(1.0 - (0.5 * (diff / year_tol)), 2)
                return True, score, f"Jó évszámbecslés! Eltérés: {int(diff)} év. (Helyes: {int(correct_val)})"
            elif diff <= year_tol * 2:
                score = round(max(0.1, 0.4 - (0.3 * ((diff - year_tol) / year_tol))), 2)
                return False, score, f"Közel volt! Eltérés: {int(diff)} év. (Helyes: {int(correct_val)})"
            else:
                return False, 0.0, f"Túl nagy eltérés ({int(diff)} év). A helyes évszám: {int(correct_val)}"

        # Általános számértékeknél százalékos tűrés
        relative_error_pct = (diff / abs(correct_val)) * 100.0 if correct_val != 0 else 100.0

        if relative_error_pct <= tol_pct:
            score = 1.0 - (0.5 * (relative_error_pct / tol_pct))
            return True, round(score, 2), f"Jó becslés! Eltérés: {relative_error_pct:.1f}% (Helyes: {correct_val})"
        elif relative_error_pct <= tol_pct * 2:
            score = max(0.1, 0.5 - (0.4 * ((relative_error_pct - tol_pct) / tol_pct)))
            return False, round(score, 2), f"Közel volt, de a tűréshatáron kívül. Eltérés: {relative_error_pct:.1f}% (Helyes: {correct_val})"
        else:
            return False, 0.0, f"Túl nagy eltérés ({relative_error_pct:.1f}%). A helyes érték: {correct_val}"
