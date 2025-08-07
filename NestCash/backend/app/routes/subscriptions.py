# app/routes/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import (
    UserSubscription, 
    SubscriptionUpdate,
    SubscriptionTier,
    SubscriptionPlan,
    FeatureAccess
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/subscription", tags=["subscription"])

@router.get("/me", response_model=UserSubscription)
async def get_my_subscription(current_user: User = Depends(get_current_user)):
    """Jelenlegi felhasználó előfizetésének lekérése"""
    try:
        subscription_doc = await PermissionService.get_user_subscription(current_user.id)
        plan = subscription_doc.get_plan()
        
        return UserSubscription(
            id=str(subscription_doc.id),
            user_id=str(subscription_doc.user_id),
            tier=subscription_doc.tier,
            status=subscription_doc.status,
            subscribed_at=subscription_doc.subscribed_at,
            expires_at=subscription_doc.expires_at,
            days_until_expiry=subscription_doc.days_until_expiry(),
            plan=plan
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Előfizetés lekérése sikertelen"
        )

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_available_plans():
    """Elérhető előfizetési tervek lekérése"""
    return SubscriptionPlan.get_all_plans()

@router.get("/features")
async def get_my_features(current_user: User = Depends(get_current_user)):
    """Felhasználó funkciói és korlátai"""
    try:
        features_summary = await PermissionService.get_user_features_summary(current_user.id)
        return features_summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Funkciók lekérése sikertelen"
        )

@router.post("/check-feature")
async def check_feature_access(
    current_user: User = Depends(get_current_user),
    feature: str = Query(..., description="Feature name"),
    current_usage_count: Optional[int] = Query(None),
    current_active_challenges: Optional[int] = Query(None),
    current_habit_count: Optional[int] = Query(None),
    daily_lesson_count: Optional[int] = Query(None),
    current_partner_count: Optional[int] = Query(None),
    analysis_type: Optional[str] = Query(None)
):
    """
    Konkrét funkció hozzáférésének ellenőrzése
    Használható frontend oldalról mielőtt egy funkciót használnánk
    """
    try:
        kwargs = {}
        if current_usage_count is not None:
            kwargs["current_usage_count"] = current_usage_count
        if current_active_challenges is not None:
            kwargs["current_active_challenges"] = current_active_challenges
        if current_habit_count is not None:
            kwargs["current_habit_count"] = current_habit_count
        if daily_lesson_count is not None:
            kwargs["daily_lesson_count"] = daily_lesson_count
        if current_partner_count is not None:
            kwargs["current_partner_count"] = current_partner_count
        if analysis_type is not None:
            kwargs["analysis_type"] = analysis_type
        
        access = await PermissionService.check_feature_access(
            user_id=current_user.id,
            feature=feature,
            **kwargs
        )
        
        return {
            "feature": access.feature,
            "has_access": access.has_access,
            "current_limit": access.current_limit,
            "usage_count": access.usage_count,
            "remaining": (access.current_limit - access.usage_count) if access.current_limit and access.usage_count is not None else None,
            "upgrade_required": access.upgrade_required,
            "required_tier": access.required_tier.value if access.required_tier else None,
            "message": "Hozzáférés engedélyezve" if access.has_access else "Előfizetés frissítés szükséges"
        }
        
    except Exception as e:
        print(f"Feature check error: {str(e)}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Funkció ellenőrzés sikertelen: {str(e)}"
        )

@router.post("/upgrade")
async def upgrade_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Előfizetés frissítése
    FONTOS: Ez csak a belső állapot frissítése! 
    A tényleges fizetés külön payment service-n keresztül történik
    """
    try:
        # Validálás: nem lehet FREE-re "upgradelni" (azt a cancel endpoint kezeli)
        if subscription_data.tier == SubscriptionTier.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FREE tier beállításához használd a /cancel endpoint-ot"
            )
        
        # Előfizetés frissítése
        plan = SubscriptionPlan.get_plan_by_tier(subscription_data.tier)
        
        updated_subscription = await PermissionService.upgrade_subscription(
            user_id=current_user.id,
            new_tier=subscription_data.tier,
            duration_days=plan.duration_days,
            payment_provider=subscription_data.payment_provider,
            external_subscription_id=subscription_data.external_subscription_id
        )
        
        return {
            "success": True,
            "message": f"Előfizetés sikeresen frissítve {subscription_data.tier.value} szintre",
            "subscription": {
                "tier": updated_subscription.tier,
                "status": updated_subscription.status,
                "expires_at": updated_subscription.expires_at,
                "days_until_expiry": updated_subscription.days_until_expiry()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Előfizetés frissítés sikertelen: {str(e)}"
        )

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    reason: Optional[str] = "user_request"
):
    """Előfizetés lemondása (FREE tier-re visszaállítás)"""
    try:
        cancelled_subscription = await PermissionService.cancel_subscription(
            user_id=current_user.id,
            reason=reason
        )
        
        return {
            "success": True,
            "message": "Előfizetés sikeresen lemondva. FREE tier funkciók továbbra is elérhetők.",
            "subscription": {
                "tier": SubscriptionTier.FREE,
                "status": cancelled_subscription.status,
                "cancelled_at": cancelled_subscription.cancelled_at
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Előfizetés lemondás sikertelen: {str(e)}"
        )

@router.get("/usage/{feature}")
async def get_feature_usage(
    feature: str,
    current_user: User = Depends(get_current_user)
):
    """Konkrét funkció használati statisztikáinak lekérése"""
    try:
        # Itt lekérdeznénk a konkrét használati adatokat az adott funkcióhoz
        # Példa implementáció
        
        if feature == "challenges":
            # Challenges collection-ből lekérdezni az aktív challenges-ek számát
            from app.models.challenge import UserChallengeDocument
            active_challenges = await UserChallengeDocument.find(
                UserChallengeDocument.user_id == current_user.id,
                UserChallengeDocument.status == "active"
            ).count()
            
            access = await PermissionService.check_feature_access(
                user_id=current_user.id,
                feature=feature,
                current_active_challenges=active_challenges
            )
            
            return {
                "feature": feature,
                "usage_count": active_challenges,
                "limit": access.current_limit,
                "remaining": (access.current_limit - active_challenges) if access.current_limit else None,
                "has_access": access.has_access,
                "upgrade_required": access.upgrade_required
            }
        
        elif feature == "habit_streak":
            # Habits collection-ből lekérdezni a habits számát
            from app.models.habit import Habit
            habit_count = await Habit.find(Habit.user_id == current_user.id).count()
            
            access = await PermissionService.check_feature_access(
                user_id=current_user.id,
                feature=feature,
                current_habit_count=habit_count
            )
            
            return {
                "feature": feature,
                "usage_count": habit_count,
                "limit": access.current_limit,
                "remaining": (access.current_limit - habit_count) if access.current_limit else None,
                "has_access": access.has_access,
                "upgrade_required": access.upgrade_required
            }
        
        else:
            # Általános funkciók esetén alapvető hozzáférés info
            access = await PermissionService.check_feature_access(
                user_id=current_user.id,
                feature=feature
            )
            
            return {
                "feature": feature,
                "has_access": access.has_access,
                "upgrade_required": access.upgrade_required,
                "required_tier": access.required_tier.value if access.required_tier else None
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Használati adatok lekérése sikertelen: {str(e)}"
        )

@router.get("/history")
async def get_subscription_history(current_user: User = Depends(get_current_user)):
    """Előfizetési történet lekérése"""
    try:
        subscription_doc = await PermissionService.get_user_subscription(current_user.id)
        
        return {
            "current_subscription": {
                "tier": subscription_doc.tier,
                "status": subscription_doc.status,
                "subscribed_at": subscription_doc.subscribed_at,
                "expires_at": subscription_doc.expires_at
            },
            "upgrade_history": subscription_doc.upgrade_history,
            "payment_info": {
                "payment_provider": subscription_doc.payment_provider,
                "last_payment_at": subscription_doc.last_payment_at,
                "next_billing_at": subscription_doc.next_billing_at
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Előfizetési történet lekérése sikertelen"
        )