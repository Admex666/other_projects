from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from app.services.auth import authenticate_user, create_access_token
from app.core.security import get_current_user
from app.models.user import User
from app.models.reg import RegisterRequest
from app.core.db import init_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "user_id": current_user.user_id
    }

@router.post("/register", status_code=201)
async def register_user(data: RegisterRequest):
    # Ellenőrizd, hogy nincs-e már ilyen email vagy username
    db = init_db()
    users_collection = db["users"]
    existing_user = await users_collection.find_one(
        {"$or": [{"email": data.email}, {"username": data.username}]}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_pw = pwd_context.hash(data.password)

    new_user = {
        "username": data.username,
        "email": data.email,
        "password": hashed_pw,
    }

    result = await users_collection.insert_one(new_user)

    return {
        "id": str(result.inserted_id),
        "username": data.username,
        "email": data.email,
    }