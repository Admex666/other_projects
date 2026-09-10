"""Unit tesztek az összes kérdésmechanizmus kiértékeléséhez."""

import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.quiz_engine.mechanisms.abcd import ABCDMechanism
from quizforge.quiz_engine.mechanisms.estimation import EstimationMechanism
from quizforge.quiz_engine.mechanisms.ordering import OrderingMechanism
from quizforge.quiz_engine.mechanisms.matching import MatchingMechanism
from quizforge.quiz_engine.mechanisms.connection import ConnectionMechanism


class TestMechanisms(unittest.TestCase):

    def test_abcd_mechanism(self):
        mech = ABCDMechanism()
        ok, score, fb = mech.evaluate("Békéscsaba", "Békéscsaba")
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)

        ok_bad, score_bad, _ = mech.evaluate("Szeged", "Békéscsaba")
        self.assertFalse(ok_bad)
        self.assertEqual(score_bad, 0.0)

    def test_estimation_mechanism(self):
        mech = EstimationMechanism()
        # Évszám pontos
        ok, score, _ = mech.evaluate(1937, 1937)
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)

        # 1 év eltérés (1938 vs 1937)
        ok_near, score_near, _ = mech.evaluate(1938, 1937)
        self.assertTrue(ok_near)
        self.assertGreaterEqual(score_near, 0.8)

        # Nagy eltérés
        ok_far, score_far, _ = mech.evaluate(1800, 1937)
        self.assertFalse(ok_far)
        self.assertEqual(score_far, 0.0)

    def test_ordering_mechanism(self):
        mech = OrderingMechanism()
        correct = ["A", "B", "C"]
        ok, score, _ = mech.evaluate(["A", "B", "C"], correct)
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)

        ok_partial, score_partial, _ = mech.evaluate(["A", "C", "B"], correct)
        self.assertFalse(ok_partial)
        self.assertGreater(score_partial, 0.0)

    def test_matching_mechanism(self):
        mech = MatchingMechanism()
        correct_pairs = {"petőfi": "jános vitéz", "arany": "toldi"}
        given = {"petőfi": "jános vitéz", "arany": "toldi"}
        ok, score, _ = mech.evaluate(given, correct_pairs, metadata={"pairs": correct_pairs})
        self.assertTrue(ok)
        self.assertEqual(score, 1.0)

        given_half = {"petőfi": "jános vitéz", "arany": "cirkusz"}
        ok_half, score_half, _ = mech.evaluate(given_half, correct_pairs, metadata={"pairs": correct_pairs})
        self.assertFalse(ok_half)
        self.assertEqual(score_half, 0.5)

    def test_connection_mechanism(self):
        mech = ConnectionMechanism()
        correct = "Mindketten Nobel-díjas magyar kutatók"
        ok, score, _ = mech.evaluate("Magyar Nobel-díjas tudósok", correct)
        self.assertTrue(ok)
        self.assertGreaterEqual(score, 0.6)


if __name__ == "__main__":
    unittest.main()
