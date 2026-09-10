"""Unit tesztek az adatgyűjtési és forrásvalidációs modulokhoz."""

import sys
import unittest
from pathlib import Path

# src hozzáadása az importokhoz
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.core.models import Entity
from quizforge.ingestion.quiz_sources import HungarianPubQuizSampleCorpus
from quizforge.ingestion.wikidata import WikidataIngestor
from quizforge.ingestion.wikipedia import WikipediaIngestor
from quizforge.ingestion.mek import MEKIngestor


class TestIngestion(unittest.TestCase):

    def test_entity_creation(self):
        e = Entity(
            entity_id="wd:Q234594",
            label_hu="Szent-Györgyi Albert",
            domain=Domain.SCIENCE_TECH,
            subdomain="nobel_laureate"
        )
        self.assertEqual(e.entity_id, "wd:Q234594")
        self.assertEqual(e.label_hu, "Szent-Györgyi Albert")
        self.assertEqual(e.domain, Domain.SCIENCE_TECH)

    def test_seed_quiz_corpus(self):
        questions = HungarianPubQuizSampleCorpus.get_seed_questions()
        self.assertGreaterEqual(len(questions), 5)
        mechanisms = {q.mechanism for q in questions}
        self.assertIn(QuestionMechanism.ABCD, mechanisms)
        self.assertIn(QuestionMechanism.ESTIMATION, mechanisms)
        self.assertIn(QuestionMechanism.ORDERING, mechanisms)
        self.assertIn(QuestionMechanism.MATCHING, mechanisms)
        self.assertIn(QuestionMechanism.CONNECTION, mechanisms)

    def test_wikidata_triplet_extraction(self):
        ingestor = WikidataIngestor()
        sample_data = [
            {
                "person_uri": "http://www.wikidata.org/entity/Q234594",
                "person_label": "Szent-Györgyi Albert",
                "award_uri": "http://www.wikidata.org/entity/Q7191",
                "award_label": "Nobel-díj",
                "year": "1937"
            }
        ]
        entities, relations = ingestor.extract_triplets(sample_data)
        self.assertEqual(len(entities), 2)
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].relation_type, "KAPOTT_DÍJAT")
        self.assertEqual(relations[0].metadata.get("year"), "1937")

    def test_wikipedia_triplet_extraction(self):
        ingestor = WikipediaIngestor()
        sample_data = [
            {
                "pageid": "12345",
                "title": "Bűvös kocka",
                "extract": "A bűvös kocka háromdimenziós mechanikus logikai játék...",
                "fullurl": "https://hu.wikipedia.org/wiki/B%C5%B1v%C3%B6s_kocka"
            }
        ]
        entities, relations = ingestor.extract_triplets(sample_data)
        self.assertEqual(len(entities), 2)
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].relation_type, "KATEGÓRIÁJA")

    def test_mek_triplet_extraction(self):
        ingestor = MEKIngestor()
        sample_data = [
            {
                "identifier": "https://mek.oszk.hu/001/001/",
                "title": "Toldi estéje",
                "creator": "Arany János",
                "date": "1854"
            }
        ]
        entities, relations = ingestor.extract_triplets(sample_data)
        self.assertEqual(len(entities), 2)
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].relation_type, "SZERZŐJE")


if __name__ == "__main__":
    unittest.main()
