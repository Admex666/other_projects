# app/models/user.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from beanie import Document

class SharedAchievement(BaseModel):
    type: str = Field(..., description="Teljesítmény típusa (badge, lesson, challenge)")
    achievement_id: str = Field(..., description="Teljesítmény egyedi azonosítója")
    shared_at: datetime = Field(default_factory=datetime.utcnow)

# Beanie Document a MongoDB-hez
class UserDocument(Document):
    username: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    user_type: Optional[str] = None  # "aware_spender", "community_driven", "learner", "advanced", "competitive"
    selected_intents: list[str] = Field(default_factory=list)  # A kiválasztott célok listája
    onboarding_completed: bool = False
    onboarding_step: int = 0  # Jelenlegi onboarding lépés (0-6)
    preferred_currency: str = "HUF"  # Alapértelmezett deviza
    referral_source: Optional[str] = None
    referral_details: Optional[str] = None 
    shared_achievements: List[SharedAchievement] = Field(default_factory=list, description="Megosztott teljesítmények")

    class Settings:
        name = "users"

# Csak válaszhoz (nincs jelszó)
class User(BaseModel):
    id: str  # Changed from _id to id for standard Pydantic usage
    username: str
    email: EmailStr
    mobile: Optional[str] = None
    registration_date: datetime
    user_type: Optional[str] = None
    selected_intents: list[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    onboarding_step: int = 0
    preferred_currency: str = "HUF"
    referral_source: Optional[str] = None
    referral_details: Optional[str] = None

# Belső használatra (benne van a password)
class UserInDB(User):
    password: str

# Regisztrációhoz (input)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None