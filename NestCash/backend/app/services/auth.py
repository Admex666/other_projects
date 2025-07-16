import hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM

async def authenticate_user(username: str, password: str):
    user = await User.find_one({"username": username})
    if not user:
        return None

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user.password != password_hash:
        return None

    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
