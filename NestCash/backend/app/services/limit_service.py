# app/services/limit_service.py
from typing import List, Optional, Tuple
from beanie import PydanticObjectId
from datetime import datetime
import logging

from app.models.limit import Limit, LimitType
from app.models.transaction import Transaction
from app.models.limit_schemas import LimitCheckResult

logger = logging.getLogger(__name__)

class LimitService:
    """Limit ellenőrzési és kezelési szolgáltatás"""
    
    @staticmethod
    async def check_transaction_against_limits(
        user_id: str,
        amount: float,
        category: Optional[str] = None,
        main_account: Optional[str] = None,
        sub_account_name: Optional[str] = None
    ) -> LimitCheckResult:
        """
        Tranzakció ellenőrzése az aktív limitek ellen
        
        Args:
            user_id: Felhasználó ID
            amount: Tranzakció összege (negatív = kiadás)
            category: Kategória
            main_account: Főszámla
            sub_account_name: Alszámla neve
            
        Returns:
            LimitCheckResult: Ellenőrzés eredménye
        """
        try:
            # Csak kiadásokat ellenőrizzük
            if amount >= 0:
                return LimitCheckResult(is_allowed=True)
            
            # Aktív limitek lekérdezése
            active_limits = await Limit.find(
                Limit.user_id == PydanticObjectId(user_id),
                Limit.is_active == True
            ).to_list()
            
            exceeded_limits = []
            warnings = []
            
            for limit in active_limits:
                # Ellenőrizzük, hogy vonatkozik-e a tranzakcióra
                if not LimitService._applies_to_transaction(
                    limit, category, main_account, sub_account_name
                ):
                    continue
                
                # Jelenlegi kiadás lekérdezése
                current_spending = await LimitService._get_current_spending(user_id, limit)
                projected_spending = current_spending + abs(amount)
                
                # Limit túllépés ellenőrzése
                if projected_spending > limit.amount:
                    exceeded_limits.append(f"{limit.name}")
                # Küszöb ellenőrzése
                elif (limit.notification_threshold and 
                      (projected_spending / limit.amount) * 100 >= limit.notification_threshold):
                    usage_pct = (projected_spending / limit.amount) * 100
                    warnings.append(f"{limit.name}: {usage_pct:.1f}% elérve")
            
            is_allowed = len(exceeded_limits) == 0
            message = None
            
            if exceeded_limits:
                message = f"Limitek túllépnének: {', '.join(exceeded_limits)}"
            elif warnings:
                message = f"Figyelem: {'; '.join(warnings)}"
            
            return LimitCheckResult(
                is_allowed=is_allowed,
                exceeded_limits=exceeded_limits,
                warnings=warnings,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error checking limits for user {user_id}: {e}")
            # Hiba esetén engedjük a tranzakciót, de loggoljuk
            return LimitCheckResult(
                is_allowed=True,
                message="Limit ellenőrzés hiba miatt kihagyva"
            )
    
    @staticmethod
    async def get_exceeded_limits(user_id: str) -> List[Limit]:
        """Túllépett limitek lekérdezése"""
        try:
            active_limits = await Limit.find(
                Limit.user_id == PydanticObjectId(user_id),
                Limit.is_active == True
            ).to_list()
            
            exceeded = []
            for limit in active_limits:
                current_spending = await LimitService._get_current_spending(user_id, limit)
                if current_spending > limit.amount:
                    exceeded.append(limit)
            
            return exceeded
            
        except Exception as e:
            logger.error(f"Error getting exceeded limits for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_warning_limits(user_id: str) -> List[Tuple[Limit, float]]:
        """Figyelmeztetési küszöb feletti limitek lekérdezése"""
        try:
            active_limits = await Limit.find(
                Limit.user_id == PydanticObjectId(user_id),
                Limit.is_active == True,
                Limit.notification_threshold != None
            ).to_list()
            
            warnings = []
            for limit in active_limits:
                current_spending = await LimitService._get_current_spending(user_id, limit)
                usage_percentage = (current_spending / limit.amount) * 100
                
                if (current_spending <= limit.amount and 
                    usage_percentage >= limit.notification_threshold):
                    warnings.append((limit, usage_percentage))
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error getting warning limits for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def _get_current_spending(user_id: str, limit: Limit) -> float:
        """Aktuális kiadás számítása egy limit alapján"""
        try:
            period_start = limit.get_period_start()
            period_end = limit.get_period_end()
            
            # Alapszűrő
            query_filter = {
                "user_id": PydanticObjectId(user_id),
                "date": {
                    "$gte": period_start.strftime("%Y-%m-%d"),
                    "$lte": period_end.strftime("%Y-%m-%d")
                },
                "amount": {"$lt": 0}  # Csak kiadások
            }
            
            # Típus specifikus szűrés
            if limit.type == LimitType.CATEGORY and limit.category:
                query_filter["kategoria"] = limit.category
            elif limit.type == LimitType.ACCOUNT:
                if limit.main_account:
                    query_filter["main_account"] = limit.main_account
                if limit.sub_account_name:
                    query_filter["sub_account_name"] = limit.sub_account_name
            
            transactions = await Transaction.find(query_filter).to_list()
            return abs(sum(t.amount for t in transactions))
            
        except Exception as e:
            logger.error(f"Error calculating current spending: {e}")
            return 0.0
    
    @staticmethod
    def _applies_to_transaction(
        limit: Limit, 
        category: Optional[str], 
        main_account: Optional[str], 
        sub_account_name: Optional[str]
    ) -> bool:
        """Ellenőrzi, hogy a limit vonatkozik-e a tranzakcióra"""
        if limit.type == LimitType.SPENDING:
            return True  # Általános kiadási limit
        elif limit.type == LimitType.CATEGORY:
            return limit.category == category
        elif limit.type == LimitType.ACCOUNT:
            account_match = True
            if limit.main_account and limit.main_account != main_account:
                account_match = False
            if limit.sub_account_name and limit.sub_account_name != sub_account_name:
                account_match = False
            return account_match
        
        return False
    
    @staticmethod
    async def create_default_limits(user_id: str) -> List[Limit]:
        """Alapértelmezett limitek létrehozása új felhasználónak"""
        try:
            default_limits = [
                {
                    "name": "Havi általános kiadási limit",
                    "type": LimitType.SPENDING,
                    "amount": 200000,
                    "period": "monthly",
                    "notification_threshold": 80
                },
                {
                    "name": "Havi élelmiszer limit",
                    "type": LimitType.CATEGORY,
                    "category": "Élelmiszer",
                    "amount": 50000,
                    "period": "monthly",
                    "notification_threshold": 75
                }
            ]
            
            created_limits = []
            for limit_data in default_limits:
                limit = Limit(
                    user_id=PydanticObjectId(user_id),
                    **limit_data
                )
                await limit.insert()
                created_limits.append(limit)
            
            return created_limits
            
        except Exception as e:
            logger.error(f"Error creating default limits for user {user_id}: {e}")
            return []