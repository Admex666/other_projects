from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import os

from database import get_db
from models.user import User
from models.progress import LearningProgress
from schemas.academy import Lesson, LessonProgress, QuizSubmission
from api.auth import get_current_user

router = APIRouter()

# Path to lessons data
LESSONS_DIR = os.path.join(os.path.dirname(__file__), "..", "academy", "lessons")


def load_lesson(lesson_id: str) -> dict:
    """Load lesson data from JSON file"""
    lesson_path = os.path.join(LESSONS_DIR, f"{lesson_id}.json")
    
    if not os.path.exists(lesson_path):
        return None
    
    with open(lesson_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.get("/lessons", response_model=List[Lesson])
async def get_lessons(
    category: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available lessons, optionally filtered by category"""
    
    # TODO: Load from database or file system
    # For now, return sample lessons
    sample_lessons = [
        {
            "id": "basic_math_01",
            "title": "Póker Matematika Alapok",
            "category": "theory",
            "difficulty": "beginner",
            "duration_minutes": 10,
            "content": "# Póker Matematika\n\nA pókerben minden döntés matematikai alapokon nyugszik...",
            "prerequisites": []
        },
        {
            "id": "position_basics_01",
            "title": "Pozíció Jelentősége",
            "category": "theory",
            "difficulty": "beginner",
            "duration_minutes": 8,
            "content": "# Pozíció a Pókerben\n\nA pozíció az egyik legfontosabb koncepció...",
            "prerequisites": []
        },
        {
            "id": "range_construction_01",
            "title": "Range Építés",
            "category": "strategy",
            "difficulty": "intermediate",
            "duration_minutes": 15,
            "content": "# Range vs Range Gondolkodás\n\nA modern póker alapja...",
            "prerequisites": ["basic_math_01", "position_basics_01"]
        }
    ]
    
    if category:
        sample_lessons = [l for l in sample_lessons if l["category"] == category]
    
    return sample_lessons


@router.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific lesson by ID"""
    
    # Sample lesson data
    lessons = {
        "basic_math_01": {
            "id": "basic_math_01",
            "title": "Póker Matematika Alapok",
            "category": "theory",
            "difficulty": "beginner",
            "duration_minutes": 10,
            "content": """# Póker Matematika Alapok

## Pot Odds (Pot Esélyek)

A pot odds azt mutatja meg, hogy milyen arányban kell nyernünk ahhoz, hogy egy call nyereséges legyen.

**Képlet:** Pot Odds = Call mérete / (Pot mérete + Call mérete)

**Példa:**
- Pot: 100 BB
- Ellenfél bet: 50 BB
- Call méretünk: 50 BB

Pot Odds = 50 / (100 + 50 + 50) = 50/200 = 25%

Tehát legalább 25%-ban kell nyernünk ahhoz, hogy a call nyereséges legyen.

## Equity (Esély a nyerésre)

Az equity azt mutatja, hogy milyen eséllyel nyerjük meg a pot-ot.

**Példa:**
- Kezünk: A♠ K♠
- Board: Q♠ 10♠ 3♣
- Ellenfél: J♦ J♥

Nekünk van flush draw (9 out) + straight draw (8 out, de 3 átfed) = ~12 out

12 out × 2 = ~24% equity a turn-ön

## EV (Expected Value - Várható Érték)

EV = (Nyerési esély × Nyeremény) - (Vesztési esély × Veszteség)

**Példa:**
- Pot: 100 BB
- Call: 50 BB
- Equity: 30%

EV = (0.30 × 150) - (0.70 × 50) = 45 - 35 = +10 BB

Pozitív EV → call nyereséges!
""",
            "quiz_questions": [
                {
                    "id": "q1",
                    "question": "Ha a pot 80 BB és az ellenfél 40 BB-t bet-el, mennyi a pot odds?",
                    "options": ["25%", "33%", "50%"],
                    "correct": "25%"
                }
            ],
            "prerequisites": []
        }
    }
    
    if lesson_id not in lessons:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return lessons[lesson_id]


@router.post("/progress")
async def update_progress(
    progress_data: LessonProgress,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update lesson progress"""
    
    # Find existing progress
    existing = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.lesson_id == progress_data.lesson_id
    ).first()
    
    if existing:
        # Update existing
        existing.completed = progress_data.completed
        existing.time_spent_minutes += progress_data.time_spent_minutes
        if progress_data.quiz_score is not None:
            existing.quiz_score = progress_data.quiz_score
        if progress_data.completed:
            from datetime import datetime
            existing.completion_date = datetime.utcnow()
    else:
        # Create new
        new_progress = LearningProgress(
            user_id=current_user.id,
            lesson_id=progress_data.lesson_id,
            lesson_category="theory",  # TODO: Get from lesson
            completed=progress_data.completed,
            time_spent_minutes=progress_data.time_spent_minutes,
            quiz_score=progress_data.quiz_score
        )
        db.add(new_progress)
    
    db.commit()
    
    return {"success": True, "message": "Progress updated"}


@router.get("/my-progress")
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's learning progress"""
    
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id
    ).all()
    
    return {
        "total_lessons": len(progress),
        "completed_lessons": len([p for p in progress if p.completed]),
        "total_study_time": sum(p.time_spent_minutes for p in progress),
        "average_quiz_score": sum(p.quiz_score or 0 for p in progress) / len(progress) if progress else 0,
        "lessons": progress
    }
