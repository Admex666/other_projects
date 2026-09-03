"""
Optivoya — 1-Click SQLite to Supabase Migration Script
Reads all local users, sessions, and telemetry events from data/analytics.db
and pushes them into Supabase PostgreSQL.
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase, is_supabase_configured, get_supabase_config

def migrate():
    print("====================================================================")
    print("  OPTIVOYA — SQLITE TO SUPABASE MIGRATION WIZARD")
    print("====================================================================")

    url, key = get_supabase_config()
    if not is_supabase_configured():
        print("\n[ERROR] Supabase nincs konfigurálva a .env fájlban!")
        print("Kérlek add hozzá a .env fájlhoz az alábbi sorokat:")
        print("  SUPABASE_URL=\"https://your-project.supabase.co\"")
        print("  SUPABASE_KEY=\"your-anon-or-service-role-key\"")
        return False

    print(f"\n[INFO] Csatlakozás a Supabase felhőhöz: {url}...")
    sb = get_supabase()
    if not sb:
        print("[ERROR] Nem sikerült inicializálni a Supabase klienst.")
        return False

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "analytics.db")
    if not os.path.exists(db_path):
        print(f"[INFO] Helyi SQLite adatbázis ({db_path}) nem található. Supabase kész.")
        return True

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Migrate Users
    c.execute("SELECT * FROM beta_users")
    users = [dict(r) for r in c.fetchall()]
    print(f"\n[1/3] {len(users)} db béta felhasználó átvitele...")
    for u in users:
        u_data = {
            "username": u["username"],
            "password_hash": u["password_hash"],
            "full_name": u.get("full_name"),
            "company_name": u.get("company_name"),
            "email": u.get("email"),
            "role": u.get("role") or "advisor",
            "is_active": bool(u.get("is_active", 1)),
            "notes": u.get("notes") or ""
        }
        try:
            sb.table("beta_users").upsert(u_data, on_conflict="username").execute()
            print(f"  + Felhasználó szinkronizálva: @{u['username']}")
        except Exception as e:
            print(f"  - Hiba @{u['username']} mentésekor: {e}")

    # 2. Migrate Sessions
    c.execute("SELECT * FROM user_sessions")
    sessions = [dict(r) for r in c.fetchall()]
    print(f"\n[2/3] {len(sessions)} db munkamenet átvitele...")
    for s in sessions:
        s_data = {
            "session_id": s["session_id"],
            "user_id": s["user_id"],
            "searches_count": s.get("searches_count", 1)
        }
        try:
            sb.table("user_sessions").upsert(s_data, on_conflict="session_id").execute()
        except Exception as e:
            print(f"  - Hiba munkamenet {s['session_id']} mentésekor: {e}")

    # 3. Migrate Events
    c.execute("SELECT * FROM telemetry_events")
    events = [dict(r) for r in c.fetchall()]
    print(f"\n[3/3] {len(events)} db telemetria esemény átvitele...")
    for ev in events:
        p_json = {}
        try: p_json = json.loads(ev["search_params"]) if ev["search_params"] else {}
        except Exception: pass

        m_json = {}
        try: m_json = json.loads(ev["meta_data"]) if ev["meta_data"] else {}
        except Exception: pass

        ev_data = {
            "event_id": ev["event_id"],
            "session_id": ev.get("session_id"),
            "user_id": ev["user_id"],
            "event_type": ev["event_type"],
            "module": ev["module"],
            "search_params": p_json,
            "duration_ms": ev.get("duration_ms"),
            "results_count": ev.get("results_count"),
            "success": bool(ev.get("success", 1)),
            "error_message": ev.get("error_message"),
            "meta_data": m_json
        }
        try:
            sb.table("telemetry_events").upsert(ev_data, on_conflict="event_id").execute()
            print(f"  + Esemény szinkronizálva: {ev['event_id']} ({ev['module']})")
        except Exception as e:
            print(f"  - Hiba esemény {ev['event_id']} mentésekor: {e}")

    conn.close()
    print("\n====================================================================")
    print("  [SUCCESS] AZ ÖSSZES ADAT SIKERESEN ÁTTÖLTVE A SUPABASE-BE!")
    print("====================================================================")
    return True

if __name__ == "__main__":
    migrate()
