# app/routes/habits.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from beanie import PydanticObjectId
from datetime import datetime
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.models.habit import Habit, HabitLog, PREDEFINED_HABITS, HabitCategory, TrackingType, FrequencyType
from app.models.habit_schemas import (
    HabitCreate, HabitUpdate, HabitRead, HabitListResponse,
    HabitLogCreate, HabitLogUpdate, HabitLogRead, HabitLogListResponse,
    HabitStatsResponse, UserHabitOverview, PredefinedHabitResponse,
    HabitBulkCreate, HabitBulkCreateResponse
)
from app.services.habit_service import HabitService
from app.services.badge_service import badge_service

router = APIRouter(prefix="/habits", tags=["habits"])
logger = logging.getLogger(__name__)

# === HABIT CRUD OPERATIONS ===

@router.post("/", response_model=HabitRead, status_code=201)
async def create_habit(
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_user)
):
    """Új szokás létrehozása"""
    try:
        # Ellenőrizzük, hogy már létezik-e hasonló nevű aktív szokás
        existing = await Habit.find_one({
            "user_id": PydanticObjectId(current_user.id),
            "title": habit_data.title,
            "is_active": True
        })
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Már létezik aktív szokás ezzel a névvel"
            )
        
        new_habit = Habit(
            user_id=PydanticObjectId(current_user.id),
            **habit_data.model_dump()
        )
        
        await new_habit.insert()
        
        # Badge ellenőrzés
        try:
            await badge_service.check_and_award_badges(
                user_id=current_user.id,
                trigger_event="habit_created",
                context={
                    "habit_id": str(new_habit.id),
                    "category": new_habit.category.value
                }
            )
        except Exception as e:
            logger.error(f"Badge check failed: {e}")
        
        return await _convert_habit_to_read(new_habit, current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating habit: {e}")
        raise HTTPException(status_code=500, detail="Szokás létrehozása sikertelen")

@router.get("/", response_model=HabitListResponse)
async def get_habits(
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Csak aktív szokások"),
    category: Optional[HabitCategory] = Query(None, description="Szűrés kategória szerint"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Felhasználó szokásainak lekérése"""
    try:
        # Alap szűrő
        query_filter = {"user_id": PydanticObjectId(current_user.id)}
        
        if active_only:
            query_filter["is_active"] = True
        
        if category:
            query_filter["category"] = category
        
        # Lekérdezés
        total_count = await Habit.find(query_filter).count()
        habits = await Habit.find(query_filter)\
            .sort(-Habit.created_at)\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Statisztikák számítása
        all_habits = await Habit.find({"user_id": PydanticObjectId(current_user.id)}).to_list()
        active_count = sum(1 for h in all_habits if h.is_active)
        archived_count = len(all_habits) - active_count
        
        # Konvertálás HabitRead objektumokká
        habit_reads = []
        for habit in habits:
            habit_read = await _convert_habit_to_read(habit, current_user.id)
            habit_reads.append(habit_read)
        
        return HabitListResponse(
            habits=habit_reads,
            total_count=total_count,
            active_count=active_count,
            archived_count=archived_count
        )
        
    except Exception as e:
        logger.error(f"Error getting habits: {e}")
        raise HTTPException(status_code=500, detail="Szokások lekérése sikertelen")

@router.get("/{habit_id}", response_model=HabitRead)
async def get_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user)
):
    """Egy konkrét szokás lekérése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        return await _convert_habit_to_read(habit, current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit {habit_id}: {e}")
        raise HTTPException(status_code=500, detail="Szokás lekérése sikertelen")

@router.put("/{habit_id}", response_model=HabitRead)
async def update_habit(
    habit_id: str,
    habit_data: HabitUpdate,
    current_user: User = Depends(get_current_user)
):
    """Szokás frissítése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        # Frissítés
        update_data = habit_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(habit, key, value)
        
        await habit.save()
        
        return await _convert_habit_to_read(habit, current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating habit {habit_id}: {e}")
        raise HTTPException(status_code=500, detail="Szokás frissítése sikertelen")

@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user)
):
    """Szokás törlése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        # Töröljük a szokást és az összes hozzá tartozó logot
        await HabitLog.find({"habit_id": PydanticObjectId(habit_id)}).delete()
        await habit.delete()
        
        return {"message": "Szokás sikeresen törölve"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting habit {habit_id}: {e}")
        raise HTTPException(status_code=500, detail="Szokás törlése sikertelen")

# === HABIT LOGS ===

@router.post("/{habit_id}/logs", response_model=HabitLogRead, status_code=201)
async def create_habit_log(
    habit_id: str,
    log_data: HabitLogCreate,
    current_user: User = Depends(get_current_user)
):
    """Szokás teljesítés rögzítése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        # Alapértelmezett dátum beállítása
        log_date = log_data.date or datetime.now().date().strftime("%Y-%m-%d")
        
        habit_log = await HabitService.log_habit_completion(
            user_id=current_user.id,
            habit_id=habit_id,
            completed=log_data.completed,
            value=log_data.value,
            notes=log_data.notes,
            log_date=log_date
        )
        
        # Badge ellenőrzés
        try:
            if log_data.completed:
                await badge_service.check_and_award_badges(
                    user_id=current_user.id,
                    trigger_event="habit_completed",
                    context={
                        "habit_id": habit_id,
                        "streak_count": habit.streak_count
                    }
                )
        except Exception as e:
            logger.error(f"Badge check failed: {e}")
        
        return HabitLogRead(
            id=str(habit_log.id),
            user_id=str(habit_log.user_id),
            habit_id=str(habit_log.habit_id),
            date=habit_log.date,
            completed=habit_log.completed,
            value=habit_log.value,
            notes=habit_log.notes,
            created_at=habit_log.created_at,
            updated_at=habit_log.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating habit log: {e}")
        raise HTTPException(status_code=500, detail="Szokás rögzítése sikertelen")

@router.get("/{habit_id}/logs", response_model=HabitLogListResponse)
async def get_habit_logs(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(30, ge=1, le=100),
    skip: int = Query(0, ge=0),
    from_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="YYYY-MM-DD")
):
    """Szokás teljesítéseinek lekérése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        # Szűrők
        query_filter = {
            "user_id": PydanticObjectId(current_user.id),
            "habit_id": PydanticObjectId(habit_id)
        }
        
        if from_date and to_date:
            query_filter["date"] = {"$gte": from_date, "$lte": to_date}
        elif from_date:
            query_filter["date"] = {"$gte": from_date}
        elif to_date:
            query_filter["date"] = {"$lte": to_date}
        
        # Lekérdezés
        total_count = await HabitLog.find(query_filter).count()
        logs = await HabitLog.find(query_filter)\
            .sort(-HabitLog.date)\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Konvertálás
        log_reads = []
        for log in logs:
            log_reads.append(HabitLogRead(
                id=str(log.id),
                user_id=str(log.user_id),
                habit_id=str(log.habit_id),
                date=log.date,
                completed=log.completed,
                value=log.value,
                notes=log.notes,
                created_at=log.created_at,
                updated_at=log.updated_at
            ))
        
        return HabitLogListResponse(
            logs=log_reads,
            total_count=total_count,
            habit_title=habit.title
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit logs: {e}")
        raise HTTPException(status_code=500, detail="Szokás teljesítések lekérése sikertelen")

@router.put("/{habit_id}/logs/{log_id}", response_model=HabitLogRead)
async def update_habit_log(
    habit_id: str,
    log_id: str,
    log_data: HabitLogUpdate,
    current_user: User = Depends(get_current_user)
):
    """Szokás teljesítés frissítése"""
    try:
        log = await HabitLog.get(PydanticObjectId(log_id))
        if not log:
            raise HTTPException(status_code=404, detail="Szokás teljesítés nem található")
        
        if str(log.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a teljesítéshez")
        
        # Frissítés
        update_data = log_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(log, key, value)
        
        await log.save()
        
        # Streak újraszámítása
        await HabitService.update_habit_streak(habit_id, current_user.id)
        
        return HabitLogRead(
            id=str(log.id),
            user_id=str(log.user_id),
            habit_id=str(log.habit_id),
            date=log.date,
            completed=log.completed,
            value=log.value,
            notes=log.notes,
            created_at=log.created_at,
            updated_at=log.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating habit log: {e}")
        raise HTTPException(status_code=500, detail="Szokás teljesítés frissítése sikertelen")

@router.delete("/{habit_id}/logs/{log_id}", status_code=204)
async def delete_habit_log(
    habit_id: str,
    log_id: str,
    current_user: User = Depends(get_current_user)
):
    """Szokás teljesítés törlése"""
    try:
        log = await HabitLog.get(PydanticObjectId(log_id))
        if not log:
            raise HTTPException(status_code=404, detail="Szokás teljesítés nem található")
        
        if str(log.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a teljesítéshez")
        
        await log.delete()
        
        # Streak újraszámítása
        await HabitService.update_habit_streak(habit_id, current_user.id)
        
        return {"message": "Szokás teljesítés törölve"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting habit log: {e}")
        raise HTTPException(status_code=500, detail="Szokás teljesítés törlése sikertelen")

# === STATISTICS ===

@router.get("/overview/stats", response_model=UserHabitOverview)
async def get_user_habit_overview(current_user: User = Depends(get_current_user)):
    """Felhasználó szokás áttekintő"""
    try:
        overview = await HabitService.get_user_habit_overview(current_user.id)
        return overview
        
    except Exception as e:
        logger.error(f"Error getting user habit overview: {e}")
        raise HTTPException(status_code=500, detail="Szokás áttekintő lekérése sikertelen")

@router.get("/{habit_id}/stats", response_model=HabitStatsResponse)
async def get_habit_stats(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Statisztika időszaka napokban")
):
    """Szokás statisztikák lekérése"""
    try:
        habit = await Habit.get(PydanticObjectId(habit_id))
        if not habit:
            raise HTTPException(status_code=404, detail="Szokás nem található")
        
        if str(habit.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Nincs jogosultság ehhez a szokáshoz")
        
        # Statisztikák számítása
        overall_stats = await HabitService.get_habit_progress_stats(habit_id, current_user.id, days)
        weekly_stats = await HabitService.get_weekly_stats(habit_id, current_user.id)
        monthly_stats = await HabitService.get_monthly_stats(habit_id, current_user.id)
        
        return HabitStatsResponse(
            habit_id=habit_id,
            habit_title=habit.title,
            overall=overall_stats,
            weekly_stats=weekly_stats,
            monthly_stats=monthly_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit stats: {e}")
        raise HTTPException(status_code=500, detail="Szokás statisztikák lekérése sikertelen")

# === PREDEFINED HABITS ===

@router.get("/predefined/list", response_model=List[PredefinedHabitResponse])
async def get_predefined_habits():
    """Előre definiált szokások lekérése"""
    try:
        response = []
        for category, habits in PREDEFINED_HABITS.items():
            response.append(PredefinedHabitResponse(
                category=category,
                habits=habits
            ))
        return response
        
    except Exception as e:
        logger.error(f"Error getting predefined habits: {e}")
        raise HTTPException(status_code=500, detail="Előre definiált szokások lekérése sikertelen")

@router.post("/predefined/{category}/{habit_index}", response_model=HabitRead, status_code=201)
async def create_habit_from_predefined(
    category: HabitCategory,
    habit_index: int,
    current_user: User = Depends(get_current_user)
):
    """Előre definiált szokás létrehozása"""
    try:
        if category not in PREDEFINED_HABITS:
            raise HTTPException(status_code=404, detail="Kategória nem található")
        
        habits_in_category = PREDEFINED_HABITS[category]
        if habit_index < 0 or habit_index >= len(habits_in_category):
            raise HTTPException(status_code=404, detail="Szokás index nem érvényes")
        
        habit_data = habits_in_category[habit_index]
        
        # Ellenőrizzük, hogy már létezik-e
        existing = await Habit.find_one({
            "user_id": PydanticObjectId(current_user.id),
            "title": habit_data["title"],
            "is_active": True
        })
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Már létezik aktív szokás ezzel a névvel"
            )
        
        habit = await HabitService.create_habit_from_predefined(
            current_user.id,
            category,
            habit_data
        )
        
        return await _convert_habit_to_read(habit, current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating predefined habit: {e}")
        raise HTTPException(status_code=500, detail="Előre definiált szokás létrehozása sikertelen")

# === BULK OPERATIONS ===

@router.post("/bulk", response_model=HabitBulkCreateResponse, status_code=201)
async def bulk_create_habits(
    bulk_data: HabitBulkCreate,
    current_user: User = Depends(get_current_user)
):
    """Több szokás egyszerre létrehozása"""
    try:
        habits_data = [habit.model_dump() for habit in bulk_data.habits]
        created_habits, errors = await HabitService.bulk_create_habits(current_user.id, habits_data)
        
        habit_reads = []
        for habit in created_habits:
            habit_read = await _convert_habit_to_read(habit, current_user.id)
            habit_reads.append(habit_read)
        
        return HabitBulkCreateResponse(
            created_count=len(created_habits),
            created_habits=habit_reads,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in bulk create habits: {e}")
        raise HTTPException(status_code=500, detail="Tömeges szokás létrehozás sikertelen")

# === HELPER FUNCTIONS ===

async def _convert_habit_to_read(habit: Habit, user_id: str) -> HabitRead:
    """Habit dokumentum konvertálása HabitRead objektummá"""
    
    # Kiszámított mezők
    is_completed_today, _ = await HabitService.check_habit_completion_today(str(habit.id), user_id)
    usage_percentage = await HabitService.get_habit_usage_percentage(str(habit.id), user_id)
    
    return HabitRead(
        id=str(habit.id),
        user_id=str(habit.user_id),
        title=habit.title,
        description=habit.description,
        category=habit.category,
        tracking_type=habit.tracking_type,
        frequency=habit.frequency,
        has_goal=habit.has_goal,
        target_value=habit.target_value,
        goal_period=habit.goal_period,
        daily_target=habit.daily_target,
        is_active=habit.is_active,
        streak_count=habit.streak_count,
        best_streak=habit.best_streak,
        last_completed=habit.last_completed,
        is_completed_today=is_completed_today,
        usage_percentage=usage_percentage,
        created_at=habit.created_at,
        updated_at=habit.updated_at
    )