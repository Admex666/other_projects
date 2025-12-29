from pydantic import BaseModel, Field
from typing import Optional
from models.user import SkillLevel, GameFormat, GameVariant, PlayerGoal


class OnboardingData(BaseModel):
    """Schema for onboarding data submission"""
    skill_level: SkillLevel
    game_format: GameFormat
    game_variant: GameVariant
    player_goal: PlayerGoal
    current_bankroll: Optional[float] = Field(None, ge=0)
    target_bankroll: Optional[float] = Field(None, ge=0)
    weekly_hours: Optional[float] = Field(None, ge=0, le=168)


class OnboardingResponse(BaseModel):
    """Schema for onboarding completion response"""
    success: bool
    message: str
    recommended_path: dict
    # Example: {"focus_areas": ["preflop", "position"], "starting_lessons": ["basic_math_01"]}
    
    class Config:
        from_attributes = True
