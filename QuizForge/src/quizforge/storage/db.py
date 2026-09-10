"""DuckDB kapcsolatkezelő és Parquet perzisztencia modul."""

import json
from pathlib import Path
from typing import Optional
import duckdb

from quizforge.core.config import settings
from quizforge.storage.schema import SCHEMA_SQL


class DatabaseManager:
    """DuckDB adatbázis kapcsolat és Parquet szinkronizáció kezelője."""

    def __init__(self, db_path: Optional[Path] = None, in_memory: bool = False):
        self.read_only = False
        if in_memory:
            self.db_path = ":memory:"
            self.conn = duckdb.connect(self.db_path)
        else:
            self.db_path = str(db_path or settings.DUCKDB_PATH)
            try:
                self.conn = duckdb.connect(self.db_path)
            except duckdb.IOException as e:
                if "folyamat nem fér hozzá" in str(e).lower() or "already open" in str(e).lower():
                    print("[FIGYELEM] A quizforge.duckdb zárolva van egy másik folyamat (pl. Harlequin) által.")
                    print("--> Átváltás biztonságos in-memory Parquet módra a lekérdezésekhez...")
                    self.db_path = ":memory:"
                    self.conn = duckdb.connect(self.db_path)
                    self.read_only = True
                    self.init_schema()
                    self.load_from_parquet()
                else:
                    raise e
        if not self.read_only:
            self.init_schema()

    def init_schema(self):
        """Táblák és sémák inicializálása."""
        self.conn.execute(SCHEMA_SQL)
        self.clean_junk_data()

    def clean_junk_data(self):
        """Kiszűri az 'Ismeretlen / MEK szerző' és haszontalan rekordokat az adatbázisból és relációkból."""
        try:
            self.conn.execute("""
                DELETE FROM relations 
                WHERE source_entity_id IN (SELECT entity_id FROM entities WHERE label_hu ILIKE '%ismeretlen%' OR label_hu ILIKE '%MEK szerző%' OR label_hu ILIKE '%szerző nélkül%')
                   OR target_entity_id IN (SELECT entity_id FROM entities WHERE label_hu ILIKE '%ismeretlen%' OR label_hu ILIKE '%MEK szerző%' OR label_hu ILIKE '%szerző nélkül%');
            """)
            self.conn.execute("""
                DELETE FROM entities 
                WHERE label_hu ILIKE '%ismeretlen%' 
                   OR label_hu ILIKE '%MEK szerző%' 
                   OR label_hu ILIKE '%szerző nélkül%';
            """)
            self.conn.execute("""
                DELETE FROM quiz_questions 
                WHERE text ILIKE '%ismeretlen%' 
                   OR correct_answer ILIKE '%ismeretlen%';
            """)
        except Exception:
            pass

    def export_to_parquet(self, output_dir: Optional[Path] = None):
        """Minden fő tábla exportálása Parquet formátumba analitikai feldolgozáshoz."""
        target_dir = output_dir or settings.PARQUET_DATA_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        tables = ["entities", "relations", "quiz_questions", "question_entities", "entity_relevance"]
        for table in tables:
            parquet_file = target_dir / f"{table}.parquet"
            # Windowsos elérési utak formázása DuckDB kompatibilis perjelekkel
            safe_path = str(parquet_file).replace("\\", "/")
            self.conn.execute(f"COPY {table} TO '{safe_path}' (FORMAT PARQUET);")

    def load_from_parquet(self, input_dir: Optional[Path] = None):
        """Adatok visszatöltése Parquet fájlokból."""
        source_dir = input_dir or settings.PARQUET_DATA_DIR
        tables = ["entities", "relations", "quiz_questions", "question_entities", "entity_relevance"]

        for table in tables:
            parquet_file = source_dir / f"{table}.parquet"
            if parquet_file.exists():
                safe_path = str(parquet_file).replace("\\", "/")
                self.conn.execute(f"INSERT OR REPLACE INTO {table} SELECT * FROM read_parquet('{safe_path}');")
        self.clean_junk_data()

    def get_stats(self) -> dict:
        """Adatbázis statisztikák lekérdezése."""
        stats = {}
        tables = ["entities", "relations", "quiz_questions", "question_entities", "entity_relevance"]
        for t in tables:
            cnt = self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            stats[t] = cnt
        return stats

    def close(self):
        if self.conn:
            self.conn.close()
