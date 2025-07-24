# app/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import logging

from app.models.notification import (
    NotificationDocument,
    NotificationRead,
    NotificationCreate,
    NotificationUpdate,
    NotificationListResponse,
    NotificationStats,
    NotificationType,
    NotificationPriority
)
from app.services.notification_service import NotificationService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: Optional[bool] = Query(None, description="Csak olvasatlan értesítések"),
    notification_type: Optional[NotificationType] = Query(None, description="Értesítés típus szerinti szűrés"),
    priority: Optional[NotificationPriority] = Query(None, description="Prioritás szerinti szűrés"),
):
    """
    Felhasználó értesítéseinek listázása
    """
    try:
        # Alapfilter
        query_filter = {"user_id": ObjectId(current_user.id)}
        
        # Olvasatlan szűrés
        if unread_only:
            query_filter["is_read"] = False
        
        # Típus szűrés
        if notification_type:
            query_filter["type"] = notification_type
        
        # Prioritás szűrés
        if priority:
            query_filter["priority"] = priority
        
        # Lejárt értesítések kiszűrése
        now = datetime.utcnow()
        query_filter["$or"] = [
            {"expires_at": {"$gt": now}},
            {"expires_at": None}
        ]
        
        # Összesített számok
        total_count = await NotificationDocument.find(query_filter).count()
        unread_count = await NotificationDocument.find({
            "user_id": ObjectId(current_user.id),
            "is_read": False,
            "$or": [
                {"expires_at": {"$gt": now}},
                {"expires_at": None}
            ]
        }).count()
        
        # Értesítések lekérdezése
        notifications = await NotificationDocument.find(query_filter)\
            .sort(-NotificationDocument.created_at)\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Konvertálás response modellekké
        notification_reads = []
        for notification in notifications:
            notification_reads.append(NotificationRead(
                id=str(notification.id),
                user_id=str(notification.user_id),
                type=notification.type,
                title=notification.title,
                message=notification.message,
                priority=notification.priority,
                is_read=notification.is_read,
                created_at=notification.created_at,
                read_at=notification.read_at,
                expires_at=notification.expires_at,
                action_url=notification.action_url,
                action_text=notification.action_text,
                related_transaction_id=str(notification.related_transaction_id) if notification.related_transaction_id else None,
                related_forum_post_id=str(notification.related_forum_post_id) if notification.related_forum_post_id else None,
                related_user_id=str(notification.related_user_id) if notification.related_user_id else None,
            ))
        
        return NotificationListResponse(
            notifications=notification_reads,
            total_count=total_count,
            unread_count=unread_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list notifications: {e}")

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Értesítési statisztikák lekérése
    """
    try:
        user_id = ObjectId(current_user.id)
        now = datetime.utcnow()
        
        # Aktív értesítések (nem lejártak)
        active_filter = {
            "user_id": user_id,
            "$or": [
                {"expires_at": {"$gt": now}},
                {"expires_at": None}
            ]
        }
        
        total_count = await NotificationDocument.find(active_filter).count()
        unread_count = await NotificationDocument.find({
            **active_filter,
            "is_read": False
        }).count()
        
        # Prioritás szerinti bontás
        priority_counts = {}
        for priority in NotificationPriority:
            count = await NotificationDocument.find({
                **active_filter,
                "priority": priority
            }).count()
            priority_counts[priority.value] = count
        
        # Típus szerinti bontás
        type_counts = {}
        for notification_type in NotificationType:
            count = await NotificationDocument.find({
                **active_filter,
                "type": notification_type
            }).count()
            type_counts[notification_type.value] = count
        
        return NotificationStats(
            total_count=total_count,
            unread_count=unread_count,
            priority_counts=priority_counts,
            type_counts=type_counts
        )
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification stats: {e}")

@router.post("/", response_model=NotificationRead, status_code=201)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Új értesítés létrehozása (admin funkcionalitás vagy rendszer használatra)
    """
    try:
        notification = await NotificationService.create_notification(
            current_user.id,
            notification_data
        )
        
        return NotificationRead(
            id=str(notification.id),
            user_id=str(notification.user_id),
            type=notification.type,
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            expires_at=notification.expires_at,
            action_url=notification.action_url,
            action_text=notification.action_text,
            related_transaction_id=str(notification.related_transaction_id) if notification.related_transaction_id else None,
            related_forum_post_id=str(notification.related_forum_post_id) if notification.related_forum_post_id else None,
            related_user_id=str(notification.related_user_id) if notification.related_user_id else None,
        )
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {e}")

@router.put("/{notification_id}/read", response_model=dict)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Értesítés olvasottnak jelölése
    """
    try:
        success = await NotificationService.mark_as_read(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {e}")

@router.put("/mark-all-read", response_model=dict)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    """
    Összes értesítés olvasottnak jelölése
    """
    try:
        count = await NotificationService.mark_all_as_read(current_user.id)
        
        return {
            "message": f"{count} notification(s) marked as read",
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {e}")

@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Értesítés törlése
    """
    try:
        success = await NotificationService.delete_notification(notification_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {e}")

@router.get("/{notification_id}", response_model=NotificationRead)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Egy konkrét értesítés lekérése
    """
    try:
        from beanie import PydanticObjectId
        notification = await NotificationDocument.get(PydanticObjectId(notification_id))
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Ellenőrizzük, hogy a felhasználó sajátja-e
        if str(notification.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this notification")
        
        return NotificationRead(
            id=str(notification.id),
            user_id=str(notification.user_id),
            type=notification.type,
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            expires_at=notification.expires_at,
            action_url=notification.action_url,
            action_text=notification.action_text,
            related_transaction_id=str(notification.related_transaction_id) if notification.related_transaction_id else None,
            related_forum_post_id=str(notification.related_forum_post_id) if notification.related_forum_post_id else None,
            related_user_id=str(notification.related_user_id) if notification.related_user_id else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification: {e}")

# Segéd endpoint a lejárt értesítések törlésére (cronjob-hoz vagy admin funkcióhoz)
@router.delete("/cleanup/expired", response_model=dict)
async def cleanup_expired_notifications(
    current_user: User = Depends(get_current_user)
):
    """
    Lejárt értesítések törlése (admin funkcionalitás)
    """
    try:
        count = await NotificationService.cleanup_expired_notifications()
        
        return {
            "message": f"{count} expired notification(s) deleted",
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired notifications: {e}")