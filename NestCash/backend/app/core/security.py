# app/core/security.py
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from bson import ObjectId  

from app.models.user import User
from app.core.db import get_db

SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_data = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user_data is None:
        raise credentials_exception

    # MongoDB dokumentum átalakítása Pydantic modellé
    # Make sure to convert ObjectId to string and store it as id (not _id)
    return User(
        id=str(user_data["_id"]),  # Use 'id' instead of '_id'
        username=user_data["username"],
        email=user_data["email"],
        mobile=user_data.get("mobile"),
        registration_date=user_data.get("registration_date"),
    )