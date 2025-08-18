# app/services/health_score_service.py
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from beanie import PydanticObjectId
from app.models.analytics import UserHealthScore, UserSessionTracking, FeatureUsageTracking, HealthScoreResponse
from app.models.user import UserDocument
from app.models.transaction import Transaction
from app.models.forum_models import ForumPostDocument, CommentDocument
from app.models.badge import UserBadge
from app.models.accountability_models import Partnership

class HealthScoreService:
    
    @staticmethod
    async def calculate_health_score(user_id: str) -> HealthScoreResponse:
        """Calculate comprehensive health score for user"""
        
        # Konvertáljuk ObjectId-ra a kereséshez
        try:
            user_obj_id = PydanticObjectId(user_id)
        except:
            raise ValueError(f"Invalid user_id format: {user_id}")
        
        # DEBUG: Ellenőrizzük a sessions adatokat
        debug_sessions = await UserSessionTracking.find({"user_id": user_obj_id}).to_list()
        print(f"DEBUG - Found {len(debug_sessions)} sessions for user {user_id}")
        if debug_sessions:
            print(f"DEBUG - Latest session: {debug_sessions[0].session_start if debug_sessions else 'None'}")
    
        # Lekérdezzük a UserDocument-et
        user_doc = await UserDocument.get(user_obj_id)
        if not user_doc:
            raise ValueError(f"User with id {user_id} not found")

        # 1. Login Frequency Score (30%)
        login_score, days_since_last_login, total_sessions = await HealthScoreService._calculate_login_frequency_score(user_obj_id)
        
        # 2. Feature Usage Score (40%)
        feature_score, onboarding_completed, transaction_count = await HealthScoreService._calculate_feature_usage_score(user_obj_id, user_doc.onboarding_completed)
        
        # 3. Engagement Score (30%)
        engagement_score, forum_posts_count, forum_comments_count, has_active_partnership, badge_progress_count = await HealthScoreService._calculate_engagement_score(user_obj_id)
        
        # Overall score calculation
        overall_score = (login_score * 0.3) + (feature_score * 0.4) + (engagement_score * 0.3)
        
        # Determine health level
        health_level = HealthScoreService._determine_health_level(overall_score)
        
        # Save or update the UserHealthScore document
        health_score_doc = await UserHealthScore.find_one({"user_id": user_obj_id})
        if not health_score_doc:
            health_score_doc = UserHealthScore(
                user_id=user_obj_id,
                overall_score=overall_score,
                login_frequency_score=login_score,
                feature_usage_score=feature_score,
                engagement_score=engagement_score,
                days_since_last_login=days_since_last_login,
                total_sessions=total_sessions,
                transaction_count=transaction_count,
                onboarding_completed=onboarding_completed,
                badge_progress_count=badge_progress_count,
                forum_posts_count=forum_posts_count,
                forum_comments_count=forum_comments_count,
                has_active_partnership=has_active_partnership,
                health_level=health_level,
                calculated_at=datetime.utcnow()
            )
        else:
            health_score_doc.overall_score = overall_score
            health_score_doc.login_frequency_score = login_score
            health_score_doc.feature_usage_score = feature_score
            health_score_doc.engagement_score = engagement_score
            health_score_doc.days_since_last_login = days_since_last_login
            health_score_doc.total_sessions = total_sessions
            health_score_doc.transaction_count = transaction_count
            health_score_doc.onboarding_completed = onboarding_completed
            health_score_doc.badge_progress_count = badge_progress_count
            health_score_doc.forum_posts_count = forum_posts_count
            health_score_doc.forum_comments_count = forum_comments_count
            health_score_doc.has_active_partnership = has_active_partnership
            health_score_doc.health_level = health_level
            health_score_doc.calculated_at = datetime.utcnow()
            
        await health_score_doc.save()
        
        return HealthScoreResponse(
            user_id=user_obj_id,
            overall_score=overall_score,
            login_frequency_score=login_score,
            feature_usage_score=feature_score,
            engagement_score=engagement_score,
            health_level=health_level,
            calculated_at=datetime.utcnow(),
            details={
                "days_since_last_login": days_since_last_login,
                "total_sessions": total_sessions,
                "transaction_count": transaction_count,
                "onboarding_completed": onboarding_completed,
                "badge_progress_count": badge_progress_count,
                "forum_posts_count": forum_posts_count,
                "forum_comments_count": forum_comments_count,
                "has_active_partnership": has_active_partnership
            },
            recommendations=HealthScoreService._get_recommendations(health_score_doc)
        )
    
    @staticmethod
    async def _calculate_login_frequency_score(user_obj_id: PydanticObjectId) -> (float, int, int):
        """Calculate login frequency score and return details"""
        
        # DEBUG: Ellenőrizzük az ObjectId formátumot
        print(f"DEBUG - Looking for sessions with user_id: {user_obj_id} (type: {type(user_obj_id)})")
        
        # JAVÍTÁS: Közvetlenül a MongoDB collection-t használjuk
        from app.core.db import get_db
        db = get_db()
        sessions_collection = db["user_sessions"]
        
        # Raw MongoDB lekérdezés ObjectId-val
        sessions_cursor = sessions_collection.find(
            {"user_id": user_obj_id}
        ).sort("session_start", -1)
        
        sessions_list = await sessions_cursor.to_list(length=None)
        total_sessions = len(sessions_list)
        
        print(f"DEBUG - Found {total_sessions} sessions for user {user_obj_id}")
        
        if not sessions_list:
            return 0.0, 999, 0
            
        last_session = sessions_list[0]
        last_session_date = last_session["session_start"]
        
        print(f"DEBUG - Last session date: {last_session_date}")
        
        # Timezone-aware összehasonlítás
        now = datetime.utcnow()
        days_since_last_login = (now - last_session_date).days
        
        print(f"DEBUG - Days since last login: {days_since_last_login}")
        
        # Pontszámítás
        if days_since_last_login <= 1:
            score = 100
        elif days_since_last_login <= 3:
            score = 80
        elif days_since_last_login <= 7:
            score = 60
        elif days_since_last_login <= 14:
            score = 30
        else:
            score = 0
            
        return float(score), days_since_last_login, total_sessions
    
    @staticmethod
    async def _calculate_feature_usage_score(user_obj_id: PydanticObjectId, onboarding_completed: bool) -> (float, bool, int):
        """Calculate feature usage score and return details"""
        
        transaction_count = await Transaction.find({"user_id": user_obj_id}).count()
        
        # HOZZÁADÁS: Feature usage tracking elemzése
        feature_usage_count = await FeatureUsageTracking.find({"user_id": user_obj_id}).count()

        # Onboarding specifikus feature-ök számolása
        onboarding_features = await FeatureUsageTracking.find({
            "user_id": user_obj_id,
            "feature_name": {"$regex": "^onboarding"}
        }).count()
        
        # Egyéb fontos feature-ök
        important_features = await FeatureUsageTracking.find({
            "user_id": user_obj_id,
            "feature_name": {"$in": [
                "create_transaction", "view_dashboard", "set_limit", 
                "join_challenge", "forum_post", "knowledge_lesson"
            ]}
        }).count()
        
        print(f"DEBUG - Feature usage for user {user_obj_id}: total={feature_usage_count}, onboarding={onboarding_features}, important={important_features}")
    

        score_base = 0
        
        # Onboarding befejezés (alapvető)
        if onboarding_completed:
            score_base += 30
        
        # Tranzakciók létrehozása
        if transaction_count > 0:
            score_base += 25
            if transaction_count >= 5:
                score_base += 10
            if transaction_count >= 20:
                score_base += 10
        
        # Feature használat aktivitás
        if feature_usage_count > 5:
            score_base += 15
        if feature_usage_count > 20:
            score_base += 10
        
        # Fontos feature-ök használata
        if important_features > 0:
            score_base += 10
        
        return float(score_base), onboarding_completed, transaction_count
    
    @staticmethod
    async def _calculate_engagement_score(user_obj_id: PydanticObjectId) -> (float, int, int, bool, int):
        """Calculate engagement score and return details"""
        
        # user_id mezőt használjuk author_id helyett
        forum_posts_count = await ForumPostDocument.find({"user_id": user_obj_id}).count()
        forum_comments_count = await CommentDocument.find({"user_id": user_obj_id}).count()
            
        # JAVÍTÁS: Partnerships - helyes mező nevek használata
        has_active_partnership = await Partnership.find_one({
            "$or": [
                {"requester_id": user_obj_id}, 
                {"requested_id": user_obj_id}
            ],
            "status": "active"  # vagy PartnershipStatus.ACTIVE
        }) is not None

        # Badge progress
        badge_progress_count = await UserBadge.find({"user_id": user_obj_id}).count()
        
        score_base = 0
        if forum_posts_count > 0 or forum_comments_count > 0:
            score_base += 40
        if has_active_partnership:
            score_base += 40
        if badge_progress_count > 0:
            score_base += 20
        
        # DEBUG információ hozzáadása
        print(f"DEBUG - Engagement for user {user_obj_id}: posts={forum_posts_count}, comments={forum_comments_count}, partnership={has_active_partnership}, badges={badge_progress_count}")
   
        return float(score_base), forum_posts_count, forum_comments_count, has_active_partnership, badge_progress_count

    
    @staticmethod
    def _determine_health_level(score: float) -> str:
        """Determine health level based on score"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
    
    @staticmethod
    def _get_recommendations(details: UserHealthScore) -> List[str]:
        """Ajánlásokat generál az adatok alapján"""
        recommendations = []
        
        if details.days_since_last_login > 7:
            recommendations.append("Lépj be rendszeresebben az appba, hogy naprakész maradj")
        if not details.onboarding_completed:
            recommendations.append("Fejezd be az onboardingot, hogy hozzáférj az összes funkcióhoz")
        if details.transaction_count == 0:
            recommendations.append("Rögzítsd az első tranzakciódat, hogy elinduljon a nyomon követés")
        if details.badge_progress_count == 0:
            recommendations.append("Kezdj el egy kihívást vagy leckét, hogy megszerezd az első jelvényed")
        if details.forum_posts_count == 0:
            recommendations.append("Csatlakozz a közösséghez - írj egy bejegyzést a fórumra")
        if not details.has_active_partnership:
            recommendations.append("Keress egy accountability partnert")
            
        return recommendations
    
    @staticmethod
    def _generate_recommendations(login_score: float, feature_score: float, 
                                engagement_score: float, details: dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if login_score < 50:
            recommendations.append("Próbálj meg naponta bejelentkezni az app-ba")
            
        if feature_score < 50:
            if not details.get("onboarding_completed", False):
                recommendations.append("Fejezd be az onboarding folyamatot")
            if details.get("transaction_count", 0) < 5:
                recommendations.append("Rögzíts több tranzakciót a jobb áttekintéshez")
                
        if engagement_score < 50:
            if details.get("forum_posts_count", 0) == 0:
                recommendations.append("Csatlakozz a közösséghez - írj egy bejegyzést a fórumra")
            if not details.get("has_active_partnership", False):
                recommendations.append("Keress egy accountability partnert")
                
        return recommendations

    @staticmethod
    async def track_session(user_id: str) -> None:
        # unchanged method
        """Track user session"""
        try:
            from beanie import PydanticObjectId
            user_obj_id = PydanticObjectId(user_id)
            
            # Ellenőrizzük, hogy nincs-e már aktív session (utolsó 30 percben)
            thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
            
            recent_session = await UserSessionTracking.find_one(
                {"user_id": user_obj_id, "session_start": {"$gte": thirty_minutes_ago}}
            )
            
            # Ha nincs aktív session, újat indítunk
            if not recent_session:
                session = UserSessionTracking(user_id=user_obj_id)
                await session.save()
                print(f"New session created for user: {user_id}")
            else:
                # Frissítjük a session_end időt, ha van aktív session
                recent_session.session_end = datetime.utcnow()
                await recent_session.save()  # JAVÍTÁS: .save() használata .update_one() helyett
                print(f"Active session updated for user: {user_id}")
                
        except Exception as e:
            print(f"Error tracking session for user {user_id}: {e}")
            raise

    @staticmethod
    async def track_feature_usage(user_id: str, feature_name: str) -> None:
        """Track feature usage"""
        try:
            from beanie import PydanticObjectId
            user_obj_id = PydanticObjectId(user_id)
            
            # Új feature usage tracking
            feature_usage = FeatureUsageTracking(
                user_id=user_obj_id,
                feature_name=feature_name,
                used_at=datetime.utcnow()
            )
            await feature_usage.save()
            print(f"Feature usage tracked: {feature_name} for user: {user_id}")
            
        except Exception as e:
            print(f"Error tracking feature usage for user {user_id}: {e}")
            raise