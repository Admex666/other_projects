# app/models/notification.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
from enum import Enum

class NotificationType(str, Enum):
    TRANSACTION_ADDED = "transaction_added"
    ACCOUNT_BALANCE_LOW = "account_balance_low"
    MONTHLY_SUMMARY = "monthly_summary"
    BUDGET_EXCEEDED = "budget_exceeded"
    FORUM_LIKE = "forum_like"
    FORUM_COMMENT = "forum_comment"
    FORUM_FOLLOW = "forum_follow"
    SYSTEM_MESSAGE = "system_message"
    KNOWLEDGE_PROGRESS = "knowledge_progress"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationDocument(Document):
    user_id: PydanticObjectId
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    is_read: bool = False
    
    # Kapcsolódó entitások (opcionális)
    related_transaction_id: Optional[PydanticObjectId] = None
    related_forum_post_id: Optional[PydanticObjectId] = None
    related_user_id: Optional[PydanticObjectId] = None
    
    # Metaadatok
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Akció gomb (opcionális)
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    
    class Settings:
        name = "notifications"
        indexes = [
            "user_id",
            "is_read",
            "created_at",
            "type",
            "priority",
            [("user_id", 1), ("is_read", 1), ("created_at", -1)],  # Összetett index
        ]

# Response modellek
class NotificationRead(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    priority: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    
    # Kapcsolódó entitások
    related_transaction_id: Optional[str] = None
    related_forum_post_id: Optional[str] = None
    related_user_id: Optional[str] = None

class NotificationCreate(BaseModel):
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    
    # Kapcsolódó entitások (opcionális)
    related_transaction_id: Optional[str] = None
    related_forum_post_id: Optional[str] = None
    related_user_id: Optional[str] = None
    
    # Metaadatok
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None

class NotificationListResponse(BaseModel):
    notifications: List[NotificationRead]
    total_count: int
    unread_count: int
    skip: int
    limit: int

class NotificationStats(BaseModel):
    total_count: int
    unread_count: int
    priority_counts: dict
    type_counts: dict