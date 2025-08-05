# app/routes/sharing.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from beanie import PydanticObjectId
from typing import Optional
import logging

from app.routes.auth import get_current_user
from app.models.user import UserDocument
from app.services.sharing_service import SharingService

# Logger beállítása
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sharing", tags=["sharing"])

class ShareAchievementRequest(BaseModel):
    achievement_type: str  # "badge", "lesson", "challenge"
    achievement_id: str

class ShareAchievementResponse(BaseModel):
    success: bool
    message: str
    forum_post_id: Optional[str] = None

@router.post("/share", response_model=ShareAchievementResponse)
async def share_achievement(
    request: ShareAchievementRequest,
    current_user: UserDocument = Depends(get_current_user)
):
    """Teljesítmény megosztása a fórumra"""
    
    logger.info(f"Share request - User: {current_user.id}, Type: {request.achievement_type}, ID: {request.achievement_id}")
    
    try:
        forum_post_id = None
        
        # JAVÍTÁS: PydanticObjectId konverzió itt is
        user_oid = PydanticObjectId(current_user.id)
        
        if request.achievement_type == "badge":
            logger.info(f"Attempting to share badge: {request.achievement_id}")
            forum_post_id = await SharingService.share_badge_achievement(
                user_oid, request.achievement_id  # String ID-t adunk át
            )
            logger.info(f"Badge share result - forum_post_id: {forum_post_id}")
            
        elif request.achievement_type == "lesson":
            logger.info(f"Attempting to share lesson: {request.achievement_id}")
            forum_post_id = await SharingService.share_lesson_completion(
                user_oid, request.achievement_id  # String ID-t adunk át
            )
            logger.info(f"Lesson share result - forum_post_id: {forum_post_id}")
            
        else:
            logger.warning(f"Unsupported achievement type: {request.achievement_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nem támogatott teljesítmény típus"
            )
        
        if forum_post_id is None:
            logger.warning(f"Forum post ID is None - achievement may already be shared or not found")
            return ShareAchievementResponse(
                success=False,
                message="A teljesítmény már meg lett osztva vagy nem található"
            )
        
        logger.info(f"Successfully shared achievement - forum_post_id: {forum_post_id}")
        return ShareAchievementResponse(
            success=True,
            message="Teljesítmény sikeresen megosztva!",
            forum_post_id=forum_post_id
        )
        
    except Exception as e:
        logger.error(f"Error sharing achievement: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hiba történt a megosztás során: {str(e)}"
        )

@router.get("/can-share/{achievement_type}/{achievement_id}")
async def can_share_achievement(
    achievement_type: str,
    achievement_id: str,
    current_user: UserDocument = Depends(get_current_user)
):
    """Ellenőrzi, hogy megosztható-e a teljesítmény"""
    
    logger.info(f"Can share check - User: {current_user.id}, Type: {achievement_type}, ID: {achievement_id}")
    
    can_share = await SharingService.can_share_achievement(
        current_user.id, achievement_type, PydanticObjectId(achievement_id)
    )
    
    logger.info(f"Can share result: {can_share}")
    return {"can_share": can_share}

