# app/services/badge_service.py
from typing import List, Dict, Optional, Any
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime, timedelta
import logging

from app.models.badge import (
    BadgeType, UserBadge, BadgeProgress, BadgeEarnedEvent,
    BadgeCategory, BadgeRarity
)
from app.models.transaction import Transaction
from app.models.knowledge import UserProgress
from app.models.forum_models import ForumPostDocument, LikeDocument, FollowDocument
from app.models.user import UserDocument

logger = logging.getLogger(__name__)

class BadgeService:
    """Badge rendszer szolgáltatásai"""
    
    async def check_and_award_badges(self, user_id: str, trigger_event: str, context: Dict[str, Any] = None) -> List[BadgeEarnedEvent]:
        """
        Ellenőrzi és odaítéli a badge-eket egy esemény alapján
        
        Args:
            user_id: Felhasználó ID
            trigger_event: Esemény típusa (pl. "transaction_created", "lesson_completed")
            context: További kontextus információk
        
        Returns:
            Lista a megszerzett badge-ekről
        """
        earned_badges = []
        
        try:
            # Aktív badge típusok lekérése az esemény típusa alapján
            relevant_badges = await self._get_relevant_badges(trigger_event)
            
            for badge_type in relevant_badges:
                # Ellenőrizzük, hogy a felhasználó már megszerezte-e
                if not badge_type.is_repeatable:
                    existing = await UserBadge.find_one({
                        "user_id": ObjectId(user_id),
                        "badge_code": badge_type.code
                    })
                    if existing:
                        continue
                
                # Feltétel ellenőrzése
                is_earned, current_progress = await self._check_badge_condition(
                    user_id, badge_type, context
                )
                
                if is_earned:
                    # Badge odaítélése
                    earned_badge = await self._award_badge(user_id, badge_type, context)
                    if earned_badge:
                        earned_badges.append(earned_badge)
                else:
                    # Haladás frissítése
                    await self._update_badge_progress(user_id, badge_type, current_progress)
            
            return earned_badges
            
        except Exception as e:
            logger.error(f"Error checking badges for user {user_id}: {e}")
            return []
    
    async def _get_relevant_badges(self, trigger_event: str) -> List[BadgeType]:
        """Releváns badge típusok lekérése esemény alapján"""
        
        # Esemény típus -> badge feltétel típus mapping
        event_mapping = {
            "transaction_created": ["transaction_count", "spending_milestone", "saving_milestone"],
            "lesson_completed": ["knowledge_lessons", "knowledge_streak", "quiz_performance"],
            "forum_post_created": ["social_posts", "social_engagement"],
            "daily_login": ["streak_login", "milestone_days"],
            "account_created": ["milestone_registration"]
        }
        
        condition_types = event_mapping.get(trigger_event, [])
        
        if not condition_types:
            return []
        
        badges = await BadgeType.find({
            "is_active": True,
            "condition_type": {"$in": condition_types}
        }).to_list()
        
        return badges
    
    async def _check_badge_condition(self, user_id: str, badge_type: BadgeType, context: Dict[str, Any] = None) -> tuple[bool, float]:
        """
        Badge feltétel ellenőrzése
        
        Returns:
            (is_earned, current_progress_value)
        """
        condition_type = badge_type.condition_type
        config = badge_type.condition_config
        
        try:
            if condition_type == "transaction_count":
                return await self._check_transaction_count(user_id, config)
            elif condition_type == "spending_milestone":
                return await self._check_spending_milestone(user_id, config)
            elif condition_type == "saving_milestone":
                return await self._check_saving_milestone(user_id, config)
            elif condition_type == "knowledge_lessons":
                return await self._check_knowledge_lessons(user_id, config)
            elif condition_type == "knowledge_streak":
                return await self._check_knowledge_streak(user_id, config)
            elif condition_type == "social_posts":
                return await self._check_social_posts(user_id, config)
            elif condition_type == "streak_login":
                return await self._check_login_streak(user_id, config)
            elif condition_type == "milestone_days":
                return await self._check_registration_milestone(user_id, config)
            else:
                logger.warning(f"Unknown badge condition type: {condition_type}")
                return False, 0.0
                
        except Exception as e:
            logger.error(f"Error checking badge condition {condition_type}: {e}")
            return False, 0.0
    
    async def _check_transaction_count(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Tranzakció szám alapú badge ellenőrzése"""
        target_count = config.get("target_count", 0)
        transaction_type = config.get("transaction_type")
        category = config.get("category")
        time_period_days = config.get("time_period_days")
        
        # Query építése
        query = {"user_id": ObjectId(user_id)}
        
        if transaction_type:
            query["type"] = transaction_type
        
        if category:
            query["kategoria"] = category
        
        if time_period_days:
            start_date = (datetime.now() - timedelta(days=time_period_days)).strftime("%Y-%m-%d")
            query["date"] = {"$gte": start_date}
        
        current_count = await Transaction.find(query).count()
        
        return current_count >= target_count, current_count
    
    async def _check_spending_milestone(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Kiadási mérföldkő ellenőrzése"""
        target_amount = config.get("target_amount", 0)
        time_period_days = config.get("time_period_days")
        
        query = {
            "user_id": ObjectId(user_id),
            "amount": {"$lt": 0}  # Csak kiadások
        }
        
        if time_period_days:
            start_date = (datetime.now() - timedelta(days=time_period_days)).strftime("%Y-%m-%d")
            query["date"] = {"$gte": start_date}
        
        transactions = await Transaction.find(query).to_list()
        total_spent = abs(sum(t.amount for t in transactions))
        
        return total_spent >= target_amount, total_spent
    
    async def _check_saving_milestone(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Megtakarítási mérföldkő ellenőrzése"""
        target_amount = config.get("target_amount", 0)
        account_type = config.get("account_type", "megtakaritas")
        
        # Itt a számla egyenlegeket kellene lekérdezni
        # Egyszerűsített változat: megtakarítási számlára befizetések
        query = {
            "user_id": ObjectId(user_id),
            "main_account": account_type,
            "amount": {"$gt": 0}  # Pozitív összegek (befizetések)
        }
        
        transactions = await Transaction.find(query).to_list()
        total_saved = sum(t.amount for t in transactions)
        
        return total_saved >= target_amount, total_saved
    
    async def _check_knowledge_lessons(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Tudásbeli lecke teljesítés ellenőrzése"""
        target_lessons = config.get("target_lessons", 0)
        min_quiz_score = config.get("min_quiz_score", 0)
        
        user_progress = await UserProgress.find_one({"user_id": ObjectId(user_id)})
        if not user_progress:
            return False, 0
        
        # Teljesített leckék számolása
        completed_lessons = [
            comp for comp in user_progress.completed_lessons
            if comp.pages_completed >= comp.total_pages and
               (comp.best_quiz_score is None or comp.best_quiz_score >= min_quiz_score)
        ]
        
        current_count = len(completed_lessons)
        return current_count >= target_lessons, current_count
    
    async def _check_knowledge_streak(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Tudásbeli sorozat ellenőrzése"""
        target_streak = config.get("target_streak", 0)
        
        user_progress = await UserProgress.find_one({"user_id": ObjectId(user_id)})
        if not user_progress:
            return False, 0
        
        current_streak = user_progress.current_streak
        return current_streak >= target_streak, current_streak
    
    async def _check_social_posts(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Közösségi poszt ellenőrzése"""
        target_posts = config.get("target_posts", 0)
        time_period_days = config.get("time_period_days")
        
        query = {"user_id": ObjectId(user_id)}
        
        if time_period_days:
            start_date = datetime.now() - timedelta(days=time_period_days)
            query["created_at"] = {"$gte": start_date}
        
        current_count = await ForumPostDocument.find(query).count()
        return current_count >= target_posts, current_count
    
    async def _check_login_streak(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Bejelentkezési sorozat ellenőrzése (egyszerűsített)"""
        target_streak = config.get("target_streak", 0)
        
        # Itt egy login_history táblát kellene használni
        # Egyszerűsített változat: knowledge streak alapján
        user_progress = await UserProgress.find_one({"user_id": ObjectId(user_id)})
        if not user_progress:
            return False, 0
        
        # Ideiglenesen a knowledge streak-et használjuk
        current_streak = user_progress.current_streak
        return current_streak >= target_streak, current_streak
    
    async def _check_registration_milestone(self, user_id: str, config: Dict[str, Any]) -> tuple[bool, float]:
        """Regisztrációs mérföldkő ellenőrzése"""
        target_days = config.get("target_days", 0)
        
        user = await UserDocument.get(ObjectId(user_id))
        if not user:
            return False, 0
        
        days_since_registration = (datetime.now() - user.registration_date).days
        return days_since_registration >= target_days, days_since_registration
    
    async def _award_badge(self, user_id: str, badge_type: BadgeType, context: Dict[str, Any] = None) -> Optional[BadgeEarnedEvent]:
        """Badge odaítélése"""
        try:
            # Meglévő badge ellenőrzése szintes badge-ek esetén
            existing_badge = None
            if badge_type.has_levels:
                existing_badge = await UserBadge.find_one({
                    "user_id": ObjectId(user_id),
                    "badge_code": badge_type.code
                })
            
            if existing_badge and badge_type.has_levels:
                # Szint növelése
                if existing_badge.level < (badge_type.max_level or 99):
                    existing_badge.level += 1
                    existing_badge.earned_at = datetime.utcnow()
                    existing_badge.context_data = context or {}
                    await existing_badge.save()
                    
                    return BadgeEarnedEvent(
                        user_id=user_id,
                        badge_code=badge_type.code,
                        badge_name=badge_type.name,
                        badge_icon=badge_type.icon,
                        badge_rarity=badge_type.rarity,
                        points_earned=badge_type.points,
                        level=existing_badge.level,
                        is_new_badge=False
                    )
            else:
                # Új badge létrehozása
                new_badge = UserBadge(
                    user_id=PydanticObjectId(user_id),
                    badge_code=badge_type.code,
                    context_data=context or {}
                )
                await new_badge.insert()
                
                return BadgeEarnedEvent(
                    user_id=user_id,
                    badge_code=badge_type.code,
                    badge_name=badge_type.name,
                    badge_icon=badge_type.icon,
                    badge_rarity=badge_type.rarity,
                    points_earned=badge_type.points,
                    level=1,
                    is_new_badge=True
                )
            
        except Exception as e:
            logger.error(f"Error awarding badge {badge_type.code} to user {user_id}: {e}")
            return None
    
    async def _update_badge_progress(self, user_id: str, badge_type: BadgeType, current_value: float):
        """Badge haladás frissítése"""
        try:
            target_value = badge_type.condition_config.get("target_count", 
                          badge_type.condition_config.get("target_amount",
                          badge_type.condition_config.get("target_lessons", 1)))
            
            progress_percentage = min(100.0, (current_value / target_value) * 100)
            
            # Meglévő haladás keresése
            existing_progress = await BadgeProgress.find_one({
                "user_id": ObjectId(user_id),
                "badge_code": badge_type.code
            })
            
            if existing_progress:
                existing_progress.current_value = current_value
                existing_progress.progress_percentage = progress_percentage
                existing_progress.last_updated = datetime.utcnow()
                await existing_progress.save()
            else:
                new_progress = BadgeProgress(
                    user_id=PydanticObjectId(user_id),
                    badge_code=badge_type.code,
                    current_value=current_value,
                    target_value=target_value,
                    progress_percentage=progress_percentage
                )
                await new_progress.insert()
                
        except Exception as e:
            logger.error(f"Error updating badge progress for {badge_type.code}: {e}")
    
    async def get_user_badges(self, user_id: str, category: Optional[BadgeCategory] = None) -> List[Dict[str, Any]]:
        """Felhasználó badge-einek lekérése badge típus adatokkal"""
        try:
            # User badge-ek lekérése
            query = {"user_id": ObjectId(user_id)}
            user_badges = await UserBadge.find(query).sort(-UserBadge.earned_at).to_list()
            
            # Badge típusok lekérése
            badge_codes = [ub.badge_code for ub in user_badges]
            badge_types = await BadgeType.find({"code": {"$in": badge_codes}}).to_list()
            badge_type_dict = {bt.code: bt for bt in badge_types}
            
            # Kategória szűrés
            if category:
                badge_types = [bt for bt in badge_types if bt.category == category]
                user_badges = [ub for ub in user_badges if ub.badge_code in [bt.code for bt in badge_types]]
            
            # Összekapcsolás
            result = []
            for user_badge in user_badges:
                badge_type = badge_type_dict.get(user_badge.badge_code)
                if badge_type:
                    result.append({
                        "user_badge": user_badge,
                        "badge_type": badge_type
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user badges: {e}")
            return []
    
    async def get_user_badge_stats(self, user_id: str) -> Dict[str, Any]:
        """Felhasználó badge statisztikáinak lekérése"""
        try:
            user_badges = await UserBadge.find({"user_id": ObjectId(user_id)}).to_list()
            
            if not user_badges:
                return {
                    "total_badges": 0,
                    "total_points": 0,
                    "badges_by_category": {},
                    "badges_by_rarity": {},
                    "recent_badges": [],
                    "favorite_badges": [],
                    "in_progress_count": 0
                }
            
            # Badge típusok lekérése
            badge_codes = [ub.badge_code for ub in user_badges]
            badge_types = await BadgeType.find({"code": {"$in": badge_codes}}).to_list()
            badge_type_dict = {bt.code: bt for bt in badge_types}
            
            # Statisztikák számítása
            total_points = sum(
                badge_type_dict.get(ub.badge_code, BadgeType()).points * ub.level 
                for ub in user_badges
            )
            
            badges_by_category = {}
            badges_by_rarity = {}
            
            for user_badge in user_badges:
                badge_type = badge_type_dict.get(user_badge.badge_code)
                if badge_type:
                    # Kategória szerint
                    category = badge_type.category.value
                    badges_by_category[category] = badges_by_category.get(category, 0) + 1
                    
                    # Ritkaság szerint
                    rarity = badge_type.rarity.value
                    badges_by_rarity[rarity] = badges_by_rarity.get(rarity, 0) + 1
            
            # Legutóbbi badge-ek (top 5)
            recent_badges = sorted(user_badges, key=lambda x: x.earned_at, reverse=True)[:5]
            
            # Kedvenc badge-ek
            favorite_badges = [ub for ub in user_badges if ub.is_favorite]
            
            # Folyamatban lévő badge-ek száma
            in_progress_count = await BadgeProgress.find({
                "user_id": ObjectId(user_id),
                "progress_percentage": {"$lt": 100}
            }).count()
            
            return {
                "total_badges": len(user_badges),
                "total_points": total_points,
                "badges_by_category": badges_by_category,
                "badges_by_rarity": badges_by_rarity,
                "recent_badges": recent_badges,
                "favorite_badges": favorite_badges,
                "in_progress_count": in_progress_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user badge stats: {e}")
            return {}
    
    async def get_badge_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Felhasználó badge haladásának lekérése"""
        try:
            progress_list = await BadgeProgress.find({
                "user_id": ObjectId(user_id),
                "progress_percentage": {"$lt": 100}
            }).sort(-BadgeProgress.progress_percentage).to_list()
            
            # Badge típusok lekérése
            badge_codes = [bp.badge_code for bp in progress_list]
            badge_types = await BadgeType.find({"code": {"$in": badge_codes}}).to_list()
            badge_type_dict = {bt.code: bt for bt in badge_types}
            
            result = []
            for progress in progress_list:
                badge_type = badge_type_dict.get(progress.badge_code)
                if badge_type:
                    result.append({
                        "progress": progress,
                        "badge_type": badge_type
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting badge progress: {e}")
            return []

# Globális badge service instance
badge_service = BadgeService()