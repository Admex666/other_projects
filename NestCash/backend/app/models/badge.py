# app/models/badge.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class BadgeCategory(str, Enum):
    TRANSACTION = "transaction"  # Tranzakció alapú
    SAVINGS = "savings"         # Megtakarítás alapú
    KNOWLEDGE = "knowledge"     # Tudás alapú
    STREAK = "streak"          # Sorozat alapú
    MILESTONE = "milestone"    # Mérföldkő alapú
    SOCIAL = "social"          # Közösségi alapú
    SPECIAL = "special"        # Különleges

class BadgeRarity(str, Enum):
    COMMON = "common"      # Gyakori - 🟢
    UNCOMMON = "uncommon"  # Ritka - 🔵  
    RARE = "rare"          # Nagyon ritka - 🟣
    EPIC = "epic"          # Epikus - 🟠
    LEGENDARY = "legendary" # Legendás - 🟡

class BadgeType(Document):
    """Badge típus definíció - a rendszerben elérhető badge-ek"""
    
    # Alapadatok
    code: str = Field(..., description="Egyedi badge kód", unique=True)
    name: str = Field(..., description="Badge neve")
    description: str = Field(..., description="Badge leírása")
    
    # Vizuális megjelenés
    icon: str = Field(..., description="Badge ikonja (emoji vagy ikon név)")
    color: str = Field(default="#3B82F6", description="Badge színe (hex)")
    image_url: Optional[str] = Field(None, description="Badge képének URL-je")
    
    # Kategorizálás
    category: BadgeCategory = Field(..., description="Badge kategóriája")
    rarity: BadgeRarity = Field(default=BadgeRarity.COMMON, description="Badge ritkasága")
    
    # Feltételek
    condition_type: str = Field(..., description="Feltétel típusa (pl. transaction_count, savings_goal)")
    condition_config: Dict[str, Any] = Field(default_factory=dict, description="Feltétel konfigurációja")
    
    # Badge tulajdonságok
    is_active: bool = Field(default=True, description="Aktív-e a badge")
    is_repeatable: bool = Field(default=False, description="Többször megszerezhető-e")
    points: int = Field(default=10, description="Badge pontértéke")
    
    # Szint rendszer (opcionális)
    has_levels: bool = Field(default=False, description="Van-e szintje")
    max_level: Optional[int] = Field(None, description="Maximum szint")
    
    # Meta
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "badge_types"
        indexes = ["code", "category", "is_active"]

class UserBadge(Document):
    """Felhasználó által megszerzett badge"""
    
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    badge_code: str = Field(..., description="Badge kódja")
    
    # Szerzési információk
    earned_at: datetime = Field(default_factory=datetime.utcnow, description="Mikor szerezte meg")
    level: int = Field(default=1, description="Badge szintje")
    progress: float = Field(default=100.0, description="Haladás %-ban a következő szintig")
    
    # Kontextus információk
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Szerzéskor releváns adatok")
    
    # Meta
    is_favorite: bool = Field(default=False, description="Kedvenc badge-e")
    is_visible: bool = Field(default=True, description="Látható-e a profilban")
    
    class Settings:
        name = "user_badges"
        indexes = [
            "user_id",
            "badge_code", 
            "earned_at",
            [("user_id", 1), ("badge_code", 1)],
            [("user_id", 1), ("earned_at", -1)]
        ]

class BadgeProgress(Document):
    """Felhasználó haladása egy badge megszerzése felé"""
    
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    badge_code: str = Field(..., description="Badge kódja")
    
    # Haladás követés
    current_value: float = Field(default=0.0, description="Jelenlegi érték")
    target_value: float = Field(..., description="Cél érték")
    progress_percentage: float = Field(default=0.0, description="Haladás %-ban")
    
    # Időkövető
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Mikor kezdte")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Utolsó frissítés")
    
    # Extra adatok
    metadata: Dict[str, Any] = Field(default_factory=dict, description="További követési adatok")
    
    class Settings:
        name = "badge_progress"
        indexes = [
            "user_id",
            "badge_code",
            [("user_id", 1), ("badge_code", 1), ("progress_percentage", -1)]
        ]

# Response modellek
class BadgeTypeRead(BaseModel):
    id: str
    code: str
    name: str
    description: str
    icon: str
    color: str
    image_url: Optional[str]
    category: BadgeCategory
    rarity: BadgeRarity
    condition_type: str
    condition_config: Dict[str, Any]
    is_active: bool
    is_repeatable: bool
    points: int
    has_levels: bool
    max_level: Optional[int]

class UserBadgeRead(BaseModel):
    id: str
    user_id: str
    badge_code: str
    earned_at: datetime
    level: int
    progress: float
    context_data: Dict[str, Any]
    is_favorite: bool
    is_visible: bool
    
    # Badge típus adatok (join-elt)
    badge_name: Optional[str] = None
    badge_description: Optional[str] = None
    badge_icon: Optional[str] = None
    badge_color: Optional[str] = None
    badge_category: Optional[BadgeCategory] = None
    badge_rarity: Optional[BadgeRarity] = None
    badge_points: Optional[int] = None

class BadgeProgressRead(BaseModel):
    id: str
    user_id: str
    badge_code: str
    current_value: float
    target_value: float
    progress_percentage: float
    started_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any]
    
    # Badge típus adatok (join-elt)
    badge_name: Optional[str] = None
    badge_description: Optional[str] = None
    badge_icon: Optional[str] = None
    badge_color: Optional[str] = None

class UserBadgeStats(BaseModel):
    total_badges: int
    total_points: int
    badges_by_category: Dict[str, int]
    badges_by_rarity: Dict[str, int]
    recent_badges: List[UserBadgeRead]
    favorite_badges: List[UserBadgeRead]
    in_progress_count: int

class BadgeEarnedEvent(BaseModel):
    """Badge szerzési esemény értesítéshez"""
    user_id: str
    badge_code: str
    badge_name: str
    badge_icon: str
    badge_rarity: BadgeRarity
    points_earned: int
    level: int
    is_new_badge: bool  # Új badge vagy szint növelés