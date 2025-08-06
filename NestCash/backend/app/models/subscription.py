# app/models/subscription.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from beanie import Document
from beanie import PydanticObjectId

class SubscriptionTier(str, Enum):
    FREE = "free"
    PLUS = "plus"  
    PRO = "pro"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"

# Előfizetési terv definíciója
class SubscriptionPlan(BaseModel):
    tier: SubscriptionTier
    name: str
    price: float  # EUR-ban
    duration_days: int  # Előfizetés időtartama napokban
    features: Dict[str, Any]  # Funkciók és korlátaik

    @staticmethod
    def get_all_plans() -> List["SubscriptionPlan"]:
        """Minden előfizetési terv definíciója"""
        return [
            SubscriptionPlan(
                tier=SubscriptionTier.FREE,
                name="Free",
                price=0.0,
                duration_days=0,  # Végtelen
                features={
                    "transaction_management": "basic_manual",
                    "accounts_currencies": True,
                    "filtering_tagging": True,
                    "habits_reminders": "basic",
                    "analysis_insights": "basic_category_only",
                    "pti_index": True,
                    "export_sharing": True,
                    "knowledge_base": "1_lesson_per_day_with_ads",
                    "challenges": "1_active",
                    "habit_streak": "max_5_habits",
                    "community_forum": True,
                    "accountability_partner": "max_1",
                    "leaderboards": True
                }
            ),
            SubscriptionPlan(
                tier=SubscriptionTier.PLUS,
                name="Plus",
                price=5.0,
                duration_days=30,
                features={
                    "transaction_management": "import_bulk_edit",
                    "accounts_currencies": True,
                    "filtering_tagging": True,
                    "habits_reminders": "with_goal_linking",
                    "analysis_insights": "full_module",
                    "pti_index": True,
                    "export_sharing": True,
                    "knowledge_base": "full_unlimited",
                    "challenges": "unlimited",
                    "habit_streak": "unlimited",
                    "community_forum": "with_tier_badge",
                    "accountability_partner": "unlimited",
                    "leaderboards": "with_tier_badge"
                }
            ),
            SubscriptionPlan(
                tier=SubscriptionTier.PRO,
                name="Pro",
                price=12.5,
                duration_days=30,
                features={
                    "transaction_management": "import_bulk_edit",
                    "accounts_currencies": True,
                    "filtering_tagging": True,
                    "habits_reminders": "with_suggestions",
                    "analysis_insights": "personalized",
                    "pti_index": True,
                    "export_sharing": True,
                    "knowledge_base": "exclusive_content_learning_paths",
                    "challenges": "unlimited_with_exclusive",
                    "habit_streak": "unlimited",
                    "community_forum": "with_tier_badge",
                    "accountability_partner": "with_groups",
                    "leaderboards": "with_tier_badge"
                }
            )
        ]

    @staticmethod
    def get_plan_by_tier(tier: SubscriptionTier) -> "SubscriptionPlan":
        """Konkrét terv lekérése tier alapján"""
        plans = SubscriptionPlan.get_all_plans()
        for plan in plans:
            if plan.tier == tier:
                return plan
        return plans[0]  # Default: FREE

# MongoDB dokumentum a felhasználó előfizetéséhez
class UserSubscriptionDocument(Document):
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE)
    
    # Időbélyegek
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Fizetési információk
    payment_provider: Optional[str] = None  # stripe, paypal, etc.
    external_subscription_id: Optional[str] = None
    last_payment_at: Optional[datetime] = None
    next_billing_at: Optional[datetime] = None
    
    # Előfizetés történet
    upgrade_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Settings:
        name = "user_subscriptions"
        indexes = [
            "user_id",
            [("user_id", 1), ("status", 1)],
            "expires_at"
        ]

    def is_active(self) -> bool:
        """Ellenőrzi, hogy az előfizetés aktív-e"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        
        if self.tier == SubscriptionTier.FREE:
            return True  # Free tier mindig aktív
            
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True

    def get_plan(self) -> SubscriptionPlan:
        """Jelenlegi előfizetési terv lekérése"""
        return SubscriptionPlan.get_plan_by_tier(self.tier)

    def days_until_expiry(self) -> Optional[int]:
        """Hány nap van hátra az előfizetésből"""
        if self.tier == SubscriptionTier.FREE or not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def add_upgrade_history(self, from_tier: SubscriptionTier, to_tier: SubscriptionTier, reason: str = ""):
        """Előfizetés módosítás történethez adása"""
        self.upgrade_history.append({
            "from_tier": from_tier.value,
            "to_tier": to_tier.value,
            "changed_at": datetime.utcnow().isoformat(),
            "reason": reason
        })

# Pydantic modellek API válaszokhoz
class UserSubscription(BaseModel):
    id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    subscribed_at: datetime
    expires_at: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    plan: SubscriptionPlan

class SubscriptionUpdate(BaseModel):
    tier: SubscriptionTier
    expires_at: Optional[datetime] = None
    payment_provider: Optional[str] = None
    external_subscription_id: Optional[str] = None

# Feature ellenőrzési séma
class FeatureAccess(BaseModel):
    feature: str
    has_access: bool
    current_limit: Optional[int] = None
    usage_count: Optional[int] = None
    upgrade_required: bool = False
    required_tier: Optional[SubscriptionTier] = None