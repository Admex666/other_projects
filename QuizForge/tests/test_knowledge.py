"""Unit tesztek a Knowledge Graph és Relevancia motorhoz."""

import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.core.constants import Domain
from quizforge.core.models import Entity, Relation
from quizforge.knowledge.graph import KnowledgeGraph
from quizforge.knowledge.relevance import RelevanceEngine
from quizforge.storage.db import DatabaseManager


class TestKnowledge(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseManager(in_memory=True)
        self.kg = KnowledgeGraph(self.db)
        self.relevance = RelevanceEngine(self.db)

    def tearDown(self):
        self.db.close()

    def test_smart_distractors(self):
        # Feltöltünk néhány magyar várost
        cities = [
            Entity(entity_id="c1", label_hu="Békéscsaba", domain=Domain.GEOGRAPHY, subdomain="city"),
            Entity(entity_id="c2", label_hu="Gyula", domain=Domain.GEOGRAPHY, subdomain="city"),
            Entity(entity_id="c3", label_hu="Orosháza", domain=Domain.GEOGRAPHY, subdomain="city"),
            Entity(entity_id="c4", label_hu="Szarvas", domain=Domain.GEOGRAPHY, subdomain="city"),
            Entity(entity_id="b1", label_hu="Toldi", domain=Domain.LITERATURE, subdomain="book"),
        ]
        self.kg.ingest_triplets(cities, [])

        distractors = self.kg.get_distractors("c1", domain=Domain.GEOGRAPHY, subdomain="city", count=3)
        self.assertEqual(len(distractors), 3)
        self.assertNotIn("Békéscsaba", distractors)
        # Az azonos kategóriájú városokat kell előnyben részesítenie
        self.assertIn("Gyula", distractors)

    def test_relevance_calculation(self):
        e1 = Entity(entity_id="e1", label_hu="Szent-Györgyi Albert", domain=Domain.SCIENCE_TECH, relevance_score=1.5)
        e2 = Entity(entity_id="e2", label_hu="Nobel-díj", domain=Domain.GENERAL_KNOWLEDGE, relevance_score=1.2)
        rel = Relation(relation_id="r1", source_entity_id="e1", target_entity_id="e2", relation_type="KAPOTT_DÍJAT")
        self.kg.ingest_triplets([e1, e2], [rel])

        updated = self.relevance.recalculate_relevance_scores()
        self.assertEqual(updated, 2)

        top = self.relevance.get_top_entities(limit=2)
        self.assertEqual(len(top), 2)
        self.assertGreater(top[0]["quiz_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
