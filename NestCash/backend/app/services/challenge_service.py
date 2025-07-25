# app/services/challenge_service.py
from typing import List, Dict, Optional, Tuple
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime, timedelta
import logging

from app.models.challenge import (
    ChallengeDocument, UserChallengeDocument, ChallengeType, ChallengeDifficulty,
    ChallengeStatus, ParticipationStatus, ChallengeProgress
)
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

class ChallengeService:
    """Kihívások kezelésére szolgáló service osztály"""
    
    @staticmethod
    async def calculate_challenge_progress(
        user_id: str, 
        challenge: ChallengeDocument,
        user_challenge: UserChallengeDocument
    ) -> ChallengeProgress:
        """
        Kiszámítja a felhasználó haladását egy kihívásban
        """
        try:
            # Időszak meghatározása
            start_date = user_challenge.started_at or user_challenge.joined_at
            end_date = start_date + timedelta(days=challenge.duration_days)
            
            # Tranzakciók lekérése az időszakra
            query_filter = {
                "user_id": ObjectId(user_id),
                "date": {
                    "$gte": start_date.strftime("%Y-%m-%d"),
                    "$lte": end_date.strftime("%Y-%m-%d")
                }
            }
            
            # Típus alapú szűrés
            if challenge.challenge_type == ChallengeType.SAVINGS:
                # Megtakarítások számítása (pozitív összegek a megtakarítási számlán)
                query_filter.update({
                    "main_account": "megtakaritas",
                    "amount": {"$gt": 0}
                })
            elif challenge.challenge_type == ChallengeType.EXPENSE_REDUCTION:
                # Kiadások számítása
                query_filter["amount"] = {"$lt": 0}
                # Ha meg van adva kategória, azt is figyelembe vesszük
                if challenge.track_categories:
                    query_filter["kategoria"] = {"$in": challenge.track_categories}
            elif challenge.challenge_type == ChallengeType.INVESTMENT:
                # Befektetések számítása
                query_filter.update({
                    "main_account": "befektetes",
                    "amount": {"$gt": 0}
                })
            
            # Számla szűrés ha van
            if challenge.track_accounts:
                query_filter["sub_account_name"] = {"$in": challenge.track_accounts}
            
            transactions = await Transaction.find(query_filter).to_list()
            
            # Haladás számítása típus alapján
            current_value = 0.0
            
            if challenge.challenge_type == ChallengeType.SAVINGS:
                current_value = sum(abs(t.amount) for t in transactions)
            elif challenge.challenge_type == ChallengeType.EXPENSE_REDUCTION:
                # Kiadás csökkentésnél az előző időszakhoz viszonyítunk
                current_value = await ChallengeService._calculate_expense_reduction(
                    user_id, challenge, start_date, transactions
                )
            elif challenge.challenge_type == ChallengeType.HABIT_STREAK:
                current_value = await ChallengeService._calculate_streak(
                    user_id, challenge, start_date, transactions
                )
            elif challenge.challenge_type == ChallengeType.INVESTMENT:
                current_value = sum(abs(t.amount) for t in transactions)
            else:
                current_value = sum(abs(t.amount) for t in transactions)
            
            # Célérték meghatározása
            target_value = user_challenge.personal_target or challenge.target_amount or 0.0
            
            # Százalék számítása
            percentage = min((current_value / target_value * 100) if target_value > 0 else 0, 100.0)
            
            return ChallengeProgress(
                current_value=current_value,
                target_value=target_value,
                unit="HUF" if challenge.challenge_type != ChallengeType.HABIT_STREAK else "nap",
                percentage=percentage
            )
            
        except Exception as e:
            logger.error(f"Error calculating challenge progress: {e}")
            return ChallengeProgress(
                current_value=0.0,
                target_value=user_challenge.personal_target or challenge.target_amount or 0.0,
                unit="HUF",
                percentage=0.0
            )
    
    @staticmethod
    async def _calculate_expense_reduction(
        user_id: str, 
        challenge: ChallengeDocument, 
        start_date: datetime,
        current_transactions: List[Transaction]
    ) -> float:
        """Kiadás csökkentés számítása az előző időszakhoz viszonyítva"""
        try:
            # Előző időszak tranzakcióinak lekérése
            prev_start = start_date - timedelta(days=challenge.duration_days)
            prev_end = start_date - timedelta(days=1)
            
            prev_query = {
                "user_id": ObjectId(user_id),
                "date": {
                    "$gte": prev_start.strftime("%Y-%m-%d"),
                    "$lte": prev_end.strftime("%Y-%m-%d")
                },
                "amount": {"$lt": 0}
            }
            
            if challenge.track_categories:
                prev_query["kategoria"] = {"$in": challenge.track_categories}
            
            prev_transactions = await Transaction.find(prev_query).to_list()
            
            # Összegek számítása
            prev_total = sum(abs(t.amount) for t in prev_transactions)
            current_total = sum(abs(t.amount) for t in current_transactions)
            
            # Megtakarítás (pozitív érték = jó)
            return max(0, prev_total - current_total)
            
        except Exception as e:
            logger.error(f"Error calculating expense reduction: {e}")
            return 0.0
    
    @staticmethod
    async def _calculate_streak(
        user_id: str,
        challenge: ChallengeDocument,
        start_date: datetime,
        transactions: List[Transaction]
    ) -> float:
        """Szokás sorozat számítása"""
        try:
            # Napok csoportosítása
            daily_transactions = {}
            for t in transactions:
                date_key = t.date
                if date_key not in daily_transactions:
                    daily_transactions[date_key] = []
                daily_transactions[date_key].append(t)
            
            # Streak számítása
            current_streak = 0
            current_date = start_date.date()
            end_date = (start_date + timedelta(days=challenge.duration_days)).date()
            
            while current_date <= end_date and current_date <= datetime.now().date():
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Ellenőrizzük, hogy volt-e megfelelő aktivitás ezen a napon
                if await ChallengeService._check_daily_goal_met(
                    challenge, daily_transactions.get(date_str, [])
                ):
                    current_streak += 1
                else:
                    break  # Megszakad a sorozat
                
                current_date += timedelta(days=1)
            
            return float(current_streak)
            
        except Exception as e:
            logger.error(f"Error calculating streak: {e}")
            return 0.0
    
    @staticmethod
    async def _check_daily_goal_met(
        challenge: ChallengeDocument, 
        daily_transactions: List[Transaction]
    ) -> bool:
        """Ellenőrzi, hogy a napi cél teljesült-e"""
        if not daily_transactions:
            return False
        
        # Szabályok alapján ellenőrzés
        for rule in challenge.rules:
            if rule.type == "min_transactions":
                if len(daily_transactions) < rule.value:
                    return False
            elif rule.type == "min_amount":
                total = sum(abs(t.amount) for t in daily_transactions)
                if total < rule.value:
                    return False
            elif rule.type == "required_category":
                categories = {t.kategoria for t in daily_transactions if t.kategoria}
                if rule.description not in categories:
                    return False
        
        return True
    
    @staticmethod
    async def update_challenge_statistics(challenge_id: str):
        """Kihívás statisztikáinak frissítése"""
        try:
            challenge = await ChallengeDocument.get(PydanticObjectId(challenge_id))
            if not challenge:
                return
            
            # Résztvevők száma
            participant_count = await UserChallengeDocument.find({
                "challenge_id": ObjectId(challenge_id),
                "status": {"$in": [ParticipationStatus.ACTIVE, ParticipationStatus.COMPLETED]}
            }).count()
            
            # Befejezési arány
            completed_count = await UserChallengeDocument.find({
                "challenge_id": ObjectId(challenge_id),
                "status": ParticipationStatus.COMPLETED
            }).count()
            
            completion_rate = (completed_count / participant_count * 100) if participant_count > 0 else 0
            
            # Frissítés
            challenge.participant_count = participant_count
            challenge.completion_rate = completion_rate
            challenge.updated_at = datetime.utcnow()
            
            await challenge.save()
            
        except Exception as e:
            logger.error(f"Error updating challenge statistics: {e}")
    
    @staticmethod
    async def check_challenge_completion(user_challenge: UserChallengeDocument) -> bool:
        """Ellenőrzi, hogy a kihívás teljesítve van-e"""
        try:
            if user_challenge.status != ParticipationStatus.ACTIVE:
                return False
            
            progress = user_challenge.progress
            return progress.percentage >= 100.0
            
        except Exception as e:
            logger.error(f"Error checking challenge completion: {e}")
            return False
    
    @staticmethod
    async def award_completion_rewards(
        user_challenge: UserChallengeDocument, 
        challenge: ChallengeDocument
    ):
        """Befejezési jutalmak odaítélése"""
        try:
            # Pontok odaítélése
            user_challenge.earned_points += challenge.rewards.points
            
            # Kitűzők hozzáadása
            for badge in challenge.rewards.badges:
                if badge not in user_challenge.earned_badges:
                    user_challenge.earned_badges.append(badge)
            
            # Státusz frissítése
            user_challenge.status = ParticipationStatus.COMPLETED
            user_challenge.completed_at = datetime.utcnow()
            user_challenge.updated_at = datetime.utcnow()
            
            await user_challenge.save()
            
            # Kihívás statisztikáinak frissítése
            await ChallengeService.update_challenge_statistics(str(challenge.id))
            
        except Exception as e:
            logger.error(f"Error awarding completion rewards: {e}")
    
    @staticmethod
    async def get_recommended_challenges(
        user_id: str,
        limit: int = 5
    ) -> List[ChallengeDocument]:
        """Ajánlott kihívások lekérése a felhasználó aktivitása alapján"""
        try:
            # Felhasználó tranzakcióinak elemzése az utóbbi 30 napban
            recent_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            user_transactions = await Transaction.find({
                "user_id": ObjectId(user_id),
                "date": {"$gte": recent_date}
            }).to_list()
            
            # Aktivitás alapú ajánlások
            recommendations = []
            
            # Ha sok kiadása van, ajánljunk kiadás csökkentést
            expense_total = sum(abs(t.amount) for t in user_transactions if t.amount < 0)
            if expense_total > 50000:  # 50k HUF felett
                expense_challenges = await ChallengeDocument.find({
                    "challenge_type": ChallengeType.EXPENSE_REDUCTION,
                    "status": ChallengeStatus.ACTIVE,
                    "difficulty": {"$in": [ChallengeDifficulty.EASY, ChallengeDifficulty.MEDIUM]}
                }).limit(2).to_list()
                recommendations.extend(expense_challenges)
            
            # Ha kevés megtakarítása van, ajánljunk megtakarítási kihívást
            savings_total = sum(t.amount for t in user_transactions 
                              if t.amount > 0 and t.main_account == "megtakaritas")
            if savings_total < 20000:  # 20k HUF alatt
                savings_challenges = await ChallengeDocument.find({
                    "challenge_type": ChallengeType.SAVINGS,
                    "status": ChallengeStatus.ACTIVE,
                    "difficulty": ChallengeDifficulty.EASY
                }).limit(2).to_list()
                recommendations.extend(savings_challenges)
            
            # Kiegészítés népszerű kihívásokkal
            if len(recommendations) < limit:
                popular_challenges = await ChallengeDocument.find({
                    "status": ChallengeStatus.ACTIVE
                }).sort([("participant_count", -1)]).limit(limit - len(recommendations)).to_list()
                recommendations.extend(popular_challenges)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommended challenges: {e}")
            return []