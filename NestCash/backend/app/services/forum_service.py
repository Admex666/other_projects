# app/services/forum_service.py
from typing import List, Dict, Optional
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
import logging

from app.models.forum_models import (
    ForumPostDocument, FollowDocument, NotificationDocument, UserForumSettingsDocument,
    PrivacyLevel, NotificationType
)

logger = logging.getLogger(__name__)

class ForumService:
    """Forum szolgáltatásokat kezelő osztály"""
    
    async def can_user_see_post(self, user_id: str, post: ForumPostDocument) -> bool:
        """
        Ellenőrzi, hogy a felhasználó láthatja-e a posztot
        """
        try:
            # Saját poszt mindig látható
            if str(post.user_id) == user_id:
                return True
            
            # Publikus posztok mindenkinek láthatók
            if post.privacy_level == PrivacyLevel.PUBLIC:
                return True
            
            # Privát posztok csak a szerzőnek láthatók
            if post.privacy_level == PrivacyLevel.PRIVATE:
                return False
            
            # "Friends" szintű posztok csak követőknek láthatók
            if post.privacy_level == PrivacyLevel.FRIENDS:
                follow_relationship = await FollowDocument.find_one({
                    "follower_id": ObjectId(user_id),
                    "following_id": post.user_id
                })
                return follow_relationship is not None
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking post visibility: {e}")
            return False
    
    async def build_visibility_filter(self, user_id: str) -> Dict:
        """
        Építi a láthatósági szűrőt a posztok lekérdezéséhez
        """
        try:
            # Követett felhasználók ID-jainak lekérése
            following = await FollowDocument.find(
                {"follower_id": ObjectId(user_id)}
            ).to_list()
            following_ids = [follow.following_id for follow in following]
            
            # Láthatósági szűrő összeállítása
            visibility_filter = {
                "$or": [
                    # Publikus posztok
                    {"privacy_level": PrivacyLevel.PUBLIC},
                    # Saját posztok
                    {"user_id": ObjectId(user_id)},
                    # "Friends" szintű posztok követett felhasználóktól
                    {
                        "privacy_level": PrivacyLevel.FRIENDS,
                        "user_id": {"$in": following_ids}
                    }
                ]
            }
            
            return visibility_filter
            
        except Exception as e:
            logger.error(f"Error building visibility filter: {e}")
            return {"privacy_level": PrivacyLevel.PUBLIC}  # Fallback csak publikus
    
    async def create_notification(
        self,
        user_id: str,
        from_user_id: str,
        from_username: str,
        notification_type: NotificationType,
        message: str,
        post_id: Optional[str] = None
    ) -> bool:
        """
        Értesítés létrehozása
        """
        try:
            # Ellenőrizzük, hogy a felhasználó engedélyezi-e ezt az értesítés típust
            settings = await UserForumSettingsDocument.find_one(
                {"user_id": ObjectId(user_id)}
            )
            
            if settings and not settings.notifications_enabled.get(notification_type.value, True):
                return False  # Felhasználó letiltotta ezt az értesítés típust
            
            notification = NotificationDocument(
                user_id=PydanticObjectId(user_id),
                from_user_id=PydanticObjectId(from_user_id),
                from_username=from_username,
                type=notification_type,
                post_id=PydanticObjectId(post_id) if post_id else None,
                message=message
            )
            
            await notification.insert()
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False
    
    async def get_user_forum_settings(self, user_id: str) -> UserForumSettingsDocument:
        """
        Felhasználó fórum beállításainak lekérése, vagy alapértelmezett létrehozása
        """
        try:
            settings = await UserForumSettingsDocument.find_one(
                {"user_id": ObjectId(user_id)}
            )
            
            if not settings:
                # Alapértelmezett beállítások létrehozása
                settings = UserForumSettingsDocument(
                    user_id=PydanticObjectId(user_id)
                )
                await settings.insert()
            
            return settings
            
        except Exception as e:
            logger.error(f"Error getting user forum settings: {e}")
            # Alapértelmezett beállítások visszaadása hiba esetén
            return UserForumSettingsDocument(
                user_id=PydanticObjectId(user_id)
            )
    
    async def update_user_forum_settings(
        self,
        user_id: str,
        default_privacy_level: Optional[PrivacyLevel] = None,
        notifications_enabled: Optional[Dict[str, bool]] = None
    ) -> UserForumSettingsDocument:
        """
        Felhasználó fórum beállításainak frissítése
        """
        try:
            settings = await self.get_user_forum_settings(user_id)
            
            if default_privacy_level is not None:
                settings.default_privacy_level = default_privacy_level
            
            if notifications_enabled is not None:
                settings.notifications_enabled.update(notifications_enabled)
            
            settings.updated_at = datetime.utcnow()
            await settings.save()
            
            return settings
            
        except Exception as e:
            logger.error(f"Error updating user forum settings: {e}")
            raise e
    
    async def get_forum_stats(self, user_id: str) -> Dict:
        """
        Felhasználó fórum statisztikáinak lekérése
        """
        try:
            # Saját posztok száma
            my_posts_count = await ForumPostDocument.find(
                {"user_id": ObjectId(user_id)}
            ).count()
            
            # Kapott like-ok száma (saját posztokra)
            user_posts = await ForumPostDocument.find(
                {"user_id": ObjectId(user_id)}
            ).to_list()
            my_likes_received = sum(post.like_count for post in user_posts)
            
            # Követők száma
            followers_count = await FollowDocument.find(
                {"following_id": ObjectId(user_id)}
            ).count()
            
            # Követettek száma
            following_count = await FollowDocument.find(
                {"follower_id": ObjectId(user_id)}
            ).count()
            
            return {
                "my_posts_count": my_posts_count,
                "my_likes_received": my_likes_received,
                "followers_count": followers_count,
                "following_count": following_count
            }
            
        except Exception as e:
            logger.error(f"Error getting forum stats: {e}")
            return {
                "my_posts_count": 0,
                "my_likes_received": 0,
                "followers_count": 0,
                "following_count": 0
            }