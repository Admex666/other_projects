# app/routes/knowledge.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from beanie import PydanticObjectId

from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge import (
    KnowledgeCategory, Lesson, UserProgress, LessonCompletion,
    CategoryWithLessons, LessonSummary, UserStats, QuizResult,
    QuizQuestion, DifficultyLevel
)
from app.services.badge_service import badge_service
from app.models.notification import NotificationPriority
from app.services.health_score_service import HealthScoreService
from app.services.lesson_service import lesson_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)

# Request models
class QuizSubmission(BaseModel):
    answers: List[List[int]]  # Minden kérdéshez a kiválasztott válaszok indexei

class LessonProgressUpdate(BaseModel):
    pages_completed: int
    total_pages: int

# === KATEGÓRIÁK ÉS LECKÉK ===

@router.get("/categories", response_model=List[CategoryWithLessons])
async def get_categories_with_lessons(
    current_user: User = Depends(get_current_user),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Szűrés nehézségi szint alapján"),
    lang: str = Query('hu', description="Nyelv kód (hu, en)")
):
    """Összes kategória lekérése a hozzájuk tartozó leckékkel és haladással"""
    
    # Feature usage tracking
    await HealthScoreService.track_feature_usage(current_user.id, "knowledge_browse_categories")

    try:
        # Felhasználó haladásának lekérése
        query_user_id = PydanticObjectId(current_user.id)
        user_progress = await UserProgress.find_one({"user_id": query_user_id})
        
        # Haladási adatok formázása
        progress_data = None
        if user_progress:
            completed_lessons = {}
            for comp in user_progress.completed_lessons:
                lesson_id = str(comp.lesson_id)
                pages_ok = comp.pages_completed >= comp.total_pages
                quiz_ok = comp.quiz_score is None or comp.quiz_score >= 70
                
                completed_lessons[lesson_id] = {
                    'is_completed': pages_ok and quiz_ok,
                    'quiz_score': comp.best_quiz_score or comp.quiz_score,
                    'pages_completed': comp.pages_completed,
                    'total_pages': comp.total_pages
                }
            
            progress_data = {'completed_lessons': completed_lessons}
        
        # Leckék lekérése a service-ből
        categories_data = lesson_service.get_categories_with_lessons(
            lang=lang, 
            user_progress=progress_data
        )
        
        # Nehézségi szint szerinti szűrés
        if difficulty:
            for category in categories_data:
                category['lessons'] = [
                    lesson for lesson in category['lessons'] 
                    if lesson['difficulty'] == difficulty.value
                ]
                category['total_lessons'] = len(category['lessons'])
                category['completed_lessons'] = sum(
                    1 for lesson in category['lessons'] if lesson['is_completed']
                )
        
        # Response model konvertálása
        result = []
        for category_data in categories_data:
            lesson_summaries = []
            for lesson_data in category_data['lessons']:
                lesson_summaries.append(LessonSummary(
                    id=lesson_data['id'],
                    title=lesson_data['title'],
                    description=lesson_data['description'],
                    difficulty=DifficultyLevel(lesson_data['difficulty']),
                    estimated_minutes=lesson_data['estimated_minutes'],
                    total_pages=lesson_data['total_pages'],
                    has_quiz=lesson_data['has_quiz'],
                    is_completed=lesson_data['is_completed'],
                    quiz_score=lesson_data['quiz_score'],
                    category_name=category_data['name']
                ))
            
            result.append(CategoryWithLessons(
                id=category_data['id'],
                name=category_data['name'],
                description=category_data['description'],
                icon=category_data['icon'],
                color=category_data['color'],
                lessons=lesson_summaries,
                total_lessons=category_data['total_lessons'],
                completed_lessons=category_data['completed_lessons']
            ))
        
        return result

    except Exception as e:
        logger.error(f"Error in get_categories_with_lessons: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lessons/{lesson_id}")
async def get_lesson_detail(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    lang: str = Query('hu', description="Nyelv kód (hu, en)")
):
    """Egy lecke részletes adatainak lekérése"""
    
    # Lecke lekérése a service-ből
    lesson_data = lesson_service.get_lesson_by_id(lesson_id, lang)
    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Felhasználó haladásának ellenőrzése
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    completion_data = None
    
    if user_progress:
        for comp in user_progress.completed_lessons:
            if str(comp.lesson_id) == lesson_id:
                completion_data = comp
                break
    
    # Feature usage tracking
    await HealthScoreService.track_feature_usage(current_user.id, "knowledge_view_lesson")
    
    return {
        "lesson": lesson_data,
        "completion": completion_data.dict() if completion_data else None
    }

# === HALADÁS KEZELÉS ===

@router.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: str,
    progress: LessonProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    """Lecke haladásának frissítése (oldalak teljesítése)"""

    # Lecke létezésének ellenőrzése
    lesson = lesson_service.get_lesson_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Felhasználó haladásának lekérése/létrehozása
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    print(f"DEBUG: Found user_progress: {user_progress is not None}")
    
    if not user_progress:
        user_progress = UserProgress(user_id=PydanticObjectId(current_user.id))
        print(f"DEBUG: Created new UserProgress with user_id: {user_progress.user_id} (type: {type(user_progress.user_id)})")
        await user_progress.insert()
        print(f"DEBUG: UserProgress inserted, ID: {user_progress.id}")
    
    # Lecke teljesítés keresése vagy létrehozása
    lesson_completion = None
    completion_index = -1
    for i, comp in enumerate(user_progress.completed_lessons):
        if str(comp.lesson_id) == lesson_id:
            lesson_completion = comp
            completion_index = i
            break
    
    if not lesson_completion:
        lesson_completion = LessonCompletion(
            lesson_id=lesson_id,
            total_pages=progress.total_pages
        )
        user_progress.completed_lessons.append(lesson_completion)
        completion_index = len(user_progress.completed_lessons) - 1
    
    # Haladás frissítése
    lesson_completion.pages_completed = progress.pages_completed
    lesson_completion.total_pages = progress.total_pages
    
    # Ha minden oldalt teljesített ÉS nincs kvíz, akkor teljesítettnek tekintjük
    is_lesson_completed = progress.pages_completed >= progress.total_pages
    
    if is_lesson_completed and len(lesson.quiz_questions) == 0:
        # Kvíz nélküli lecke teljesítése
        was_already_completed = _is_lesson_already_completed(user_progress, lesson_id)
        if not was_already_completed:
            await _complete_lesson(user_progress, lesson, completion_index)
    elif is_lesson_completed:
        # Kvízzel rendelkező lecke - csak a haladást frissítjük, teljesítés majd kvíz után
        await _update_user_stats(user_progress, lesson.estimated_minutes)
    
    user_progress.updated_at = datetime.now()
    await user_progress.save()
    
    # Feature usage tracking hozzáadása
    await HealthScoreService.track_feature_usage(current_user.id, "knowledge_lesson_progress")
    
    return {"message": "Progress updated successfully"}

@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResult)
async def submit_quiz(
    lesson_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user)
):
    """Kvíz beküldése és eredmény kiértékelése"""

    # Lecke lekérése és validáció
    lesson = lesson_service.get_lesson_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    quiz_questions = lesson.get('quiz_questions', [])
    if not quiz_questions:
        raise HTTPException(status_code=400, detail="This lesson has no quiz")

    if len(submission.answers) != len(quiz_questions):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match number of questions")

    # Válaszok kiértékelése
    correct_count = 0
    total_questions = len(quiz_questions)

    for i, (user_answers, question) in enumerate(zip(submission.answers, quiz_questions)):
        # Rendezni kell mindkét listát az összehasonlításhoz
        if sorted(user_answers) == sorted(question['correct_answers']):
            correct_count += 1

    score = int((correct_count / total_questions) * 100)
    passed = score >= 70  # 70% a sikeres teljesítés küszöbe

    # Felhasználó haladásának frissítése
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    print(f"DEBUG: Found user_progress: {user_progress is not None}")

    if not user_progress:
        user_progress = UserProgress(user_id=PydanticObjectId(current_user.id))
        print(f"DEBUG: Created new UserProgress with user_id: {user_progress.user_id} (type: {type(user_progress.user_id)})")
        await user_progress.insert()
        print(f"DEBUG: UserProgress inserted, ID: {user_progress.id}")

    # Lecke teljesítés keresése vagy létrehozása
    lesson_completion = None
    completion_index = -1
    for i, comp in enumerate(user_progress.completed_lessons):
        if str(comp.lesson_id) == lesson_id:
            lesson_completion = comp
            completion_index = i
            break

    if not lesson_completion:
        lesson_completion = LessonCompletion(
            lesson_id=lesson_id,
            total_pages=len(lesson.pages)
        )
        user_progress.completed_lessons.append(lesson_completion)
        completion_index = len(user_progress.completed_lessons) - 1

    # JAVÍTÁS: Ha kvízt csinál, akkor feltételezzük, hogy minden oldalt elolvasott
    lesson_completion.pages_completed = len(lesson.pages)
    lesson_completion.total_pages = len(lesson.pages)

    # Kvíz eredmény mentése
    lesson_completion.quiz_attempts += 1
    is_best_score = False

    if lesson_completion.best_quiz_score is None or score > lesson_completion.best_quiz_score:
        lesson_completion.best_quiz_score = score
        is_best_score = True

    lesson_completion.quiz_score = score

    # Ha sikeresen teljesítette, frissítjük a statisztikákat
    if passed:
        # FIX: Az _is_lesson_already_completed függvény most már pontosabban ellenőriz
        was_already_completed = await _is_lesson_already_completed(user_progress, lesson_id) 
        if not was_already_completed:
            await _complete_lesson(user_progress, lesson, completion_index)
        else:
            # Már teljesített lecke, csak a statisztikákat frissítjük
            await _update_user_stats(user_progress, lesson.estimated_minutes)

    # Statisztikák frissítése
    user_progress.total_quiz_attempts += 1

    # Átlagos kvíz eredmény újraszámítása
    all_scores = [comp.best_quiz_score for comp in user_progress.completed_lessons 
                  if comp.best_quiz_score is not None]
    if all_scores:
        user_progress.average_quiz_score = sum(all_scores) / len(all_scores)

    user_progress.updated_at = datetime.now()
    await user_progress.save()

    # Feature usage tracking hozzáadása
    await HealthScoreService.track_feature_usage(current_user.id, "knowledge_quiz_submit")

    return QuizResult(
        score=score,
        correct_answers=correct_count,
        total_questions=total_questions,
        passed=passed,
        is_best_score=is_best_score
    )

# === STATISZTIKÁK ===

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Felhasználó tanulási statisztikáinak lekérése"""
    
    # Debug: A bejelentkezett felhasználó ID-jének kiírása
    print(f"DEBUG: get_user_stats called for user ID: {current_user.id} (type: {type(current_user.id)})")
    
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    
    if not user_progress:
        print(f"DEBUG: No user_progress found for user {current_user.id}. Returning default UserStats.")
        return UserStats(
            current_streak=0,
            longest_streak=0,
            total_lessons_completed=0,
            total_quiz_attempts=0,
            average_quiz_score=0.0,
            total_study_minutes=0,
            daily_challenge_completed_today=False,
            daily_challenge_streak=0
        )
    
    # Debug: A talált user_progress objektum attribútumainak kiírása
    print(f"DEBUG: Found user_progress for user {current_user.id}:")
    print(f"  - _id: {user_progress.id}")
    print(f"  - user_id: {user_progress.user_id}")
    print(f"  - current_streak: {user_progress.current_streak}")
    print(f"  - longest_streak: {user_progress.longest_streak}")
    print(f"  - total_lessons_completed: {user_progress.total_lessons_completed}")
    print(f"  - total_quiz_attempts: {user_progress.total_quiz_attempts}")
    print(f"  - average_quiz_score: {user_progress.average_quiz_score}")
    print(f"  - total_study_minutes: {user_progress.total_study_minutes}")
    print(f"  - daily_challenge_completed_today: {user_progress.daily_challenge_completed_today}")
    print(f"  - daily_challenge_streak: {user_progress.daily_challenge_streak}")
    
    return UserStats(
        current_streak=user_progress.current_streak,
        longest_streak=user_progress.longest_streak,
        total_lessons_completed=user_progress.total_lessons_completed,
        total_quiz_attempts=user_progress.total_quiz_attempts,
        average_quiz_score=user_progress.average_quiz_score,
        total_study_minutes=user_progress.total_study_minutes,
        daily_challenge_completed_today=user_progress.daily_challenge_completed_today,
        daily_challenge_streak=user_progress.daily_challenge_streak
    )

@router.post("/daily-challenge")
async def complete_daily_challenge(current_user: User = Depends(get_current_user)):
    """Napi kihívás teljesítése (5 perces tanulás)"""
    
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    if not user_progress:
        user_progress = UserProgress(user_id=PydanticObjectId(current_user.id))
        await user_progress.insert()
    
    today = datetime.now().date()
    
    # Ellenőrizzük, hogy ma már teljesítette-e
    if user_progress.daily_challenge_completed_today:
        return {"message": "Daily challenge already completed today", "streak": user_progress.daily_challenge_streak}
    
    # Napi kihívás teljesítése
    user_progress.daily_challenge_completed_today = True
    user_progress.daily_challenge_streak += 1

    # Értesítés küldése
    from app.services.notification_service import NotificationService
    await NotificationService.create_system_notification(
        user_id=current_user.id,
        title="Napi tanulási cél teljesítve!",
        message=f"Szuper! {user_progress.daily_challenge_streak} napos sorozatod van!",
        priority=NotificationPriority.LOW,
        action_url="/knowledge",
        action_text="Tudástár megtekintése"
    )
    
    # Streak frissítése is egyben
    await _update_user_stats(user_progress, 5)  # 5 perces napi kihívás
    
    user_progress.updated_at = datetime.now()
    await user_progress.save()
    
    # Feature usage tracking hozzáadása
    await HealthScoreService.track_feature_usage(current_user.id, "knowledge_daily_challenge")

    return {
        "message": "Daily challenge completed!",
        "streak": user_progress.daily_challenge_streak
    }

# === HELPER FUNKCIÓK ===

async def _update_user_stats(user_progress: UserProgress, study_minutes: int):
    """Felhasználói statisztikák frissítése"""

    today = datetime.now().date()

    # Streak számítás
    if user_progress.last_activity_date:
        last_date = user_progress.last_activity_date.date()
        days_diff = (today - last_date).days

        if days_diff == 0:
            # Ma már tanult
            pass
        elif days_diff == 1:
            # Tegnap tanult, streak folytatódik
            user_progress.current_streak += 1
        else:
            # Megszakadt a streak
            user_progress.current_streak = 1
    else:
        # Első tanulás
        user_progress.current_streak = 1

    # Leghosszabb streak frissítése
    if user_progress.current_streak > user_progress.longest_streak:
        user_progress.longest_streak = user_progress.current_streak

    # Utolsó aktivitás frissítése
    user_progress.last_activity_date = datetime.now()

    # Statisztikák frissítése
    user_progress.total_study_minutes += study_minutes

    # FIX: Teljesített leckék számának HELYES újraszámítása
    completed_count = 0
    for comp in user_progress.completed_lessons:
        # Az aszinkron helper funkció használata
        if await _is_lesson_already_completed(user_progress, str(comp.lesson_id)):
            completed_count += 1

    user_progress.total_lessons_completed = completed_count

    # Napi kihívás reset éjfélkor (ezt egy cron job-nak kellene csinálnia)
    if user_progress.last_activity_date and user_progress.last_activity_date.date() != today:
        user_progress.daily_challenge_completed_today = False

async def _is_lesson_already_completed(user_progress: UserProgress, lesson_id: str) -> bool:
    """Ellenőrzi, hogy a lecke már teljesítve van-e az összes feltétel alapján (oldalak + kvíz, ha van)"""
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        # Ha a lecke nem található (pl. törölték), akkor nem tekintjük teljesítettnek
        return False

    has_quiz = len(lesson.quiz_questions) > 0

    for comp in user_progress.completed_lessons:
        if str(comp.lesson_id) == lesson_id:
            pages_done = comp.pages_completed >= comp.total_pages

            if has_quiz:
                quiz_passed = comp.best_quiz_score is not None and comp.best_quiz_score >= 70
            else:
                # Ha nincs kvíz a leckénél, akkor a quiz_passed mindig True
                quiz_passed = True

            return pages_done and quiz_passed
    return False

async def _complete_lesson(user_progress: UserProgress, lesson: Lesson, completion_index: int):
    """Lecke teljesítésének kezelése (badge, értesítés, statisztikák)"""
    try:
        # Badge ellenőrzés
        earned_badges = await badge_service.check_and_award_badges(
            user_id=str(user_progress.user_id),  
            trigger_event="lesson_completed",
            context={
                "lesson_id": str(lesson.id),
                "lesson_difficulty": lesson.difficulty.value
            }
        )

        # Ha szerzett badge-eket, logoljuk
        if earned_badges:
            print(f"DEBUG: User {user_progress.user_id} earned {len(earned_badges)} badges for completing lesson {lesson.id}")

        # Értesítés küldése
        from app.services.notification_service import NotificationService
        await NotificationService.create_system_notification(
            user_id=str(user_progress.user_id),  
            title="Lecke sikeresen teljesítve!",
            message=f"Gratulálunk! Sikeresen teljesítetted a '{lesson.title}' leckét.",
            priority=NotificationPriority.MEDIUM,
            action_url=f"/knowledge/lessons/{lesson.id}",
            action_text="Lecke megtekintése"
        )
    except Exception as e:
        logger.error(f"Error in lesson completion handling: {e}")

    # Statisztikák frissítése
    await _update_user_stats(user_progress, lesson.estimated_minutes)
    
    # ÚJDONSÁG: Lecke teljesítés dátumának frissítése
    lesson_completion = user_progress.completed_lessons[completion_index]
    lesson_completion.completed_at = datetime.now()

# Hozz létre egy új endpoint-ot ideiglenes javításhoz
@router.post("/debug/fix-progress")
async def fix_user_progress(current_user: User = Depends(get_current_user)):
    """Ideiglenes endpoint a user progress javításához"""
    
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    if not user_progress:
        return {"message": "No progress found"}
    
    print(f"Before fix - user_progress: {user_progress.dict()}")
    
    fixed_count = 0
    for comp in user_progress.completed_lessons:
        # Ha van kvíz eredmény és legalább 70%, akkor a pages_completed-et javítjuk
        if comp.quiz_score is not None and comp.quiz_score >= 70:
            if comp.pages_completed < comp.total_pages:
                print(f"Fixing lesson {comp.lesson_id}: pages {comp.pages_completed} -> {comp.total_pages}")
                comp.pages_completed = comp.total_pages
                fixed_count += 1
    
    # Teljesített leckék újraszámítása
    completed_count = 0
    for comp in user_progress.completed_lessons:
        pages_done = comp.pages_completed >= comp.total_pages
        quiz_passed = comp.quiz_score is None or comp.quiz_score >= 70
        if pages_done and quiz_passed:
            completed_count += 1
    
    user_progress.total_lessons_completed = completed_count
    
    # Ha volt javítás, mentjük
    if fixed_count > 0 or user_progress.total_lessons_completed != completed_count:
        user_progress.updated_at = datetime.now()
        await user_progress.save()
    
    print(f"After fix - completed_count: {completed_count}")
    
    return {
        "message": "Progress fixed",
        "fixes_made": fixed_count,
        "total_completed": completed_count,
        "progress": user_progress.dict()
    }

@router.post("/debug/trigger-badge-check")
async def trigger_badge_check(current_user: User = Depends(get_current_user)):
    """Debug endpoint - badge ellenőrzés manuális kiváltása"""
    try:
        earned_badges = await badge_service.check_and_award_badges(
            user_id=current_user.id,
            trigger_event="lesson_completed",
            context={"debug": True}
        )
        
        return {
            "message": "Badge check completed",
            "earned_badges": [
                {
                    "badge_code": badge.badge_code,
                    "badge_name": badge.badge_name,
                    "points": badge.points_earned,
                    "level": badge.level,
                    "is_new": badge.is_new_badge
                }
                for badge in earned_badges
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Badge check failed: {str(e)}")
    
@router.get("/daily-stats")
async def get_daily_stats(current_user: User = Depends(get_current_user)):
    """Napi tanulási statisztikák lekérése (lecke számok, progress)"""
    
    user_progress = await UserProgress.find_one({"user_id": PydanticObjectId(current_user.id)})
    
    if not user_progress:
        return {
            "daily_lessons_completed": 0,
            "daily_lessons_limit": 1,  
            "can_take_more_lessons": True,
            "daily_challenge_completed": False,
            "current_streak": 0
        }
    
    # Mai nap kezdete
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Mai teljesített leckék számolása - JAVÍTOTT logika
    daily_lessons_count = 0
    for comp in user_progress.completed_lessons:
        # Ellenőrizzük, hogy ma teljesítették-e ÉS tényleg teljesítve van-e
        if (comp.completed_at and comp.completed_at >= today_start):
            pages_done = comp.pages_completed >= comp.total_pages
            
            # Lecke objektum lekérése a kvíz ellenőrzéshez
            lesson = await Lesson.get(str(comp.lesson_id))
            if lesson:
                has_quiz = len(lesson.quiz_questions) > 0
                if has_quiz:
                    quiz_passed = comp.best_quiz_score is not None and comp.best_quiz_score >= 70
                else:
                    quiz_passed = True
                
                if pages_done and quiz_passed:
                    daily_lessons_count += 1
    
    return {
        "daily_lessons_completed": daily_lessons_count,
        "daily_lessons_limit": 1,  
        "can_take_more_lessons": daily_lessons_count < 1,
        "daily_challenge_completed": user_progress.daily_challenge_completed_today,
        "current_streak": user_progress.current_streak
    }

@router.get("/debug/lesson-stats")
async def get_lesson_stats(current_user: User = Depends(get_current_user)):
    """Debug endpoint - lecke statisztikák"""
    if not current_user.is_admin:  # Ha van admin jogosultság ellenőrzés
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return lesson_service.get_lesson_stats()

@router.get("/debug/available-languages/{lesson_id}")
async def get_lesson_languages(
    lesson_id: str, 
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint - lecke elérhető nyelvei"""
    return {
        "lesson_id": lesson_id,
        "available_languages": lesson_service.get_available_languages(lesson_id)
    }