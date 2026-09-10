"""Unit tesztek a Brier Score és a konfidencia-kalibráció matematikai pontosságára."""

import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.player.calibration import CalibrationEngine
from quizforge.storage.db import DatabaseManager
from quizforge.player.repository import PlayerRepository
from quizforge.player.tracker import PlayerTracker
from quizforge.core.models import RawQuizQuestion
from quizforge.core.constants import Domain, QuestionMechanism, SourceType


class TestCalibration(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseManager(in_memory=True)
        self.tracker = PlayerTracker(self.db)
        self.repo = PlayerRepository(self.db)

    def tearDown(self):
        self.db.close()

    def test_brier_score_perfect(self):
        """Tökéletes kalibráció tesztelése (100% magabiztos és 100% helyes)."""
        answers = [
            {"confidence_level": 1.0, "is_correct": True},
            {"confidence_level": 1.0, "is_correct": True},
            {"confidence_level": 1.0, "is_correct": True},
        ]
        bs = CalibrationEngine.calculate_brier_score(answers)
        self.assertEqual(bs, 0.0)

    def test_brier_score_random_guessing(self):
        """Véletlen találgatás 50%-os magabiztossággal (BS ~ 0.25)."""
        answers = [
            {"confidence_level": 0.5, "is_correct": True},
            {"confidence_level": 0.5, "is_correct": False},
            {"confidence_level": 0.5, "is_correct": True},
            {"confidence_level": 0.5, "is_correct": False},
        ]
        bs = CalibrationEngine.calculate_brier_score(answers)
        self.assertAlmostEqual(bs, 0.25, places=3)

    def test_overconfidence_bias(self):
        """Túlzott magabiztosság (Overconfidence) felismerése."""
        answers = [
            {"confidence_level": 0.9, "is_correct": False},
            {"confidence_level": 0.9, "is_correct": False},
            {"confidence_level": 0.9, "is_correct": True},
        ]
        bias_res = CalibrationEngine.calculate_bias(answers)
        self.assertEqual(bias_res["type"], "overconfident")
        self.assertGreater(bias_res["bias"], 0.0)

    def test_underconfidence_bias(self):
        """Kishitűség (Underconfidence) felismerése."""
        answers = [
            {"confidence_level": 0.3, "is_correct": True},
            {"confidence_level": 0.4, "is_correct": True},
            {"confidence_level": 0.35, "is_correct": True},
        ]
        bias_res = CalibrationEngine.calculate_bias(answers)
        self.assertEqual(bias_res["type"], "underconfident")
        self.assertLess(bias_res["bias"], 0.0)

    def test_calibration_curve_binning(self):
        """Kalibrációs görbe sávjainak felépülése."""
        answers = [
            {"confidence_level": 0.1, "is_correct": False},
            {"confidence_level": 0.7, "is_correct": True},
            {"confidence_level": 0.75, "is_correct": True},
            {"confidence_level": 0.95, "is_correct": True},
        ]
        curve = CalibrationEngine.calculate_calibration_curve(answers, n_bins=5)
        self.assertEqual(len(curve), 5)
        # Sáv 3 (60%-80%)
        bin_60_80 = curve[3]
        self.assertEqual(bin_60_80["sample_count"], 2)
        self.assertEqual(bin_60_80["accuracy"], 1.0)

    def test_tracker_answer_lifecycle(self):
        """Teljes válaszadási folyamat, mentés és képességfrissítés tesztje."""
        # Kérdés beszúrása
        q = RawQuizQuestion(
            question_id="test:q1",
            text="Mi Magyarország fővárosa?",
            mechanism=QuestionMechanism.ABCD,
            correct_answer="Budapest",
            options=["Budapest", "Debrecen", "Szeged", "Pécs"],
            domain=Domain.GEOGRAPHY,
            source_type=SourceType.MANUAL,
            source_name="Test"
        )
        self.tracker.q_repo.add_question(q)

        # Felhasználó
        user = self.repo.get_or_create_user("TesztElek")
        user_id = user["user_id"]

        # Helyes válasz beküldése 90%-os magabiztossággal
        res = self.tracker.evaluate_and_record_answer(
            user_id=user_id,
            question_id="test:q1",
            given_answer="Budapest",
            confidence_level=0.9,
            response_time_ms=1200
        )
        self.assertTrue(res["is_correct"])
        self.assertEqual(res["total_answers"], 1)

        # Profil ellenőrzése
        prof = self.tracker.get_player_profile(user_id)
        self.assertEqual(prof["total_answers"], 1)
        self.assertEqual(prof["accuracy"], 1.0)
        self.assertAlmostEqual(prof["brier_score"], 0.01, places=3)


if __name__ == "__main__":
    unittest.main()
