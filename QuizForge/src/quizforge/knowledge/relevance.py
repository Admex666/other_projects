"""Magyar kvízrelevancia-számító motor."""

import math
from typing import Any, Dict, List
from quizforge.storage.db import DatabaseManager


class RelevanceEngine:
    """A magyar kvízrelevancia indexelését és súlyozását végző motor."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def recalculate_relevance_scores(self) -> int:
        """
        Kiszámítja minden entitás relevanciáját:
        - corpus_frequency: az entitáshoz kapcsolt kvízkérdések száma a question_entities táblában
        - degree_centrality: az entitás ki- és bejövő relációinak összege a relations táblában
        - hungarian_quiz_score = base_relevance * (1 + ln(1 + corpus_freq)) * (1 + 0.1 * degree)
        """
        # 1. Korpusz gyakoriságok és fokszámok lekérése
        query = """
            SELECT 
                e.entity_id,
                e.relevance_score AS base_score,
                COALESCE(q.cnt, 0) AS corpus_freq,
                (COALESCE(r_out.cnt, 0) + COALESCE(r_in.cnt, 0)) AS degree
            FROM entities e
            LEFT JOIN (
                SELECT entity_id, COUNT(*) AS cnt FROM question_entities GROUP BY entity_id
            ) q ON e.entity_id = q.entity_id
            LEFT JOIN (
                SELECT source_entity_id, COUNT(*) AS cnt FROM relations GROUP BY source_entity_id
            ) r_out ON e.entity_id = r_out.source_entity_id
            LEFT JOIN (
                SELECT target_entity_id, COUNT(*) AS cnt FROM relations GROUP BY target_entity_id
            ) r_in ON e.entity_id = r_in.target_entity_id
        """
        rows = self.db.conn.execute(query).fetchall()

        updated_count = 0
        for r in rows:
            ent_id = r[0]
            base_score = r[1] or 1.0
            corpus_freq = r[2]
            degree = r[3]

            # Formula:
            quiz_score = base_score * (1.0 + math.log(1.0 + corpus_freq)) * (1.0 + 0.1 * min(degree, 20))
            quiz_score = round(quiz_score, 3)

            self.db.conn.execute("""
                INSERT OR REPLACE INTO entity_relevance 
                (entity_id, corpus_frequency, degree_centrality, hungarian_quiz_score, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (ent_id, corpus_freq, degree, quiz_score))

            # Frissítjük az entitás fő tábláját is a gyorsabb lekérdezésekhez
            self.db.conn.execute("""
                UPDATE entities SET relevance_score = ? WHERE entity_id = ?
            """, (quiz_score, ent_id))

            updated_count += 1

        return updated_count

    def get_top_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """A legmagasabb magyar kvízrelevanciájú entitások listája."""
        query = """
            SELECT e.entity_id, e.label_hu, e.domain, e.subdomain, er.corpus_frequency, er.degree_centrality, er.hungarian_quiz_score
            FROM entity_relevance er
            JOIN entities e ON er.entity_id = e.entity_id
            ORDER BY er.hungarian_quiz_score DESC
            LIMIT ?
        """
        rows = self.db.conn.execute(query, (limit,)).fetchall()
        results = []
        for r in rows:
            results.append({
                "entity_id": r[0],
                "label": r[1],
                "domain": r[2],
                "subdomain": r[3],
                "corpus_freq": r[4],
                "degree": r[5],
                "quiz_score": r[6]
            })
        return results
