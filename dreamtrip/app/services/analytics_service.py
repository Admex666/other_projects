"""
Optivoya Beta Analytics & Telemetry Tracking Service
Tracks search queries, durations, errors, module usage, and calculates Time Saved / Client.
"""
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.analytics_models import get_db_connection

# Manual research baseline: egy átlagos utazási tanácsadó manuálisan ~45 percet tölt research-csel ügyfelenként
MANUAL_RESEARCH_BASELINE_MINUTES = 45.0

def record_telemetry_event(
    user_id: str,
    event_type: str,
    module: str,
    session_id: Optional[str] = None,
    search_params: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    results_count: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None
) -> str:
    """Records an atomic telemetry event in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    event_id = "evt_" + uuid.uuid4().hex[:12]
    
    clean_user = user_id or "anonymous_guest"
    clean_session = session_id or "sess_" + uuid.uuid4().hex[:8]

    params_json = json.dumps(search_params or {}, ensure_ascii=False)
    meta_json = json.dumps(meta_data or {}, ensure_ascii=False)

    try:
        # Ensure user exists in beta_users directory
        if clean_user and clean_user not in ('anonymous_guest', 'anonymous_advisor', 'guest_planner', 'default_user'):
            cursor.execute("""
            INSERT INTO beta_users (username, password_hash, full_name, company_name, role, is_active, last_active_at)
            VALUES (?, 'demo', ?, 'Béta Advisor', 'advisor', 1, CURRENT_TIMESTAMP)
            ON CONFLICT(username) DO UPDATE SET last_active_at = CURRENT_TIMESTAMP
            """, (clean_user, clean_user.capitalize()))

        cursor.execute("""
        INSERT INTO telemetry_events (
            event_id, session_id, user_id, event_type, module, 
            search_params, duration_ms, results_count, success, error_message, meta_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, clean_session, clean_user, event_type, module,
            params_json, duration_ms, results_count, 1 if success else 0, error_message, meta_json
        ))

        # Update or create session
        cursor.execute("""
        INSERT INTO user_sessions (session_id, user_id, last_event_at, searches_count)
        VALUES (?, ?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(session_id) DO UPDATE SET 
            last_event_at = CURRENT_TIMESTAMP,
            searches_count = searches_count + 1
        """, (clean_session, clean_user))

        conn.commit()
    except Exception as e:
        print(f"[ANALYTICS ERROR] Failed to record event: {e}")

    finally:
        conn.close()

    return event_id

def get_analytics_kpis() -> Dict[str, Any]:
    """Calculates high-level validation KPIs for the admin dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Beta Users
    cursor.execute("SELECT COUNT(*) FROM beta_users WHERE is_active = 1")
    total_users = cursor.fetchone()[0]

    # Total Searches & Success Rate
    cursor.execute("""
    SELECT 
        COUNT(*) as total_searches,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_searches,
        AVG(CASE WHEN duration_ms IS NOT NULL AND duration_ms > 0 THEN duration_ms ELSE NULL END) as avg_duration_ms
    FROM telemetry_events
    WHERE event_type = 'search_completed'
    """)
    search_row = cursor.fetchone()
    total_searches = search_row["total_searches"] or 0
    successful_searches = search_row["successful_searches"] or 0
    avg_duration_ms = round(search_row["avg_duration_ms"] or 1800.0, 1)
    
    success_rate = round((successful_searches / total_searches * 100), 1) if total_searches > 0 else 100.0

    # Module breakdown
    cursor.execute("""
    SELECT module, COUNT(*) as count 
    FROM telemetry_events 
    WHERE event_type IN ('search_completed', 'search_started')
    GROUP BY module
    """)
    module_rows = cursor.fetchall()
    module_usage = {r["module"]: r["count"] for r in module_rows}

    # Proposals Exported
    cursor.execute("SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'proposal_exported'")
    proposals_count = cursor.fetchone()[0]

    # Time Saved Calculation (H2 Hipotézis)
    # Feltételezve: minden sikeres összetett tervezés / export ~42 perc időmegtakarítás
    optivoya_avg_min = (avg_duration_ms / 1000.0) / 60.0
    saved_minutes_per_search = max(5.0, MANUAL_RESEARCH_BASELINE_MINUTES - optivoya_avg_min)
    total_time_saved_hours = round((successful_searches * saved_minutes_per_search) / 60.0, 1)

    # Repeat Usage (H4 Hipotézis)
    cursor.execute("""
    SELECT user_id, COUNT(DISTINCT session_id) as session_count
    FROM telemetry_events
    WHERE user_id != 'anonymous_guest'
    GROUP BY user_id
    HAVING session_count > 1
    """)
    repeat_users_count = len(cursor.fetchall())

    conn.close()

    return {
        "total_users": total_users,
        "total_searches": total_searches,
        "successful_searches": successful_searches,
        "success_rate_pct": success_rate,
        "avg_duration_ms": avg_duration_ms,
        "avg_duration_sec": round(avg_duration_ms / 1000.0, 2),
        "total_time_saved_hours": total_time_saved_hours,
        "repeat_users_count": repeat_users_count,
        "proposals_exported": proposals_count,
        "module_usage": module_usage
    }

def get_user_timeline(user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Returns chronologically ordered telemetry events for deep user inspection."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        e.id, e.event_id, e.session_id, e.user_id, e.event_type, e.module, 
        e.search_params, e.duration_ms, e.results_count, e.success, e.error_message, 
        e.meta_data, e.created_at,
        u.full_name, u.company_name
    FROM telemetry_events e
    LEFT JOIN beta_users u ON e.user_id = u.username
    """
    params = []
    if user_id and user_id != "all":
        query += " WHERE e.user_id = ?"
        params.append(user_id)

    query += " ORDER BY e.created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    
    timeline = []
    for r in rows:
        p_data = {}
        try:
            p_data = json.loads(r["search_params"]) if r["search_params"] else {}
        except Exception:
            pass

        m_data = {}
        try:
            m_data = json.loads(r["meta_data"]) if r["meta_data"] else {}
        except Exception:
            pass

        timeline.append({
            "id": r["id"],
            "event_id": r["event_id"],
            "session_id": r["session_id"],
            "user_id": r["user_id"],
            "user_display": f"{r['full_name'] or r['user_id']} ({r['company_name'] or 'Advisor'})" if r["full_name"] else r["user_id"],
            "event_type": r["event_type"],
            "module": r["module"],
            "search_params": p_data,
            "duration_ms": r["duration_ms"],
            "duration_formatted": f"{r['duration_ms']:.0f} ms" if r["duration_ms"] else "-",
            "results_count": r["results_count"] if r["results_count"] is not None else "-",
            "success": bool(r["success"]),
            "error_message": r["error_message"],
            "meta_data": m_data,
            "created_at": r["created_at"]
        })

    conn.close()
    return timeline
