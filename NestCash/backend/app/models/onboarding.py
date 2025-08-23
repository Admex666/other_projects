# app/models/onboarding.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class UserType(str, Enum):
    AWARE_SPENDER = "aware_spender"
    COMMUNITY_DRIVEN = "community_driven" 
    LEARNER = "learner"
    ADVANCED = "advanced"
    COMPETITIVE = "competitive"
    DEFAULT = "aware_spender"

class UserIntent(str, Enum):
    TRACK_SPENDING = "track_spending"
    COMPARE_WITH_OTHERS = "compare_with_others"
    LEARN_AND_IMPROVE = "learn_and_improve"
    COMMUNITY_GROWTH = "community_growth"
    ADVANCED_FEATURES = "advanced_features"
    NOT_SURE = "not_sure"

class ReferralSource(str, Enum):
    SOCIAL_MEDIA = "social_media"
    FRIEND_FAMILY = "friend_family"
    ADVERTISEMENT = "advertisement"
    SEARCH_ENGINE = "search_engine"
    BLOG_ARTICLE = "blog_article"
    PODCAST = "podcast"
    APP_STORE = "app_store"
    OTHER = "other"

class OnboardingStep(BaseModel):
    step_number: int
    completed: bool = False
    data: Optional[dict] = None

class UserIntentSelection(BaseModel):
    intents: List[UserIntent]

class BasicSetupData(BaseModel):
    preferred_currency: str = "HUF"
    initial_balance: Optional[float] = None
    main_account_name: Optional[str] = "Fő számla"
    referral_source: Optional[ReferralSource] = None
    referral_details: Optional[str] = None  # További részletek, ha "other" vagy pontosítás

class OnboardingProgress(BaseModel):
    current_step: int = 0
    completed_steps: List[OnboardingStep] = Field(default_factory=list)
    user_type: Optional[UserType] = None
    selected_intents: List[UserIntent] = Field(default_factory=list)
    basic_setup: Optional[BasicSetupData] = None
    referral_source: Optional[ReferralSource] = None
    referral_details: Optional[str] = None
    tutorial_completed: bool = False
    onboarding_completed: bool = False

# API Request/Response modellek
class UpdateOnboardingStepRequest(BaseModel):
    step: int
    data: Optional[dict] = None

class CompleteOnboardingRequest(BaseModel):
    user_type: UserType
    selected_intents: List[UserIntent]
    basic_setup: BasicSetupData

class OnboardingStatusResponse(BaseModel):
    current_step: int
    user_type: Optional[UserType]
    selected_intents: List[UserIntent]
    onboarding_completed: bool
    next_recommended_action: Optional[str] = None