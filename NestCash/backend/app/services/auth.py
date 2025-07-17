# app/services/auth.py
import hashlib
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def authenticate_user(login: str, password_plain: str):
    """
    login: username VAGY email (ha később bővíted; most username-et keresünk).
    Vegyes hash-készlet támogatása:
      - Új user: bcrypt -> passlib verify()
      - Régi user: SHA-256 hex -> összehasonlítás + MIGRÁCIÓ bcrypt-re
    """
    # Ha emailt is engedsz majd, cseréld erre:
    # user = await User.find_one({"$or": [{"username": login}, {"email": login}]})
    user = await User.find_one({"username": login})
    if not user:
        return None

    stored = user.password or ""

    # Bcrypt eset
    if stored.startswith("$2"):
        try:
            if not pwd_context.verify(password_plain, stored):
                return None
        except Exception:
            return None
        return user

    # SHA-256 fallback (régi adatok)
    sha = hashlib.sha256(password_plain.encode()).hexdigest()
    if sha != stored:
        return None

    # ---- MIGRÁCIÓ: sikeres SHA‑256 hit után bcrypt-re konvertálunk ----
    try:
        new_hash = pwd_context.hash(password_plain)
        user.password = new_hash
        await user.save()   # Beanie Document mentés
        # (opcionális: logger.info(f"Migrated user {user.username} password to bcrypt"))
    except Exception:
        # Ha a mentés nem sikerül, a belépést attól még engedhetjük
        pass

    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
