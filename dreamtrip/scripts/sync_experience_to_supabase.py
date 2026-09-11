"""
Sync Raw Experience Records from Local Disk Store to Supabase Cloud
Usage:
    python scripts/sync_experience_to_supabase.py --destination IT_BARI
    python scripts/sync_experience_to_supabase.py --all
"""
import sys
import os
import argparse

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase, is_supabase_configured
from app.services.experience.raw_store import RawDataStore

def verify_and_sync(destination_id: str = None):
    print("=" * 80)
    print("🚀 OPTIVOYA EXPERIENCE -> SUPABASE SYNCHRONIZER")
    print("=" * 80)

    if not is_supabase_configured():
        print("❌ Supabase is NOT configured in .env! (Missing SUPABASE_URL / SUPABASE_KEY)")
        return

    sb = get_supabase()
    if not sb:
        print("❌ Could not connect to Supabase.")
        return

    # Check if raw_source_records table exists
    try:
        sb.table("raw_source_records").select("id").limit(1).execute()
        print("✅ Supabase table 'raw_source_records' is ready and accessible!")
    except Exception as e:
        print("⚠️ Supabase table 'raw_source_records' does not exist yet!")
        print("\n👉 Please execute the SQL script in your Supabase SQL Editor:")
        print("   File: supabase_experience_schema.sql")
        print("   (It creates raw_source_records, experience_entities, and destination_experience_profiles)")
        return

    store = RawDataStore()
    base_dir = store.base_dir
    destinations = [destination_id] if destination_id else [
        d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
    ]

    total_synced = 0
    for dest in destinations:
        records = store.load_records(dest)
        print(f"\n📂 Loading '{dest}': found {len(records)} raw records on disk...")
        if not records:
            continue

        synced = store._sync_records_to_supabase(records, dest)
        print(f" -> Successfully synced {synced} records to Supabase 'raw_source_records'!")
        total_synced += synced

    # Query current count in Supabase
    try:
        res = sb.table("raw_source_records").select("id, source", count="exact").execute()
        total_in_sb = res.count if hasattr(res, "count") and res.count is not None else len(res.data)
        print(f"\n🎉 Total raw records in Supabase 'raw_source_records': {total_in_sb}")
    except Exception as e:
        print(f"Count query error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync raw experience records to Supabase")
    parser.add_argument("--destination", default="IT_BARI", help="Destination ID to sync (e.g. IT_BARI)")
    parser.add_argument("--all", action="store_true", help="Sync all destinations in raw store")
    args = parser.parse_args()

    dest = None if args.all else args.destination
    verify_and_sync(dest)
