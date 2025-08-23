# app/routes/onboarding.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.models.user import User, UserDocument
from app.models.onboarding import (
    UserType, UserIntent, UserIntentSelection, 
    BasicSetupData, UpdateOnboardingStepRequest,
    OnboardingStatusResponse, CompleteOnboardingRequest
)
from app.services.onboarding_service import OnboardingService
from app.services.health_score_service import HealthScoreService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(current_user: User = Depends(get_current_user)):
    """Visszaadja a felhasználó jelenlegi onboarding állapotát"""
    
    await HealthScoreService.track_feature_usage(current_user.id, "onboarding_status_check")

    user_doc = await UserDocument.find_one(UserDocument.id == PydanticObjectId(current_user.id))
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    next_action = None
    if user_doc.user_type and not user_doc.onboarding_completed:
        next_action = OnboardingService.get_next_recommended_action(
            UserType(user_doc.user_type)
        )
    
    return OnboardingStatusResponse(
        current_step=user_doc.onboarding_step,
        user_type=user_doc.user_type,
        selected_intents=[UserIntent(intent) for intent in user_doc.selected_intents],
        onboarding_completed=user_doc.onboarding_completed,
        next_recommended_action=next_action
    )

@router.post("/step/{step_number}")
async def update_onboarding_step(
    step_number: int,
    request: UpdateOnboardingStepRequest,
    current_user: User = Depends(get_current_user)
):
    """Frissíti az onboarding lépést és menteti a hozzá tartozó adatokat"""
    
    if step_number < 0 or step_number > 6:
        raise HTTPException(status_code=400, detail="Invalid step number")
    
    try:
        updated_user = await OnboardingService.update_user_onboarding_progress(
            current_user.id, step_number, request.data
        )

        # Feature tracking - minden lépéshez külön
        await HealthScoreService.track_feature_usage(
            current_user.id, 
            f"onboarding_step_{step_number}"
        )

        # Ha befejezett egy lépést, azt is trackeljük
        if step_number > 0:
            await HealthScoreService.track_feature_usage(
                current_user.id, 
                f"onboarding_step_{step_number}_completed"
            )
        
        return {
            "message": f"Onboarding step {step_number} updated successfully",
            "current_step": updated_user.onboarding_step,
            "user_type": updated_user.user_type
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/intents")
async def save_user_intents(
    intents: UserIntentSelection,
    current_user: User = Depends(get_current_user)
):
    """Elmenti a felhasználó által kiválasztott szándékokat és meghatározza a típusát"""
    
    # Feature tracking
    await HealthScoreService.track_feature_usage(current_user.id, "onboarding_intents_selection")
    await HealthScoreService.track_feature_usage(current_user.id, "user_type_determination")

    # Meghatározzuk a user típusát a szándékok alapján
    determined_type = OnboardingService.determine_user_type(intents.intents)
    
    # Frissítjük az onboarding állapotot
    updated_user = await OnboardingService.update_user_onboarding_progress(
        current_user.id, 
        1,  # Célfelmérés lépés
        {
            "selected_intents": [intent.value for intent in intents.intents],
            "user_type": determined_type.value
        }
    )
    
    return {
        "message": "User intents saved successfully",
        "determined_type": determined_type,
        "selected_intents": intents.intents,
        "tutorial_content": OnboardingService.get_tutorial_content(determined_type)
    }

@router.post("/basic-setup")
async def save_basic_setup(
    setup_data: BasicSetupData,
    current_user: User = Depends(get_current_user)
):
    """Elmenti az alapbeállításokat és létrehozza a kezdeti számlát"""
    
    try:
        # Feature tracking
        await HealthScoreService.track_feature_usage(current_user.id, "onboarding_basic_setup")
        await HealthScoreService.track_feature_usage(current_user.id, "initial_account_creation")

        # Referral source tracking
        if setup_data.referral_source:
            await HealthScoreService.track_feature_usage(
                current_user.id, 
                f"referral_source_{setup_data.referral_source.value}"
            )

        # Onboarding állapot frissítése
        await OnboardingService.update_user_onboarding_progress(
            current_user.id,
            2,  # Alapbeállítások lépés
            {"basic_setup": setup_data.dict()}
        )
        
        # Kezdeti számla létrehozása
        user_accounts = await OnboardingService.create_initial_account(
            current_user.id, setup_data
        )
        
        return {
            "message": "Basic setup completed successfully",
            "accounts_created": True,
            "preferred_currency": setup_data.preferred_currency,
            "initial_balance": setup_data.initial_balance,
            "referral_source": setup_data.referral_source.value if setup_data.referral_source else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save basic setup: {str(e)}")

@router.get("/tutorial/{user_type}")
async def get_tutorial_content(user_type: UserType):
    """Visszaadja a megadott user típushoz tartozó tutorial tartalmat"""
    
    tutorial_content = OnboardingService.get_tutorial_content(user_type)
    return tutorial_content

@router.post("/complete")
async def complete_onboarding(current_user: User = Depends(get_current_user)):
    """Befejezi az onboarding folyamatot"""
    
    try:
        completed_user = await OnboardingService.complete_onboarding(current_user.id)
        
        # Feature tracking - fontos mérföldkő!
        await HealthScoreService.track_feature_usage(current_user.id, "onboarding_completed")
        await HealthScoreService.track_feature_usage(current_user.id, "onboarding_full_completion")

        return {
            "message": "Onboarding completed successfully!",
            "user_type": completed_user.user_type,
            "welcome_message": f"Üdvözlünk a NestCash-ben! Készen állsz a pénzügyi célok elérésére.",
            "next_recommended_action": OnboardingService.get_next_recommended_action(
                UserType(completed_user.user_type) if completed_user.user_type else UserType.DEFAULT
            )
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/restart")
async def restart_onboarding(current_user: User = Depends(get_current_user)):
    """Újraindítja az onboarding folyamatot"""
    
    user_doc = await UserDocument.find_one(UserDocument.id == PydanticObjectId(current_user.id))
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Onboarding állapot visszaállítása
    user_doc.onboarding_step = 0
    user_doc.onboarding_completed = False
    user_doc.user_type = None
    user_doc.selected_intents = []
    
    await user_doc.save()
    
    return {
        "message": "Onboarding restarted successfully",
        "current_step": 0
    }

@router.get("/user-types")
async def get_available_user_types():
    """Visszaadja az elérhető user típusokat leírásokkal"""
    
    types_info = {
        UserType.AWARE_SPENDER: {
            "name": "Tudatos költő",
            "description": "Szeretnéd jobban követni és kontrollálni a kiadásaidat"
        },
        UserType.COMMUNITY_DRIVEN: {
            "name": "Közösségorientált",
            "description": "Fontos számodra a közösség és a másokkal való fejlődés"
        },
        UserType.LEARNER: {
            "name": "Tanulni vágyó", 
            "description": "Inspirációt és tanulási lehetőségeket keresel"
        },
        UserType.ADVANCED: {
            "name": "Haladó",
            "description": "Mindent akarsz, mélyre szeretnél ásni a funkciókban"
        },
        UserType.COMPETITIVE: {
            "name": "Versengő",
            "description": "Szeretnéd látni, hogyan állsz másokhoz képest"
        }
    }
    
    return types_info

@router.get("/referral-sources")
async def get_referral_sources():
    """Visszaadja az elérhető referral forrásokat leírásokkal"""
    
    sources_info = {
        "social_media": {
            "name": "Közösségi média",
            "description": "Facebook, Instagram, TikTok, Twitter, stb.",
            "icon": "share"
        },
        "friend_family": {
            "name": "Barát/családtag ajánlása",
            "description": "Valaki ajánlotta neked",
            "icon": "people"
        },
        "advertisement": {
            "name": "Hirdetés",
            "description": "Online vagy offline reklám",
            "icon": "campaign"
        },
        "search_engine": {
            "name": "Keresőmotor",
            "description": "Google, Bing keresés",
            "icon": "search"
        },
        "blog_article": {
            "name": "Blog/cikk",
            "description": "Online cikk vagy blog poszt",
            "icon": "article"
        },
        "podcast": {
            "name": "Podcast",
            "description": "Podcastban hallottam róla",
            "icon": "podcast"
        },
        "app_store": {
            "name": "App áruház",
            "description": "Google Play vagy App Store böngészés",
            "icon": "store"
        },
        "other": {
            "name": "Egyéb",
            "description": "Máshol hallottam róla",
            "icon": "more"
        }
    }
    
    return sources_info