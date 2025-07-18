from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.services.auth import authenticate_user, create_access_token
from app.core.security import get_current_user
from app.models.user import User
from app.models.reg import RegisterRequest
from app.core.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user.dict()

@router.post("/register", status_code=201)
async def register_user(
    data: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    users_collection = db["users"]

    existing_user = await users_collection.find_one(
        {"$or": [{"email": data.email}, {"username": data.username}]}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = pwd_context.hash(data.password)

    result = await users_collection.insert_one(
        {
            "username": data.username,
            "email": data.email,
            "password": hashed_pw,
            "mobile": data.mobile,
            "registration_date": str(datetime.now()),
        }
    )

    return {
        "id": str(result.inserted_id),
        "username": data.username,
        "email": data.email,
        "mobile": data.mobile,
    }
