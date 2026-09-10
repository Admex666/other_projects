"""Unit tesztek a DuckDB és Parquet tároláshoz."""

import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.core.models import Entity, RawQuizQuestion, Relation
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import EntityRepository, QuizQuestionRepository, RelationRepository


class TestStorage(unittest.TestCase):

    def setUp(self):
        # In-memory DuckDB adatbázis a tesztekhez
        self.db = DatabaseManager(in_memory=True)
        self.entity_repo = EntityRepository(self.db)
        self.relation_repo = RelationRepository(self.db)
        self.question_repo = QuizQuestionRepository(self.db)

    def tearDown(self):
        self.db.close()

    def test_entity_crud(self):
        ent = Entity(
            entity_id="wd:Q191532",
            label_hu="Békés vármegye",
            domain=Domain.GEOGRAPHY,
            subdomain="county",
            relevance_score=1.4
        )
        self.entity_repo.upsert(ent)
        fetched = self.entity_repo.get_by_id("wd:Q191532")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.label_hu, "Békés vármegye")
        self.assertEqual(fetched.domain, Domain.GEOGRAPHY)
        self.assertEqual(fetched.relevance_score, 1.4)

    def test_relation_neighbors(self):
        e1 = Entity(entity_id="e1", label_hu="Arany János", domain=Domain.LITERATURE)
        e2 = Entity(entity_id="e2", label_hu="Toldi", domain=Domain.LITERATURE)
        self.entity_repo.upsert(e1)
        self.entity_repo.upsert(e2)

        rel = Relation(relation_id="r1", source_entity_id="e1", target_entity_id="e2", relation_type="SZERZŐJE")
        self.relation_repo.upsert(rel)

        neighbors = self.relation_repo.get_neighbors("e1")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]["target_label"], "Toldi")
        self.assertEqual(neighbors[0]["relation_type"], "SZERZŐJE")

    def test_quiz_question_storage(self):
        q = RawQuizQuestion(
            question_id="test_q1",
            text="Mi a székhelye?",
            mechanism=QuestionMechanism.ABCD,
            correct_answer="Békéscsaba",
            options=["Békéscsaba", "Gyula"],
            domain=Domain.GEOGRAPHY,
            source_name="Test",
            entities=["wd:Q191532"]
        )
        self.question_repo.add_question(q)
        listed = self.question_repo.list_by_mechanism(QuestionMechanism.ABCD)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["correct_answer"], "Békéscsaba")


if __name__ == "__main__":
    unittest.main()
