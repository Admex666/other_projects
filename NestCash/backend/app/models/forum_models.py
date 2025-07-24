# app/models/forum_models.py
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
from enum import Enum

class PrivacyLevel(str, Enum):
    PUBLIC = "public"          # Mindenki láthatja
    FRIENDS = "friends"        # Csak követők láthatják
    PRIVATE = "private"        # Csak saját maga láthatja

class PostCategory(str, Enum):
    GENERAL = "general"
    BUDGETING = "budgeting"
    INVESTING = "investing"
    SAVINGS = "savings"
    CAREER = "career"
    EXPENSES = "expenses"
    TIPS = "tips"
    QUESTIONS = "questions"

class FeedType(str, Enum):
    ALL = "all"               # Összes poszt (publikus + követettek)
    FOLLOWING = "following"   # Csak követettek posztjai
    MY_POSTS = "my_posts"     # Csak saját posztok

class SortBy(str, Enum):
    NEWEST = "newest"         # Legújabb először
    POPULAR = "popular"       # Legnépszerűbb (like-ok alapján)
    MOST_COMMENTED = "most_commented"  # Legtöbb komment

class NotificationType(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"

# === FORUM POST DOCUMENT ===
class ForumPostDocument(Document):
    user_id: PydanticObjectId
    username: str  # Denormalizált adat a gyorsabb lekérdezésekért
    title: str
    content: str
    category: PostCategory
    privacy_level: PrivacyLevel = Field(default=PrivacyLevel.PUBLIC)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    like_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    
    class Settings:
        name = "forum_posts"

# === COMMENT DOCUMENT ===
class CommentDocument(Document):
    post_id: PydanticObjectId
    user_id: PydanticObjectId
    username: str  # Denormalizált adat
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forum_comments"

# === LIKE DOCUMENT ===
class LikeDocument(Document):
    post_id: PydanticObjectId
    user_id: PydanticObjectId
    username: str  # Denormalizált adat
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forum_likes"

# === FOLLOW DOCUMENT ===
class FollowDocument(Document):
    follower_id: PydanticObjectId  # Ki követ
    following_id: PydanticObjectId # Kit követ
    follower_username: str
    following_username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forum_follows"

# === NOTIFICATION DOCUMENT ===
class NotificationDocument(Document):
    user_id: PydanticObjectId  # Kinek szól az értesítés
    from_user_id: PydanticObjectId  # Ki váltotta ki
    from_username: str
    type: NotificationType
    post_id: Optional[PydanticObjectId] = None  # Ha poszt-related
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forum_notifications"

# === USER FORUM SETTINGS DOCUMENT ===
class UserForumSettingsDocument(Document):
    user_id: PydanticObjectId
    default_privacy_level: PrivacyLevel = Field(default=PrivacyLevel.PUBLIC)
    notifications_enabled: Dict[str, bool] = Field(default={
        "like": True,
        "comment": True,
        "follow": True
    })
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "forum_user_settings"

# === RESPONSE SCHEMAS ===
class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10, max_length=5000)
    category: PostCategory
    privacy_level: PrivacyLevel = Field(default=PrivacyLevel.PUBLIC)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[PostCategory] = None
    privacy_level: Optional[PrivacyLevel] = None

class PostRead(BaseModel):
    id: str
    user_id: str
    username: str
    title: str
    content: str
    category: PostCategory
    privacy_level: PrivacyLevel
    created_at: datetime
    updated_at: datetime
    like_count: int
    comment_count: int
    is_liked_by_me: bool = Field(default=False)  # Csak válaszban
    is_my_post: bool = Field(default=False)      # Csak válaszban

class PostListResponse(BaseModel):
    posts: List[PostRead]
    total_count: int
    skip: int
    limit: int

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class CommentRead(BaseModel):
    id: str
    post_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_my_comment: bool = Field(default=False)

class CommentListResponse(BaseModel):
    comments: List[CommentRead]
    total_count: int

class UserSearch(BaseModel):
    id: str
    username: str
    is_following: bool = Field(default=False)
    is_followed_by: bool = Field(default=False)

class UserSearchResponse(BaseModel):
    users: List[UserSearch]
    total_count: int

class FollowRead(BaseModel):
    follower_id: str
    following_id: str
    follower_username: str
    following_username: str
    created_at: datetime

class FollowListResponse(BaseModel):
    follows: List[FollowRead]
    total_count: int

class NotificationRead(BaseModel):
    id: str
    from_user_id: str
    from_username: str
    type: NotificationType
    post_id: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    notifications: List[NotificationRead]
    unread_count: int
    total_count: int

class ForumSettingsRead(BaseModel):
    default_privacy_level: PrivacyLevel
    notifications_enabled: Dict[str, bool]

class ForumSettingsUpdate(BaseModel):
    default_privacy_level: Optional[PrivacyLevel] = None
    notifications_enabled: Optional[Dict[str, bool]] = None

class ForumStatsResponse(BaseModel):
    my_posts_count: int
    my_likes_received: int
    followers_count: int
    following_count: int