from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId

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
    
    user_model = User(
        id=str(user.id), # A Beanie documentumok _id attribútum neve id
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        registration_date=user.registration_date,
    )

    token = create_access_token({"sub": str(user_model.id)})
    return {"access_token": token, "token_type": "bearer", "user_id": str(user_model.id), "username": user_model.username,}

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

@router.put("/update-profile")
async def update_profile(
    data: dict,  # Egyszerű dict a frissítendő mezőkhöz
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    users_collection = db["users"]
    
    # Átalakítjuk a current_user.id-t ObjectId típussá a MongoDB lekérdezésekhez.
    # A security.py-ban a User modell stringként tárolja az id-t,
    # de a MongoDB-ben az _id ObjectId típusú.
    current_user_obj_id = ObjectId(current_user.id) # Ez az új sor!
    
    # Frissítendő mezők előkészítése
    update_data = {}
    
    if "username" in data and data["username"]:
        # Ellenőrizd, hogy nem foglalt-e már a username, KIVÉVE a jelenlegi felhasználót.
        existing_user = await users_collection.find_one(
            {"username": data["username"], "_id": {"$ne": current_user_obj_id}} # Itt használjuk az ObjectId-t
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_data["username"] = data["username"]
    
    if "email" in data and data["email"]:
        # Ellenőrizd, hogy nem foglalt-e már az email, KIVÉVE a jelenlegi felhasználót.
        existing_user = await users_collection.find_one(
            {"email": data["email"], "_id": {"$ne": current_user_obj_id}} # Itt használjuk az ObjectId-t
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data["email"] = data["email"]
    
    if "mobile" in data:
        update_data["mobile"] = data["mobile"]
    
    if "password" in data and data["password"]:
        # Jelszó hash-elése
        hashed_pw = pwd_context.hash(data["password"])
        update_data["password"] = hashed_pw
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # Frissítés a MongoDB-ben
    result = await users_collection.update_one(
        {"_id": current_user_obj_id}, # Itt is az ObjectId-t használjuk
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Profile updated successfully", "updated_fields": list(update_data.keys())}