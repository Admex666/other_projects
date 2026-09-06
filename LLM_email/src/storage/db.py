import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from src.models import ProcessedEmail


class EmailDatabase:
    """SQLite alapú állapotkezelő a már feldolgozott emailek idempotens nyilvántartására."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_emails (
                    message_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    account_name TEXT,
                    sender TEXT,
                    subject TEXT,
                    email_date TEXT,
                    category TEXT,
                    urgency TEXT,
                    importance TEXT,
                    summary TEXT,
                    action_items_json TEXT,
                    deadlines_json TEXT,
                    processed_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_account_date 
                ON processed_emails (account_id, email_date)
                """
            )
            conn.commit()

    def is_processed(self, message_id: str) -> bool:
        """Megadja, hogy egy adott üzenet már fel lett-e dolgozva korábban."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,))
            return cursor.fetchone() is not None

    def filter_unprocessed_ids(self, message_ids: List[str]) -> Set[str]:
        """Kiszűri a már feldolgozott üzeneteket és visszaadja a még feldolgozatlanok halmazát."""
        if not message_ids:
            return set()

        placeholders = ",".join("?" for _ in message_ids)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT message_id FROM processed_emails WHERE message_id IN ({placeholders})",
                message_ids,
            )
            processed = {row[0] for row in cursor.fetchall()}
            return set(message_ids) - processed

    def save_processed_email(self, item: ProcessedEmail) -> None:
        """Elment egy sikeresen feldolgozott levelet az adatbázisba."""
        self.save_processed_emails([item])

    def save_processed_emails(self, items: List[ProcessedEmail]) -> None:
        """Kötegelten menti az elemzett leveleket az adatbázisba."""
        if not items:
            return

        now_str = datetime.now().isoformat()
        records = [
            (
                item.raw.message_id,
                item.raw.account_id,
                item.raw.account_name,
                item.raw.sender,
                item.raw.subject,
                item.raw.date.isoformat(),
                item.analysis.category,
                item.analysis.urgency,
                item.analysis.importance,
                item.analysis.summary,
                json.dumps(item.analysis.action_items, ensure_ascii=False),
                json.dumps(item.analysis.deadlines, ensure_ascii=False),
                now_str,
            )
            for item in items
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO processed_emails (
                    message_id, account_id, account_name, sender, subject,
                    email_date, category, urgency, importance, summary,
                    action_items_json, deadlines_json, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            conn.commit()

    def get_recent_count(self, limit: int = 100) -> int:
        """Lekérdezi az összes feldolgozott levél számát."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_emails")
            row = cursor.fetchone()
            return row[0] if row else 0
