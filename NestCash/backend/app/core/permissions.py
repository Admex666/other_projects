# app/core/permissions.py
from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer

from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import SubscriptionTier, FeatureAccess
from app.services.permission_service import PermissionService

security = HTTPBearer()

class PermissionChecker:
    """Jogosultság ellenőrzési osztály"""
    
    def __init__(self, 
                 feature: str, 
                 required_tier: Optional[SubscriptionTier] = None,
                 check_usage: bool = False):
        self.feature = feature
        self.required_tier = required_tier
        self.check_usage = check_usage

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        FastAPI dependency-ként használható jogosultság ellenőrzés
        """
        try:
            # Alapvető feature hozzáférés ellenőrzése
            access = await PermissionService.check_feature_access(
                user_id=current_user.id,
                feature=self.feature
            )
            
            if not access.has_access:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "feature_access_denied",
                        "message": f"A(z) '{self.feature}' funkció használatához magasabb szintű előfizetés szükséges.",
                        "feature": self.feature,
                        "required_tier": access.required_tier.value if access.required_tier else None,
                        "upgrade_required": access.upgrade_required
                    }
                )
            
            # Ha van használati korlát, ellenőrizzük
            if self.check_usage and access.current_limit is not None:
                if access.usage_count >= access.current_limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "usage_limit_exceeded", 
                            "message": f"Elérted a(z) '{self.feature}' funkció használati korlátját ({access.current_limit}).",
                            "feature": self.feature,
                            "current_limit": access.current_limit,
                            "usage_count": access.usage_count,
                            "required_tier": access.required_tier.value if access.required_tier else None
                        }
                    )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Jogosultság ellenőrzési hiba"
            )

# Előre definiált permission checker-ek
require_knowledge_access = PermissionChecker("knowledge_base", check_usage=True)
require_challenges_access = PermissionChecker("challenges", check_usage=True) 
require_habit_access = PermissionChecker("habit_streak", check_usage=True)
require_analysis_access = PermissionChecker("analysis_insights")
require_partner_access = PermissionChecker("accountability_partner", check_usage=True)

# Tier-alapú ellenőrzések
require_plus_tier = PermissionChecker("tier_check", required_tier=SubscriptionTier.PLUS)
require_pro_tier = PermissionChecker("tier_check", required_tier=SubscriptionTier.PRO)

# Decorator funkcionalitás route-okhoz
def require_feature(feature: str, check_usage: bool = False):
    """
    Decorator funkció route-ok jogosultság ellenőrzéséhez
    
    Usage:
        @require_feature("knowledge_base", check_usage=True)
        async def get_lesson(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Keressük meg a current_user paramétert
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Jogosultság ellenőrzés
            access = await PermissionService.check_feature_access(
                user_id=current_user.id,
                feature=feature
            )
            
            if not access.has_access:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "feature_access_denied",
                        "message": f"A(z) '{feature}' funkció használatához magasabb szintű előfizetés szükséges.",
                        "feature": feature,
                        "required_tier": access.required_tier.value if access.required_tier else None
                    }
                )
            
            if check_usage and access.current_limit is not None:
                if access.usage_count >= access.current_limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "usage_limit_exceeded",
                            "message": f"Elérted a(z) '{feature}' funkció használati korlátját.",
                            "current_limit": access.current_limit,
                            "usage_count": access.usage_count
                        }
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Middleware használati példa
class SubscriptionMiddleware:
    """Middleware az előfizetés állapotának ellenőrzéséhez"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Itt lehet általános előfizetés állapot ellenőrzéseket végezni
        # pl. lejárt előfizetések automatikus FREE tier-re állítása
        return await self.app(scope, receive, send)

# Utility függvények route-okból való használatra
async def check_and_increment_usage(user_id: str, feature: str, **kwargs) -> FeatureAccess:
    """
    Ellenőrzi a hozzáférést és növeli a használat számát
    Hasznos olyan funkciókhoz, ahol trackelni kell a használatot
    """
    access = await PermissionService.check_feature_access(
        user_id=user_id,
        feature=feature,
        **kwargs
    )
    
    if not access.has_access:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "feature_access_denied",
                "feature": feature,
                "required_tier": access.required_tier.value if access.required_tier else None
            }
        )
    
    return access

async def get_usage_info(user_id: str, feature: str, **kwargs) -> dict:
    """Használati információk lekérése frontend számára"""
    access = await PermissionService.check_feature_access(
        user_id=user_id,
        feature=feature,
        **kwargs
    )
    
    return {
        "has_access": access.has_access,
        "current_limit": access.current_limit,
        "usage_count": access.usage_count,
        "remaining": (access.current_limit - access.usage_count) if access.current_limit else None,
        "upgrade_required": access.upgrade_required,
        "required_tier": access.required_tier.value if access.required_tier else None
    }