# app/routes/forum_settings.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.models.forum_models import (
    ForumSettingsRead, ForumSettingsUpdate, ForumStatsResponse,
    PrivacyLevel
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum/settings", tags=["forum-settings"])
logger = logging.getLogger(__name__)

# === FÓRUM BEÁLLÍTÁSOK LEKÉRÉSE ===
@router.get("/", response_model=ForumSettingsRead)
async def get_forum_settings(
    current_user: User = Depends(get_current_user)
):
    try:
        forum_service = ForumService()
        settings = await forum_service.get_user_forum_settings(current_user.id)
        
        return ForumSettingsRead(
            default_privacy_level=settings.default_privacy_level,
            notifications_enabled=settings.notifications_enabled
        )
        
    except Exception as e:
        logger.error(f"Error getting forum settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get forum settings")

# === FÓRUM BEÁLLÍTÁSOK FRISSÍTÉSE ===
@router.put("/", response_model=ForumSettingsRead)
async def update_forum_settings(
    settings_data: ForumSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        forum_service = ForumService()
        
        # Beállítások frissítése
        updated_settings = await forum_service.update_user_forum_settings(
            user_id=current_user.id,
            default_privacy_level=settings_data.default_privacy_level,
            notifications_enabled=settings_data.notifications_enabled
        )
        
        return ForumSettingsRead(
            default_privacy_level=updated_settings.default_privacy_level,
            notifications_enabled=updated_settings.notifications_enabled
        )
        
    except Exception as e:
        logger.error(f"Error updating forum settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update forum settings")

# === FÓRUM STATISZTIKÁK ===
@router.get("/stats", response_model=ForumStatsResponse)
async def get_forum_stats(
    current_user: User = Depends(get_current_user)
):
    try:
        forum_service = ForumService()
        stats = await forum_service.get_forum_stats(current_user.id)
        
        return ForumStatsResponse(
            my_posts_count=stats["my_posts_count"],
            my_likes_received=stats["my_likes_received"],
            followers_count=stats["followers_count"],
            following_count=stats["following_count"]
        )
        
    except Exception as e:
        logger.error(f"Error getting forum stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get forum stats")

# === ALAPÉRTELMEZETT ADATVÉDELMI SZINT FRISSÍTÉSE ===
@router.put("/privacy-level")
async def update_default_privacy_level(
    privacy_level: PrivacyLevel,
    current_user: User = Depends(get_current_user)
):
    try:
        forum_service = ForumService()
        
        updated_settings = await forum_service.update_user_forum_settings(
            user_id=current_user.id,
            default_privacy_level=privacy_level
        )
        
        return {
            "message": "Default privacy level updated successfully",
            "privacy_level": updated_settings.default_privacy_level
        }
        
    except Exception as e:
        logger.error(f"Error updating privacy level: {e}")
        raise HTTPException(status_code=500, detail="Failed to update privacy level")

# === ÉRTESÍTÉSI BEÁLLÍTÁSOK FRISSÍTÉSE ===
@router.put("/notifications")
async def update_notification_settings(
    notifications_enabled: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        # Érvényes kulcsok ellenőrzése
        valid_keys = {"like", "comment", "follow"}
        if not all(key in valid_keys for key in notifications_enabled.keys()):
            raise HTTPException(status_code=400, detail="Invalid notification settings keys")
        
        forum_service = ForumService()
        
        updated_settings = await forum_service.update_user_forum_settings(
            user_id=current_user.id,
            notifications_enabled=notifications_enabled
        )
        
        return {
            "message": "Notification settings updated successfully",
            "notifications_enabled": updated_settings.notifications_enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification settings")