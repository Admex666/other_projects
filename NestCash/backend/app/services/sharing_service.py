# app/services/sharing_service.py
from datetime import datetime
from typing import Optional, Dict, Any
from beanie import PydanticObjectId

from app.models.user import UserDocument, SharedAchievement
from app.models.forum_models import ForumPostDocument
from app.models.badge import UserBadge, BadgeType
from app.models.knowledge import Lesson, UserProgress, LessonCompletion

class SharingService:
    
    @staticmethod
    async def can_share_achievement(user_id: PydanticObjectId, achievement_type: str, achievement_id: str) -> bool:
        """Ellenőrzi, hogy a teljesítmény megosztható-e (még nem osztotta meg)"""
        try:
            user = await UserDocument.get(user_id)
            if not user:
                print(f"ERROR: User not found in can_share_achievement: {user_id}")
                return False
                
            # Ellenőrzi, hogy már megosztotta-e
            for shared in user.shared_achievements:
                if shared.type == achievement_type and shared.achievement_id == achievement_id:  # JAVÍTÁS: String összehasonlítás
                    print(f"INFO: Achievement already shared: {achievement_type}/{achievement_id}")
                    return False
            
            print(f"INFO: Achievement can be shared: {achievement_type}/{achievement_id}")
            return True
            
        except Exception as e:
            print(f"ERROR: Exception in can_share_achievement: {e}")
            return False
    
    @staticmethod
    async def share_badge_achievement(user_id: PydanticObjectId, badge_id: str) -> Optional[str]:
        """Badge megszerzésének megosztása"""
        # Ellenőrzi, hogy megosztható-e
        if not await SharingService.can_share_achievement(user_id, "badge", badge_id):
            return None
            
        # Badge adatok lekérése
        try:
            badge_oid = PydanticObjectId(badge_id)
            user_badge = await UserBadge.find_one({"_id": badge_oid, "user_id": user_id})
        except Exception as e:
            print(f"ERROR: Invalid badge_id format: {badge_id} - {e}")
            return None
            
        if not user_badge:
            print(f"ERROR: Badge not found: {badge_id}")
            return None
            
        badge_type = await BadgeType.find_one({"code": user_badge.badge_code})
        if not badge_type:
            print(f"ERROR: Badge type not found: {user_badge.badge_code}")
            return None
        
        # Fórum post létrehozása
        post_content = f"🏆 Új kitűzőt szereztem!\n\n"
        post_content += f"{badge_type.name}\n"
        post_content += f"{badge_type.description}\n\n"
        post_content += f"Ritkaság: {badge_type.rarity.value} {SharingService._get_rarity_emoji(badge_type.rarity.value)}\n"
        post_content += f"Pontok: {badge_type.points} ⭐\n"
        if user_badge.level > 1:
            post_content += f"Szint: {user_badge.level}\n"
        
        # Először szerezzük be a felhasználó adatait
        user = await UserDocument.get(user_id)
        if not user:
            print(f"ERROR: User not found: {user_id}")
            return None

        forum_post = ForumPostDocument(
            user_id=user_id,
            username=user.username,  # HOZZÁADVA
            title=f"🏆 {badge_type.name} kitűző megszerezve",
            content=post_content,
            category="general",  # HOZZÁADVA - vagy használj PostCategory.TIPS-t
            achievement_type="badge",
            achievement_data={
                "badge_code": badge_type.code,
                "badge_name": badge_type.name,
                "badge_icon": badge_type.icon,
                "rarity": badge_type.rarity.value,
                "points": badge_type.points,
                "level": user_badge.level
            }
        )
        
        await forum_post.insert()
        
        # Megosztás rögzítése a felhasználónál
        try:
            user = await UserDocument.get(user_id)
            if user:
                user.shared_achievements.append(SharedAchievement(
                    type="badge",
                    achievement_id=str(badge_oid),  # JAVÍTÁS: ObjectId használata
                    shared_at=datetime.utcnow()
                ))
                await user.save()
            else:
                print(f"ERROR: User not found: {user_id}")
        except Exception as e:
            print(f"ERROR: Failed to record shared achievement: {e}")
        
        return str(forum_post.id)
    
    @staticmethod
    async def share_lesson_completion(user_id: PydanticObjectId, lesson_id: str) -> Optional[str]:
        """Lecke elvégzésének megosztása"""
        # Ellenőrzi, hogy megosztható-e
        if not await SharingService.can_share_achievement(user_id, "lesson", lesson_id):
            return None
            
        # Lecke adatok lekérése - JAVÍTÁS: PydanticObjectId konverzió
        try:
            lesson_oid = PydanticObjectId(lesson_id)
            lesson = await Lesson.get(lesson_oid)
        except Exception as e:
            print(f"ERROR: Invalid lesson_id format: {lesson_id} - {e}")
            return None
            
        if not lesson:
            print(f"ERROR: Lesson not found: {lesson_id}")
            return None
            
        # Felhasználó haladásának ellenőrzése
        user_progress = await UserProgress.find_one({"user_id": user_id})
        if not user_progress:
            print(f"ERROR: User progress not found for user: {user_id}")
            return None
            
        # Lecke teljesítésének keresése - JAVÍTÁS: ObjectId összehasonlítás
        lesson_completion = None
        for completion in user_progress.completed_lessons:
            # KRITIKUS JAVÍTÁS: ObjectId összehasonlítás helyett string összehasonlítás
            if str(completion.lesson_id) == lesson_id:
                lesson_completion = completion
                break
                
        if not lesson_completion:
            print(f"ERROR: Lesson completion not found for lesson: {lesson_id}")
            return None
        
        # Ellenőrizzük, hogy ténylegesen teljesítve van-e a lecke
        pages_completed = lesson_completion.pages_completed >= lesson_completion.total_pages
        quiz_passed = True  # Alapértelmezett
        
        if len(lesson.quiz_questions) > 0:
            # Van kvíz, ellenőrizzük az eredményt
            quiz_passed = (lesson_completion.best_quiz_score or lesson_completion.quiz_score or 0) >= 70
        
        if not (pages_completed and quiz_passed):
            print(f"ERROR: Lesson not fully completed. Pages: {pages_completed}, Quiz: {quiz_passed}")
            return None
        
        # Fórum post létrehozása
        post_content = f"📚 Elvégeztem egy leckét!\n\n"
        post_content += f"{lesson.title}\n"
        if lesson.description:
            post_content += f"{lesson.description}\n\n"
        post_content += f"Szint: {lesson.difficulty.value} {'🟢' if lesson.difficulty.value == 'beginner' else '🔵'}\n"
        post_content += f"Időtartam: {lesson.estimated_minutes} perc ⏱️\n"
        if lesson_completion.best_quiz_score is not None:
            post_content += f"Kvíz eredmény: {lesson_completion.best_quiz_score}% 📊\n"
        elif lesson_completion.quiz_score is not None:
            post_content += f"Kvíz eredmény: {lesson_completion.quiz_score}% 📊\n"
        
        # Először szerezzük be a felhasználó adatait
        user = await UserDocument.get(user_id)
        if not user:
            print(f"ERROR: User not found: {user_id}")
            return None

        try:
            forum_post = ForumPostDocument(
                user_id=user_id,
                username=user.username,  # HOZZÁADVA
                title=f"📚 {lesson.title} lecke elvégezve",
                content=post_content,
                category="general",  # HOZZÁADVA - vagy használj PostCategory.TIPS-t
                achievement_type="lesson",
                achievement_data={
                    "lesson_title": lesson.title,
                    "lesson_difficulty": lesson.difficulty.value,
                    "estimated_minutes": lesson.estimated_minutes,
                    "quiz_score": lesson_completion.best_quiz_score or lesson_completion.quiz_score,
                    "pages_completed": lesson_completion.pages_completed
                }
            )
            
            await forum_post.insert()
            print(f"SUCCESS: Forum post created with ID: {forum_post.id}")
            
        except Exception as e:
            print(f"ERROR: Failed to create forum post: {e}")
            return None
        
        # Megosztás rögzítése - JAVÍTÁS: PydanticObjectId konverzió
        try:
            user = await UserDocument.get(user_id)
            if user:
                user.shared_achievements.append(SharedAchievement(
                    type="lesson",
                    achievement_id=str(lesson_oid),  # JAVÍTÁS: ObjectId használata
                    shared_at=datetime.utcnow()
                ))
                await user.save()
                print(f"SUCCESS: Shared achievement recorded for user: {user_id}")
            else:
                print(f"ERROR: User not found: {user_id}")
        except Exception as e:
            print(f"ERROR: Failed to record shared achievement: {e}")
            # De a forum post már létrejött, így visszaadjuk az ID-t
        
        return str(forum_post.id)
    
    @staticmethod
    def _get_rarity_emoji(rarity: str) -> str:
        """Ritkaság emoji visszaadása"""
        rarity_emojis = {
            "common": "🟢",
            "uncommon": "🔵", 
            "rare": "🟣",
            "epic": "🟠",
            "legendary": "🟡"
        }
        return rarity_emojis.get(rarity, "⚪")