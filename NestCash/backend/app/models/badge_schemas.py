# app/models/badge_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.badge import BadgeCategory, BadgeRarity, UserBadgeRead, BadgeProgressRead

# Request modellek
class BadgeTypeCreate(BaseModel):
    code: str = Field(..., description="Egyedi badge kód")
    name: str = Field(..., description="Badge neve")
    description: str = Field(..., description="Badge leírása")
    icon: str = Field(..., description="Badge ikonja")
    color: str = Field(default="#3B82F6", description="Badge színe")
    image_url: Optional[str] = Field(None, description="Badge képének URL-je")
    category: BadgeCategory = Field(..., description="Badge kategóriája")
    rarity: BadgeRarity = Field(default=BadgeRarity.COMMON, description="Badge ritkasága")
    condition_type: str = Field(..., description="Feltétel típusa")
    condition_config: Dict[str, Any] = Field(default_factory=dict, description="Feltétel konfigurációja")
    is_repeatable: bool = Field(default=False, description="Többször megszerezhető-e")
    points: int = Field(default=10, description="Badge pontértéke")
    has_levels: bool = Field(default=False, description="Van-e szintje")
    max_level: Optional[int] = Field(None, description="Maximum szint")

class BadgeTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[BadgeCategory] = None
    rarity: Optional[BadgeRarity] = None
    condition_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_repeatable: Optional[bool] = None
    points: Optional[int] = None
    has_levels: Optional[bool] = None
    max_level: Optional[int] = None

class UserBadgeUpdate(BaseModel):
    is_favorite: Optional[bool] = None
    is_visible: Optional[bool] = None

# Response modellek
class BadgeListResponse(BaseModel):
    badges: List[UserBadgeRead]
    total_count: int
    total_points: int

class BadgeProgressListResponse(BaseModel):
    progress_list: List[BadgeProgressRead]
    total_count: int
    completion_rate: float  # Általános teljesítési arány

class BadgeCategoryStats(BaseModel):
    category: BadgeCategory
    total_badges: int
    earned_badges: int
    total_points: int
    earned_points: int
    completion_rate: float

class BadgeLeaderboard(BaseModel):
    rank: int
    user_id: str
    username: str
    total_badges: int
    total_points: int
    recent_badge: Optional[UserBadgeRead] = None

class BadgeLeaderboardResponse(BaseModel):
    leaderboard: List[BadgeLeaderboard]
    user_rank: Optional[int] = None
    total_users: int

# Specifikus badge feltétel konfigurációk példák
class TransactionCountBadgeConfig(BaseModel):
    """Tranzakció szám alapú badge konfiguráció"""
    target_count: int
    transaction_type: Optional[str] = None  # income, expense, transfer
    category: Optional[str] = None
    time_period_days: Optional[int] = None  # Ha időkorlát van

class SavingsGoalBadgeConfig(BaseModel):
    """Megtakarítási cél alapú badge konfiguráció"""
    target_amount: float
    account_type: Optional[str] = None  # megtakaritas, befektetes
    currency: str = "HUF"

class StreakBadgeConfig(BaseModel):
    """Sorozat alapú badge konfiguráció"""
    target_streak: int
    activity_type: str  # daily_transaction, knowledge_lesson, etc.

class KnowledgeBadgeConfig(BaseModel):
    """Tudás alapú badge konfiguráció"""
    target_lessons: Optional[int] = None
    target_categories: Optional[int] = None
    min_quiz_score: Optional[int] = None
    difficulty_level: Optional[str] = None

class MilestoneBadgeConfig(BaseModel):
    """Mérföldkő alapú badge konfiguráció"""
    milestone_type: str  # registration_days, total_transactions, etc.
    target_value: float
    
class SocialBadgeConfig(BaseModel):
    """Közösségi alapú badge konfiguráció"""
    target_posts: Optional[int] = None
    target_likes: Optional[int] = None
    target_followers: Optional[int] = None
    target_comments: Optional[int] = None