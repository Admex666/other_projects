# app/services/habit_service.py
from typing import List, Dict, Optional, Tuple
from beanie import PydanticObjectId
from datetime import datetime, date, timedelta
import logging
from collections import defaultdict

from app.models.habit import Habit, HabitLog, TrackingType, FrequencyType, HabitCategory
from app.models.habit_schemas import (
    HabitProgressStats, HabitWeeklyStats, HabitMonthlyStats,
    UserHabitOverview
)

logger = logging.getLogger(__name__)

class HabitService:
    """Szokások kezelését végző szolgáltatás"""
    
    @staticmethod
    async def create_habit_from_predefined(
        user_id: str,
        category: HabitCategory,
        habit_data: Dict
    ) -> Habit:
        """Előre definiált szokás létrehozása"""
        try:
            habit = Habit(
                user_id=PydanticObjectId(user_id),
                title=habit_data["title"],
                description=habit_data["description"],
                category=category,
                tracking_type=TrackingType(habit_data["tracking_type"]),
                frequency=FrequencyType(habit_data["frequency"])
            )
            
            await habit.insert()
            return habit
            
        except Exception as e:
            logger.error(f"Error creating predefined habit: {e}")
            raise e
    
    @staticmethod
    async def log_habit_completion(
        user_id: str,
        habit_id: str,
        completed: bool,
        value: Optional[float] = None,
        notes: Optional[str] = None,
        log_date: Optional[str] = None
    ) -> HabitLog:
        """Szokás teljesítésének rögzítése"""
        try:
            if log_date is None:
                log_date = datetime.now().date().strftime("%Y-%m-%d")
            
            # Ellenőrizzük, hogy létezik-e már bejegyzés erre a napra
            existing_log = await HabitLog.find_one({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": log_date
            })
            
            if existing_log:
                # Frissítjük a meglévő bejegyzést
                existing_log.completed = completed
                existing_log.value = value
                existing_log.notes = notes
                await existing_log.save()
                habit_log = existing_log
            else:
                # Új bejegyzés létrehozása
                habit_log = HabitLog(
                    user_id=PydanticObjectId(user_id),
                    habit_id=PydanticObjectId(habit_id),
                    date=log_date,
                    completed=completed,
                    value=value,
                    notes=notes
                )
                await habit_log.insert()
            
            # Streak frissítése
            await HabitService.update_habit_streak(habit_id, user_id)
            
            return habit_log
            
        except Exception as e:
            logger.error(f"Error logging habit completion: {e}")
            raise e
    
    @staticmethod
    async def update_habit_streak(habit_id: str, user_id: str) -> None:
        """Szokás streak számítás frissítése"""
        try:
            habit = await Habit.get(PydanticObjectId(habit_id))
            if not habit or str(habit.user_id) != user_id:
                return
            
            # Utolsó 60 nap logjai (biztonság kedvéért hosszabb időszak)
            sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            logs = await HabitLog.find({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": {"$gte": sixty_days_ago}
            }).sort("date", -1).to_list()
            
            if not logs:
                habit.streak_count = 0
                habit.best_streak = 0
                habit.last_completed = None
                await habit.save()
                return
            
            # Jelenlegi streak számítása
            current_streak = 0
            today = datetime.now().date()
            
            # Rendezzük a logokat dátum szerint csökkenő sorrendbe
            logs_by_date = {log.date: log for log in logs}
            
            # Kezdjük a mai nappal (vagy a legutóbbi nappal)
            check_date = today
            
            while True:
                date_str = check_date.strftime("%Y-%m-%d")
                
                if date_str in logs_by_date and logs_by_date[date_str].completed:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
                
                # Végtelen ciklus elkerülése
                if current_streak > 365:
                    break
            
            # Legjobb streak keresése
            best_streak = 0
            temp_streak = 0
            
            # Időrendben végigmegyünk a logokon
            sorted_dates = sorted(logs_by_date.keys())
            prev_date = None
            
            for date_str in sorted_dates:
                current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                log = logs_by_date[date_str]
                
                if log.completed:
                    # Ha ez az első nap vagy egymást követő napok
                    if prev_date is None or (current_date - prev_date).days == 1:
                        temp_streak += 1
                    else:
                        # Megszakadt a sorozat
                        temp_streak = 1
                    
                    best_streak = max(best_streak, temp_streak)
                    prev_date = current_date
                else:
                    temp_streak = 0
                    prev_date = None
            
            # Utoljára teljesített dátum keresése
            last_completed = None
            for log in sorted(logs, key=lambda x: x.date, reverse=True):
                if log.completed:
                    last_completed = log.date
                    break
            
            # Habit frissítése
            habit.streak_count = current_streak
            habit.best_streak = best_streak
            habit.last_completed = last_completed
            await habit.save()
            
        except Exception as e:
            logger.error(f"Error updating habit streak: {e}")
    
    @staticmethod
    async def get_habit_progress_stats(
        habit_id: str,
        user_id: str,
        days: int = 30
    ) -> HabitProgressStats:
        """Szokás haladási statisztikák számítása"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            logs = await HabitLog.find({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": {"$gte": start_date}
            }).to_list()
            
            habit = await Habit.get(PydanticObjectId(habit_id))
            
            total_days = len(logs)
            completed_days = sum(1 for log in logs if log.completed)
            completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
            
            # Numerikus szokásoknál átlagérték számítása
            average_value = None
            if habit and habit.tracking_type == TrackingType.NUMERIC:
                values = [log.value for log in logs if log.value is not None and log.completed]
                if values:
                    average_value = sum(values) / len(values)
            
            return HabitProgressStats(
                total_days=total_days,
                completed_days=completed_days,
                completion_rate=completion_rate,
                current_streak=habit.streak_count if habit else 0,
                best_streak=habit.best_streak if habit else 0,
                average_value=average_value
            )
            
        except Exception as e:
            logger.error(f"Error calculating habit progress stats: {e}")
            return HabitProgressStats(
                total_days=0,
                completed_days=0,
                completion_rate=0,
                current_streak=0,
                best_streak=0
            )
    
    @staticmethod
    async def get_weekly_stats(
        habit_id: str,
        user_id: str,
        weeks: int = 8
    ) -> List[HabitWeeklyStats]:
        """Heti statisztikák számítása"""
        try:
            habit = await Habit.get(PydanticObjectId(habit_id))
            if not habit:
                return []
            
            # Utolsó N hét kezdete
            today = datetime.now().date()
            start_date = today - timedelta(weeks=weeks)
            
            logs = await HabitLog.find({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": {"$gte": start_date.strftime("%Y-%m-%d")}
            }).to_list()
            
            # Hetek szerinti csoportosítás
            weekly_data = defaultdict(list)
            
            for log in logs:
                log_date = datetime.strptime(log.date, "%Y-%m-%d").date()
                # Hét kezdete (hétfő)
                week_start = log_date - timedelta(days=log_date.weekday())
                weekly_data[week_start].append(log)
            
            # Statisztikák összeállítása
            weekly_stats = []
            for week_start in sorted(weekly_data.keys()):
                week_end = week_start + timedelta(days=6)
                week_logs = weekly_data[week_start]
                
                completed_days = sum(1 for log in week_logs if log.completed)
                total_value = None
                
                if habit.tracking_type == TrackingType.NUMERIC:
                    values = [log.value for log in week_logs if log.value is not None and log.completed]
                    if values:
                        total_value = sum(values)
                
                weekly_stats.append(HabitWeeklyStats(
                    week_start=week_start.strftime("%Y-%m-%d"),
                    week_end=week_end.strftime("%Y-%m-%d"),
                    completed_days=completed_days,
                    total_value=total_value
                ))
            
            return weekly_stats
            
        except Exception as e:
            logger.error(f"Error calculating weekly stats: {e}")
            return []
    
    @staticmethod
    async def get_monthly_stats(
        habit_id: str,
        user_id: str,
        months: int = 6
    ) -> List[HabitMonthlyStats]:
        """Havi statisztikák számítása"""
        try:
            habit = await Habit.get(PydanticObjectId(habit_id))
            if not habit:
                return []
            
            # Utolsó N hónap kezdete
            today = datetime.now().date()
            start_date = today.replace(day=1) - timedelta(days=30 * months)
            
            logs = await HabitLog.find({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": {"$gte": start_date.strftime("%Y-%m-%d")}
            }).to_list()
            
            # Hónapok szerinti csoportosítás
            monthly_data = defaultdict(list)
            
            for log in logs:
                log_date = datetime.strptime(log.date, "%Y-%m-%d").date()
                month_key = log_date.strftime("%Y-%m")
                monthly_data[month_key].append(log)
            
            # Statisztikák összeállítása
            monthly_stats = []
            for month_key in sorted(monthly_data.keys()):
                month_logs = monthly_data[month_key]
                
                # A hónap napjainak száma
                year, month = map(int, month_key.split("-"))
                if month == 12:
                    next_month = datetime(year + 1, 1, 1)
                else:
                    next_month = datetime(year, month + 1, 1)
                current_month = datetime(year, month, 1)
                total_days_in_month = (next_month - current_month).days
                
                completed_days = sum(1 for log in month_logs if log.completed)
                completion_rate = (completed_days / len(month_logs) * 100) if month_logs else 0
                
                total_value = None
                if habit.tracking_type == TrackingType.NUMERIC:
                    values = [log.value for log in month_logs if log.value is not None and log.completed]
                    if values:
                        total_value = sum(values)
                
                monthly_stats.append(HabitMonthlyStats(
                    month=month_key,
                    completed_days=completed_days,
                    total_days=len(month_logs),
                    completion_rate=completion_rate,
                    total_value=total_value
                ))
            
            return monthly_stats
            
        except Exception as e:
            logger.error(f"Error calculating monthly stats: {e}")
            return []
    
    @staticmethod
    async def get_user_habit_overview(user_id: str) -> UserHabitOverview:
        """Felhasználó szokás áttekintő statisztikái"""
        try:
            # Összes szokás lekérése
            habits = await Habit.find({"user_id": PydanticObjectId(user_id)}).to_list()
            
            total_habits = len(habits)
            active_habits = sum(1 for h in habits if h.is_active)
            archived_habits = total_habits - active_habits
            
            # Mai teljesítések
            today = datetime.now().date().strftime("%Y-%m-%d")
            today_logs = await HabitLog.find({
                "user_id": PydanticObjectId(user_id),
                "date": today,
                "completed": True
            }).to_list()
            
            completed_today = len(today_logs)
            
            # Átlagos streak számítása
            active_habit_streaks = [h.streak_count for h in habits if h.is_active]
            current_average_streak = sum(active_habit_streaks) / len(active_habit_streaks) if active_habit_streaks else 0
            
            # Legjobb összesített streak
            best_overall_streak = max([h.best_streak for h in habits], default=0)
            
            # Kategóriák szerinti bontás
            categories_breakdown = defaultdict(int)
            for habit in habits:
                if habit.is_active:
                    categories_breakdown[habit.category.value] += 1
            
            return UserHabitOverview(
                total_habits=total_habits,
                active_habits=active_habits,
                archived_habits=archived_habits,
                completed_today=completed_today,
                current_average_streak=current_average_streak,
                best_overall_streak=best_overall_streak,
                categories_breakdown=dict(categories_breakdown)
            )
            
        except Exception as e:
            logger.error(f"Error getting user habit overview: {e}")
            return UserHabitOverview(
                total_habits=0,
                active_habits=0,
                archived_habits=0,
                completed_today=0,
                current_average_streak=0,
                best_overall_streak=0,
                categories_breakdown={}
            )
    
    @staticmethod
    async def check_habit_completion_today(habit_id: str, user_id: str) -> Tuple[bool, Optional[HabitLog]]:
        """Ellenőrzi, hogy ma teljesítve lett-e a szokás"""
        try:
            today = datetime.now().date().strftime("%Y-%m-%d")
            
            log = await HabitLog.find_one({
                "user_id": PydanticObjectId(user_id),
                "habit_id": PydanticObjectId(habit_id),
                "date": today
            })
            
            if log:
                return log.completed, log
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"Error checking habit completion today: {e}")
            return False, None
    
    @staticmethod
    async def get_habit_usage_percentage(habit_id: str, user_id: str) -> Optional[float]:
        """Cél teljesítési százalék számítása (ha van cél beállítva)"""
        try:
            habit = await Habit.get(PydanticObjectId(habit_id))
            if not habit or not habit.has_goal or not habit.daily_target:
                return None
            
            today = datetime.now().date().strftime("%Y-%m-%d")
            
            if habit.goal_period == FrequencyType.DAILY:
                # Napi cél esetén csak a mai napot nézzük
                log = await HabitLog.find_one({
                    "user_id": PydanticObjectId(user_id),
                    "habit_id": PydanticObjectId(habit_id),
                    "date": today
                })
                
                if not log:
                    return 0.0
                
                if habit.tracking_type == TrackingType.BOOLEAN:
                    return 100.0 if log.completed else 0.0
                else:
                    actual_value = log.value or 0
                    return min(100.0, (actual_value / habit.daily_target) * 100)
            
            elif habit.goal_period == FrequencyType.WEEKLY:
                # Heti cél esetén az aktuális hét teljesítését nézzük
                today_date = datetime.now().date()
                week_start = today_date - timedelta(days=today_date.weekday())
                
                logs = await HabitLog.find({
                    "user_id": PydanticObjectId(user_id),
                    "habit_id": PydanticObjectId(habit_id),
                    "date": {"$gte": week_start.strftime("%Y-%m-%d"), "$lte": today}
                }).to_list()
                
                if habit.tracking_type == TrackingType.BOOLEAN:
                    completed_days = sum(1 for log in logs if log.completed)
                    return min(100.0, (completed_days / habit.target_value) * 100)
                else:
                    total_value = sum(log.value or 0 for log in logs if log.completed)
                    return min(100.0, (total_value / habit.target_value) * 100)
            
            elif habit.goal_period == FrequencyType.MONTHLY:
                # Havi cél esetén az aktuális hónap teljesítését nézzük
                today_date = datetime.now().date()
                month_start = today_date.replace(day=1)
                
                logs = await HabitLog.find({
                    "user_id": PydanticObjectId(user_id),
                    "habit_id": PydanticObjectId(habit_id),
                    "date": {"$gte": month_start.strftime("%Y-%m-%d"), "$lte": today}
                }).to_list()
                
                if habit.tracking_type == TrackingType.BOOLEAN:
                    completed_days = sum(1 for log in logs if log.completed)
                    return min(100.0, (completed_days / habit.target_value) * 100)
                else:
                    total_value = sum(log.value or 0 for log in logs if log.completed)
                    return min(100.0, (total_value / habit.target_value) * 100)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating habit usage percentage: {e}")
            return None
    
    @staticmethod
    async def bulk_create_habits(user_id: str, habits_data: List[Dict]) -> Tuple[List[Habit], List[str]]:
        """Több szokás egyszerre történő létrehozása"""
        try:
            created_habits = []
            errors = []
            
            for i, habit_data in enumerate(habits_data):
                try:
                    habit = Habit(
                        user_id=PydanticObjectId(user_id),
                        **habit_data
                    )
                    await habit.insert()
                    created_habits.append(habit)
                    
                except Exception as e:
                    errors.append(f"Habit {i+1}: {str(e)}")
            
            return created_habits, errors
            
        except Exception as e:
            logger.error(f"Error in bulk create habits: {e}")
            return [], [str(e)]