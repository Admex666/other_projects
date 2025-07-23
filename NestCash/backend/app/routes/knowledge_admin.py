# app/routes/knowledge_admin.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime

from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge import (
    KnowledgeCategory, Lesson, LessonPage, QuizQuestion, 
    DifficultyLevel, QuestionType, UserProgress
)
from pydantic import BaseModel

router = APIRouter(prefix="/admin/knowledge", tags=["knowledge-admin"])

# Request models
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    order: int = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: str
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    pages: List[LessonPage] = []
    quiz_questions: List[QuizQuestion] = []
    estimated_minutes: int = 5
    order: int = 0

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    pages: Optional[List[LessonPage]] = None
    quiz_questions: Optional[List[QuizQuestion]] = None
    estimated_minutes: Optional[int] = None
    order: Optional[int] = None
    is_published: Optional[bool] = None

class SampleDataCreate(BaseModel):
    create_categories: bool = True
    create_lessons: bool = True
    lessons_per_category: int = 3

# TODO: Itt egy admin jogosultság ellenőrzést kellene implementálni
# async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
#     if not current_user.is_admin:  # Ez a mező nincs még implementálva
#         raise HTTPException(status_code=403, detail="Admin access required")
#     return current_user

# === KATEGÓRIA KEZELÉS ===

@router.get("/categories", response_model=List[KnowledgeCategory])
async def get_all_categories(
    current_user: User = Depends(get_current_user),  # Később: get_admin_user
    include_inactive: bool = False
):
    """Összes kategória lekérése (adminisztrációs)"""
    
    query = {} if include_inactive else {"is_active": True}
    categories = await KnowledgeCategory.find(query).sort("order").to_list()
    return categories

@router.post("/categories", response_model=KnowledgeCategory)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Új kategória létrehozása"""
    
    category = KnowledgeCategory(**category_data.dict())
    await category.insert()
    return category

@router.put("/categories/{category_id}", response_model=KnowledgeCategory)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Kategória frissítése"""
    
    category = await KnowledgeCategory.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Csak a megadott mezők frissítése
    update_data = {k: v for k, v in category_data.dict().items() if v is not None}
    
    for key, value in update_data.items():
        setattr(category, key, value)
    
    await category.save()
    return category

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Kategória törlése"""
    
    category = await KnowledgeCategory.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Ellenőrizzük, hogy vannak-e leckék a kategóriában
    lessons_in_category = await Lesson.find({"category_id": category.id}).to_list()
    if lessons_in_category:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with existing lessons. Move or delete lessons first."
        )
    
    await category.delete()
    return {"message": "Category deleted successfully"}

# === LECKE KEZELÉS ===

@router.post("/lessons", response_model=Lesson)
async def create_lesson(
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Új lecke létrehozása"""
    
    # Ellenőrizzük, hogy létezik-e a kategória
    category = await KnowledgeCategory.get(lesson_data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    lesson = Lesson(**lesson_data.dict())
    await lesson.insert()
    return lesson

@router.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson_admin(
    lesson_id: str,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Lecke részletes adatainak lekérése (adminisztrációs)"""
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return lesson

@router.put("/lessons/{lesson_id}", response_model=Lesson)
async def update_lesson(
    lesson_id: str,
    lesson_data: LessonUpdate,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Lecke frissítése"""
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Ha kategória változik, ellenőrizzük hogy létezik-e
    if lesson_data.category_id and lesson_data.category_id != str(lesson.category_id):
        category = await KnowledgeCategory.get(lesson_data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="New category not found")
    
    # Csak a megadott mezők frissítése
    update_data = {k: v for k, v in lesson_data.dict().items() if v is not None}
    
    for key, value in update_data.items():
        setattr(lesson, key, value)
    
    lesson.updated_at = datetime.now()
    await lesson.save()
    return lesson

@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Lecke törlése"""
    
    lesson = await Lesson.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    await lesson.delete()
    return {"message": "Lesson deleted successfully"}

@router.get("/lessons", response_model=List[Lesson])
async def get_all_lessons(
    current_user: User = Depends(get_current_user),  # Később: get_admin_user
    category_id: Optional[str] = None,
    include_unpublished: bool = True
):
    """Összes lecke lekérése (adminisztrációs)"""
    
    query = {}
    if category_id:
        query["category_id"] = category_id
    if not include_unpublished:
        query["is_published"] = True
    
    lessons = await Lesson.find(query).sort("category_id", "order").to_list()
    return lessons

# === GYORS ADATFELTÖLTÉS ===

@router.post("/bulk-create-sample-data")
async def create_sample_data(
    data_config: SampleDataCreate,
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Minta adatok létrehozása teszteléshez"""
    
    created_categories = []
    created_lessons = []
    
    if data_config.create_categories:
        # Kategóriák létrehozása
        sample_categories = [
            {
                "name": "💰 Alapvető pénzügyek",
                "description": "Pénzügyi alapismeretek mindenkinek",
                "icon": "💰",
                "color": "#4CAF50",
                "order": 1
            },
            {
                "name": "📊 Befektetések",
                "description": "Hogyan fektessük be okosan a pénzünket",
                "icon": "📊", 
                "color": "#2196F3",
                "order": 2
            },
            {
                "name": "🏠 Ingatlan",
                "description": "Ingatlanvásárlás és -finanszírozás",
                "icon": "🏠",
                "color": "#FF9800",
                "order": 3
            },
            {
                "name": "🎯 Pénzügyi tervezés",
                "description": "Hosszú távú pénzügyi célok elérése",
                "icon": "🎯",
                "color": "#9C27B0",
                "order": 4
            }
        ]
        
        for cat_data in sample_categories:
            category = KnowledgeCategory(**cat_data)
            await category.insert()
            created_categories.append(category)
    
    if data_config.create_lessons and created_categories:
        # Leckék létrehozása minden kategóriához
        sample_lessons = {
            "💰 Alapvető pénzügyek": [
                {
                    "title": "Mi a pénz?",
                    "description": "A pénz története és szerepe a modern világban",
                    "difficulty": DifficultyLevel.BEGINNER,
                    "estimated_minutes": 10,
                    "pages": [
                        {
                            "title": "A pénz definíciója",
                            "content": "A pénz egy **csereeszköz**, **értékmérő** és **értéktároló**.\n\nFunkciói:\n- Megkönnyíti a kereskedelmet\n- Lehetővé teszi az értékek összehasonlítását\n- Időben megőrzi az értéket",
                            "order": 1
                        },
                        {
                            "title": "A pénz történeti fejlődése",
                            "content": "A pénz fejlődése:\n\n1. **Naturálgazdaság** - áruk cseréje\n2. **Árucsere** - értékes tárgyak (só, tea)\n3. **Fémek** - arany, ezüst\n4. **Papírpénz** - modern bankjegyek\n5. **Digitális pénz** - bankkártyák, kriptovaluták",
                            "order": 2
                        }
                    ],
                    "quiz_questions": [
                        {
                            "question": "Melyek a pénz fő funkciói?",
                            "type": QuestionType.MULTIPLE_CHOICE,
                            "options": ["Csereeszköz", "Értékmérő", "Értéktároló", "Státuszszimbólum"],
                            "correct_answers": [0, 1, 2],
                            "explanation": "A pénz három fő funkciója: csereeszköz, értékmérő és értéktároló."
                        }
                    ]
                },
                {
                    "title": "Költségvetés készítése",
                    "description": "Hogyan tervezzük meg havi kiadásainkat",
                    "difficulty": DifficultyLevel.BEGINNER,
                    "estimated_minutes": 15,
                    "pages": [
                        {
                            "title": "Miért fontos a költségvetés?",
                            "content": "A **költségvetés** segít:\n\n✅ Kontrollt szerezni a pénzügyek felett\n✅ Spórolási célokat elérni\n✅ Felesleges kiadásokat azonosítani\n✅ Pénzügyi stresszt csökkenteni",
                            "order": 1
                        },
                        {
                            "title": "50/30/20 szabály",
                            "content": "**Egyszerű költségvetési szabály:**\n\n- **50%** - Szükségletek (lakhatás, étel, közlekedés)\n- **30%** - Vágyak (szórakozás, hobbik)\n- **20%** - Megtakarítás és adósságtörlesztés\n\nPéldául 300.000 Ft nettó jövedelem esetén:\n- 150.000 Ft szükségletekre\n- 90.000 Ft vágyakra  \n- 60.000 Ft megtakarításra",
                            "order": 2
                        }
                    ],
                    "quiz_questions": [
                        {
                            "question": "Az 50/30/20 szabály szerint mennyi százalékot kellene megtakarításra fordítani?",
                            "type": QuestionType.SINGLE_CHOICE,
                            "options": ["10%", "20%", "30%", "50%"],
                            "correct_answers": [1],
                            "explanation": "Az 50/30/20 szabály szerint a jövedelem 20%-át kellene megtakarításra és adósságtörlesztésre fordítani."
                        }
                    ]
                }
            ],
            "📊 Befektetések": [
                {
                    "title": "Befektetési alapok",
                    "description": "Mi az a befektetés és miért fontos?",
                    "difficulty": DifficultyLevel.BEGINNER,
                    "estimated_minutes": 12,
                    "pages": [
                        {
                            "title": "Mit jelent befektetni?",
                            "content": "**Befektetés** = pénzünket olyan eszközökbe fektetjük, amelyek idővel növelik az értéküket.\n\n**Célja:** Megvédeni a pénzünket az inflációtól és növelni a vagyonunkat.\n\n**Alapelv:** Ne tedd egy kosárba az összes tojást! (diverzifikáció)",
                            "order": 1
                        }
                    ],
                    "quiz_questions": [
                        {
                            "question": "Mi a befektetés fő célja?",
                            "type": QuestionType.SINGLE_CHOICE,
                            "options": ["Gyors meggazdagodás", "Infláció elleni védelem és vagyonnövelés", "Spekuláció", "Szerencsejáték"],
                            "correct_answers": [1],
                            "explanation": "A befektetés fő célja a pénz inflációtól való megvédése és hosszú távú vagyonnövelés."
                        }
                    ]
                }
            ]
        }
        
        for category in created_categories:
            if category.name in sample_lessons:
                lessons_data = sample_lessons[category.name]
                for i, lesson_data in enumerate(lessons_data[:data_config.lessons_per_category]):
                    lesson_data["category_id"] = category.id
                    lesson_data["order"] = i + 1
                    
                    lesson = Lesson(**lesson_data)
                    await lesson.insert()
                    created_lessons.append(lesson)
    
    return {
        "message": "Sample data created successfully",
        "created_categories": len(created_categories),
        "created_lessons": len(created_lessons)
    }

@router.delete("/clear-all-data")
async def clear_all_data(
    current_user: User = Depends(get_current_user),  # Később: get_admin_user
    confirm: bool = False
):
    """FIGYELEM: Összes tudástár adat törlése (csak fejlesztéshez!)"""
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Please set confirm=true to delete all data. This action cannot be undone!"
        )
    
    # Összes adat törlése
    await Lesson.delete_all()
    await KnowledgeCategory.delete_all()
    await UserProgress.delete_all()
    
    return {"message": "All knowledge data has been deleted"}

# === STATISZTIKÁK ÉS JELENTÉSEK ===

@router.get("/stats/overview")
async def get_admin_stats(
    current_user: User = Depends(get_current_user)  # Később: get_admin_user
):
    """Admin áttekintő statisztikák"""
    
    # Kategóriák száma
    total_categories = await KnowledgeCategory.find({"is_active": True}).count()
    
    # Leckék száma
    total_lessons = await Lesson.find({"is_published": True}).count()
    published_lessons = await Lesson.find({"is_published": True}).count()
    draft_lessons = await Lesson.find({"is_published": False}).count()
    
    # Felhasználói statisztikák
    total_users_with_progress = await UserProgress.find().count()
    
    # Legnépszerűbb leckék (legtöbbet teljesített)
    all_progress = await UserProgress.find().to_list()
    lesson_completion_count = {}
    
    for progress in all_progress:
        for completion in progress.completed_lessons:
            lesson_id = str(completion.lesson_id)
            if completion.pages_completed >= completion.total_pages:
                lesson_completion_count[lesson_id] = lesson_completion_count.get(lesson_id, 0) + 1
    
    # Top 5 lecke
    top_lessons = sorted(lesson_completion_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "categories": {
            "total": total_categories
        },
        "lessons": {
            "total": total_lessons,
            "published": published_lessons,
            "drafts": draft_lessons
        },
        "users": {
            "with_progress": total_users_with_progress
        },
        "popular_lessons": [
            {"lesson_id": lesson_id, "completions": count} 
            for lesson_id, count in top_lessons
        ]
    }

@router.get("/stats/user-progress")
async def get_user_progress_stats(
    current_user: User = Depends(get_current_user),  # Később: get_admin_user
    limit: int = 20
):
    """Felhasználói haladás statisztikák"""
    
    # Top felhasználók (legtöbb teljesített lecke)
    all_progress = await UserProgress.find().sort([("total_lessons_completed", -1)]).limit(limit).to_list()
    
    user_stats = []
    for progress in all_progress:
        user_stats.append({
            "user_id": str(progress.user_id),
            "total_lessons_completed": progress.total_lessons_completed,
            "current_streak": progress.current_streak,
            "total_study_minutes": progress.total_study_minutes,
            "average_quiz_score": progress.average_quiz_score
        })
    
    return {
        "top_users": user_stats
    }