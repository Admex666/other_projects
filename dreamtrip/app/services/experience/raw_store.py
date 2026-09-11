"""
Raw Data Store for Optivoya Experience Ingestion Pipeline
Persists raw records to disk and Supabase, enabling offline re-parsing and zero data loss.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from .connectors.base import RawSourceRecord

RAW_STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "raw_sources"))

class RawDataStore:
    def __init__(self, base_dir: str = RAW_STORE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_records(self, records: List[RawSourceRecord], destination_id: str, sync_supabase: bool = True) -> int:
        """Saves records to structured disk store and optionally syncs to Supabase."""
        saved_count = 0
        dest_upper = destination_id.upper()
        for rec in records:
            source = rec.source
            dest_dir = os.path.join(self.base_dir, dest_upper, source)
            os.makedirs(dest_dir, exist_ok=True)

            # Sanitize filename
            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', rec.source_id)[:60]
            filename = f"{safe_id}.json"
            filepath = os.path.join(dest_dir, filename)

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(rec.to_dict(), f, ensure_ascii=False, indent=2)
                saved_count += 1
            except Exception as e:
                print(f"[RAW STORE ERROR] Failed to write {filepath}: {e}")

        # Supabase synchronization
        if sync_supabase and records:
            self._sync_records_to_supabase(records, dest_upper)

        return saved_count

    def _sync_records_to_supabase(self, records: List[RawSourceRecord], destination_id: str) -> int:
        """Upserts a list of raw source records into Supabase raw_source_records table in batches."""
        try:
            from app.core.supabase import get_supabase, is_supabase_configured
            if not is_supabase_configured():
                return 0

            sb = get_supabase()
            if not sb:
                return 0

            # Map to database schema
            db_records = []
            for r in records:
                db_records.append({
                    "destination_id": destination_id,
                    "source": r.source,
                    "source_id": str(r.source_id),
                    "name_candidate": r.name_candidate,
                    "raw_payload": r.raw_payload,
                    "license": r.license,
                    "retrieved_at": r.retrieved_at or datetime.utcnow().isoformat(),
                    "parser_version": r.parser_version or "v1.0"
                })

            # Upsert in batches of 50 to respect payload boundaries
            batch_size = 50
            upserted_count = 0
            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                try:
                    res = sb.table("raw_source_records").upsert(
                        batch,
                        on_conflict="destination_id,source,source_id"
                    ).execute()
                    if res.data:
                        upserted_count += len(res.data)
                except Exception as e:
                    # If table is not created yet, log a clear notice
                    err_msg = str(e)
                    if "PGRST205" in err_msg or "Could not find the table" in err_msg:
                        print("[RAW STORE NOTICE] Supabase table 'raw_source_records' not created yet. Please execute 'supabase_experience_schema.sql' in Supabase SQL Editor.")
                        return 0
                    else:
                        print(f"[RAW STORE WARN] Supabase batch upsert failed: {e}")

            return upserted_count
        except Exception as e:
            print(f"[RAW STORE ERROR] Supabase sync error: {e}")
            return 0

    def load_records(self, destination_id: str, source: Optional[str] = None) -> List[RawSourceRecord]:
        """Loads saved raw records for re-processing or analysis."""
        dest_dir = os.path.join(self.base_dir, destination_id.upper())
        if not os.path.exists(dest_dir):
            return []

        sources_to_load = [source] if source else os.listdir(dest_dir)
        loaded: List[RawSourceRecord] = []

        for s in sources_to_load:
            s_dir = os.path.join(dest_dir, s)
            if not os.path.isdir(s_dir):
                continue
            for fname in os.listdir(s_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(s_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            loaded.append(RawSourceRecord(
                                source=data["source"],
                                source_id=data["source_id"],
                                destination_id=data["destination_id"],
                                name_candidate=data["name_candidate"],
                                raw_payload=data["raw_payload"],
                                license=data.get("license", ""),
                                retrieved_at=data.get("retrieved_at", ""),
                                parser_version=data.get("parser_version", "v1.0")
                            ))
                    except Exception as e:
                        print(f"[RAW STORE WARN] Failed to read {fpath}: {e}")

        return loaded
