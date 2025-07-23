# app/models/knowledge.py

from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"  # 🟢Kezdő
    PROFESSIONAL = "professional"  # 🔵Profi

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SINGLE_CHOICE = "single_choice"

class QuizQuestion(BaseModel):
    question: str = Field(..., description="A kérdés szövege")
    type: QuestionType = Field(default=QuestionType.MULTIPLE_CHOICE)
    options: List[str] = Field(..., description="Válaszlehetőségek")
    correct_answers: List[int] = Field(..., description="Helyes válaszok indexei (0-tól kezdve)")
    explanation: Optional[str] = Field(None, description="Magyarázat a válaszhoz")

class LessonPage(BaseModel):
    title: str = Field(..., description="Oldal címe")
    content: str = Field(..., description="Oldal tartalma (markdown vagy sima szöveg)")
    order: int = Field(..., description="Oldal sorrendje a leckén belül")

class Lesson(Document):
    title: str = Field(..., description="Lecke címe")
    description: Optional[str] = Field(None, description="Lecke rövid leírása")
    category_id: PydanticObjectId = Field(..., description="Kategória ID")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    
    # Lecke tartalma
    pages: List[LessonPage] = Field(default_factory=list, description="Lecke oldalai")
    estimated_minutes: int = Field(default=5, description="Becsült tanulási idő percekben")
    
    # Kvíz
    quiz_questions: List[QuizQuestion] = Field(default_factory=list, description="Lecke végi kvíz kérdései")
    
    # Meta adatok
    order: int = Field(default=0, description="Lecke sorrendje a kategórián belül")
    is_published: bool = Field(default=True, description="Publikált-e a lecke")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "lessons"

class KnowledgeCategory(Document):
    name: str = Field(..., description="Kategória neve")
    description: Optional[str] = Field(None, description="Kategória leírása")
    icon: Optional[str] = Field(None, description="Kategória ikonja (emoji vagy ikon név)")
    color: Optional[str] = Field(None, description="Kategória színe (hex kód)")
    order: int = Field(default=0, description="Kategória sorrendje")
    is_active: bool = Field(default=True, description="Aktív-e a kategória")
    
    class Settings:
        name = "knowledge_categories"

# Felhasználói haladás követéshez
class LessonCompletion(BaseModel):
    lesson_id: PydanticObjectId
    completed_at: datetime = Field(default_factory=datetime.now)
    pages_completed: int = Field(default=0, description="Hány oldalt teljesített")
    total_pages: int = Field(default=0, description="Összesen hány oldal van")
    quiz_score: Optional[int] = Field(None, description="Kvíz pontszám %-ban")
    quiz_attempts: int = Field(default=0, description="Hányszor próbálkozott a kvízzel")
    best_quiz_score: Optional[int] = Field(None, description="Legjobb kvíz eredmény")

class UserProgress(Document):
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    
    # Teljesített leckék
    completed_lessons: List[LessonCompletion] = Field(default_factory=list)
    
    # Streak számítás
    current_streak: int = Field(default=0, description="Jelenlegi tanulási sorozat (napok)")
    longest_streak: int = Field(default=0, description="Leghosszabb tanulási sorozat")
    last_activity_date: Optional[datetime] = Field(None, description="Utolsó tanulási aktivitás dátuma")
    
    # Statisztikák
    total_lessons_completed: int = Field(default=0, description="Összes teljesített lecke")
    total_quiz_attempts: int = Field(default=0, description="Összes kvíz próbálkozás")
    average_quiz_score: float = Field(default=0.0, description="Átlagos kvíz eredmény")
    total_study_minutes: int = Field(default=0, description="Összes tanulási idő percekben")
    
    # Napi kihívás
    daily_challenge_completed_today: bool = Field(default=False, description="Ma teljesítette-e a napi kihívást")
    daily_challenge_streak: int = Field(default=0, description="Napi kihívás sorozat")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "user_progress"

# Response modellek
class LessonSummary(BaseModel):
    id: str
    title: str
    description: Optional[str]
    difficulty: DifficultyLevel
    estimated_minutes: int
    total_pages: int
    has_quiz: bool
    is_completed: bool = False
    quiz_score: Optional[int] = None
    category_name: str

class CategoryWithLessons(BaseModel):
    id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    lessons: List[LessonSummary]
    total_lessons: int
    completed_lessons: int

class UserStats(BaseModel):
    current_streak: int
    longest_streak: int
    total_lessons_completed: int
    total_quiz_attempts: int
    average_quiz_score: float
    total_study_minutes: int
    daily_challenge_completed_today: bool
    daily_challenge_streak: int

class QuizResult(BaseModel):
    score: int  # Pontszám %-ban
    correct_answers: int
    total_questions: int
    passed: bool  # Átment-e (pl. 70% felett)
    is_best_score: bool  # Ez-e az eddigi legjobb eredmény