# app/services/pti_notifications.py
import logging
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.models.pti import PTIScore, UserPTISettings, PTIPeriod
from app.models.notification import NotificationDocument
from app.services.pti_service import PTIService

logger = logging.getLogger(__name__)

class PTINotificationService:
    """PTI értesítések kezelése"""
    
    @staticmethod
    async def send_weekly_pti_summary(user_id: str) -> bool:
        """Heti PTI összefoglaló értesítés küldése"""
        try:
            # Felhasználó beállításainak ellenőrzése
            settings = await UserPTISettings.find_one(
                UserPTISettings.user_id == PydanticObjectId(user_id)
            )
            
            if not settings or not settings.notify_weekly_summary:
                return False
            
            # Aktuális heti PTI lekérése
            current_pti = await PTIService.calculate_pti_score(user_id, PTIPeriod.WEEKLY)
            
            # Rangsor lekérése
            ranking = await PTIService.get_user_ranking(
                user_id, PTIPeriod.WEEKLY, from app.models.pti import RankingScope.GLOBAL, 1, 0
            )
            
            # Értesítés szövegének összeállítása
            title = "📊 Heti PTI Összefoglaló"
            
            message_parts = [
                f"🎯 PTI pontszámod: {current_pti.total_pti:.1f}",
                f"📍 Rangsorod: {ranking.user_rank if ranking.user_rank else 'N/A'}"
            ]
            
            # Cél teljesítés
            if settings.weekly_pti_goal:
                goal_progress = (current_pti.total_pti / settings.weekly_pti_goal) * 100
                if goal_progress >= 100:
                    message_parts.append("🎉 Heti célodat teljesítetted!")
                else:
                    message_parts.append(f"⏳ Heti cél: {goal_progress:.0f}% ({settings.weekly_pti_goal - current_pti.total_pti:.1f} pont hiányzik)")
            
            # Komponensek kiemelése
            best_component = max([
                ("Tanulás", current_pti.learning_points),
                ("Szokások", current_pti.habit_score),
                ("Badge-ek", current_pti.badge_score),
                ("Limitek", current_pti.limit_score)
            ], key=lambda x: x[1])
            
            message_parts.append(f"💪 Legerősebb terület: {best_component[0]} ({best_component[1]:.1f} pont)")
            
            message = "\n".join(message_parts)
            
            # Értesítés létrehozása
            notification = NotificationDocument(
                user_id=PydanticObjectId(user_id),
                title=title,
                message=message,
                type="pti_weekly_summary",
                priority="normal",
                data={
                    "pti_score": current_pti.total_pti,
                    "rank": ranking.user_rank,
                    "components": {
                        "learning": current_pti.learning_points,
                        "habits": current_pti.habit_score,
                        "badges": current_pti.badge_score,
                        "limits": current_pti.limit_score
                    }
                }
            )
            
            await notification.insert()
            logger.info(f"Weekly PTI summary sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending weekly PTI summary to user {user_id}: {e}")
            return False
    
    @staticmethod
    async def notify_rank_change(user_id: str, period: PTIPeriod, old_rank: Optional[int], new_rank: int) -> bool:
        """Rangsor változás értesítése"""
        try:
            # Felhasználó beállításainak ellenőrzése
            settings = await UserPTISettings.find_one(
                UserPTISettings.user_id == PydanticObjectId(user_id)
            )
            
            if not settings or not settings.notify_rank_change:
                return False
            
            # Ha nincs jelentős változás, ne küldjünk értesítést
            if old_rank and abs(old_rank - new_rank) < 3:
                return False
            
            # Értesítés szövegének összeállítása
            period_text = {
                PTIPeriod.WEEKLY: "heti",
                PTIPeriod.MONTHLY: "havi", 
                PTIPeriod.YEARLY: "éves"
            }[period]
            
            if old_rank is None:
                title = f"📈 Első {period_text} rangsorod"
                message = f"Gratulálunk! A {period_text} ranglistán a {new_rank}. helyen állsz!"
                emoji = "🎉"
            elif new_rank < old_rank:
                # Javulás
                improvement = old_rank - new_rank
                title = f"🚀 Rangsor javulás"
                message = f"Szuper! A {period_text} ranglistán {improvement} helyet léptél előre!\n{old_rank}. → {new_rank}. hely"
                emoji = "📈"
            else:
                # Romlás
                decline = new_rank - old_rank
                title = f"📉 Rangsor változás"
                message = f"A {period_text} ranglistán {decline} helyet léptél vissza.\n{old_rank}. → {new_rank}. hely\n\nNe izgulj, a következő időszakban visszaveheted az előkelő helyet!"
                emoji = "💪"
            
            # Értesítés létrehozása
            notification = NotificationDocument(
                user_id=PydanticObjectId(user_id),
                title=title,
                message=message,
                type="pti_rank_change",
                priority="normal" if new_rank < old_rank else "low",
                data={
                    "period": period.value,
                    "old_rank": old_rank,
                    "new_rank": new_rank,
                    "change": (old_rank - new_rank) if old_rank else 0
                }
            )
            
            await notification.insert()
            logger.info(f"Rank change notification sent to user {user_id}: {old_rank} -> {new_rank}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending rank change notification to user {user_id}: {e}")
            return False
    
    @staticmethod
    async def notify_pti_milestone(user_id: str, milestone_type: str, value: float) -> bool:
        """PTI mérföldkő értesítése"""
        try:
            # Felhasználó beállításainak ellenőrzése
            settings = await UserPTISettings.find_one(
                UserPTISettings.user_id == PydanticObjectId(user_id)
            )
            
            if not settings or not settings.notify_achievements:
                return False
            
            # Mérföldkő típus alapján szöveg összeállítása
            milestones = {
                "first_50": ("🎯 Első 50 PTI pont!", f"Gratulálunk! Elérted az első 50 PTI pontot ({value:.1f})!"),
                "first_70": ("⭐ 70 PTI pont!", f"Szuper teljesítmény! 70+ PTI pontot értél el ({value:.1f})!"),
                "first_90": ("🏆 90+ PTI pont!", f"Kiváló! Elérted a 90+ PTI pontot ({value:.1f})!"),
                "perfect_100": ("💎 Tökéletes PTI!", f"Hihetetlen! 100 PTI pontot értél el! ({value:.1f})"),
                "goal_achieved": ("🎉 Cél teljesítve!", f"Gratulálunk! Elérted a kitűzött célodat! ({value:.1f} PTI pont)")
            }
            
            if milestone_type not in milestones:
                return False
            
            title, message = milestones[milestone_type]
            
            # Értesítés létrehozása
            notification = NotificationDocument(
                user_id=PydanticObjectId(user_id),
                title=title,
                message=message,
                type="pti_milestone",
                priority="high",
                data={
                    "milestone_type": milestone_type,
                    "pti_value": value
                }
            )
            
            await notification.insert()
            logger.info(f"PTI milestone notification sent to user {user_id}: {milestone_type}")
            return True