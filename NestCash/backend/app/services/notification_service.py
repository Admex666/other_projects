# app/services/notification_service.py
from typing import List, Optional
from datetime import datetime, timedelta
from beanie import PydanticObjectId
from bson import ObjectId

from app.models.notification import (
    NotificationDocument, 
    NotificationType, 
    NotificationPriority,
    NotificationCreate
)

class NotificationService:
    
    @staticmethod
    async def create_notification(
        user_id: str,
        notification: NotificationCreate
    ) -> NotificationDocument:
        """Új értesítés létrehozása"""
        
        new_notification = NotificationDocument(
            user_id=PydanticObjectId(user_id),
            type=notification.type,
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            related_transaction_id=PydanticObjectId(notification.related_transaction_id) if notification.related_transaction_id else None,
            related_forum_post_id=PydanticObjectId(notification.related_forum_post_id) if notification.related_forum_post_id else None,
            related_user_id=PydanticObjectId(notification.related_user_id) if notification.related_user_id else None,
            expires_at=notification.expires_at,
            action_url=notification.action_url,
            action_text=notification.action_text
        )
        
        await new_notification.insert()
        return new_notification
    
    @staticmethod
    async def create_transaction_notification(
        user_id: str,
        transaction_id: str,
        amount: float,
        account_name: str,
        transaction_type: str
    ) -> NotificationDocument:
        """Tranzakció értesítés létrehozása"""
        
        if transaction_type == "income":
            title = "Új bevétel rögzítve"
            message = f"+{amount:,.0f} HUF érkezett a(z) {account_name} számlára"
            priority = NotificationPriority.MEDIUM
        else:
            title = "Új kiadás rögzítve"
            message = f"-{abs(amount):,.0f} HUF levonva a(z) {account_name} számláról"
            priority = NotificationPriority.MEDIUM
        
        notification = NotificationCreate(
            type=NotificationType.TRANSACTION_ADDED,
            title=title,
            message=message,
            priority=priority,
            related_transaction_id=transaction_id,
            action_url=f"/transactions/{transaction_id}",
            action_text="Részletek megtekintése"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_low_balance_notification(
        user_id: str,
        account_name: str,
        current_balance: float,
        threshold: float = 10000
    ) -> NotificationDocument:
        """Alacsony egyenleg értesítés"""
        
        notification = NotificationCreate(
            type=NotificationType.ACCOUNT_BALANCE_LOW,
            title="Alacsony egyenleg figyelmeztetés",
            message=f"A(z) {account_name} számla egyenlege {current_balance:,.0f} HUF alá csökkent",
            priority=NotificationPriority.HIGH,
            action_url="/accounts",
            action_text="Számlák megtekintése"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_monthly_summary_notification(
        user_id: str,
        month: str,
        total_income: float,
        total_expense: float,
        net_balance: float
    ) -> NotificationDocument:
        """Havi összesítő értesítés"""
        
        notification = NotificationCreate(
            type=NotificationType.MONTHLY_SUMMARY,
            title=f"Havi összesítő - {month}",
            message=f"Bevétel: +{total_income:,.0f} HUF, Kiadás: {total_expense:,.0f} HUF, Egyenleg: {net_balance:,.0f} HUF",
            priority=NotificationPriority.LOW,
            expires_at=datetime.utcnow() + timedelta(days=30),
            action_url="/analysis",
            action_text="Részletes elemzés"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_forum_like_notification(
        user_id: str,
        liker_username: str,
        post_id: str,
        post_title: str
    ) -> NotificationDocument:
        """Fórum like értesítés"""
        
        notification = NotificationCreate(
            type=NotificationType.FORUM_LIKE,
            title="Új kedvelés",
            message=f"{liker_username} kedvelte a '{post_title}' bejegyzésed",
            priority=NotificationPriority.LOW,
            related_forum_post_id=post_id,
            action_url=f"/forum/posts/{post_id}",
            action_text="Bejegyzés megtekintése"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_forum_comment_notification(
        user_id: str,
        commenter_username: str,
        post_id: str,
        post_title: str
    ) -> NotificationDocument:
        """Fórum komment értesítés"""
        
        notification = NotificationCreate(
            type=NotificationType.FORUM_COMMENT,
            title="Új komment",
            message=f"{commenter_username} kommentelt a '{post_title}' bejegyzésed alatt",
            priority=NotificationPriority.MEDIUM,
            related_forum_post_id=post_id,
            action_url=f"/forum/posts/{post_id}",
            action_text="Komment megtekintése"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_forum_follow_notification(
        user_id: str,
        follower_username: str,
        follower_id: str
    ) -> NotificationDocument:
        """Fórum követés értesítés"""
        
        notification = NotificationCreate(
            type=NotificationType.FORUM_FOLLOW,
            title="Új követő",
            message=f"{follower_username} követni kezdett téged",
            priority=NotificationPriority.LOW,
            related_user_id=follower_id,
            action_url=f"/forum/users/{follower_id}",
            action_text="Profil megtekintése"
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def create_system_notification(
        user_id: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> NotificationDocument:
        """Rendszer értesítés létrehozása"""
        
        notification = NotificationCreate(
            type=NotificationType.SYSTEM_MESSAGE,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            action_text=action_text
        )
        
        return await NotificationService.create_notification(user_id, notification)
    
    @staticmethod
    async def mark_as_read(
        notification_id: str,
        user_id: str
    ) -> bool:
        """Értesítés olvasottnak jelölése"""
        
        notification = await NotificationDocument.get(PydanticObjectId(notification_id))
        
        if not notification or str(notification.user_id) != user_id:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await notification.save()
        
        return True
    
    @staticmethod
    async def mark_all_as_read(user_id: str) -> int:
        """Összes értesítés olvasottnak jelölése"""
        
        unread_notifications = await NotificationDocument.find(
            {
                "user_id": ObjectId(user_id),
                "is_read": False
            }
        ).to_list()
        
        count = 0
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await notification.save()
            count += 1
        
        return count
    
    @staticmethod
    async def delete_notification(
        notification_id: str,
        user_id: str
    ) -> bool:
        """Értesítés törlése"""
        
        notification = await NotificationDocument.get(PydanticObjectId(notification_id))
        
        if not notification or str(notification.user_id) != user_id:
            return False
        
        await notification.delete()
        return True
    
    @staticmethod
    async def cleanup_expired_notifications():
        """Lejárt értesítések törlése"""
        
        now = datetime.utcnow()
        expired_notifications = await NotificationDocument.find(
            {
                "expires_at": {"$lte": now}
            }
        ).to_list()
        
        count = 0
        for notification in expired_notifications:
            await notification.delete()
            count += 1
        
        return count