"""Kvízkérdés adatgyűjtő és minta-korpusz generáló modul."""

import html
from typing import Any, Dict, List, Tuple
from quizforge.core.constants import Domain, QuestionMechanism, SourceType
from quizforge.core.models import Entity, RawQuizQuestion, Relation
from quizforge.ingestion.base import BaseIngestor


class OpenTriviaIngestor(BaseIngestor):
    """Open Trivia Database (OpenTDB) lekérdező nyílt trivia kérdések gyűjtéséhez."""

    OPENTDB_ENDPOINT = "https://opentdb.com/api.php"

    def __init__(self):
        super().__init__(
            source_name="Open Trivia DB",
            source_type=SourceType.OPEN_TRIVIA,
            endpoint=self.OPENTDB_ENDPOINT
        )

    def fetch_sample(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Mintakérdések lekérdezése az OpenTDB-ről."""
        params = {
            "amount": limit,
            "type": "multiple"
        }
        resp = self.client.get(self.OPENTDB_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        parsed = []
        for r in results:
            parsed.append({
                "category": html.unescape(r.get("category", "")),
                "type": r.get("type", ""),
                "difficulty": r.get("difficulty", ""),
                "question": html.unescape(r.get("question", "")),
                "correct_answer": html.unescape(r.get("correct_answer", "")),
                "incorrect_answers": [html.unescape(a) for a in r.get("incorrect_answers", [])]
            })
        return parsed

    def extract_triplets(self, sample_data: List[Dict[str, Any]]) -> Tuple[List[Entity], List[Relation]]:
        """Kvízkérdésekből entitások kinyerése (Kategória entitások + kérdés-kapcsolatok)."""
        entities: Dict[str, Entity] = {}
        relations: List[Relation] = []

        for idx, q in enumerate(sample_data):
            cat_name = q.get("category", "General")
            cat_id = f"opentdb:cat:{abs(hash(cat_name)) % 100000}"
            if cat_id not in entities:
                entities[cat_id] = Entity(
                    entity_id=cat_id,
                    label_hu=cat_name,
                    domain=Domain.GENERAL_KNOWLEDGE,
                    subdomain="trivia_category"
                )

            ans = q.get("correct_answer", "")
            ans_id = f"opentdb:ans:{abs(hash(ans)) % 100000}"
            if ans and ans_id not in entities:
                entities[ans_id] = Entity(
                    entity_id=ans_id,
                    label_hu=ans,
                    domain=Domain.GENERAL_KNOWLEDGE,
                    subdomain="trivia_answer"
                )

            if ans_id in entities and cat_id in entities:
                relations.append(Relation(
                    relation_id=f"rel:opentdb:{idx}",
                    source_entity_id=ans_id,
                    target_entity_id=cat_id,
                    relation_type="KATEGÓRIÁBA_TARTOZIK"
                ))

        return list(entities.values()), relations


class HungarianPubQuizSampleCorpus:
    """Valósághű magyar pub quiz tesztkorpusz a különböző mechanizmusok validálásához."""

    @staticmethod
    def get_seed_questions() -> List[RawQuizQuestion]:
        return [
            RawQuizQuestion(
                question_id="sample_01",
                text="Melyik évben kapott orvosi Nobel-díjat Szent-Györgyi Albert a C-vitamin kutatásáért?",
                mechanism=QuestionMechanism.ESTIMATION,
                correct_answer="1937",
                domain=Domain.SCIENCE_TECH,
                subdomain="nobel",
                source_name="Hungarian Pub Quiz Seeds",
                entities=["wd:Q234594", "wd:Q7191"]
            ),
            RawQuizQuestion(
                question_id="sample_02",
                text="Mi Békés vármegye székhelye?",
                mechanism=QuestionMechanism.ABCD,
                correct_answer="Békéscsaba",
                options=["Békéscsaba", "Gyula", "Orosháza", "Szarvas"],
                domain=Domain.GEOGRAPHY,
                subdomain="counties",
                source_name="Hungarian Pub Quiz Seeds",
                entities=["wd:Q191532", "wd:Q179638"]
            ),
            RawQuizQuestion(
                question_id="sample_03",
                text="Állítsd időrendi sorrendbe a következő magyar irodalmi műveket megjelenésük szerint!",
                mechanism=QuestionMechanism.ORDERING,
                correct_answer="Ómagyar Mária-siralom, Toldi, Az ember tragédiája, Egri csillagok",
                options=["Toldi", "Egri csillagok", "Ómagyar Mária-siralom", "Az ember tragédiája"],
                domain=Domain.LITERATURE,
                subdomain="classics",
                source_name="Hungarian Pub Quiz Seeds",
                entities=["wd:Q718", "wd:Q438"]
            ),
            RawQuizQuestion(
                question_id="sample_04",
                text="Párosítsd a magyar feltalálókat leghíresebb találmányukkal!",
                mechanism=QuestionMechanism.MATCHING,
                correct_answer="Bíró László: golyóstoll, Rubik Ernő: bűvös kocka, Jedlik Ányos: dinamó elv, Puskás Tivadar: telefonközpont",
                options=["Bíró László", "Rubik Ernő", "Jedlik Ányos", "Puskás Tivadar"],
                domain=Domain.SCIENCE_TECH,
                subdomain="inventions",
                source_name="Hungarian Pub Quiz Seeds",
                entities=["wd:Q211832", "wd:Q181938"]
            ),
            RawQuizQuestion(
                question_id="sample_05",
                text="Mi a közös a következő személyekben: Wekerle Sándor, Teleki Pál, Nagy Imre?",
                mechanism=QuestionMechanism.CONNECTION,
                correct_answer="Mindannyian többször is betöltötték Magyarország miniszterelnöki tisztségét",
                options=[],
                domain=Domain.HISTORY,
                subdomain="prime_ministers",
                source_name="Hungarian Pub Quiz Seeds",
                entities=["wd:Q123"]
            )
        ]
