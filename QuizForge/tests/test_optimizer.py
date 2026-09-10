"""Unit tesztek a kvíz tájképekhez és a célzott tanulási motorhoz (Phase 5)."""

import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.optimizer.landscape import QuizLandscapeEngine, QuizProfile
from quizforge.optimizer.targeted import TargetedLearningEngine
from quizforge.storage.db import DatabaseManager
from quizforge.knowledge.bank_expander import expand_database_bank


class TestOptimizer(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseManager(in_memory=True)
        expand_database_bank(self.db)
        self.landscape = QuizLandscapeEngine()
        self.engine = TargetedLearningEngine(self.db)

    def tearDown(self):
        self.db.close()

    def test_landscape_profiles_loaded(self):
        profiles = self.landscape.list_profiles()
        self.assertGreaterEqual(len(profiles), 6)

        profile_ids = [p.profile_id for p in profiles]
        expected_ids = ["csomor", "quizkrumpli", "quizland", "kertvarosi", "inquizitor", "honfoglalo"]
        for p_id in expected_ids:
            self.assertIn(p_id, profile_ids)

    def test_inquizitor_profile_weights(self):
        inq = self.landscape.get_profile("inquizitor")
        self.assertIsNotNone(inq)
        self.assertIn(QuestionMechanism.DEDUCTION.value, inq.mechanism_weights)
        self.assertIn(QuestionMechanism.ESTIMATION.value, inq.mechanism_weights)
        self.assertIn(Domain.LITERATURE.value, inq.domain_weights)

    def test_kertvarosi_estimation_focus(self):
        kert = self.landscape.get_profile("kertvarosi")
        self.assertIsNotNone(kert)
        self.assertGreater(kert.get_mechanism_weight("estimation"), 0.3)

    def test_weak_spots_calculation(self):
        # Új játékosnál (nincs előzmény) a legmagasabb súlyú témák a legnagyobb kockázatok
        weak_spots = self.engine.calculate_weak_spots("test_user_new", "inquizitor", limit=3)
        self.assertEqual(len(weak_spots), 3)
        self.assertGreater(weak_spots[0]["risk_score"], 0.0)

    def test_targeted_questions_selection(self):
        questions = self.engine.select_targeted_questions("test_user_new", "inquizitor", count=4)
        self.assertEqual(len(questions), 4)
        # Inquizitor esetében irodalom vagy dedukció / becslés kérdéseknek kell lenniük
        domains = [q.domain for q in questions]
        self.assertTrue(any(d in [Domain.LITERATURE, Domain.POP_CULTURE] for d in domains))


if __name__ == "__main__":
    unittest.main()
