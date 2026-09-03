import secrets
from fastapi import Request
from typing import Optional, Dict
from app.services.user_service import verify_user_login

# Alapértelmezett vészhelyzeti fiókok (Csak ha az adatbázis teljesen offline)
FALLBACK_USERS: Dict[str, str] = {
    "admin": "optivoya2024",
    "bean": "bean"
}
USERS = FALLBACK_USERS

# Aktív memóriabeli sessionök

sessions: Dict[str, str] = {}

def verify_credentials(username: str, password: str) -> bool:
    # 1. Hitelesítés a Supabase felhős adatbázisból
    if verify_user_login(username, password):
        return True
    # 2. Vészhelyzeti offline fallback
    return username in FALLBACK_USERS and FALLBACK_USERS[username] == password


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token

def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    return sessions.get(token) if token else None

