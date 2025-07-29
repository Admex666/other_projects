# app/routes/knowledge.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge import (
    KnowledgeCategory, Lesson, UserProgress, LessonCompletion,
    CategoryWithLessons, LessonSummary, UserStats, QuizResult,
    QuizQuestion, DifficultyLevel
)
from app.services.badge_service import badge_service
from app.models.notification import NotificationPriority

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
    difficulty: Optional[DifficultyLevel] = Query(None, description="Szűrés nehézségi szint alapján")
):
    """Összes kategória lekérése a hozzájuk tartozó leckékkel és haladással"""
    print(f"DEBUG: get_categories called for user {current_user.id} (type: {type(current_user.id)})")

    # Felhasználó haladásának lekérése
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    print(f"DEBUG: Searching for user_progress with user_id: {current_user.id}")
    completed_lesson_ids = []
    lesson_scores = {}

    # Lista az összes UserProgress dokumentumról (csak debug céljából)
    all_progress = await UserProgress.find({}).to_list()
    print(f"DEBUG: Total UserProgress documents in DB: {len(all_progress)}")
    for i, prog in enumerate(all_progress):
        print(f"  Progress {i}: user_id={prog.user_id} (type: {type(prog.user_id)}), id={prog.id}")
   
    if user_progress:
        print(f"Found user_progress document: {user_progress.id}")
        print(f"User progress has {len(user_progress.completed_lessons)} completed_lessons entries")
        
        for i, comp in enumerate(user_progress.completed_lessons):
            lesson_id = str(comp.lesson_id)
            
            # FIX: Proper lesson completion logic
            pages_done = comp.pages_completed >= comp.total_pages
            
            # FIX: Check if lesson has quiz questions first
            lesson = await Lesson.get(comp.lesson_id)
            has_quiz = lesson and len(lesson.quiz_questions) > 0
            
            # If lesson has quiz, check quiz score; if no quiz, only check pages
            if has_quiz:
                quiz_passed = comp.quiz_score is not None and comp.quiz_score >= 70
            else:
                quiz_passed = True  # No quiz means quiz is automatically "passed"
            
            is_completed = pages_done and quiz_passed
            
            print(f"  Lesson {i}: ID={lesson_id}")
            print(f"    pages: {comp.pages_completed}/{comp.total_pages} (done: {pages_done})")
            print(f"    has_quiz: {has_quiz}")
            print(f"    quiz_score: {comp.quiz_score} (passed: {quiz_passed})")
            print(f"    overall completed: {is_completed}")
            
            if is_completed:
                completed_lesson_ids.append(lesson_id)
            
            if comp.best_quiz_score is not None:
                lesson_scores[lesson_id] = comp.best_quiz_score
            elif comp.quiz_score is not None:
                lesson_scores[lesson_id] = comp.quiz_score
        
        print(f"Total completed lesson IDs: {completed_lesson_ids}")
    else:
        print(f"No user_progress document found for user {current_user.id}")
    
    print(f"User {current_user.id} progress: {len(completed_lesson_ids)} completed lessons")

    # Kategóriák lekérése
    categories = await KnowledgeCategory.find({"is_active": True}).sort("order").to_list()
    result = []

    for category in categories:
        # Leckék lekérése a kategóriához
        lesson_filter = {"category_id": category.id, "is_published": True}
        if difficulty:
            lesson_filter["difficulty"] = difficulty
            
        lessons = await Lesson.find(lesson_filter).sort("order").to_list()
        
        lesson_summaries = []
        completed_count = 0
        
        print(f"\nCategory: {category.name} has {len(lessons)} lessons")
        
        for lesson in lessons:
            lesson_id = str(lesson.id)
            is_completed = lesson_id in completed_lesson_ids
            if is_completed:
                completed_count += 1
            
            print(f"  Lesson: {lesson.title} (ID: {lesson_id}) - completed: {is_completed}")
            
            lesson_summaries.append(LessonSummary(
                id=lesson_id,
                title=lesson.title,
                description=lesson.description,
                difficulty=lesson.difficulty,
                estimated_minutes=lesson.estimated_minutes,
                total_pages=len(lesson.pages),
                has_quiz=len(lesson.quiz_questions) > 0,
                is_completed=is_completed,
                quiz_score=lesson_scores.get(lesson_id),
                category_name=category.name
            ))
        
        print(f"Category {category.name}: {completed_count}/{len(lesson_summaries)} lessons completed")

        result.append(CategoryWithLessons(
            id=str(category.id),
            name=category.name,
            description=category.description,
            icon=category.icon,
            color=category.color,
            lessons=lesson_summaries,
            total_lessons=len(lesson_summaries),
            completed_lessons=completed_count
        ))
    
    return result

@router.get("/lessons/{lesson_id}")
async def get_lesson_detail(
    lesson_id: str,
    current_user: User = Depends(get_current_user)
):
    """Egy lecke részletes adatainak lekérése"""
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Felhasználó haladásának ellenőrzése
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    completion_data = None
    
    if user_progress:
        for comp in user_progress.completed_lessons:
            if str(comp.lesson_id) == lesson_id:
                completion_data = comp
                break
    
    return {
        "lesson": lesson.dict(),
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

    print(f"DEBUG: update_lesson_progress called for user {current_user.id} (type: {type(current_user.id)})")
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Felhasználó haladásának lekérése/létrehozása
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    print(f"DEBUG: Found user_progress: {user_progress is not None}")
    
    if not user_progress:
        user_progress = UserProgress(user_id=current_user.id)
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
    
    return {"message": "Progress updated successfully"}

@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResult)
async def submit_quiz(
    lesson_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user)
):
    """Kvíz beküldése és eredmény kiértékelése"""

    print(f"DEBUG: submit_quiz called for user {current_user.id} (type: {type(current_user.id)})")
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    if not lesson.quiz_questions:
        raise HTTPException(status_code=400, detail="This lesson has no quiz")
    
    if len(submission.answers) != len(lesson.quiz_questions):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match number of questions")
    
    # Válaszok kiértékelése
    correct_count = 0
    total_questions = len(lesson.quiz_questions)
    
    for i, (user_answers, question) in enumerate(zip(submission.answers, lesson.quiz_questions)):
        # Rendezni kell mindkét listát az összehasonlításhoz
        if sorted(user_answers) == sorted(question.correct_answers):
            correct_count += 1
    
    score = int((correct_count / total_questions) * 100)
    passed = score >= 70  # 70% a sikeres teljesítés küszöbe
    
    # Felhasználó haladásának frissítése
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    print(f"DEBUG: Found user_progress: {user_progress is not None}")
    
    if not user_progress:
        user_progress = UserProgress(user_id=current_user.id)
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
        was_already_completed = _is_lesson_already_completed(user_progress, lesson_id)
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
    
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    
    if not user_progress:
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
    
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    if not user_progress:
        user_progress = UserProgress(user_id=current_user.id)
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
        pages_done = comp.pages_completed >= comp.total_pages
        
        # Fetch lesson to check if it has quiz
        try:
            lesson = await Lesson.get(comp.lesson_id)
            has_quiz = lesson and len(lesson.quiz_questions) > 0
            
            if has_quiz:
                quiz_passed = comp.quiz_score is not None and comp.quiz_score >= 70
            else:
                quiz_passed = True  # No quiz means automatically passed
                
        except:
            # If lesson fetch fails, use fallback logic
            quiz_passed = comp.quiz_score is None or comp.quiz_score >= 70
        
        if pages_done and quiz_passed:
            completed_count += 1
    
    user_progress.total_lessons_completed = completed_count
    
    # Napi kihívás reset éjfélkor (ezt egy cron job-nak kellene csinálnia)
    if user_progress.last_activity_date and user_progress.last_activity_date.date() != today:
        user_progress.daily_challenge_completed_today = False

def _is_lesson_already_completed(user_progress: UserProgress, lesson_id: str) -> bool:
    """Ellenőrzi, hogy a lecke már teljesítve van-e"""
    for comp in user_progress.completed_lessons:
        if str(comp.lesson_id) == lesson_id:
            pages_done = comp.pages_completed >= comp.total_pages
            
            # Check if we need to verify quiz score
            # Note: This is a simplified check. In a real scenario, you'd want to 
            # fetch the lesson to check if it has quiz questions
            if comp.quiz_score is not None:
                # Lesson has quiz, check if passed
                quiz_passed = comp.quiz_score >= 70
            else:
                # No quiz attempted or no quiz exists, consider passed
                quiz_passed = True
                
            return pages_done and quiz_passed
    return False

async def _complete_lesson(user_progress: UserProgress, lesson: Lesson, completion_index: int):
    """Lecke teljesítésének kezelése (badge, értesítés, statisztikák)"""
    try:
        # Badge ellenőrzés
        earned_badges = await badge_service.check_and_award_badges(
            user_id=user_progress.user_id,
            trigger_event="lesson_completed",
            context={
                "lesson_id": str(lesson.id),
                "lesson_difficulty": lesson.difficulty.value
            }
        )
        
        # Értesítés küldése
        from app.services.notification_service import NotificationService
        await NotificationService.create_system_notification(
            user_id=user_progress.user_id,
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

# Hozz létre egy új endpoint-ot ideiglenes javításhoz
@router.post("/debug/fix-progress")
async def fix_user_progress(current_user: User = Depends(get_current_user)):
    """Ideiglenes endpoint a user progress javításához"""
    
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
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