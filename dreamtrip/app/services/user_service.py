"""
Optivoya Beta User Service
Handles user creation, verification, authentication, and directory queries.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.analytics_models import get_db_connection

def get_all_beta_users() -> List[Dict[str, Any]]:
    """Returns all beta users with activity statistics."""
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
            "created_at": r["created_at"],
            "last_active_at": r["latest_search_at"] or r["last_active_at"] or r["created_at"],
            "is_active": bool(r["is_active"]),
            "notes": r["notes"] or "",
            "total_events": r["total_events"] or 0,
            "successful_searches": r["successful_searches"] or 0
        })
    conn.close()
    return users

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beta_users WHERE username = ? AND is_active = 1", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def verify_user_login(username: str, password: str) -> bool:
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

def toggle_user_active(user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE beta_users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def update_user_activity(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE beta_users SET last_active_at = ? WHERE username = ?", (now_iso, username))
    conn.commit()
    conn.close()
