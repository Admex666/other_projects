from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserProfile, UserGoals
from schemas.onboarding import OnboardingData, OnboardingResponse
from api.auth import get_current_user

router = APIRouter()


def generate_learning_path(data: OnboardingData) -> dict:
    """Generate personalized learning path based on onboarding data"""
    
    focus_areas = []
    starting_lessons = []
    
    # Determine focus areas based on skill level
    if data.skill_level == "beginner":
        focus_areas = ["poker_math", "position", "starting_hands", "pot_odds"]
        starting_lessons = ["basic_math_01", "position_basics_01", "preflop_fundamentals_01"]
    elif data.skill_level == "intermediate":
        focus_areas = ["range_thinking", "cbetting", "3betting", "board_textures"]
        starting_lessons = ["range_construction_01", "continuation_betting_01", "3bet_strategy_01"]
    else:  # advanced
        focus_areas = ["gto_concepts", "exploits", "population_tendencies", "advanced_math"]
        starting_lessons = ["gto_intro_01", "exploit_strategies_01", "advanced_equity_01"]
    
    # Adjust for game format
    if data.game_format == "mtt":
        focus_areas.append("icm")
        starting_lessons.append("tournament_basics_01")
    elif data.game_format == "spin_and_go":
        focus_areas.append("short_stack")
        starting_lessons.append("push_fold_01")
    
    # Goal-specific recommendations
    if data.player_goal in ["professional", "high_stakes"]:
        focus_areas.extend(["mental_game", "bankroll_management", "game_selection"])
    
    return {
        "focus_areas": focus_areas,
        "starting_lessons": starting_lessons,
        "estimated_weeks": 4 if data.skill_level == "beginner" else 8,
        "recommended_study_hours_per_week": min(data.weekly_hours or 5, 20)
    }


@router.post("/complete", response_model=OnboardingResponse)
async def complete_onboarding(
    data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete onboarding and create user profile"""
    
    # Check if profile already exists
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already completed"
        )
    
    # Create user profile
    profile = UserProfile(
        user_id=current_user.id,
        skill_level=data.skill_level,
        game_format=data.game_format,
        game_variant=data.game_variant
    )
    db.add(profile)
    
    # Create user goals
    goals = UserGoals(
        user_id=current_user.id,
        player_goal=data.player_goal,
        current_bankroll=data.current_bankroll,
        target_bankroll=data.target_bankroll,
        weekly_hours=data.weekly_hours
    )
    db.add(goals)
    
    db.commit()
    
    # Generate learning path
    learning_path = generate_learning_path(data)
    
    return OnboardingResponse(
        success=True,
        message="Onboarding completed successfully",
        recommended_path=learning_path
    )


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has completed onboarding"""
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    return {
        "completed": profile is not None,
        "profile": profile if profile else None
    }
