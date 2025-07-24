# app/routes/forum_notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId
from bson import ObjectId
import logging

from app.models.forum_models import (
    NotificationDocument, NotificationRead, NotificationListResponse,
    NotificationType
)
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/forum/notifications", tags=["forum-notifications"])
logger = logging.getLogger(__name__)

# === ÉRTESÍTÉSEK LISTÁZÁSA ===
@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: bool = Query(False, description="Csak olvasatlan értesítések")
):
    try:
        # Szűrő összeállítása
        filter_criteria = {"user_id": ObjectId(current_user.id)}
        if unread_only:
            filter_criteria["is_read"] = False
        
        # Értesítések lekérdezése
        total_count = await NotificationDocument.find(filter_criteria).count()
        notifications = await NotificationDocument.find(filter_criteria)\
            .sort("-created_at")\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Olvasatlan értesítések száma
        unread_count = await NotificationDocument.find({
            "user_id": ObjectId(current_user.id),
            "is_read": False
        }).count()
        
        # Válasz összeállítása
        notification_list = []
        for notification in notifications:
            notification_list.append(NotificationRead(
                id=str(notification.id),
                from_user_id=str(notification.from_user_id),
                from_username=notification.from_username,
                type=notification.type,
                post_id=str(notification.post_id) if notification.post_id else None,
                message=notification.message,
                is_read=notification.is_read,
                created_at=notification.created_at
            ))
        
        return NotificationListResponse(
            notifications=notification_list,
            unread_count=unread_count,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notifications")

# === ÉRTESÍTÉS OLVASOTTÁ JELÖLÉSE ===
@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(notification_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    try:
        notification = await NotificationDocument.get(oid)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Csak saját értesítés jelölhető olvasottá
        if str(notification.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this notification")
        
        if not notification.is_read:
            notification.is_read = True
            await notification.save()
        
        return {"message": "Notification marked as read", "is_read": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

# === ÖSSZES ÉRTESÍTÉS OLVASOTTÁ JELÖLÉSE ===
@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user)
):
    try:
        # Összes olvasatlan értesítés frissítése
        result = await NotificationDocument.find({
            "user_id": ObjectId(current_user.id),
            "is_read": False
        }).update({"$set": {"is_read": True}})
        
        return {
            "message": "All notifications marked as read",
            "updated_count": result.modified_count if hasattr(result, 'modified_count') else 0
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")

# === ÉRTESÍTÉS TÖRLÉSE ===
@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(notification_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    try:
        notification = await NotificationDocument.get(oid)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Csak saját értesítés törölhető
        if str(notification.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
        
        await notification.delete()
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

# === ÖSSZES ÉRTESÍTÉS TÖRLÉSE ===
@router.delete("/")
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
    read_only: bool = Query(False, description="Csak az olvasott értesítések törlése")
):
    try:
        # Szűrő összeállítása
        filter_criteria = {"user_id": ObjectId(current_user.id)}
        if read_only:
            filter_criteria["is_read"] = True
        
        # Értesítések törlése
        result = await NotificationDocument.find(filter_criteria).delete()
        
        return {
            "message": f"{'Read' if read_only else 'All'} notifications deleted successfully",
            "deleted_count": result.deleted_count if hasattr(result, 'deleted_count') else 0
        }
        
    except Exception as e:
        logger.error(f"Error deleting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notifications")

# === OLVASATLAN ÉRTESÍTÉSEK SZÁMA ===
@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    try:
        unread_count = await NotificationDocument.find({
            "user_id": ObjectId(current_user.id),
            "is_read": False
        }).count()
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")