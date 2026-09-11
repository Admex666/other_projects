"""
Experience Engine Database Layer (Supabase PostgreSQL).
Manages persistence for canonical experience entities and destination profiles.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.supabase import get_supabase, is_supabase_configured
from .models import CanonicalExperienceEntity, DestinationExperienceProfile

class ExperienceDB:
    def __init__(self):
        self._sb = get_supabase() if is_supabase_configured() else None

    def is_ready(self) -> bool:
        return self._sb is not None

    def upsert_canonical_entities(self, entities: List[CanonicalExperienceEntity]) -> int:
        """Batch upserts resolved canonical entities into Supabase."""
        if not self._sb or not entities:
            return 0

        db_records = []
        now_iso = datetime.utcnow().isoformat()
        for e in entities:
            db_records.append({
                "entity_id": e.entity_id,
                "destination_id": e.destination_id.upper(),
                "canonical_name": e.canonical_name,
                "category": e.category,
                "subcategory": e.subcategory,
                "lat": e.lat,
                "lon": e.lon,
                "rating": e.rating,
                "review_count": e.review_count,
                "price_level": e.price_level,
                "est_duration_hours": e.est_duration_hours,
                "best_time_of_day": e.best_time_of_day,
                "confidence_score": e.confidence_score,
                "sources_present": e.sources_present,
                "source_ids": e.source_ids,
                "image_urls": e.image_urls,
                "description": e.description,
                "tags": e.tags,
                "metadata": e.metadata,
                "updated_at": now_iso
            })

        # Deduplicate db_records by entity_id to avoid PostgreSQL 21000 batch collision
        unique_records = {}
        for r in db_records:
            unique_records[r["entity_id"]] = r
        db_records = list(unique_records.values())

        batch_size = 50
        total_upserted = 0
        for i in range(0, len(db_records), batch_size):
            batch = db_records[i:i + batch_size]
            try:
                res = self._sb.table("experience_entities").upsert(
                    batch,
                    on_conflict="entity_id"
                ).execute()
                if res.data:
                    total_upserted += len(res.data)
            except Exception as e:
                err_str = str(e)
                if "PGRST205" in err_str or "Could not find the table" in err_str:
                    print("[EXPERIENCE DB NOTICE] Table 'experience_entities' not found in Supabase. Please execute 'supabase_experience_schema.sql'.")
                    return 0
                else:
                    print(f"[EXPERIENCE DB WARN] Batch upsert failed: {e}")

        return total_upserted

    def get_canonical_entities(self, destination_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries canonical experience entities for a destination, optionally filtered by category."""
        if not self._sb:
            return []

        try:
            q = self._sb.table("experience_entities").select("*").eq("destination_id", destination_id.upper())
            if category:
                q = q.eq("category", category)
            res = q.order("rating", desc=True).execute()
            return res.data or []
        except Exception as e:
            print(f"[EXPERIENCE DB ERROR] get_canonical_entities failed: {e}")
            return []

    def upsert_destination_profile(self, profile: DestinationExperienceProfile) -> bool:
        """Upserts a destination's pre-calculated experience profile into Supabase."""
        if not self._sb:
            return False

        try:
            res = self._sb.table("destination_experience_profiles").upsert(
                profile.to_dict(),
                on_conflict="destination_id"
            ).execute()
            return bool(res.data)
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "Could not find the table" in err_str:
                print("[EXPERIENCE DB NOTICE] Table 'destination_experience_profiles' not found in Supabase.")
            else:
                print(f"[EXPERIENCE DB ERROR] upsert_destination_profile failed: {e}")
            return False

    def get_destination_profile(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """Instant lookup of pre-aggregated destination experience profile."""
        if not self._sb:
            return None

        try:
            res = self._sb.table("destination_experience_profiles").select("*").eq("destination_id", destination_id.upper()).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"[EXPERIENCE DB ERROR] get_destination_profile failed: {e}")
            return None
