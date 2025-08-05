# app/services/pti_service.py
from typing import List, Dict, Optional, Tuple
from beanie import PydanticObjectId
from datetime import datetime, date, timedelta
import logging
from collections import defaultdict
import math

from app.models.pti import (
    PTIScore, PTIHistory, UserPTISettings, PTIPeriod, RankingScope,
    PTIComponentBreakdown, PTIRankingEntry, PTIRankingResponse
)
from app.models.knowledge import UserProgress, LessonCompletion
from app.models.habit import Habit, HabitLog
from app.models.badge import UserBadge, BadgeType
from app.models.limit import Limit
from app.models.transaction import Transaction
from app.services.limit_service import LimitService
from app.models.user import UserDocument
from app.models.pti_schemas import PTIHistoryResponse, PTIPeriodInfo

logger = logging.getLogger(__name__)

class PTIService:
    """PTI (Pénzügyi Tudatosság Index) számítás és kezelés"""
    
    # PTI súlyok
    LEARNING_WEIGHT = 0.30
    HABIT_WEIGHT = 0.30
    BADGE_WEIGHT = 0.20
    LIMIT_WEIGHT = 0.20
    
    @staticmethod
    def get_period_info(period: PTIPeriod, reference_date: datetime = None):
        """Időszak kulcs generálása"""
        if reference_date is None:
            reference_date = datetime.utcnow()
            
        if period == PTIPeriod.WEEKLY:
            year, week, _ = reference_date.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == PTIPeriod.MONTHLY:
            return reference_date.strftime("%Y-%m")
        elif period == PTIPeriod.YEARLY:
            return str(reference_date.year)
        
        return reference_date.strftime("%Y-%m-%d")
    
    @staticmethod
    def get_period_dates(period: PTIPeriod, period_key: str) -> Tuple[datetime, datetime]:
        """Időszak kezdő és záró dátumának meghatározása"""
        try:
            if period == PTIPeriod.WEEKLY:
                # 2025-W03 formátum
                year, week = period_key.split('-W')
                year = int(year)
                week = int(week)
                
                # Első nap a hét hétfője
                jan4 = datetime(year, 1, 4)  # ISO week szabvány szerint
                week_start = jan4 + timedelta(days=(week - 1) * 7 - jan4.weekday())
                week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                return week_start, week_end
                
            elif period == PTIPeriod.MONTHLY:
                # 2025-01 formátum
                year, month = map(int, period_key.split('-'))
                month_start = datetime(year, month, 1)
                
                if month == 12:
                    month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                else:
                    month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
                
                return month_start, month_end
                
            elif period == PTIPeriod.YEARLY:
                # 2025 formátum
                year = int(period_key)
                year_start = datetime(year, 1, 1)
                year_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
                
                return year_start, year_end
                
        except Exception as e:
            logger.error(f"Error parsing period key {period_key}: {e}")
            # Fallback: aktuális nap
            now = datetime.utcnow()
            return now.replace(hour=0, minute=0, second=0, microsecond=0), \
                   now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    async def calculate_learning_points(user_id: str, start_date: datetime, end_date: datetime) -> float:
        """Tanulási pontok számítása"""
        try:
            user_progress = await UserProgress.find_one(
                UserProgress.user_id == PydanticObjectId(user_id)
            )
            
            if not user_progress:
                return 0.0
            
            # Időszakban teljesített leckék
            period_lessons = [
                lesson for lesson in user_progress.completed_lessons
                if start_date <= lesson.completed_at <= end_date
            ]
            
            if not period_lessons:
                return 0.0
            
            # Pontszámítás
            total_points = 0.0
            for lesson in period_lessons:
                # Alap pont a lecke teljesítéséért
                lesson_points = 10.0
                
                # Kvíz bónusz
                if lesson.quiz_score:
                    if lesson.quiz_score >= 90:
                        lesson_points += 5.0  # Kiváló
                    elif lesson.quiz_score >= 70:
                        lesson_points += 3.0  # Jó
                    elif lesson.quiz_score >= 50:
                        lesson_points += 1.0  # Átlagos
                
                # Első próbálkozás bónusz
                if lesson.quiz_attempts == 1:
                    lesson_points += 2.0
                
                total_points += lesson_points
            
            # Streak bónusz
            if user_progress.current_streak >= 7:
                total_points *= 1.2  # 20% bónusz 7+ napos streak esetén
            elif user_progress.current_streak >= 3:
                total_points *= 1.1  # 10% bónusz 3+ napos streak esetén
            
            # Napi kihívás bónusz
            if user_progress.daily_challenge_streak >= 7:
                total_points += 20.0
            elif user_progress.daily_challenge_streak >= 3:
                total_points += 10.0
            
            return min(total_points, 100.0)  # Maximum 100 pont
            
        except Exception as e:
            logger.error(f"Error calculating learning points for user {user_id}: {e}")
            return 0.0
    
    @staticmethod
    async def calculate_habit_score(user_id: str, start_date: datetime, end_date: datetime) -> float:
        """Szokáskövetés pontszám számítása"""
        try:
            # Aktív szokások lekérése
            habits = await Habit.find(
                Habit.user_id == PydanticObjectId(user_id),
                Habit.is_active == True
            ).to_list()
            
            if not habits:
                return 0.0
            
            total_score = 0.0
            habit_count = len(habits)
            
            for habit in habits:
                # Időszakban való teljesítések lekérése
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                logs = await HabitLog.find(
                    HabitLog.user_id == PydanticObjectId(user_id),
                    HabitLog.habit_id == habit.id,
                    HabitLog.date >= start_date_str,
                    HabitLog.date <= end_date_str
                ).to_list()
                
                if not logs:
                    continue
                
                # Teljesítési arány
                total_days = len(logs)
                completed_days = sum(1 for log in logs if log.completed)
                completion_rate = completed_days / total_days if total_days > 0 else 0
                
                # Alap pontszám (0-20 pont szokásonként)
                habit_score = completion_rate * 20
                
                # Streak bónusz
                if habit.streak_count >= 30:
                    habit_score *= 1.5  # 50% bónusz 30+ napos streak
                elif habit.streak_count >= 14:
                    habit_score *= 1.3  # 30% bónusz 14+ napos streak
                elif habit.streak_count >= 7:
                    habit_score *= 1.2  # 20% bónusz 7+ napos streak
                elif habit.streak_count >= 3:
                    habit_score *= 1.1  # 10% bónusz 3+ napos streak
                
                habit_score = min(habit_score, 25.0)

                # Célteljesítés bónusz (ha van cél beállítva)
                if habit.has_goal and habit.target_value:
                    # Itt lehetne egy célteljesítési számítást csinálni
                    # Egyszerűsítve: ha 90%+ teljesítési arány, akkor +2 pont
                    if completion_rate >= 0.9:
                        habit_score += 2.0
                    elif completion_rate >= 0.8:
                        habit_score += 1.0

                    habit_score = min(habit_score, 25.0)
                
                total_score += habit_score
            
            # Átlagolás és normalizálás
            if habit_count > 0:
                average_score = total_score / habit_count
                # Több szokás esetén bónusz (max 4 szokás után már nem növekszik)
                multiplier = min(1.0 + (habit_count - 1) * 0.1, 1.3)
                return min(average_score * multiplier, 100.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating habit score for user {user_id}: {e}")
            return 0.0
    
    @staticmethod
    async def calculate_badge_score(user_id: str, start_date: datetime, end_date: datetime) -> float:
        """Badge pontszám számítása"""
        try:
            # Időszakban szerzett badge-ek
            period_badges = await UserBadge.find(
                UserBadge.user_id == PydanticObjectId(user_id),
                UserBadge.earned_at >= start_date,
                UserBadge.earned_at <= end_date
            ).to_list()
            
            if not period_badges:
                # Ha nem szerzett új badge-et, de vannak meglévő badge-ei
                existing_badges = await UserBadge.find(
                    UserBadge.user_id == PydanticObjectId(user_id)
                ).count()
                # Kis alappont meglévő badge-ekért (max 10 pont)
                return min(existing_badges * 0.5, 10.0)
            
            total_score = 0.0
            
            for user_badge in period_badges:
                # Badge típus lekérése a pontértékért
                badge_type = await BadgeType.find_one(
                    BadgeType.code == user_badge.badge_code
                )
                
                if badge_type:
                    # Alap pontszám
                    badge_points = badge_type.points
                    
                    # Ritkasági szorzó
                    rarity_multipliers = {
                        "common": 1.0,
                        "uncommon": 1.2,
                        "rare": 1.5,
                        "epic": 2.0,
                        "legendary": 3.0
                    }
                    
                    multiplier = rarity_multipliers.get(badge_type.rarity.value, 1.0)
                    badge_points *= multiplier
                    
                    # Szint szorzó (ha van szintje)
                    if badge_type.has_levels and user_badge.level > 1:
                        badge_points *= (1.0 + (user_badge.level - 1) * 0.2)
                    
                    total_score += badge_points
                else:
                    # Ha nem találjuk a badge típust, alap pont
                    total_score += 5.0
            
            # Kombinációs bónusz (több különböző kategóriájú badge)
            badge_categories = set()
            for user_badge in period_badges:
                badge_type = await BadgeType.find_one(
                    BadgeType.code == user_badge.badge_code
                )
                if badge_type:
                    badge_categories.add(badge_type.category)
            
            if len(badge_categories) >= 3:
                total_score *= 1.3  # 30% bónusz 3+ kategóriáért
            elif len(badge_categories) >= 2:
                total_score *= 1.2  # 20% bónusz 2+ kategóriáért
            
            return min(total_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating badge score for user {user_id}: {e}")
            return 0.0
    
    @staticmethod
    async def calculate_limit_score(user_id: str, start_date: datetime, end_date: datetime) -> float:
        """Limit betartási pontszám számítása"""
        try:
            # Aktív limitek lekérése
            limits = await Limit.find(
                Limit.user_id == PydanticObjectId(user_id),
                Limit.is_active == True
            ).to_list()
            
            if not limits:
                return 0.0  # Alappontszám ha nincs limit beállítva
            
            total_score = 0.0
            limit_scores = []
            
            for limit in limits:
                # Időszakbeli kiadások lekérése
                current_spending = await LimitService._get_current_spending(user_id, limit)
                
                # Limit betartás mértéke
                if current_spending <= limit.amount:
                    # Betartotta a limitet
                    usage_percentage = (current_spending / limit.amount) * 100
                    
                    if usage_percentage <= 50:
                        limit_score = 30.0  # Kiváló - limit felét sem használta fel
                    elif usage_percentage <= 70:
                        limit_score = 25.0  # Jó - 50-70% között
                    elif usage_percentage <= 85:
                        limit_score = 20.0  # Megfelelő - 70-85% között
                    else:
                        limit_score = 15.0  # Közel a limithez - 85-100% között
                else:
                    # Túllépte a limitet
                    overspend_percentage = ((current_spending - limit.amount) / limit.amount) * 100
                    
                    if overspend_percentage <= 10:
                        limit_score = 8.0   # Kis túllépés
                    elif overspend_percentage <= 25:
                        limit_score = 5.0   # Közepes túllépés
                    else:
                        limit_score = 0.0   # Nagy túllépés
                
                limit_scores.append(limit_score)
            
            # Átlagos limit betartási pontszám
            if limit_scores:
                avg_score = sum(limit_scores) / len(limit_scores)
                
                # Bónusz ha minden limitet betartott
                if all(score >= 15.0 for score in limit_scores):
                    avg_score *= 1.2  # 20% bónusz
                
                # Több limit esetén kis bónusz (komolyabb pénzügyi tudatosság)
                if len(limit_scores) >= 3:
                    avg_score *= 1.1  # 10% bónusz 3+ limitért
                
                return min(avg_score, 100.0)
            
            return 0.0  # Alappontszám
            
        except Exception as e:
            logger.error(f"Error calculating limit score for user {user_id}: {e}")
            return 0.0  # Alappontszám hiba esetén
    
    @staticmethod
    async def calculate_pti_score(
        user_id: str, 
        period: PTIPeriod = PTIPeriod.WEEKLY,
        reference_date: datetime = None
    ) -> PTIComponentBreakdown:
        """PTI pontszám számítása egy adott időszakra"""
        try:
            if reference_date is None:
                reference_date = datetime.utcnow()
            
            period_key = PTIService.get_period_key(period, reference_date)
            start_date, end_date = PTIService.get_period_dates(period, period_key)
            
            # Komponensek számítása párhuzamosan
            learning_points = await PTIService.calculate_learning_points(user_id, start_date, end_date)
            habit_score = await PTIService.calculate_habit_score(user_id, start_date, end_date)
            badge_score = await PTIService.calculate_badge_score(user_id, start_date, end_date)
            limit_score = await PTIService.calculate_limit_score(user_id, start_date, end_date)
            
            # Súlyozott összeg számítása
            learning_contribution = learning_points * PTIService.LEARNING_WEIGHT
            habit_contribution = habit_score * PTIService.HABIT_WEIGHT
            badge_contribution = badge_score * PTIService.BADGE_WEIGHT
            limit_contribution = limit_score * PTIService.LIMIT_WEIGHT
            
            total_pti = (learning_contribution + habit_contribution + 
                        badge_contribution + limit_contribution)
            
            return PTIComponentBreakdown(
                learning_points=learning_points,
                learning_contribution=learning_contribution,
                habit_score=habit_score,
                habit_contribution=habit_contribution,
                badge_score=badge_score,
                badge_contribution=badge_contribution,
                limit_score=limit_score,
                limit_contribution=limit_contribution,
                total_pti=total_pti
            )
            
        except Exception as e:
            logger.error(f"Error calculating PTI score for user {user_id}: {e}")
            # Fallback: nulla értékek
            return PTIComponentBreakdown(
                learning_points=0.0,
                learning_contribution=0.0,
                habit_score=0.0,
                habit_contribution=0.0,
                badge_score=0.0,
                badge_contribution=0.0,
                limit_score=0.0,
                limit_contribution=0.0,
                total_pti=0.0
            )
    
    @staticmethod
    async def save_pti_score(
        user_id: str,
        period: PTIPeriod,
        components: PTIComponentBreakdown,
        reference_date: datetime = None
    ) -> PTIScore:
        """PTI pontszám mentése az adatbázisba"""
        try:
            if reference_date is None:
                reference_date = datetime.utcnow()
            
            period_key = PTIService.get_period_key(period, reference_date)
            
            # Meglévő bejegyzés keresése
            existing_score = await PTIScore.find_one(
                PTIScore.user_id == PydanticObjectId(user_id),
                PTIScore.period == period,
                PTIScore.period_key == period_key
            )
            
            # User beállítások lekérése anonimizáláshoz
            user_settings = await UserPTISettings.find_one(
                UserPTISettings.user_id == PydanticObjectId(user_id)
            )
            is_anonymous = user_settings.is_anonymous if user_settings else False
            
            if existing_score:
                # Frissítés
                existing_score.learning_points = components.learning_points
                existing_score.habit_score = components.habit_score
                existing_score.badge_score = components.badge_score
                existing_score.limit_score = components.limit_score
                existing_score.raw_pti = components.total_pti
                existing_score.normalized_pti = min(components.total_pti, 100.0)
                existing_score.is_anonymous = is_anonymous
                existing_score.calculated_at = datetime.utcnow()
                
                await existing_score.save()
                return existing_score
            else:
                # Új bejegyzés
                pti_score = PTIScore(
                    user_id=PydanticObjectId(user_id),
                    period=period,
                    period_key=period_key,
                    learning_points=components.learning_points,
                    habit_score=components.habit_score,
                    badge_score=components.badge_score,
                    limit_score=components.limit_score,
                    raw_pti=components.total_pti,
                    normalized_pti=min(components.total_pti, 100.0),
                    is_anonymous=is_anonymous
                )
                
                await pti_score.insert()
                return pti_score
                
        except Exception as e:
            logger.error(f"Error saving PTI score for user {user_id}: {e}")
            raise e
    
    @staticmethod
    async def update_rankings(period: PTIPeriod, period_key: str) -> None:
        """Rangsorok frissítése egy adott időszakra"""
        try:
            # Összes PTI pontszám lekérése az időszakra, csökkenő sorrendben
            all_scores = await PTIScore.find(
                PTIScore.period == period,
                PTIScore.period_key == period_key
            ).sort([("normalized_pti", -1)]).to_list()
            
            total_users = len(all_scores)
            
            # Rangsorok frissítése
            for rank, score in enumerate(all_scores, 1):
                score.global_rank = rank
                score.total_users = total_users
                await score.save()
                
        except Exception as e:
            logger.error(f"Error updating rankings for {period} {period_key}: {e}")
    
    @staticmethod
    async def get_user_ranking(
        user_id: str,
        period: PTIPeriod,
        scope: RankingScope = RankingScope.GLOBAL,
        limit: int = 50,
        offset: int = 0
    ) -> PTIRankingResponse:
        """Felhasználó ranglistájának lekérése"""
        try:
            reference_date = datetime.utcnow()
            period_key = PTIService.get_period_key(period, reference_date)
            
            # Alap query
            base_query = {
                "period": period,
                "period_key": period_key
            }
            
            # Scope szerinti szűrés
            if scope == RankingScope.FRIENDS:
                # Barátok lekérése (követett felhasználók)
                from app.models.forum_models import FollowDocument
                follows = await FollowDocument.find(
                    FollowDocument.follower_id == PydanticObjectId(user_id)
                ).to_list()
                
                friend_ids = [follow.following_id for follow in follows]
                friend_ids.append(PydanticObjectId(user_id))  # Saját magát is tartalmazza
                
                base_query["user_id"] = {"$in": friend_ids}
            elif scope == RankingScope.PRIVATE:
                # Csak saját adat
                base_query["user_id"] = PydanticObjectId(user_id)
            
            # Ranglista lekérése
            total_scores = await PTIScore.find(base_query).count()
            ranking_scores = await PTIScore.find(base_query)\
                .sort([("normalized_pti", -1)])\
                .limit(limit)\
                .skip(offset)\
                .to_list()
            
            # Felhasználó saját pozíciójának keresése
            user_score = await PTIScore.find_one(
                PTIScore.user_id == PydanticObjectId(user_id),
                PTIScore.period == period,
                PTIScore.period_key == period_key
            )
            
            user_rank = None
            user_pti = None
            if user_score:
                # Rangsor számítása
                better_scores = await PTIScore.find({
                    **base_query,
                    "normalized_pti": {"$gt": user_score.normalized_pti}
                }).count()
                user_rank = better_scores + 1
                user_pti = user_score.normalized_pti
            
            # Ranking bejegyzések összeállítása
            rankings = []
            for rank, score in enumerate(ranking_scores, offset + 1):
                # Felhasználó adatok lekérése
                user = await UserDocument.get(score.user_id)
                user_settings = await UserPTISettings.find_one(
                    UserPTISettings.user_id == score.user_id
                )
                
                # Komponensek összeállítása
                components = PTIComponentBreakdown(
                    learning_points=score.learning_points,
                    learning_contribution=score.learning_points * PTIService.LEARNING_WEIGHT,
                    habit_score=score.habit_score,
                    habit_contribution=score.habit_score * PTIService.HABIT_WEIGHT,
                    badge_score=score.badge_score,
                    badge_contribution=score.badge_score * PTIService.BADGE_WEIGHT,
                    limit_score=score.limit_score,
                    limit_contribution=score.limit_score * PTIService.LIMIT_WEIGHT,
                    total_pti=score.normalized_pti
                )
                
                # Anonimizálás kezelése
                username = None
                anonymous_name = None
                is_anonymous = score.is_anonymous
                
                if is_anonymous and user_settings and user_settings.anonymous_name:
                    anonymous_name = user_settings.anonymous_name
                elif not is_anonymous:
                    username = user.username if user else "Ismeretlen"
                
                rankings.append(PTIRankingEntry(
                    rank=rank,
                    user_id=str(score.user_id),
                    username=username,
                    anonymous_name=anonymous_name,
                    is_anonymous=is_anonymous,
                    pti_score=score.normalized_pti,
                    components=components,
                    is_current_user=(str(score.user_id) == user_id)
                ))
            
            return PTIRankingResponse(
                period=period,
                period_key=period_key,
                scope=scope,
                rankings=rankings,
                user_rank=user_rank,
                user_score=user_pti,
                total_participants=total_scores,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting user ranking: {e}")
            return PTIRankingResponse(
                period=period,
                period_key=period_key,
                scope=scope,
                rankings=[],
                total_participants=0,
                generated_at=datetime.utcnow()
            )
    
    @staticmethod
    async def calculate_and_save_all_periods(user_id: str) -> Dict[str, PTIComponentBreakdown]:
        """Felhasználó PTI számítása és mentése minden időszakra"""
        try:
            results = {}
            reference_date = datetime.utcnow()
            
            for period in [PTIPeriod.WEEKLY, PTIPeriod.MONTHLY, PTIPeriod.YEARLY]:
                components = await PTIService.calculate_pti_score(user_id, period, reference_date)
                await PTIService.save_pti_score(user_id, period, components, reference_date)
                results[period.value] = components
                
                # Rangsorok frissítése
                period_key = PTIService.get_period_key(period, reference_date)
                await PTIService.update_rankings(period, period_key)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating all periods for user {user_id}: {e}")
            return {}
    
    @staticmethod
    async def get_improvement_suggestions(user_id: str) -> List[str]:
        """Fejlesztési javaslatok generálása a PTI komponensek alapján"""
        try:
            suggestions = []
            
            # Aktuális PTI komponensek lekérése
            components = await PTIService.calculate_pti_score(user_id, PTIPeriod.WEEKLY)
            
            # Tanulási javaslatok
            if components.learning_points < 20:
                suggestions.append("📚 Teljesíts legalább 2-3 leckét hetente a tanulási pontok növeléséhez")
                suggestions.append("🎯 Próbáld meg elsőre teljesíteni a kvízeket a extra pontokért")
            
            # Szokás javaslatok
            if components.habit_score < 30:
                suggestions.append("💪 Hozz létre új pénzügyi szokásokat és kövesd őket naponta")
                suggestions.append("🔥 Építs fel legalább 7 napos streak-et a bónusz pontokért")
            
            # Badge javaslatok
            if components.badge_score < 15:
                suggestions.append("🏆 Szerezz új badge-eket különböző kategóriákban")
                suggestions.append("⭐ Törekedj magasabb szintű badge-ekre a több pontért")
            
            # Limit javaslatok
            if components.limit_score < 40:
                suggestions.append("📊 Állíts be és tartsd be a kiadási limiteket")
                suggestions.append("💰 Próbáld meg a limiteid 80%-a alatt maradni")
            
            # Általános javaslatok
            if components.total_pti < 50:
                suggestions.append("🚀 Fokozd az aktivitásod minden területen az összesített PTI javításához")
            
            return suggestions[:5]  # Maximum 5 javaslat
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions for user {user_id}: {e}")
            return ["📈 Folytasd a pénzügyi tudatosság fejlesztését minden területen!"]
        

    # Új metódusok hozzáadása a PTIService osztályhoz

    @staticmethod
    def get_period_info(period: PTIPeriod, reference_date: datetime = None) -> 'PTIPeriodInfo':
        """Aktuális időszak információk lekérése"""
        if reference_date is None:
            reference_date = datetime.utcnow()
        
        period_key = PTIService.get_period_key(period, reference_date)
        start_date, end_date = PTIService.get_period_dates(period, period_key)
        
        # Hátralévő napok számítása
        days_remaining = max(0, (end_date - reference_date).days)
        
        # Időszak haladásának számítása
        total_duration = (end_date - start_date).total_seconds()
        elapsed_duration = (reference_date - start_date).total_seconds()
        progress_percentage = min((elapsed_duration / total_duration) * 100, 100) if total_duration > 0 else 0
        
        from app.models.pti_schemas import PTIPeriodInfo
        return PTIPeriodInfo(
            period=period,
            period_key=period_key,
            period_start=start_date,
            period_end=end_date,
            days_remaining=days_remaining,
            progress_percentage=progress_percentage
        )

    @staticmethod
    async def get_user_pti_history(
        user_id: str, 
        period: PTIPeriod, 
        limit: int = 10, 
        offset: int = 0
    ):
        """Felhasználó PTI történetének lekérése"""
        try:
            from app.models.pti_schemas import PTIHistoryResponse, PTIHistoryEntry
            
            # Összes PTI score lekérése az adott időszakra, időrend szerint
            historical_scores = await PTIScore.find(
                PTIScore.user_id == PydanticObjectId(user_id),
                PTIScore.period == period
            ).sort([("period_key", -1)]).limit(limit).skip(offset).to_list()
            
            # Összes bejegyzés számának lekérése
            total_entries = await PTIScore.find(
                PTIScore.user_id == PydanticObjectId(user_id),
                PTIScore.period == period
            ).count()
            
            # History bejegyzések összeállítása
            history_entries = []
            current_entry = None
            current_period_key = PTIService.get_period_key(period)
            
            for score in historical_scores:
                start_date, end_date = PTIService.get_period_dates(period, score.period_key)
                
                components = PTIComponentBreakdown(
                    learning_points=score.learning_points,
                    learning_contribution=score.learning_points * PTIService.LEARNING_WEIGHT,
                    habit_score=score.habit_score,
                    habit_contribution=score.habit_score * PTIService.HABIT_WEIGHT,
                    badge_score=score.badge_score,
                    badge_contribution=score.badge_score * PTIService.BADGE_WEIGHT,
                    limit_score=score.limit_score,
                    limit_contribution=score.limit_score * PTIService.LIMIT_WEIGHT,
                    total_pti=score.normalized_pti
                )
                
                entry = PTIHistoryEntry(
                    period_key=score.period_key,
                    period_start=start_date,
                    period_end=end_date,
                    pti_score=score.normalized_pti,
                    components=components,
                    rank=score.global_rank,
                    total_users=score.total_users,
                    calculated_at=score.calculated_at
                )
                
                if score.period_key == current_period_key:
                    current_entry = entry
                else:
                    history_entries.append(entry)
            
            # Ha nincs aktuális időszak adat, számítsuk ki
            if current_entry is None:
                current_components = await PTIService.calculate_pti_score(user_id, period)
                start_date, end_date = PTIService.get_period_dates(period, current_period_key)
                
                current_entry = PTIHistoryEntry(
                    period_key=current_period_key,
                    period_start=start_date,
                    period_end=end_date,
                    pti_score=current_components.total_pti,
                    components=current_components,
                    rank=None,
                    total_users=None,
                    calculated_at=datetime.utcnow()
                )
            
            return PTIHistoryResponse(
                period=period,
                entries=history_entries,
                current_period=current_entry,
                total_entries=total_entries
            )
            
        except Exception as e:
            logger.error(f"Error getting PTI history for user {user_id}: {e}")
            return PTIHistoryResponse(
                period=period,
                entries=[],
                current_period=None,
                total_entries=0
            )
        
    @staticmethod
    def get_period_key(period: PTIPeriod, reference_date: datetime = None) -> str:
        """Időszak kulcs generálása - alias a get_period_info metódushoz"""
        if reference_date is None:
            reference_date = datetime.utcnow()
            
        if period == PTIPeriod.WEEKLY:
            year, week, _ = reference_date.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == PTIPeriod.MONTHLY:
            return reference_date.strftime("%Y-%m")
        elif period == PTIPeriod.YEARLY:
            return str(reference_date.year)
        
        return reference_date.strftime("%Y-%m-%d")