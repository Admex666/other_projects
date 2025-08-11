# app/models/accountability_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from .accountability_models import (
    PartnershipStatus, CheckInFrequency, MotivationStyle, 
    PersonalityType, GoalCategory
)

# Profile schemas
class AccountabilityProfileCreate(BaseModel):
    goal_categories: List[GoalCategory]
    checkin_frequency: CheckInFrequency
    motivation_style: MotivationStyle
    personality_type: PersonalityType
    timezone: str = "Europe/Budapest"
    availability_hours: Dict[str, List[str]] = Field(default_factory=dict)
    bio: Optional[str] = None
    max_age_difference: Optional[int] = None
    preferred_experience_level: Optional[str] = None

class AccountabilityProfileUpdate(BaseModel):
    goal_categories: Optional[List[GoalCategory]] = None
    checkin_frequency: Optional[CheckInFrequency] = None
    motivation_style: Optional[MotivationStyle] = None
    personality_type: Optional[PersonalityType] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    is_looking_for_partners: Optional[bool] = None

class AccountabilityProfileRead(BaseModel):
    id: str
    user_id: str
    goal_categories: List[GoalCategory]
    checkin_frequency: CheckInFrequency
    motivation_style: MotivationStyle
    personality_type: PersonalityType
    timezone: str
    bio: Optional[str]
    is_active: bool
    is_looking_for_partners: bool
    created_at: datetime

# Partnership schemas
class PartnershipRequest(BaseModel):
    target_user_id: str  # <-- "requested_user_id" helyett "target_user_id"
    checkin_frequency: CheckInFrequency
    shared_goals: List[str] = Field(default_factory=list)
    message: Optional[str] = None

class PartnershipResponse(BaseModel):
    partnership_id: str
    accept: bool
    message: Optional[str] = None

class PartnershipRead(BaseModel):
    id: str
    partner_user_id: str
    partner_username: str
    status: PartnershipStatus
    checkin_frequency: CheckInFrequency
    shared_goals: List[str]
    created_at: datetime
    accepted_at: Optional[datetime]
    total_checkins: int
    successful_checkins: int

# Check-in schemas
class CheckInCreate(BaseModel):
    goals_met: bool
    progress_rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None
    habit_completions: List[str] = Field(default_factory=list)

class CheckInRead(BaseModel):
    id: str
    partnership_id: str
    user_id: str
    date: str
    goals_met: bool
    progress_rating: int
    notes: Optional[str]
    created_at: datetime

# Matching schemas
class PartnerSuggestionRead(BaseModel):
    user_id: str
    username: str
    bio: Optional[str]
    goal_categories: List[GoalCategory]
    compatibility_score: float
    common_goals: List[str]
    matching_factors: Dict[str, str]

class MatchingPreferences(BaseModel):
    max_distance_km: Optional[int] = None
    min_compatibility_score: float = 0.6
    preferred_goal_categories: Optional[List[GoalCategory]] = None