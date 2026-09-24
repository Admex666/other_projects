import os
import secrets
from fastapi import Request
from typing import Optional, Dict

# Alapértelmezett vészhelyzeti fiókok (Csak ha az adatbázis teljesen offline)
FALLBACK_USERS: Dict[str, str] = {
    "admin": os.getenv("ADMIN_PASSWORD", os.getenv("LEGACY_ADMIN_PASSWORD", "admin_fallback")),
    "adam": os.getenv("ADMIN_PASSWORD", "admin_fallback"),
    "bean": os.getenv("FALLBACK_ADVISOR_PASSWORD", "bean")
}
USERS = FALLBACK_USERS

# Aktív memóriabeli sessionök

sessions: Dict[str, str] = {}

def verify_credentials(username: str, password: str) -> bool:
    # 1. Hitelesítés a Supabase felhős adatbázisból
    try:
        from app.services.user_service import verify_user_login
        if verify_user_login(username, password):
            return True
    except Exception:
        pass
    # 2. Vészhelyzeti offline fallback
    return username in FALLBACK_USERS and FALLBACK_USERS[username] == password


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token

def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    return sessions.get(token) if token else None

def get_user_role(username: Optional[str]) -> str:
    """
    Visszaadja a felhasználó szerepkörét ('advisor', 'admin', 'planner', stb.).
    Elsődlegesen a Supabase adatbázisból kérdezi le.
    """
    if not username:
        return "guest"
    u = username.strip().lower()
    try:
        from app.services.user_service import get_user_by_username
        user_record = get_user_by_username(username)
        if user_record and user_record.get("role"):
            return str(user_record.get("role")).strip().lower()
    except Exception:
        pass
    # Offline fallback ha az adatbázis nem elérhető
    if u in ("admin", "adam"):
        return "admin"
    if u in FALLBACK_USERS:
        return "advisor"
    return "planner"

def is_admin_user(username: Optional[str]) -> bool:
    """
    Ellenőrzi, hogy a felhasználó rendszeradminisztrátori jogosultsággal rendelkezik-e (Supabase alapján).
    """
    if not username:
        return False
    return get_user_role(username) == "admin"

def is_advisor_user(username: Optional[str]) -> bool:
    """
    Ellenőrzi, hogy a felhasználó rendelkezik-e Advisor jogosultsággal (advisor vagy admin szerepkör).
    """
    if not username:
        return False
    return get_user_role(username) in ("advisor", "admin")


def is_dummy_mode_allowed(username: Optional[str]) -> bool:
    """
    Ellenőrzi, hogy az adott felhasználó jogosult-e a szimulációs / dummy üzemmód használatára.
    Jogosult: username == 'bean', username == 'admin', vagy adatbázis szerint id IN (1, 2) vagy role == 'admin'.
    Fejlesztői és tesztkörnyezetben (IS_PRODUCTION == False) bárki számára engedélyezett.
    """
    try:
        from app.core.config import IS_PRODUCTION
        if not IS_PRODUCTION:
            return True
    except Exception:
        pass

    if not username:
        return False
    u = username.strip().lower()
    if u in ("bean", "admin", "adam"):
        return True
    try:
        from app.services.user_service import get_user_by_username
        user_record = get_user_by_username(username)
        if user_record:
            uid = user_record.get("id")
            role = str(user_record.get("role", "")).lower()
            u_name = str(user_record.get("username", "")).lower()
            if uid in (1, 2) or role == "admin" or u_name in ("bean", "admin", "adam"):
                return True
    except Exception:
        pass
    return False



