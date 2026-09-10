"""Repository osztályok az entitások, relációk és kérdések kezelésére."""

import json
from typing import Any, Dict, List, Optional
from quizforge.core.constants import Domain, QuestionMechanism, SourceType
from quizforge.core.models import Entity, RawQuizQuestion, Relation
from quizforge.storage.db import DatabaseManager


class EntityRepository:
    """Entitások CRUD és lekérdező műveletei."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def upsert(self, entity: Entity):
        """Entitás beszúrása vagy frissítése."""
        self.db.conn.execute("""
            INSERT OR REPLACE INTO entities 
            (entity_id, label_hu, label_en, domain, subdomain, wikidata_qid, description, metadata, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.entity_id,
            entity.label_hu,
            entity.label_en,
            entity.domain.value if isinstance(entity.domain, Domain) else entity.domain,
            entity.subdomain,
            entity.wikidata_qid,
            entity.description,
            json.dumps(entity.metadata or {}),
            entity.relevance_score
        ))

    def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """Entitás lekérése azonosító alapján."""
        res = self.db.conn.execute("""
            SELECT entity_id, label_hu, label_en, domain, subdomain, wikidata_qid, description, metadata, relevance_score
            FROM entities WHERE entity_id = ?
        """, (entity_id,)).fetchone()
        if not res:
            return None
        return Entity(
            entity_id=res[0],
            label_hu=res[1],
            label_en=res[2],
            domain=Domain(res[3]) if res[3] in [d.value for d in Domain] else Domain.GENERAL_KNOWLEDGE,
            subdomain=res[4],
            wikidata_qid=res[5],
            description=res[6],
            metadata=json.loads(res[7]) if res[7] else {},
            relevance_score=res[8] or 1.0
        )

    def list_by_domain(self, domain: Domain, limit: int = 50) -> List[Entity]:
        """Entitások listázása téma szerint."""
        rows = self.db.conn.execute("""
            SELECT entity_id, label_hu, label_en, domain, subdomain, wikidata_qid, description, metadata, relevance_score
            FROM entities WHERE domain = ? LIMIT ?
        """, (domain.value, limit)).fetchall()
        
        entities = []
        for res in rows:
            entities.append(Entity(
                entity_id=res[0],
                label_hu=res[1],
                label_en=res[2],
                domain=Domain(res[3]) if res[3] in [d.value for d in Domain] else Domain.GENERAL_KNOWLEDGE,
                subdomain=res[4],
                wikidata_qid=res[5],
                description=res[6],
                metadata=json.loads(res[7]) if res[7] else {},
                relevance_score=res[8] or 1.0
            ))
        return entities


class RelationRepository:
    """Relációk kezelése a Knowledge Graphban."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def upsert(self, relation: Relation):
        self.db.conn.execute("""
            INSERT OR REPLACE INTO relations 
            (relation_id, source_entity_id, target_entity_id, relation_type, weight, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            relation.relation_id,
            relation.source_entity_id,
            relation.target_entity_id,
            relation.relation_type,
            relation.weight,
            json.dumps(relation.metadata or {})
        ))

    def get_neighbors(self, entity_id: str) -> List[Dict[str, Any]]:
        """Egy entitás összes ki- és bejövő kapcsolatának lekérése cél- és forrásnevekkel."""
        query = """
            SELECT r.relation_id, r.relation_type, r.weight,
                   e_src.entity_id AS src_id, e_src.label_hu AS src_label,
                   e_tgt.entity_id AS tgt_id, e_tgt.label_hu AS tgt_label
            FROM relations r
            JOIN entities e_src ON r.source_entity_id = e_src.entity_id
            JOIN entities e_tgt ON r.target_entity_id = e_tgt.entity_id
            WHERE r.source_entity_id = ? OR r.target_entity_id = ?
        """
        rows = self.db.conn.execute(query, (entity_id, entity_id)).fetchall()
        neighbors = []
        for r in rows:
            neighbors.append({
                "relation_id": r[0],
                "relation_type": r[1],
                "weight": r[2],
                "source_id": r[3],
                "source_label": r[4],
                "target_id": r[5],
                "target_label": r[6]
            })
        return neighbors


class QuizQuestionRepository:
    """Kvízkérdések és entitás-kapcsolatok mentése."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_question(self, question: RawQuizQuestion):
        self.db.conn.execute("""
            INSERT OR REPLACE INTO quiz_questions
            (question_id, text, mechanism, correct_answer, options, domain, subdomain, source_type, source_name, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question.question_id,
            question.text,
            question.mechanism.value if isinstance(question.mechanism, QuestionMechanism) else question.mechanism,
            question.correct_answer,
            json.dumps(question.options or []),
            question.domain.value if isinstance(question.domain, Domain) else question.domain,
            question.subdomain,
            question.source_type.value if isinstance(question.source_type, SourceType) else question.source_type,
            question.source_name,
            json.dumps(question.metadata or {})
        ))

        # Kapcsolódó entitások feljegyzése
        for ent_id in question.entities:
            self.db.conn.execute("""
                INSERT OR REPLACE INTO question_entities (question_id, entity_id, role)
                VALUES (?, ?, 'topic')
            """, (question.question_id, ent_id))

    def list_by_mechanism(self, mechanism: QuestionMechanism, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self.db.conn.execute("""
            SELECT question_id, text, mechanism, correct_answer, options, domain, subdomain, source_name
            FROM quiz_questions WHERE mechanism = ? LIMIT ?
        """, (mechanism.value, limit)).fetchall()
        results = []
        for r in rows:
            results.append({
                "question_id": r[0],
                "text": r[1],
                "mechanism": r[2],
                "correct_answer": r[3],
                "options": json.loads(r[4]) if r[4] else [],
                "domain": r[5],
                "subdomain": r[6],
                "source_name": r[7]
            })
        return results

    def get_by_id(self, question_id: str) -> Optional[RawQuizQuestion]:
        row = self.db.conn.execute("""
            SELECT question_id, text, mechanism, correct_answer, options, domain, subdomain, source_type, source_name, metadata
            FROM quiz_questions WHERE question_id = ?
        """, [question_id]).fetchone()
        if not row:
            return None
        return RawQuizQuestion(
            question_id=row[0],
            text=row[1],
            mechanism=QuestionMechanism(row[2]) if row[2] in [m.value for m in QuestionMechanism] else QuestionMechanism.ABCD,
            correct_answer=row[3],
            options=json.loads(row[4]) if row[4] else [],
            domain=Domain(row[5]) if row[5] in [d.value for d in Domain] else Domain.GENERAL_KNOWLEDGE,
            subdomain=row[6],
            source_type=SourceType(row[7]) if row[7] in [s.value for s in SourceType] else SourceType.MANUAL,
            source_name=row[8],
            metadata=json.loads(row[9]) if row[9] else {}
        )
