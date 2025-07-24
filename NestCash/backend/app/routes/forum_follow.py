# app/routes/forum_follow.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from beanie import PydanticObjectId
from bson import ObjectId
import logging

from app.models.forum_models import (
    FollowDocument, UserSearch, UserSearchResponse, FollowRead, FollowListResponse,
    NotificationType
)
from app.models.user import UserDocument
from app.core.security import get_current_user
from app.models.user import User
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum/follow", tags=["forum-follow"])
logger = logging.getLogger(__name__)

# === FELHASZNÁLÓK KERESÉSE ===
@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    current_user: User = Depends(get_current_user),
    q: str = Query(..., min_length=2, description="Keresési kifejezés"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    try:
        # Keresés username és email alapján
        search_filter = {
            "$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ],
            "_id": {"$ne": ObjectId(current_user.id)}  # Saját magat ne jelenítse meg
        }
        
        # Felhasználók lekérdezése
        total_count = await UserDocument.find(search_filter).count()
        users = await UserDocument.find(search_filter)\
            .sort("username")\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Követési állapotok ellenőrzése
        user_ids = [user.id for user in users]
        
        # Kik azok, akiket követünk
        following = await FollowDocument.find({
            "follower_id": ObjectId(current_user.id),
            "following_id": {"$in": user_ids}
        }).to_list()
        following_ids = {follow.following_id for follow in following}
        
        # Kik azok, akik minket követnek
        followers = await FollowDocument.find({
            "following_id": ObjectId(current_user.id),
            "follower_id": {"$in": user_ids}
        }).to_list()
        follower_ids = {follow.follower_id for follow in followers}
        
        # Válasz összeállítása
        user_results = []
        for user in users:
            user_results.append(UserSearch(
                id=str(user.id),
                username=user.username,
                is_following=user.id in following_ids,
                is_followed_by=user.id in follower_ids
            ))
        
        return UserSearchResponse(
            users=user_results,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to search users")

# === FELHASZNÁLÓ KÖVETÉSE ===
@router.post("/users/{user_id}")
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        target_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    try:
        # Cél felhasználó létezésének ellenőrzése
        target_user = await UserDocument.get(target_oid)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ellenőrizzük, hogy már követjük-e
        existing_follow = await FollowDocument.find_one({
            "follower_id": ObjectId(current_user.id),
            "following_id": target_oid
        })
        
        if existing_follow:
            raise HTTPException(status_code=400, detail="Already following this user")
        
        # Követés létrehozása
        new_follow = FollowDocument(
            follower_id=PydanticObjectId(current_user.id),
            following_id=target_oid,
            follower_username=current_user.username,
            following_username=target_user.username
        )
        await new_follow.insert()
        
        # Értesítés küldése
        forum_service = ForumService()
        await forum_service.create_notification(
            user_id=user_id,
            from_user_id=current_user.id,
            from_username=current_user.username,
            notification_type=NotificationType.FOLLOW,
            message=f"{current_user.username} started following you"
        )
        
        return {
            "message": "User followed successfully",
            "is_following": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to follow user")

# === FELHASZNÁLÓ KÖVETÉSÉNEK MEGSZÜNTETÉSE ===
@router.delete("/users/{user_id}")
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        target_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    try:
        # Követési kapcsolat keresése
        follow_relationship = await FollowDocument.find_one({
            "follower_id": ObjectId(current_user.id),
            "following_id": target_oid
        })
        
        if not follow_relationship:
            raise HTTPException(status_code=400, detail="Not following this user")
        
        # Követés törlése
        await follow_relationship.delete()
        
        return {
            "message": "User unfollowed successfully",
            "is_following": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfollow user")

# === KÖVETETTEK LISTÁJA ===
@router.get("/following", response_model=FollowListResponse)
async def list_following(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
):
    try:
        # Követettek lekérdezése
        total_count = await FollowDocument.find(
            {"follower_id": ObjectId(current_user.id)}
        ).count()
        
        following = await FollowDocument.find(
            {"follower_id": ObjectId(current_user.id)}
        ).sort("-created_at").skip(skip).limit(limit).to_list()
        
        # Válasz összeállítása
        follow_list = []
        for follow in following:
            follow_list.append(FollowRead(
                follower_id=str(follow.follower_id),
                following_id=str(follow.following_id),
                follower_username=follow.follower_username,
                following_username=follow.following_username,
                created_at=follow.created_at
            ))
        
        return FollowListResponse(
            follows=follow_list,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing following: {e}")
        raise HTTPException(status_code=500, detail="Failed to list following")

# === KÖVETŐK LISTÁJA ===
@router.get("/followers", response_model=FollowListResponse)
async def list_followers(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
):
    try:
        # Követők lekérdezése
        total_count = await FollowDocument.find(
            {"following_id": ObjectId(current_user.id)}
        ).count()
        
        followers = await FollowDocument.find(
            {"following_id": ObjectId(current_user.id)}
        ).sort("-created_at").skip(skip).limit(limit).to_list()
        
        # Válasz összeállítása
        follow_list = []
        for follow in followers:
            follow_list.append(FollowRead(
                follower_id=str(follow.follower_id),
                following_id=str(follow.following_id),
                follower_username=follow.follower_username,
                following_username=follow.following_username,
                created_at=follow.created_at
            ))
        
        return FollowListResponse(
            follows=follow_list,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing followers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list followers")