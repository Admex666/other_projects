"""
Optivoya Beta Analytics & Telemetry Tracking Service
Supports Supabase Cloud PostgreSQL with seamless SQLite fallback.
Tracks search queries, durations, errors, module usage, and calculates Time Saved / Client.
"""
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from app.models.analytics_models import get_db_connection
from app.core.supabase import get_supabase

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
    """Records an atomic telemetry event in Supabase or SQLite."""
    event_id = "evt_" + uuid.uuid4().hex[:12]
    clean_user = user_id or "anonymous_guest"
    clean_session = session_id or "sess_" + uuid.uuid4().hex[:8]

    sb = get_supabase()
    if sb:
        try:
            # 1. Auto-ensure user exists in Supabase beta_users
            if clean_user and clean_user not in ('anonymous_guest', 'anonymous_advisor', 'guest_planner', 'default_user'):
                sb.table("beta_users").upsert({
                    "username": clean_user,
                    "password_hash": "demo",
                    "full_name": clean_user.capitalize(),
                    "company_name": "Béta Advisor",
                    "role": "advisor",
                    "is_active": True,
                    "last_active_at": datetime.utcnow().isoformat()
                }, on_conflict="username").execute()

            # 2. Insert telemetry event
            sb.table("telemetry_events").insert({
                "event_id": event_id,
                "session_id": clean_session,
                "user_id": clean_user,
                "event_type": event_type,
                "module": module,
                "search_params": search_params or {},
                "duration_ms": duration_ms,
                "results_count": results_count,
                "success": success,
                "error_message": error_message,
                "meta_data": meta_data or {}
            }).execute()

            # 3. Update session
            sb.table("user_sessions").upsert({
                "session_id": clean_session,
                "user_id": clean_user,
                "last_event_at": datetime.utcnow().isoformat()
            }, on_conflict="session_id").execute()

            return event_id
        except Exception as e:
            print(f"[ANALYTICS ERROR] Supabase record_telemetry_event failed: {e}, falling back to SQLite...")

    # Fallback to local SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    params_json = json.dumps(search_params or {}, ensure_ascii=False)
    meta_json = json.dumps(meta_data or {}, ensure_ascii=False)

    try:
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

        cursor.execute("""
        INSERT INTO user_sessions (session_id, user_id, last_event_at, searches_count)
        VALUES (?, ?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(session_id) DO UPDATE SET 
            last_event_at = CURRENT_TIMESTAMP,
            searches_count = searches_count + 1
        """, (clean_session, clean_user))

        conn.commit()
    except Exception as e:
        print(f"[ANALYTICS ERROR] SQLite record_telemetry_event failed: {e}")
    finally:
        conn.close()

    return event_id

def _normalize_user_filter(user_id: Optional[Union[str, List[str]]]) -> List[str]:
    if not user_id:
        return []
    if isinstance(user_id, list):
        res = []
        for u in user_id:
            if u and u != "all":
                for part in str(u).split(","):
                    p = part.strip()
                    if p and p != "all" and p not in res:
                        res.append(p)
        return res
    if isinstance(user_id, str):
        if user_id.strip() == "all" or not user_id.strip():
            return []
        parts = [p.strip() for p in user_id.split(",") if p.strip() and p.strip() != "all"]
        return list(dict.fromkeys(parts))
    return []

def get_analytics_kpis(user_id: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """Calculates validation KPIs from Supabase or SQLite, filtered by user(s) if specified."""
    target_users = _normalize_user_filter(user_id)
    is_filtered = len(target_users) > 0

    sb = get_supabase()
    if sb:
        try:
            # 1. Total users
            if is_filtered:
                total_users = len(target_users)
            else:
                users_res = sb.table("beta_users").select("id, is_active").eq("is_active", True).execute()
                total_users = len(users_res.data or [])

            # 2. Events & search metrics
            q = sb.table("telemetry_events").select("*")
            if is_filtered:
                if len(target_users) == 1:
                    q = q.eq("user_id", target_users[0])
                else:
                    q = q.in_("user_id", target_users)
            events_res = q.execute()
            events = events_res.data or []

            search_events = [e for e in events if e.get("event_type") == "search_completed"]
            total_searches = len(search_events)
            successful_searches = len([e for e in search_events if e.get("success")])
            
            durations = [e.get("duration_ms") for e in search_events if e.get("duration_ms") and e.get("duration_ms") > 0]
            avg_duration_ms = round(sum(durations) / len(durations), 1) if durations else (1800.0 if total_searches == 0 else 0.0)
            success_rate = round((successful_searches / total_searches * 100), 1) if total_searches > 0 else 100.0

            # Module usage
            module_usage: Dict[str, int] = {}
            for e in events:
                m = e.get("module") or "other"
                module_usage[m] = module_usage.get(m, 0) + 1

            # Proposals count
            proposals_count = len([e for e in events if e.get("event_type") == "proposal_exported"])

            # Time saved
            optivoya_avg_min = (avg_duration_ms / 1000.0) / 60.0
            saved_minutes_per_search = max(5.0, MANUAL_RESEARCH_BASELINE_MINUTES - optivoya_avg_min)
            total_time_saved_hours = round((successful_searches * saved_minutes_per_search) / 60.0, 1)

            # Repeat users
            user_sessions: Dict[str, set] = {}
            for e in events:
                uid = e.get("user_id")
                sid = e.get("session_id")
                if uid and uid != "anonymous_guest" and sid:
                    if uid not in user_sessions:
                        user_sessions[uid] = set()
                    user_sessions[uid].add(sid)
            repeat_users_count = len([uid for uid, sids in user_sessions.items() if len(sids) > 1])

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
                "module_usage": module_usage,
                "is_filtered": is_filtered,
                "filtered_users": target_users
            }
        except Exception as e:
            print(f"[ANALYTICS ERROR] Supabase get_analytics_kpis failed: {e}, falling back to SQLite...")

    # Fallback to local SQLite
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_filtered:
        total_users = len(target_users)
        placeholders = ",".join(["?"] * len(target_users))
        user_where = f" AND user_id IN ({placeholders})"
        user_params = target_users
    else:
        cursor.execute("SELECT COUNT(*) FROM beta_users WHERE is_active = 1")
        total_users = cursor.fetchone()[0]
        user_where = ""
        user_params = []

    cursor.execute(f"""
    SELECT 
        COUNT(*) as total_searches,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_searches,
        AVG(CASE WHEN duration_ms IS NOT NULL AND duration_ms > 0 THEN duration_ms ELSE NULL END) as avg_duration_ms
    FROM telemetry_events
    WHERE event_type = 'search_completed'{user_where}
    """, user_params)
    search_row = cursor.fetchone()
    total_searches = search_row["total_searches"] or 0
    successful_searches = search_row["successful_searches"] or 0
    avg_duration_ms = round(search_row["avg_duration_ms"] or 1800.0, 1)
    success_rate = round((successful_searches / total_searches * 100), 1) if total_searches > 0 else 100.0

    cursor.execute(f"""
    SELECT module, COUNT(*) as count 
    FROM telemetry_events 
    WHERE event_type IN ('search_completed', 'search_started'){user_where}
    GROUP BY module
    """, user_params)
    module_rows = cursor.fetchall()
    module_usage = {r["module"]: r["count"] for r in module_rows}

    cursor.execute(f"SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'proposal_exported'{user_where}", user_params)
    proposals_count = cursor.fetchone()[0]

    optivoya_avg_min = (avg_duration_ms / 1000.0) / 60.0
    saved_minutes_per_search = max(5.0, MANUAL_RESEARCH_BASELINE_MINUTES - optivoya_avg_min)
    total_time_saved_hours = round((successful_searches * saved_minutes_per_search) / 60.0, 1)

    cursor.execute(f"""
    SELECT user_id, COUNT(DISTINCT session_id) as session_count
    FROM telemetry_events
    WHERE user_id != 'anonymous_guest'{user_where}
    GROUP BY user_id
    HAVING session_count > 1
    """, user_params)
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
        "module_usage": module_usage,
        "is_filtered": is_filtered,
        "filtered_users": target_users
    }

def get_user_timeline(user_id: Optional[Union[str, List[str]]] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Returns chronologically ordered telemetry events, optionally filtered by user(s)."""
    target_users = _normalize_user_filter(user_id)
    is_filtered = len(target_users) > 0

    sb = get_supabase()
    if sb:
        try:
            # 1. Fetch users mapping for display names
            users_res = sb.table("beta_users").select("username, full_name, company_name").execute()
            users_map = {u["username"]: u for u in (users_res.data or [])}

            # 2. Fetch events
            q = sb.table("telemetry_events").select("*").order("created_at", desc=True).limit(limit)
            if is_filtered:
                if len(target_users) == 1:
                    q = q.eq("user_id", target_users[0])
                else:
                    q = q.in_("user_id", target_users)
            res = q.execute()
            events = res.data or []

            timeline = []
            for ev in events:
                uid = ev.get("user_id") or "guest"
                u_info = users_map.get(uid, {})
                fn = u_info.get("full_name")
                cn = u_info.get("company_name")
                dur = ev.get("duration_ms")
                params = ev.get("search_params") or {}
                if isinstance(params, str):
                    try: params = json.loads(params)
                    except Exception: params = {}

                timeline.append({
                    "id": ev.get("id"),
                    "event_id": ev.get("event_id"),
                    "session_id": ev.get("session_id"),
                    "user_id": uid,
                    "user_display": f"{fn or uid} ({cn or 'Advisor'})" if fn else uid,
                    "event_type": ev.get("event_type"),
                    "module": ev.get("module"),
                    "search_params": params,
                    "duration_ms": dur,
                    "duration_formatted": f"{dur:.0f} ms" if dur else "-",
                    "results_count": ev.get("results_count") if ev.get("results_count") is not None else "-",
                    "success": bool(ev.get("success", True)),
                    "error_message": ev.get("error_message"),
                    "meta_data": ev.get("meta_data") or {},
                    "created_at": str(ev.get("created_at") or "")[:19].replace("T", " ")
                })
            return timeline
        except Exception as e:
            print(f"[ANALYTICS ERROR] Supabase get_user_timeline failed: {e}, falling back to SQLite...")

    # Fallback to local SQLite
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
    if is_filtered:
        placeholders = ",".join(["?"] * len(target_users))
        query += f" WHERE e.user_id IN ({placeholders})"
        params.extend(target_users)

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


def _parse_ts(ts_str: Any) -> Optional[datetime]:
    if not ts_str:
        return None
    s = str(ts_str).replace("Z", "").replace("T", " ")
    if "." in s:
        s = s.split(".")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt)
        except Exception:
            pass
    return None

def format_duration_human(seconds: float) -> str:
    s = max(0, int(round(seconds)))
    if s < 60:
        return f"{s} mp"
    m = s // 60
    rem_s = s % 60
    if m < 60:
        return f"{m} perc {rem_s} mp" if rem_s > 0 else f"{m} perc"
    h = m // 60
    rem_m = m % 60
    return f"{h} óra {rem_m} perc"


def get_user_sessions_summary(
    user_id: Optional[Union[str, List[str]]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Összegzi a telemetria eseményeket összefüggő látogatási munkamenetekre (User Journeys).
    Kiszámítja az egyes sessionök teljes időtartamát, a bejárt útvonalat és a lépések közötti tartózkodási időt (dwell time).
    """
    raw_events = get_user_timeline(user_id=user_id, limit=300)
    if not raw_events:
        return []

    from app.core.config import get_clarity_project_id

    # Csoportosítás session_id szerint
    sessions_dict: Dict[str, List[Dict[str, Any]]] = {}
    for ev in raw_events:
        sid = ev.get("session_id") or f"sess_orphan_{ev.get('user_id')}_{ev.get('id')}"
        if sid not in sessions_dict:
            sessions_dict[sid] = []
        sessions_dict[sid].append(ev)

    summaries = []
    for sid, ev_list in sessions_dict.items():
        # Kronológiai sorrend (legrégebbi elöl, hogy lássuk a haladást)
        ev_list.sort(key=lambda x: str(x.get("created_at") or ""))
        
        first_ev = ev_list[0]
        last_ev = ev_list[-1]
        
        uid = first_ev.get("user_id") or "guest"
        user_disp = first_ev.get("user_display") or uid

        t_start = _parse_ts(first_ev.get("created_at"))
        t_end = _parse_ts(last_ev.get("created_at"))

        if t_start and t_end and t_end >= t_start:
            total_duration_sec = int((t_end - t_start).total_seconds())
        else:
            total_duration_sec = 0

        # Ha csak 1 esemény volt, vagy 0 másodperc, nézzük meg a kliens dwell_sec metaadatot
        if total_duration_sec == 0:
            client_dwell = 0
            for e in ev_list:
                m = e.get("meta_data") or {}
                if isinstance(m, dict) and m.get("dwell_sec"):
                    client_dwell += int(m.get("dwell_sec", 0))
            total_duration_sec = max(client_dwell, 15 if len(ev_list) > 1 else 8)

        # Felhasználói út lépéseinek (Journey Path) kibontása
        journey_path = []
        searches_count = 0
        clicks_count = 0
        has_error = False

        for i, ev in enumerate(ev_list):
            ev_type = ev.get("event_type", "")
            mod = ev.get("module", "")
            params = ev.get("search_params") or {}
            meta = ev.get("meta_data") or {}
            if not isinstance(meta, dict): meta = {}
            if not isinstance(params, dict): params = {}

            if not ev.get("success"):
                has_error = True

            # Számoljuk a következő eseményig eltelt időt (dwell)
            step_dwell_sec = 0
            if i < len(ev_list) - 1:
                cur_t = _parse_ts(ev.get("created_at"))
                next_t = _parse_ts(ev_list[i + 1].get("created_at"))
                if cur_t and next_t and next_t >= cur_t:
                    step_dwell_sec = int((next_t - cur_t).total_seconds())
            if step_dwell_sec == 0 and meta.get("dwell_sec"):
                step_dwell_sec = int(meta.get("dwell_sec", 0))

            # Szemantikus lépés azonosítása
            step_obj = None
            if mod == "destination_matcher" and ev_type == "search_completed":
                searches_count += 1
                cnt = ev.get("results_count")
                origin = params.get("origin", "Budapest")
                journey_path.append({
                    "step_idx": 1,
                    "title": f"Célállomások szűrése ({cnt} találat)",
                    "subtitle": f"Indulás: {origin}",
                    "icon": "location_on",
                    "badge": "1. Célpont",
                    "dwell_sec": step_dwell_sec,
                    "dwell_formatted": format_duration_human(step_dwell_sec),
                    "created_at": str(ev.get("created_at") or "")[-8:]
                })
            elif mod == "flight_intelligence" and ev_type == "search_completed":
                searches_count += 1
                cnt = ev.get("results_count")
                dest = params.get("destination", "Célállomás")
                journey_path.append({
                    "step_idx": 2,
                    "title": f"Járatkeresés ({cnt} járat)",
                    "subtitle": f"Cél: {dest}",
                    "icon": "flight",
                    "badge": "2. Járat",
                    "dwell_sec": step_dwell_sec,
                    "dwell_formatted": format_duration_human(step_dwell_sec),
                    "created_at": str(ev.get("created_at") or "")[-8:]
                })
            elif mod == "accommodation_intelligence" and ev_type == "search_completed":
                searches_count += 1
                cnt = ev.get("results_count")
                city = params.get("city", "Szállás")
                journey_path.append({
                    "step_idx": 3,
                    "title": f"Szálláskeresés ({cnt} szállás)",
                    "subtitle": f"Város: {city}",
                    "icon": "hotel",
                    "badge": "3. Szállás",
                    "dwell_sec": step_dwell_sec,
                    "dwell_formatted": format_duration_human(step_dwell_sec),
                    "created_at": str(ev.get("created_at") or "")[-8:]
                })
            elif ev_type == "proposal_exported" or mod == "proposal":
                dest = params.get("destination") or "Kész Terv"
                journey_path.append({
                    "step_idx": 4,
                    "title": "Ajánlat Exportálva (PDF)",
                    "subtitle": dest,
                    "icon": "picture_as_pdf",
                    "badge": "4. Ajánlat",
                    "dwell_sec": 0,
                    "dwell_formatted": "Kész",
                    "created_at": str(ev.get("created_at") or "")[-8:]
                })
            elif ev_type == "button_click":
                clicks_count += 1
                btn_txt = meta.get("button_text") or meta.get("action") or "Gombkattintás"
                act = meta.get("action", "")
                icon = "touch_app"
                badge = "Kattintás"
                step_idx = meta.get("planner_step", 0)

                if "destination_selected" in act or "Járatok keresése" in btn_txt:
                    icon = "check_circle"
                    badge = "Célpont Kész"
                    step_idx = 1
                elif "flight_selected" in act or "Járat kiválasztása" in btn_txt:
                    icon = "done_all"
                    badge = "Járat Kész"
                    step_idx = 2
                elif "stay_selected" in act or "Szállás kiválasztása" in btn_txt:
                    icon = "bed"
                    badge = "Szállás Kész"
                    step_idx = 3

                # Csak érdemi interakciókat jelenítünk meg a fő útvonalban
                if any(k in btn_txt for k in ("keresés", "Keresés", "kiválasztása", "Kiválasztása", "Ajánlat", "Export", "Preferenciák", "Dummy")):
                    journey_path.append({
                        "step_idx": step_idx,
                        "title": btn_txt[:40],
                        "subtitle": act.replace("_", " ").title(),
                        "icon": icon,
                        "badge": badge,
                        "dwell_sec": step_dwell_sec,
                        "dwell_formatted": format_duration_human(step_dwell_sec),
                        "created_at": str(ev.get("created_at") or "")[-8:]
                    })
            elif ev_type == "step_navigation":
                to_s = meta.get("to_step", 0)
                name = meta.get("step_name") or f"{to_s}. lépés"
                journey_path.append({
                    "step_idx": to_s,
                    "title": f"Navigáció: {name}",
                    "subtitle": f"{to_s}. lépés megnyitva",
                    "icon": "arrow_forward",
                    "badge": "Lépésváltás",
                    "dwell_sec": step_dwell_sec,
                    "dwell_formatted": format_duration_human(step_dwell_sec),
                    "created_at": str(ev.get("created_at") or "")[-8:]
                })

        # Clarity direkt URL ha be van állítva a projekt ID
        clarity_url = None
        c_proj_id = get_clarity_project_id()
        if c_proj_id:
            clarity_url = f"https://clarity.microsoft.com/projects/{c_proj_id}/recordings?filters=customTags%7Ceq%7Csession_id%7C{sid}"

        # Legújabb események legfelül az eseménylistában
        ev_list_reversed = list(reversed(ev_list))

        summaries.append({
            "session_id": sid,
            "user_id": uid,
            "user_display": user_disp,
            "started_at": str(first_ev.get("created_at") or "")[:19].replace("T", " "),
            "ended_at": str(last_ev.get("created_at") or "")[:19].replace("T", " "),
            "duration_sec": total_duration_sec,
            "duration_formatted": format_duration_human(total_duration_sec),
            "total_events": len(ev_list),
            "searches_count": searches_count,
            "clicks_count": clicks_count,
            "has_error": has_error,
            "clarity_url": clarity_url,
            "journey_path": journey_path,
            "events": ev_list_reversed
        })

    # Rendezés a session kezdete szerint DESC (a legfrissebb session legelöl)
    summaries.sort(key=lambda s: s["started_at"], reverse=True)
    return summaries[:limit]
