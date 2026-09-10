"""Játékos, válasz- és képesség-adatok kezelése DuckDB-ben."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from quizforge.storage.db import DatabaseManager


class PlayerRepository:
    """DuckDB perzisztens CRUD műveletek a játékosokhoz és válaszaikhoz."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_or_create_user(self, username: str, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Felhasználó lekérése vagy létrehozása a megadott névvel."""
        clean_name = username.strip()
        if not clean_name:
            clean_name = "Teszt Játékos"

        row = self.db.conn.execute(
            "SELECT user_id, username, team_id, created_at FROM users WHERE LOWER(username) = LOWER(?)",
            [clean_name]
        ).fetchone()

        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "team_id": row[2],
                "created_at": row[3]
            }

        user_id = f"user:{uuid.uuid4().hex[:8]}"
        now = datetime.now()
        self.db.conn.execute(
            "INSERT INTO users (user_id, username, team_id, created_at) VALUES (?, ?, ?, ?)",
            [user_id, clean_name, team_id, now]
        )
        return {
            "user_id": user_id,
            "username": clean_name,
            "team_id": team_id,
            "created_at": now
        }

    def list_users(self) -> List[Dict[str, Any]]:
        """Összes regisztrált felhasználó listázása."""
        rows = self.db.conn.execute(
            "SELECT user_id, username, team_id, created_at FROM users ORDER BY created_at ASC"
        ).fetchall()
        return [
            {"user_id": r[0], "username": r[1], "team_id": r[2], "created_at": r[3]}
            for r in rows
        ]

    def record_answer(
        self,
        user_id: str,
        question_id: str,
        given_answer: str,
        is_correct: bool,
        confidence_level: float,
        response_time_ms: Optional[int] = None
    ) -> str:
        """Játékos által adott válasz és konfidencia szint rögzítése a válasznaplóban."""
        answer_id = f"ans:{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        # Normalizáljuk a konfidenciát [0.0, 1.0] közé
        conf = max(0.0, min(1.0, float(confidence_level)))

        self.db.conn.execute("""
            INSERT INTO player_answers 
            (answer_id, user_id, question_id, given_answer, is_correct, confidence_level, response_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [answer_id, user_id, question_id, str(given_answer), is_correct, conf, response_time_ms, now])

        return answer_id

    def get_user_answers(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Egy adott játékos összes korábbi válasza kérdésmetaadatokkal összekapcsolva."""
        query = """
            SELECT a.answer_id, a.user_id, a.question_id, a.given_answer, a.is_correct,
                   a.confidence_level, a.response_time_ms, a.created_at,
                   q.text, q.mechanism, q.correct_answer, q.domain, q.subdomain
            FROM player_answers a
            LEFT JOIN quiz_questions q ON a.question_id = q.question_id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT ?
        """
        rows = self.db.conn.execute(query, [user_id, limit]).fetchall()
        answers = []
        for r in rows:
            answers.append({
                "answer_id": r[0],
                "user_id": r[1],
                "question_id": r[2],
                "given_answer": r[3],
                "is_correct": bool(r[4]),
                "confidence_level": float(r[5]),
                "response_time_ms": r[6],
                "created_at": r[7],
                "question_text": r[8] or "",
                "mechanism": r[9] or "abcd",
                "correct_answer": r[10] or "",
                "domain": r[11] or "general",
                "subdomain": r[12] or ""
            })
        return answers

    def update_player_skills(
        self,
        user_id: str,
        domain: str,
        mechanism: str,
        skill_rating: float,
        confidence_bias: float,
        sample_count: int
    ):
        """Képességmátrix cella frissítése vagy beszúrása."""
        now = datetime.now()
        self.db.conn.execute("""
            INSERT OR REPLACE INTO player_skills
            (user_id, domain, mechanism, skill_rating, confidence_bias, sample_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [user_id, domain, mechanism, skill_rating, confidence_bias, sample_count, now])

    def get_player_skills(self, user_id: str) -> List[Dict[str, Any]]:
        """Játékos készségmátrix lekérdezése."""
        rows = self.db.conn.execute("""
            SELECT domain, mechanism, skill_rating, confidence_bias, sample_count, last_updated
            FROM player_skills
            WHERE user_id = ?
            ORDER BY domain, mechanism
        """, [user_id]).fetchall()
        return [
            {
                "domain": r[0],
                "mechanism": r[1],
                "skill_rating": float(r[2]),
                "confidence_bias": float(r[3]),
                "sample_count": int(r[4]),
                "last_updated": r[5]
            }
            for r in rows
        ]
