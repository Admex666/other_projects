# app/services/lesson_service.py

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.seeds.lessons import (
    LESSONS_CONTENT, 
    LESSON_CATEGORIES, 
    LESSON_CATEGORY_MAPPING,
    LessonContent as SeedLessonContent,
    LessonPage as SeedLessonPage,
    QuizQuestion as SeedQuizQuestion
)
from app.models.knowledge import (
    DifficultyLevel, 
    QuestionType,
    LessonSummary,
    CategoryWithLessons
)
from app.utils.translation_helper import translate

logger = logging.getLogger(__name__)

class LessonService:
    """Service for managing lessons from seeds"""
    
    def __init__(self):
        self._lessons_cache: Dict[str, Dict[str, Any]] = {}
        self._categories_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize lesson and category cache from seeds"""
        try:
            # Cache lessons
            for lesson_id, translations in LESSONS_CONTENT.items():
                self._lessons_cache[lesson_id] = {}
                for lang, content in translations.items():
                    self._lessons_cache[lesson_id][lang] = self._convert_seed_to_lesson_dict(
                        lesson_id, content, lang
                    )
            
            # Cache categories
            for lang in ['hu', 'en']:
                self._categories_cache[lang] = self._build_categories_with_lessons(lang)
                
            logger.info(f"Initialized lesson cache with {len(self._lessons_cache)} lessons")
            
        except Exception as e:
            logger.error(f"Error initializing lesson cache: {e}")
            raise
    
    def _convert_seed_to_lesson_dict(self, lesson_id: str, content: SeedLessonContent, lang: str) -> Dict[str, Any]:
        """Convert seed lesson content to dictionary format"""
        
        # Determine difficulty based on lesson_id (you can customize this logic)
        difficulty = DifficultyLevel.BEGINNER
        if 'advanced' in lesson_id or 'professional' in lesson_id:
            difficulty = DifficultyLevel.PROFESSIONAL
        
        # Convert pages
        pages = []
        for seed_page in content.pages:
            pages.append({
                'title': seed_page.title,
                'content': seed_page.content,
                'order': seed_page.order
            })
        
        # Convert quiz questions
        quiz_questions = []
        for seed_question in content.quiz_questions:
            question_type = QuestionType.SINGLE_CHOICE
            if seed_question.type == 'multiple_choice':
                question_type = QuestionType.MULTIPLE_CHOICE
            elif seed_question.type == 'true_false':
                question_type = QuestionType.TRUE_FALSE
            
            quiz_questions.append({
                'question': seed_question.question,
                'type': question_type,
                'options': seed_question.options,
                'correct_answers': seed_question.correct_answers,
                'explanation': seed_question.explanation
            })
        
        # Estimate reading time (rough calculation: 200 words per minute)
        total_content = ' '.join([page.content for page in content.pages])
        word_count = len(total_content.split())
        estimated_minutes = max(1, word_count // 200)
        
        return {
            'id': lesson_id,
            'title': content.title,
            'description': content.description,
            'difficulty': difficulty.value,
            'estimated_minutes': estimated_minutes,
            'pages': pages,
            'quiz_questions': quiz_questions,
            'category_id': LESSON_CATEGORY_MAPPING.get(lesson_id, 'basic_finance'),
            'is_published': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _build_categories_with_lessons(self, lang: str) -> List[Dict[str, Any]]:
        """Build categories with their lessons for a specific language"""
        categories_dict = {}
        
        # Initialize categories
        for category_id, category_names in LESSON_CATEGORIES.items():
            category_name = category_names.get(lang, category_names.get('hu', category_id))
            categories_dict[category_id] = {
                'id': category_id,
                'name': category_name,
                'description': f"{category_name} kategória leckéi" if lang == 'hu' else f"Lessons in {category_name} category",
                'icon': self._get_default_category_icon(category_id),
                'color': self._get_default_category_color(category_id),
                'lessons': [],
                'total_lessons': 0,
                'completed_lessons': 0
            }
        
        # Add lessons to categories
        for lesson_id, category_id in LESSON_CATEGORY_MAPPING.items():
            if category_id in categories_dict and lesson_id in self._lessons_cache:
                lesson_data = self._lessons_cache[lesson_id].get(lang)
                if lesson_data:
                    lesson_summary = {
                        'id': lesson_id,
                        'title': lesson_data['title'],
                        'description': lesson_data['description'],
                        'difficulty': lesson_data['difficulty'],
                        'estimated_minutes': lesson_data['estimated_minutes'],
                        'total_pages': len(lesson_data['pages']),
                        'has_quiz': len(lesson_data['quiz_questions']) > 0,
                        'is_completed': False,  # This will be updated with user progress
                        'quiz_score': None,
                        'category_name': categories_dict[category_id]['name']
                    }
                    categories_dict[category_id]['lessons'].append(lesson_summary)
                    categories_dict[category_id]['total_lessons'] += 1
        
        return list(categories_dict.values())
    
    def _get_default_category_icon(self, category_id: str) -> str:
        """Get default icon for category"""
        icons = {
            'basic_finance': '💰',
            'savings': '🏦',
            'investment': '📈',
            'debt': '💳',
            'insurance': '🛡️'
        }
        return icons.get(category_id, '📚')
    
    def _get_default_category_color(self, category_id: str) -> str:
        """Get default color for category"""
        colors = {
            'basic_finance': '#00D4A3',
            'savings': '#4A90E2',
            'investment': '#7B68EE',
            'debt': '#FF6B6B',
            'insurance': '#FFA500'
        }
        return colors.get(category_id, '#00D4A3')
    
    def get_categories_with_lessons(self, lang: str = 'hu', user_progress: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all categories with their lessons in specified language"""
        try:
            categories = self._categories_cache.get(lang, self._categories_cache.get('hu', []))
            
            # Update completion status if user progress provided
            if user_progress:
                completed_lessons = user_progress.get('completed_lessons', {})
                
                for category in categories:
                    completed_count = 0
                    for lesson in category['lessons']:
                        lesson_id = lesson['id']
                        if lesson_id in completed_lessons:
                            completion_data = completed_lessons[lesson_id]
                            pages_done = completion_data.get('pages_completed', 0) >= completion_data.get('total_pages', 1)
                            quiz_ok = completion_data.get('quiz_score') is None or completion_data.get('quiz_score', 0) >= 70
                            
                            if pages_done and quiz_ok:
                                lesson['is_completed'] = True
                                lesson['quiz_score'] = completion_data.get('quiz_score')
                                completed_count += 1
                    
                    category['completed_lessons'] = completed_count
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories with lessons: {e}")
            return []
    
    def get_lesson_by_id(self, lesson_id: str, lang: str = 'hu') -> Optional[Dict[str, Any]]:
        """Get a specific lesson by ID in specified language"""
        try:
            if lesson_id not in self._lessons_cache:
                logger.warning(f"Lesson {lesson_id} not found in cache")
                return None
            
            lesson_data = self._lessons_cache[lesson_id].get(lang)
            if not lesson_data:
                # Fallback to Hungarian if requested language not available
                lesson_data = self._lessons_cache[lesson_id].get('hu')
                if lesson_data:
                    logger.warning(f"Lesson {lesson_id} not available in {lang}, falling back to Hungarian")
            
            return lesson_data
            
        except Exception as e:
            logger.error(f"Error getting lesson {lesson_id}: {e}")
            return None
    
    def get_available_languages(self, lesson_id: str) -> List[str]:
        """Get list of available languages for a specific lesson"""
        if lesson_id in self._lessons_cache:
            return list(self._lessons_cache[lesson_id].keys())
        return []
    
    def get_all_lesson_ids(self) -> List[str]:
        """Get all available lesson IDs"""
        return list(self._lessons_cache.keys())
    
    def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists"""
        return lesson_id in self._lessons_cache
    
    def get_lessons_by_category(self, category_id: str, lang: str = 'hu') -> List[Dict[str, Any]]:
        """Get all lessons in a specific category"""
        try:
            lessons = []
            for lesson_id, mapped_category in LESSON_CATEGORY_MAPPING.items():
                if mapped_category == category_id and lesson_id in self._lessons_cache:
                    lesson_data = self._lessons_cache[lesson_id].get(lang)
                    if lesson_data:
                        lessons.append(lesson_data)
            
            return sorted(lessons, key=lambda x: x.get('order', 0))
            
        except Exception as e:
            logger.error(f"Error getting lessons for category {category_id}: {e}")
            return []
    
    def get_lesson_stats(self) -> Dict[str, int]:
        """Get statistics about available lessons"""
        total_lessons = len(self._lessons_cache)
        total_categories = len(LESSON_CATEGORIES)
        
        language_counts = {}
        for lesson_id, translations in self._lessons_cache.items():
            for lang in translations.keys():
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return {
            'total_lessons': total_lessons,
            'total_categories': total_categories,
            'languages': language_counts
        }


# Global instance
lesson_service = LessonService()