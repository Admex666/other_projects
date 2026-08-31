import secrets
from fastapi import Request
from typing import Optional, Dict

# Felhasználók adatbázisa
USERS: Dict[str, str] = {
    "admin": "optivoya2024",
    "demo": "demo123",
    "bean": "bean",
    "wayzio": "demo",
    "utazasmagus": "demo"
}

# Aktív memóriabeli sessionök
sessions: Dict[str, str] = {}

def verify_credentials(username: str, password: str) -> bool:
    return username in USERS and USERS[username] == password

def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return token

def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    return sessions.get(token) if token else None
