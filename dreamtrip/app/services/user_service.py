"""
Optivoya Beta User Service
Supports Supabase Cloud PostgreSQL with seamless SQLite fallback.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.analytics_models import get_db_connection
from app.core.supabase import get_supabase

def get_all_beta_users() -> List[Dict[str, Any]]:
    """Returns all beta users with activity statistics."""
    sb = get_supabase()
    if sb:
        try:
            # 1. Fetch all users from Supabase
            users_res = sb.table("beta_users").select("*").order("created_at", desc=True).execute()
            users_data = users_res.data or []

            # 2. Fetch event stats
            events_res = sb.table("telemetry_events").select("user_id, event_type, success, created_at").execute()
            events_data = events_res.data or []

            user_stats: Dict[str, Dict[str, Any]] = {}
            for ev in events_data:
                u = ev.get("user_id")
                if not u:
                    continue
                if u not in user_stats:
                    user_stats[u] = {"total": 0, "success": 0, "latest": None}
                user_stats[u]["total"] += 1
                if ev.get("event_type") == "search_completed" and ev.get("success"):
                    user_stats[u]["success"] += 1
                c_at = ev.get("created_at")
                if c_at and (not user_stats[u]["latest"] or c_at > user_stats[u]["latest"]):
                    user_stats[u]["latest"] = c_at

            users = []
            for u in users_data:
                uname = u["username"]
                st = user_stats.get(uname, {"total": 0, "success": 0, "latest": None})
                users.append({
                    "id": u["id"],
                    "username": uname,
                    "full_name": u.get("full_name") or uname,
                    "company_name": u.get("company_name") or "Független",
                    "email": u.get("email") or "",
                    "role": u.get("role") or "advisor",
                    "created_at": str(u.get("created_at") or "")[:19],
                    "last_active_at": str(st["latest"] or u.get("last_active_at") or u.get("created_at") or "")[:19],
                    "is_active": bool(u.get("is_active", True)),
                    "notes": u.get("notes") or "",
                    "total_events": st["total"],
                    "successful_searches": st["success"]
                })
            return users
        except Exception as e:
            print(f"[USER SERVICE ERROR] Supabase get_all_beta_users failed: {e}, falling back to SQLite...")

    # Fallback to local SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        u.id, u.username, u.full_name, u.company_name, u.email, u.role, 
        u.created_at, u.last_active_at, u.is_active, u.notes,
        COUNT(e.id) as total_events,
        SUM(CASE WHEN e.event_type = 'search_completed' AND e.success = 1 THEN 1 ELSE 0 END) as successful_searches,
        MAX(e.created_at) as latest_search_at
    FROM beta_users u
    LEFT JOIN telemetry_events e ON u.username = e.user_id
    GROUP BY u.id
    ORDER BY u.created_at DESC
    """)
    rows = cursor.fetchall()
    users = []
    for r in rows:
        users.append({
            "id": r["id"],
            "username": r["username"],
            "full_name": r["full_name"] or r["username"],
            "company_name": r["company_name"] or "Független",
            "email": r["email"] or "",
            "role": r["role"] or "advisor",
            "created_at": str(r["created_at"] or "")[:19],
            "last_active_at": str(r["latest_search_at"] or r["last_active_at"] or r["created_at"] or "")[:19],
            "is_active": bool(r["is_active"]),
            "notes": r["notes"] or "",
            "total_events": r["total_events"] or 0,
            "successful_searches": r["successful_searches"] or 0
        })
    conn.close()
    return users

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("beta_users").select("*").eq("username", username).eq("is_active", True).limit(1).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            print(f"[USER SERVICE ERROR] Supabase get_user_by_username failed: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beta_users WHERE username = ? AND is_active = 1", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def verify_user_login(username: str, password: str) -> bool:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("beta_users").select("password_hash, is_active").eq("username", username).limit(1).execute()
            if res.data:
                user = res.data[0]
                if user.get("is_active") and user.get("password_hash") == password:
                    update_user_activity(username)
                    return True
                return False
        except Exception as e:
            print(f"[USER SERVICE ERROR] Supabase verify_user_login failed: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, is_active FROM beta_users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row["is_active"] and row["password_hash"] == password:
        update_user_activity(username)
        return True
    return False

def create_beta_user(username: str, password: str, full_name: str = "", company_name: str = "", email: str = "", notes: str = "") -> Dict[str, Any]:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("beta_users").insert({
                "username": username.strip(),
                "password_hash": password.strip(),
                "full_name": full_name.strip(),
                "company_name": company_name.strip(),
                "email": email.strip(),
                "notes": notes.strip(),
                "is_active": True
            }).execute()
            if res.data:
                return {"status": "ok", "username": username}
        except Exception as e:
            return {"status": "error", "error": f"Supabase felhasználó létrehozási hiba: {str(e)}"}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO beta_users (username, password_hash, full_name, company_name, email, notes, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (username.strip(), password.strip(), full_name.strip(), company_name.strip(), email.strip(), notes.strip()))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"status": "ok", "user_id": user_id, "username": username}
    except Exception as e:
        conn.close()
        return {"status": "error", "error": f"Felhasználónév már létezik vagy érvénytelen: {str(e)}"}

def toggle_user_active(user_id: Any) -> bool:
    sb = get_supabase()
    if sb:
        try:
            curr = sb.table("beta_users").select("is_active").eq("id", user_id).limit(1).execute()
            if curr.data:
                new_val = not bool(curr.data[0].get("is_active", True))
                sb.table("beta_users").update({"is_active": new_val}).eq("id", user_id).execute()
                return True
        except Exception as e:
            print(f"[USER SERVICE ERROR] Supabase toggle_user_active failed: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE beta_users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def update_user_activity(username: str):
    sb = get_supabase()
    if sb:
        try:
            sb.table("beta_users").update({"last_active_at": datetime.utcnow().isoformat()}).eq("username", username).execute()
            return
        except Exception as e:
            print(f"[USER SERVICE ERROR] Supabase update_user_activity failed: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE beta_users SET last_active_at = ? WHERE username = ?", (now_iso, username))
    conn.commit()
    conn.close()
