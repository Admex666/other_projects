# app/models/challenge.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChallengeType(str, Enum):
    SAVINGS = "savings"  # Megtakarítás
    EXPENSE_REDUCTION = "expense_reduction"  # Kiadás csökkentés
    HABIT_STREAK = "habit_streak"  # Szokás streak
    BUDGET_CONTROL = "budget_control"  # Költségvetés betartás
    INVESTMENT = "investment"  # Befektetés
    INCOME_BOOST = "income_boost"  # Bevétel növelés

class ChallengeDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class ChallengeStatus(str, Enum):
    DRAFT = "draft"  # Tervezet
    ACTIVE = "active"  # Aktív
    COMPLETED = "completed"  # Befejezett
    CANCELLED = "cancelled"  # Megszakított

class ParticipationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

class ChallengeReward(BaseModel):
    points: int = Field(default=0, description="Pontok száma")
    badges: List[str] = Field(default_factory=list, description="Kitűzők listája")
    title: Optional[str] = Field(None, description="Különleges cím")

class ChallengeRule(BaseModel):
    type: str = Field(..., description="Szabály típusa (pl. 'min_amount', 'max_transactions')")
    value: float = Field(..., description="Szabály értéke")
    description: str = Field(..., description="Szabály leírása")

class ChallengeProgress(BaseModel):
    current_value: float = Field(default=0.0, description="Jelenlegi érték")
    target_value: float = Field(..., description="Cél érték")
    unit: str = Field(default="HUF", description="Mértékegység")
    percentage: float = Field(default=0.0, description="Százalékos teljesítmény")

# === CHALLENGE DOCUMENT ===
class ChallengeDocument(Document):
    title: str = Field(..., description="Kihívás címe")
    description: str = Field(..., description="Részletes leírás")
    short_description: Optional[str] = Field(None, description="Rövid leírás")
    
    # Alapvető tulajdonságok
    challenge_type: ChallengeType = Field(..., description="Kihívás típusa")
    difficulty: ChallengeDifficulty = Field(..., description="Nehézségi szint")
    duration_days: int = Field(..., description="Időtartam napokban", ge=1)
    
    # Célok és szabályok
    target_amount: Optional[float] = Field(None, description="Cél összeg (HUF)")
    rules: List[ChallengeRule] = Field(default_factory=list, description="Kihívás szabályai")
    
    # Jutalmak
    rewards: ChallengeReward = Field(default_factory=ChallengeReward, description="Jutalmak")
    
    # Metaadatok
    creator_id: Optional[PydanticObjectId] = Field(None, description="Létrehozó user ID (None = rendszer)")
    creator_username: Optional[str] = Field(None, description="Létrehozó felhasználónév")
    
    # Státusz és időbélyegek
    status: ChallengeStatus = Field(default=ChallengeStatus.ACTIVE, description="Kihívás státusza")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Statisztikák
    participant_count: int = Field(default=0, description="Résztvevők száma")
    completion_rate: float = Field(default=0.0, description="Befejezési arány (%)")
    
    # Kép és kategorízálás
    image_url: Optional[str] = Field(None, description="Kihívás képe")
    tags: List[str] = Field(default_factory=list, description="Címkék")
    
    # Haladási tracking beállítások
    track_categories: List[str] = Field(default_factory=list, description="Nyomon követendő kategóriák")
    track_accounts: List[str] = Field(default_factory=list, description="Nyomon követendő számlák")
    
    class Settings:
        name = "challenges"
        indexes = [
            "challenge_type",
            "difficulty", 
            "status",
            "created_at",
            "participant_count",
            [("challenge_type", 1), ("difficulty", 1)],
            [("status", 1), ("created_at", -1)]
        ]

# === USER CHALLENGE PARTICIPATION ===
class UserChallengeDocument(Document):
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    username: str = Field(..., description="Felhasználónév")
    challenge_id: PydanticObjectId = Field(..., description="Kihívás ID")
    
    # Státuszok
    status: ParticipationStatus = Field(default=ParticipationStatus.ACTIVE)
    
    # Időbélyegek
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="Tényleges kezdés ideje")
    completed_at: Optional[datetime] = Field(None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Haladás követés
    progress: ChallengeProgress = Field(..., description="Haladás adatok")
    daily_progress: Dict[str, float] = Field(default_factory=dict, description="Napi haladás {YYYY-MM-DD: érték}")
    
    # Személyes célok és beállítások
    personal_target: Optional[float] = Field(None, description="Személyre szabott cél")
    notes: Optional[str] = Field(None, description="Személyes jegyzet")
    
    # Jutalmazás
    earned_points: int = Field(default=0, description="Szerzett pontok")
    earned_badges: List[str] = Field(default_factory=list, description="Szerzett kitűzők")
    
    # Statisztikák
    best_streak: int = Field(default=0, description="Legjobb sorozat (napokban)")
    current_streak: int = Field(default=0, description="Jelenlegi sorozat")
    
    class Settings:
        name = "user_challenges"
        indexes = [
            "user_id",
            "challenge_id",
            "status",
            "joined_at",
            [("user_id", 1), ("status", 1)],
            [("challenge_id", 1), ("status", 1)],
            [("user_id", 1), ("challenge_id", 1)]  # Unique constraint
        ]

# === PYDANTIC SCHEMAS ===

# Challenge schemas
class ChallengeCreate(BaseModel):
    title: str
    description: str
    short_description: Optional[str] = None
    challenge_type: ChallengeType
    difficulty: ChallengeDifficulty
    duration_days: int = Field(..., ge=1, le=365)
    target_amount: Optional[float] = None
    rules: List[ChallengeRule] = Field(default_factory=list)
    rewards: ChallengeReward = Field(default_factory=ChallengeReward)
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    track_categories: List[str] = Field(default_factory=list)
    track_accounts: List[str] = Field(default_factory=list)

class ChallengeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    status: Optional[ChallengeStatus] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class ChallengeRead(BaseModel):
    id: str
    title: str
    description: str
    short_description: Optional[str] = None
    challenge_type: ChallengeType
    difficulty: ChallengeDifficulty
    duration_days: int
    target_amount: Optional[float] = None
    rules: List[ChallengeRule]
    rewards: ChallengeReward
    status: ChallengeStatus
    created_at: datetime
    updated_at: datetime
    participant_count: int
    completion_rate: float
    image_url: Optional[str] = None
    tags: List[str]
    creator_username: Optional[str] = None
    
    # Felhasználó-specifikus mezők (csak ha be van jelentkezve a kihívásba)
    is_participating: bool = False
    my_progress: Optional[ChallengeProgress] = None
    my_status: Optional[ParticipationStatus] = None

class ChallengeListResponse(BaseModel):
    challenges: List[ChallengeRead]
    total_count: int
    skip: int
    limit: int

# User Challenge schemas
class UserChallengeJoin(BaseModel):
    personal_target: Optional[float] = None
    notes: Optional[str] = None

class UserChallengeUpdate(BaseModel):
    personal_target: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[ParticipationStatus] = None

class UserChallengeRead(BaseModel):
    id: str
    user_id: str
    username: str
    challenge_id: str
    status: ParticipationStatus
    joined_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    progress: ChallengeProgress
    personal_target: Optional[float] = None
    notes: Optional[str] = None
    earned_points: int
    earned_badges: List[str]
    best_streak: int
    current_streak: int
    
    # Challenge info
    challenge_title: str
    challenge_type: ChallengeType
    challenge_difficulty: ChallengeDifficulty

class UserChallengeListResponse(BaseModel):
    user_challenges: List[UserChallengeRead]
    total_count: int
    skip: int
    limit: int