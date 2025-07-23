# app/routes/knowledge.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge import (
    KnowledgeCategory, Lesson, UserProgress, LessonCompletion,
    CategoryWithLessons, LessonSummary, UserStats, QuizResult,
    QuizQuestion, DifficultyLevel
)
from pydantic import BaseModel

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

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
    
    # Felhasználó haladásának lekérése
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    completed_lesson_ids = []
    lesson_scores = {}
    
    if user_progress:
        completed_lesson_ids = [str(comp.lesson_id) for comp in user_progress.completed_lessons]
        lesson_scores = {str(comp.lesson_id): comp.best_quiz_score 
                        for comp in user_progress.completed_lessons 
                        if comp.best_quiz_score is not None}
    
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
        
        for lesson in lessons:
            lesson_id = str(lesson.id)
            is_completed = lesson_id in completed_lesson_ids
            if is_completed:
                completed_count += 1
            
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
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Felhasználó haladásának lekérése/létrehozása
    user_progress = await UserProgress.find_one({"user_id": current_user.id})
    if not user_progress:
        user_progress = UserProgress(user_id=current_user.id)
        await user_progress.insert()
    
    # Lecke teljesítés keresése vagy létrehozása
    lesson_completion = None
    for i, comp in enumerate(user_progress.completed_lessons):
        if str(comp.lesson_id) == lesson_id:
            lesson_completion = comp
            break
    
    if not lesson_completion:
        lesson_completion = LessonCompletion(
            lesson_id=lesson_id,
            total_pages=progress.total_pages
        )
        user_progress.completed_lessons.append(lesson_completion)
    
    # Haladás frissítése
    lesson_completion.pages_completed = progress.pages_completed
    lesson_completion.total_pages = progress.total_pages
    
    # Ha minden oldalt teljesített, frissítjük a statisztikákat
    if progress.pages_completed >= progress.total_pages:
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
    if not user_progress:
        user_progress = UserProgress(user_id=current_user.id)
        await user_progress.insert()
    
    # Lecke teljesítés keresése vagy létrehozása
    lesson_completion = None
    for comp in user_progress.completed_lessons:
        if str(comp.lesson_id) == lesson_id:
            lesson_completion = comp
            break
    
    if not lesson_completion:
        lesson_completion = LessonCompletion(
            lesson_id=lesson_id,
            total_pages=len(lesson.pages)
        )
        user_progress.completed_lessons.append(lesson_completion)
    
    # Kvíz eredmény mentése
    lesson_completion.quiz_attempts += 1
    is_best_score = False
    
    if lesson_completion.best_quiz_score is None or score > lesson_completion.best_quiz_score:
        lesson_completion.best_quiz_score = score
        is_best_score = True
    
    lesson_completion.quiz_score = score
    
    # Ha sikeresen teljesítette, frissítjük a statisztikákat
    if passed:
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
    
    # Teljesített leckék számának frissítése (ha szükséges)
    completed_lessons = len([comp for comp in user_progress.completed_lessons 
                           if comp.pages_completed >= comp.total_pages and 
                              (comp.quiz_score is None or comp.quiz_score >= 70)])
    user_progress.total_lessons_completed = completed_lessons
    
    # Napi kihívás reset éjfélkor (ezt egy cron job-nak kellene csinálnia)
    if user_progress.last_activity_date and user_progress.last_activity_date.date() != today:
        user_progress.daily_challenge_completed_today = False