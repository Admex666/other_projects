# app/models/accountability_models.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum

class PartnershipStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DECLINED = "declined"
    ENDED = "ended"
    BLOCKED = "blocked"

class CheckInFrequency(str, Enum):
    DAILY = "daily"
    EVERY_OTHER_DAY = "every_other_day"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"

class MotivationStyle(str, Enum):
    POSITIVE_REINFORCEMENT = "positive_reinforcement"
    CHALLENGE_BASED = "challenge_based"
    STRUCTURED = "structured"
    FLEXIBLE = "flexible"

class PersonalityType(str, Enum):
    COMPETITIVE_DIRECT = "competitive_direct"
    SUPPORTIVE_GENTLE = "supportive_gentle"
    BALANCED = "balanced"

class GoalCategory(str, Enum):
    FINANCIAL = "financial"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    SPENDING_CONTROL = "spending_control"
    HABIT_BUILDING = "habit_building"

# Accountability Profil
class AccountabilityProfile(Document):
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    
    # Célok és preferenciák
    goal_categories: List[GoalCategory] = Field(default_factory=list, description="Érdeklődési területek")
    checkin_frequency: CheckInFrequency = Field(..., description="Preferált check-in gyakoriság")
    motivation_style: MotivationStyle = Field(..., description="Motivációs stílus")
    personality_type: PersonalityType = Field(..., description="Személyiség típus")
    
    # Egyéb beállítások
    timezone: str = Field(default="Europe/Budapest", description="Időzóna")
    availability_hours: Dict[str, List[str]] = Field(default_factory=dict, description="Elérhetőségi idők")
    bio: Optional[str] = Field(None, max_length=500, description="Rövid bemutatkozás")
    
    # Matching beállítások
    max_age_difference: Optional[int] = Field(None, description="Max életkor különbség")
    preferred_experience_level: Optional[str] = Field(None, description="Preferált tapasztalati szint")
    
    # Státusz
    is_active: bool = Field(default=True, description="Aktív-e a profil")
    is_looking_for_partners: bool = Field(default=True, description="Keres-e új partnereket")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "accountability_profiles"
        indexes = [
            "user_id",
            "is_active",
            "is_looking_for_partners",
            "goal_categories"
        ]

# Partner kapcsolat
class Partnership(Document):
    requester_id: PydanticObjectId = Field(..., description="Kérő felhasználó ID")
    requested_id: PydanticObjectId = Field(..., description="Megkért felhasználó ID")
    status: PartnershipStatus = Field(default=PartnershipStatus.PENDING)
    
    # Közös beállítások
    checkin_frequency: CheckInFrequency = Field(..., description="Megegyezett check-in gyakoriság")
    shared_goals: List[str] = Field(default_factory=list, description="Közös célok")
    
    # Időbélyegek
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Statisztikák
    total_checkins: int = Field(default=0)
    successful_checkins: int = Field(default=0)
    
    class Settings:
        name = "partnerships"
        indexes = [
            "requester_id",
            "requested_id",
            "status",
            [("requester_id", 1), ("status", 1)],
            [("requested_id", 1), ("status", 1)]
        ]

# Check-in bejegyzés
class CheckIn(Document):
    partnership_id: PydanticObjectId = Field(..., description="Partnership ID")
    user_id: PydanticObjectId = Field(..., description="Check-in-t végző felhasználó")
    
    # Check-in adatok
    date: str = Field(..., description="Check-in dátuma (YYYY-MM-DD)")
    goals_met: bool = Field(default=False, description="Célok teljesítve")
    progress_rating: int = Field(..., ge=1, le=5, description="Haladás értékelése 1-5")
    notes: Optional[str] = Field(None, max_length=1000, description="Jegyzetek")
    
    # Kapcsolódó adatok
    habit_completions: List[PydanticObjectId] = Field(default_factory=list, description="Teljesített szokások")
    challenge_progress: Optional[Dict] = Field(None, description="Kihívás haladás")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "checkins"
        indexes = [
            "partnership_id",
            "user_id",
            "date",
            [("partnership_id", 1), ("date", -1)]
        ]

# Matching algoritmus számára
class MatchScore(BaseModel):
    target_user_id: str
    score: float
    compatibility_factors: Dict[str, float]
    
class PartnerSuggestion(BaseModel):
    user_id: str
    username: str
    bio: Optional[str]
    goal_categories: List[GoalCategory]
    compatibility_score: float
    common_goals: List[str]
    matching_factors: Dict[str, str]