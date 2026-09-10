"""Játékos eseménykövető és önértékelés-frissítő koordinátor."""

from typing import Any, Dict, Optional
from quizforge.core.constants import QuestionMechanism
from quizforge.player.calibration import CalibrationEngine
from quizforge.player.repository import PlayerRepository
from quizforge.quiz_engine.mechanisms.abcd import ABCDMechanism
from quizforge.quiz_engine.mechanisms.connection import ConnectionMechanism
from quizforge.quiz_engine.mechanisms.estimation import EstimationMechanism
from quizforge.quiz_engine.mechanisms.matching import MatchingMechanism
from quizforge.quiz_engine.mechanisms.ordering import OrderingMechanism
from quizforge.quiz_engine.mechanisms.true_false import TrueFalseMechanism
from quizforge.quiz_engine.mechanisms.deduction import DeductionMechanism
from quizforge.quiz_engine.mechanisms.missing_letters import MissingLettersMechanism
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import QuizQuestionRepository


class PlayerTracker:
    """Központi vezérlő a játékos válaszok kiértékeléséhez, naplózásához és kalibrációjához."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.player_repo = PlayerRepository(db)
        self.q_repo = QuizQuestionRepository(db)
        self.mechanisms = {
            QuestionMechanism.ABCD.value: ABCDMechanism(),
            QuestionMechanism.ESTIMATION.value: EstimationMechanism(),
            QuestionMechanism.ORDERING.value: OrderingMechanism(),
            QuestionMechanism.MATCHING.value: MatchingMechanism(),
            QuestionMechanism.CONNECTION.value: ConnectionMechanism(),
            QuestionMechanism.TRUE_FALSE.value: TrueFalseMechanism(),
            QuestionMechanism.DEDUCTION.value: DeductionMechanism(),
            QuestionMechanism.MISSING_LETTERS.value: MissingLettersMechanism(),
            QuestionMechanism.FIRST_LETTER.value: ABCDMechanism(),
        }

    def evaluate_and_record_answer(
        self,
        user_id: str,
        question_id: str,
        given_answer: Any,
        confidence_level: float,
        response_time_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Válasz kiértékelése a mechanizmus szabályai szerint,
        mentés a DuckDB naplóba, és a játékos képességprofiljának azonnali frissítése.
        """
        # 1. Kérdés betöltése az adatbázisból
        question = self.q_repo.get_by_id(question_id)
        if not question:
            raise ValueError(f"Nem található kérdés azonosító alapján: {question_id}")

        mech_name = question.mechanism.value if hasattr(question.mechanism, "value") else str(question.mechanism)
        mech_handler = self.mechanisms.get(mech_name, self.mechanisms[QuestionMechanism.ABCD.value])

        # 2. Értékelés a mechanizmus logikájával
        is_correct, score, feedback = mech_handler.evaluate(given_answer, question.correct_answer)

        # 3. Rögzítés a válasznaplóban
        answer_id = self.player_repo.record_answer(
            user_id=user_id,
            question_id=question_id,
            given_answer=str(given_answer),
            is_correct=is_correct,
            confidence_level=confidence_level,
            response_time_ms=response_time_ms
        )

        # 4. Képességmátrix frissítése erre a (domain, mechanism) cellára
        user_answers = self.player_repo.get_user_answers(user_id)
        dom_val = question.domain.value if hasattr(question.domain, "value") else str(question.domain)
        cell_answers = [
            a for a in user_answers 
            if a.get("domain") == dom_val and a.get("mechanism") == mech_name
        ]
        if cell_answers:
            cell_acc = CalibrationEngine.calculate_accuracy(cell_answers)
            cell_bias = CalibrationEngine.calculate_bias(cell_answers)["bias"]
            self.player_repo.update_player_skills(
                user_id=user_id,
                domain=dom_val,
                mechanism=mech_name,
                skill_rating=cell_acc,
                confidence_bias=cell_bias,
                sample_count=len(cell_answers)
            )

        # 5. Teljes friss Brier score
        current_brier = CalibrationEngine.calculate_brier_score(user_answers)
        current_bias = CalibrationEngine.calculate_bias(user_answers)

        # Parquet perzisztencia frissítése
        try:
            self.db.export_to_parquet()
        except Exception:
            pass

        return {
            "answer_id": answer_id,
            "is_correct": is_correct,
            "score": score,
            "feedback": feedback,
            "correct_answer": question.correct_answer,
            "given_answer": str(given_answer),
            "confidence_level": confidence_level,
            "total_answers": len(user_answers),
            "brier_score": current_brier,
            "bias_info": current_bias
        }

    def get_player_profile(self, user_id: str) -> Dict[str, Any]:
        """A játékos teljes körű analitikai profilja és kalibrációs állapota."""
        answers = self.player_repo.get_user_answers(user_id)
        total = len(answers)
        accuracy = CalibrationEngine.calculate_accuracy(answers)
        brier = CalibrationEngine.calculate_brier_score(answers)
        bias_info = CalibrationEngine.calculate_bias(answers)
        curve = CalibrationEngine.calculate_calibration_curve(answers, n_bins=5)
        matrix = CalibrationEngine.calculate_skill_matrix(answers)

        return {
            "user_id": user_id,
            "total_answers": total,
            "accuracy": accuracy,
            "brier_score": brier,
            "bias_info": bias_info,
            "calibration_curve": curve,
            "skill_matrix": matrix,
            "recent_answers": answers[:20]
        }
