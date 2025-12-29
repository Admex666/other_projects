from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class Lesson(BaseModel):
    """Schema for lesson data"""
    id: str
    title: str
    category: str  # "theory", "strategy", "pro"
    difficulty: str  # "beginner", "intermediate", "advanced"
    duration_minutes: int
    content: str  # Markdown content
    quiz_questions: Optional[List[Dict]] = None
    prerequisites: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class LessonProgress(BaseModel):
    """Schema for lesson progress update"""
    lesson_id: str
    completed: bool = False
    time_spent_minutes: float = 0.0
    quiz_score: Optional[float] = None


class QuizSubmission(BaseModel):
    """Schema for quiz answer submission"""
    lesson_id: str
    answers: Dict[str, str]  # question_id -> answer
