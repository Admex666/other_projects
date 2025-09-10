from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

from app.services.auth_service import authenticate_user, create_access_token, create_refresh_token, verify_refresh_token
from app.core.security import get_current_user
from app.models.user import User, UserDocument
from app.models.reg import RegisterRequest
from app.core.db import get_db
from app.services.health_score_service import HealthScoreService

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    user_model = User(
        id=str(user.id),
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        registration_date=user.registration_date,
        user_type=user.user_type,
        selected_intents=user.selected_intents,
        onboarding_completed=user.onboarding_completed,
        onboarding_step=user.onboarding_step,
        preferred_currency=user.preferred_currency,
    )

    await HealthScoreService.track_session(str(user.id))

    access_token = create_access_token({"sub": str(user_model.id)})
    refresh_token = create_refresh_token({"sub": str(user_model.id)})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "user_id": str(user_model.id), 
        "username": user_model.username
    }

# Refresh token request model
class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh token endpoint
    """
    user_id = verify_refresh_token(request.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Ellenőrizzük, hogy a user még létezik
    try:
        user = await UserDocument.get(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except Exception as e:
        print(f"Error fetching user during token refresh: {e}")
        raise HTTPException(status_code=401, detail="User verification failed")
    
    # Új tokenek generálása
    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.username
    }

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
            # Onboarding mezők hozzáadása
            "user_type": None,
            "selected_intents": [],
            "onboarding_completed": False,
            "onboarding_step": 0,
            "preferred_currency": "HUF",
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

@router.delete("/delete-account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Teljes felhasználói fiók törlése az összes kapcsolódó adattal együtt
    """
    user_obj_id = ObjectId(current_user.id)
    
    try:
        # 1. Felhasználó törlése
        users_result = await db.users.delete_one({"_id": user_obj_id})
        
        # 2. Kapcsolódó adatok törlése
        collections_to_clean = [
            ("transactions", {"user_id": user_obj_id}),
            ("categories", {"user_id": user_obj_id}),
            ("user_progress", {"user_id": user_obj_id}),
            ("forum_posts", {"user_id": user_obj_id}),
            ("forum_comments", {"user_id": user_obj_id}),
            ("forum_likes", {"user_id": user_obj_id}),
            ("forum_follows", {"$or": [{"follower_id": user_obj_id}, {"following_id": user_obj_id}]}),
            ("forum_notifications", {"$or": [{"user_id": user_obj_id}, {"from_user_id": user_obj_id}]}),
            ("forum_user_settings", {"user_id": user_obj_id}),
            ("limits", {"user_id": user_obj_id}),
            ("user_challenges", {"user_id": user_obj_id}),
            ("user_badges", {"user_id": user_obj_id}),
            ("badge_progress", {"user_id": user_obj_id}),
            ("habits", {"user_id": user_obj_id}),
            ("habit_logs", {"user_id": user_obj_id}),
            ("pti_scores", {"user_id": user_obj_id}),
            ("pti_history", {"user_id": user_obj_id}),
            ("user_pti_settings", {"user_id": user_obj_id}),
            ("user_subscriptions", {"user_id": user_obj_id}),
            ("messages", {"$or": [{"sender_id": user_obj_id}, {"receiver_id": user_obj_id}]}),
            ("conversations", {"participants": user_obj_id}),
            ("accountability_profiles", {"user_id": user_obj_id}),
            ("partnerships", {"$or": [{"requester_id": user_obj_id}, {"requested_id": user_obj_id}]}),
            ("checkins", {"user_id": user_obj_id}),
            ("user_health_scores", {"user_id": user_obj_id}),
            ("user_session_tracking", {"user_id": user_obj_id}),
            ("feature_usage_tracking", {"user_id": user_obj_id})
        ]
        
        deleted_counts = {}
        for collection_name, query in collections_to_clean:
            result = await db[collection_name].delete_many(query)
            deleted_counts[collection_name] = result.deleted_count
        
        # 3. Accounts kollekció speciális kezelése (nested user_id alapú törlés)
        accounts_result = await db.accounts.update_many(
            {f"accounts.{current_user.id}": {"$exists": True}},
            {"$unset": {f"accounts.{current_user.id}": ""}}
        )
        deleted_counts["accounts"] = accounts_result.modified_count
        
        if users_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "Account successfully deleted",
            "deleted_user": True,
            "cleaned_collections": deleted_counts,
            "total_records_deleted": sum(deleted_counts.values()) + 1
        }
        
    except Exception as e:
        print(f"Error during account deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
    
# auth.py fájlban
@router.get("/export-data")
async def export_data(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Exportálja a felhasználó összes adatát egy JSON objektumba
    """
    user_obj_id = ObjectId(current_user.id)
    
    try:
        exported_data = {
            "user_profile": await db.users.find_one({"_id": user_obj_id}, {"password": 0}), # A jelszó kihagyása
            "transactions": [doc async for doc in db.transactions.find({"user_id": user_obj_id})],
            "categories": [doc async for doc in db.categories.find({"user_id": user_obj_id})],
            "user_progress": [doc async for doc in db.user_progress.find({"user_id": user_obj_id})],
            "limits": [doc async for doc in db.limits.find({"user_id": user_obj_id})],
            "user_challenges": [doc async for doc in db.user_challenges.find({"user_id": user_obj_id})],
            "user_badges": [doc async for doc in db.user_badges.find({"user_id": user_obj_id})],
            "badge_progress": [doc async for doc in db.badge_progress.find({"user_id": user_obj_id})],
            "habits": [doc async for doc in db.habits.find({"user_id": user_obj_id})],
            "habit_logs": [doc async for doc in db.habit_logs.find({"user_id": user_obj_id})],
            "pti_scores": [doc async for doc in db.pti_scores.find({"user_id": user_obj_id})],
            "pti_history": [doc async for doc in db.pti_history.find({"user_id": user_obj_id})],
            "user_pti_settings": [doc async for doc in db.user_pti_settings.find({"user_id": user_obj_id})],
            "user_subscriptions": [doc async for doc in db.user_subscriptions.find({"user_id": user_obj_id})],
            "accountability_profiles": [doc async for doc in db.accountability_profiles.find({"user_id": user_obj_id})],
            "checkins": [doc async for doc in db.checkins.find({"user_id": user_obj_id})],
            "user_health_scores": [doc async for doc in db.user_health_scores.find({"user_id": user_obj_id})],
            "user_session_tracking": [doc async for doc in db.user_session_tracking.find({"user_id": user_obj_id})],
            "feature_usage_tracking": [doc async for doc in db.feature_usage_tracking.find({"user_id": user_obj_id})],
        }
        
        # A MongoDB ObjectId és a datetime objektumok stringgé alakítása
        def convert_data(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: convert_data(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_data(item) for item in obj]
            return obj
            
        json_friendly_data = convert_data(exported_data)

        # Itt a FastAPI Response osztályát kell használni, hogy fájlt lehessen küldeni
        from fastapi.responses import JSONResponse
        
        # Javasolt, hogy a dátum is a fájlnév része legyen
        filename = f"user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return JSONResponse(
            content=json_friendly_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Error during data export: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")