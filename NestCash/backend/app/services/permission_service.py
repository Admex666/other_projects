# app/services/permission_service.py
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.models.subscription import (
    UserSubscriptionDocument, 
    SubscriptionTier, 
    SubscriptionStatus,
    SubscriptionPlan,
    FeatureAccess
)
from app.models.user import UserDocument

logger = logging.getLogger(__name__)

class PermissionService:
    """Jogosultságkezelési szolgáltatás"""
    
    @staticmethod
    async def get_user_subscription(user_id: str) -> UserSubscriptionDocument:
        """Felhasználó előfizetésének lekérése vagy létrehozása"""
        try:
            subscription = await UserSubscriptionDocument.find_one(
                UserSubscriptionDocument.user_id == PydanticObjectId(user_id)
            )
            
            if not subscription:
                # Ha nincs előfizetés, létrehozzuk a FREE tier-rel
                subscription = UserSubscriptionDocument(
                    user_id=PydanticObjectId(user_id),
                    tier=SubscriptionTier.FREE,
                    status=SubscriptionStatus.ACTIVE
                )
                await subscription.insert()
                logger.info(f"Created FREE subscription for user {user_id}")
            
            return subscription
            
        except Exception as e:
            logger.error(f"Error getting user subscription for {user_id}: {e}")
            # Hiba esetén is FREE tier-t adunk vissza
            return UserSubscriptionDocument(
                user_id=PydanticObjectId(user_id),
                tier=SubscriptionTier.FREE,
                status=SubscriptionStatus.ACTIVE
            )

    @staticmethod
    async def check_feature_access(user_id: str, feature: str, **kwargs) -> FeatureAccess:
        """
        Funkció hozzáférés ellenőrzése
        
        Args:
            user_id: Felhasználó ID
            feature: Funkció neve (pl. "knowledge_base", "challenges", stb.)
            **kwargs: További paraméterek (pl. current_usage_count)
        
        Returns:
            FeatureAccess: Hozzáférési információk
        """
        try:
            subscription = await PermissionService.get_user_subscription(user_id)
            
            if not subscription.is_active():
                # Lejárt előfizetés esetén FREE tier jogosultságok
                subscription.tier = SubscriptionTier.FREE
                subscription.status = SubscriptionStatus.EXPIRED
                await subscription.save()
            
            plan = subscription.get_plan()
            feature_config = plan.features.get(feature)
            
            if feature_config is None:
                return FeatureAccess(
                    feature=feature,
                    has_access=False,
                    upgrade_required=True,
                    required_tier=SubscriptionTier.PLUS
                )
            
            # Feature-specifikus logika
            return await PermissionService._check_specific_feature(
                feature, feature_config, subscription.tier, **kwargs
            )
            
        except Exception as e:
            logger.error(f"Error checking feature access for user {user_id}, feature {feature}: {e}")
            # Hiba esetén megtagadjuk a hozzáférést
            return FeatureAccess(
                feature=feature,
                has_access=False,
                upgrade_required=True
            )

    @staticmethod
    async def _check_specific_feature(
        feature: str, 
        feature_config: Any, 
        current_tier: SubscriptionTier,
        **kwargs
    ) -> FeatureAccess:
        """Feature-specifikus hozzáférés ellenőrzés"""
        
        # Challenges ellenőrzése
        if feature == "challenges":
            current_active = kwargs.get("current_active_challenges", 0)
            
            if feature_config == "1_active":
                return FeatureAccess(
                    feature=feature,
                    has_access=current_active < 1,
                    current_limit=1,
                    usage_count=current_active,
                    upgrade_required=current_active >= 1,
                    required_tier=SubscriptionTier.PLUS
                )
            else:  # unlimited vagy unlimited_with_exclusive
                return FeatureAccess(
                    feature=feature,
                    has_access=True,
                    current_limit=None,
                    usage_count=current_active
                )
        
        # Habit streak ellenőrzése
        elif feature == "habit_streak":
            current_habits = kwargs.get("current_habit_count", 0)
            
            if feature_config == "max_5_habits":
                return FeatureAccess(
                    feature=feature,
                    has_access=current_habits < 5,
                    current_limit=5,
                    usage_count=current_habits,
                    upgrade_required=current_habits >= 5,
                    required_tier=SubscriptionTier.PLUS
                )
            else:  # unlimited
                return FeatureAccess(
                    feature=feature,
                    has_access=True,
                    current_limit=None,
                    usage_count=current_habits
                )
        
        # Knowledge base ellenőrzése  
        elif feature == "knowledge_base":
            daily_lessons = kwargs.get("daily_lesson_count", 0)
            
            if feature_config == "1_lesson_per_day_with_ads":
                return FeatureAccess(
                    feature=feature,
                    has_access=daily_lessons < 1,
                    current_limit=1,
                    usage_count=daily_lessons,
                    upgrade_required=daily_lessons >= 1,
                    required_tier=SubscriptionTier.PLUS
                )
            else:  # full_unlimited vagy exclusive_content_learning_paths
                return FeatureAccess(
                    feature=feature,
                    has_access=True,
                    current_limit=None,
                    usage_count=daily_lessons
                )
        
        # Analysis/Insights ellenőrzése
        elif feature == "analysis_insights":
            if feature_config == "basic_category_only":
                requested_type = kwargs.get("analysis_type", "basic")
                return FeatureAccess(
                    feature=feature,
                    has_access=requested_type in ["basic", "category"],
                    upgrade_required=requested_type not in ["basic", "category"],
                    required_tier=SubscriptionTier.PLUS
                )
            else:  # full_module vagy personalized
                return FeatureAccess(
                    feature=feature,
                    has_access=True
                )
        
        # Accountability partner ellenőrzése
        elif feature == "accountability_partner":
            current_partners = kwargs.get("current_partner_count", 0)
            
            if feature_config == "max_1":
                return FeatureAccess(
                    feature=feature,
                    has_access=current_partners < 1,
                    current_limit=1,
                    usage_count=current_partners,
                    upgrade_required=current_partners >= 1,
                    required_tier=SubscriptionTier.PLUS
                )
            elif feature_config == "unlimited":
                return FeatureAccess(
                    feature=feature,
                    has_access=True,
                    current_limit=None,
                    usage_count=current_partners
                )
            else:  # with_groups
                return FeatureAccess(
                    feature=feature,
                    has_access=True,
                    current_limit=None,
                    usage_count=current_partners
                )
        
        # Alapértelmezett: boolean vagy string érték alapján
        if isinstance(feature_config, bool):
            return FeatureAccess(
                feature=feature,
                has_access=feature_config
            )
        
        # String értékek esetén hozzáférés van
        return FeatureAccess(
            feature=feature,
            has_access=True
        )

    @staticmethod
    async def upgrade_subscription(
        user_id: str, 
        new_tier: SubscriptionTier,
        duration_days: int = 30,
        payment_provider: Optional[str] = None,
        external_subscription_id: Optional[str] = None
    ) -> UserSubscriptionDocument:
        """Előfizetés frissítése"""
        try:
            subscription = await PermissionService.get_user_subscription(user_id)
            old_tier = subscription.tier
            
            # Upgrade history hozzáadása
            subscription.add_upgrade_history(
                from_tier=old_tier,
                to_tier=new_tier,
                reason="paid_upgrade" if new_tier != SubscriptionTier.FREE else "downgrade"
            )
            
            # Új adatok beállítása
            subscription.tier = new_tier
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.last_payment_at = datetime.utcnow()
            
            if new_tier != SubscriptionTier.FREE:
                subscription.expires_at = datetime.utcnow().replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ) + timedelta(days=duration_days)
                subscription.next_billing_at = subscription.expires_at
            else:
                subscription.expires_at = None
                subscription.next_billing_at = None
            
            if payment_provider:
                subscription.payment_provider = payment_provider
            if external_subscription_id:
                subscription.external_subscription_id = external_subscription_id
            
            await subscription.save()
            
            logger.info(f"Upgraded user {user_id} from {old_tier} to {new_tier}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error upgrading subscription for user {user_id}: {e}")
            raise

    @staticmethod
    async def cancel_subscription(user_id: str, reason: str = "user_request") -> UserSubscriptionDocument:
        """Előfizetés lemondása"""
        try:
            subscription = await PermissionService.get_user_subscription(user_id)
            
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.add_upgrade_history(
                from_tier=subscription.tier,
                to_tier=SubscriptionTier.FREE,
                reason=f"cancelled_{reason}"
            )
            
            await subscription.save()
            
            logger.info(f"Cancelled subscription for user {user_id}, reason: {reason}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error cancelling subscription for user {user_id}: {e}")
            raise

    @staticmethod  
    async def get_user_features_summary(user_id: str) -> Dict[str, Any]:
        """Felhasználó összes funkciójának összegzése"""
        try:
            subscription = await PermissionService.get_user_subscription(user_id)
            plan = subscription.get_plan()
            
            return {
                "subscription": {
                    "tier": subscription.tier,
                    "status": subscription.status,
                    "expires_at": subscription.expires_at,
                    "days_until_expiry": subscription.days_until_expiry(),
                    "is_active": subscription.is_active()
                },
                "plan": {
                    "name": plan.name,
                    "price": plan.price,
                    "features": plan.features
                },
                "access_summary": {
                    "can_create_unlimited_challenges": plan.features.get("challenges") != "1_active",
                    "can_track_unlimited_habits": plan.features.get("habit_streak") != "max_5_habits", 
                    "has_full_knowledge_access": plan.features.get("knowledge_base") != "1_lesson_per_day_with_ads",
                    "has_advanced_analytics": plan.features.get("analysis_insights") != "basic_category_only",
                    "can_have_multiple_partners": plan.features.get("accountability_partner") != "max_1"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting features summary for user {user_id}: {e}")
            raise