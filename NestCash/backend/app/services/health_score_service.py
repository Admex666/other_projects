# app/services/health_score_service.py
from datetime import datetime, timedelta
from typing import Optional, List
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
        
        # 1. Login Frequency Score (30%)
        login_score = await HealthScoreService._calculate_login_frequency_score(user_id)
        
        # 2. Feature Usage Score (40%)
        feature_score = await HealthScoreService._calculate_feature_usage_score(user_id)
        
        # 3. Engagement Score (30%)
        engagement_score = await HealthScoreService._calculate_engagement_score(user_id)
        
        # Overall score calculation
        overall_score = (login_score * 0.3) + (feature_score * 0.4) + (engagement_score * 0.3)
        
        # Determine health level
        health_level = HealthScoreService._determine_health_level(overall_score)
        
        # Get detailed metrics
        details = await HealthScoreService._get_detailed_metrics(user_id)
        
        # Generate recommendations
        recommendations = HealthScoreService._generate_recommendations(
            login_score, feature_score, engagement_score, details
        )
        
        # Save to database
        health_record = UserHealthScore(
            user_id=user_id,
            overall_score=overall_score,
            login_frequency_score=login_score,
            feature_usage_score=feature_score,
            engagement_score=engagement_score,
            health_level=health_level,
            **details
        )
        await health_record.save()
        
        return HealthScoreResponse(
            overall_score=overall_score,
            login_frequency_score=login_score,
            feature_usage_score=feature_score,
            engagement_score=engagement_score,
            health_level=health_level,
            calculated_at=health_record.calculated_at,
            details=details,
            recommendations=recommendations
        )
    
    @staticmethod
    async def _calculate_login_frequency_score(user_id: str) -> float:
        """Calculate login frequency score"""
        now = datetime.utcnow()
        
        # Last 30 days sessions
        thirty_days_ago = now - timedelta(days=30)
        recent_sessions = await UserSessionTracking.find(
            {"user_id": user_id, "session_start": {"$gte": thirty_days_ago}}
        ).count()
        
        # Last login
        last_session = await UserSessionTracking.find_one(
            {"user_id": user_id}, 
            sort=[("session_start", -1)]
        )
        
        if not last_session:
            return 0.0
            
        days_since_last = (now - last_session.session_start).days
        
        # Scoring logic
        if days_since_last == 0:
            recency_score = 100
        elif days_since_last <= 1:
            recency_score = 90
        elif days_since_last <= 3:
            recency_score = 70
        elif days_since_last <= 7:
            recency_score = 50
        elif days_since_last <= 14:
            recency_score = 30
        elif days_since_last <= 30:
            recency_score = 15
        else:
            recency_score = 0
            
        # Frequency score (ideal: 15+ sessions per month)
        frequency_score = min(100, (recent_sessions / 15) * 100)
        
        return (recency_score * 0.6) + (frequency_score * 0.4)
    
    @staticmethod
    async def _calculate_feature_usage_score(user_id: str) -> float:
        """Calculate feature usage score"""
        user = await UserDocument.find_one({"_id": user_id})
        if not user:
            return 0.0
            
        score = 0.0
        max_score = 100.0
        
        # Onboarding completed (25 points)
        if user.onboarding_completed:
            score += 25
            
        # Transaction activity (35 points)
        transaction_count = await Transaction.find({"user_id": user_id}).count()
        transaction_score = min(35, (transaction_count / 10) * 35)  # Max at 10 transactions
        score += transaction_score
        
        # Badge progress (20 points)
        badge_count = await UserBadge.find({"user_id": user_id}).count()
        badge_score = min(20, (badge_count / 5) * 20)  # Max at 5 badges
        score += badge_score
        
        # Recent feature usage (20 points) - módosítás itt
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_features_pipeline = [
            {"$match": {"user_id": user_id, "used_at": {"$gte": thirty_days_ago}}},
            {"$group": {"_id": "$feature_name"}},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        
        result = await FeatureUsageTracking.aggregate(recent_features_pipeline).to_list()
        unique_features_used = result[0]["count"] if result else 0
        feature_variety_score = min(20, (unique_features_used / 5) * 20)  # Max at 5 different features
        score += feature_variety_score
        
        return min(100.0, score)
    
    @staticmethod
    async def _calculate_engagement_score(user_id: str) -> float:
        """Calculate engagement score"""
        score = 0.0
        
        # Forum activity (50 points)
        forum_posts = await ForumPostDocument.find({"user_id": user_id}).count()
        forum_comments = await CommentDocument.find({"user_id": user_id}).count()
        forum_activity = forum_posts + forum_comments
        forum_score = min(50, (forum_activity / 5) * 50)  # Max at 5 posts/comments
        score += forum_score
        
        # Partnership activity (50 points)
        active_partnerships = await Partnership.find(
            {"$or": [{"user_id": user_id}, {"partner_user_id": user_id}], "status": "active"}
        ).count()
        
        partnership_score = min(50, active_partnerships * 25)  # Max at 2 partnerships
        score += partnership_score
        
        return min(100.0, score)
    
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
    async def _get_detailed_metrics(user_id: str) -> dict:
        """Get detailed metrics for the user"""
        # Last login
        last_session = await UserSessionTracking.find_one(
            {"user_id": user_id}, 
            sort=[("session_start", -1)]
        )
        days_since_last_login = 999
        if last_session:
            days_since_last_login = (datetime.utcnow() - last_session.session_start).days
        
        # Total sessions
        total_sessions = await UserSessionTracking.find({"user_id": user_id}).count()
        
        # Transaction count
        transaction_count = await Transaction.find({"user_id": user_id}).count()
        
        # Onboarding status
        user = await UserDocument.find_one({"_id": user_id})
        onboarding_completed = user.onboarding_completed if user else False
        
        # Badge progress
        badge_progress_count = await UserBadge.find({"user_id": user_id}).count()
        
        # Forum activity
        forum_posts_count = await ForumPostDocument.find({"user_id": user_id}).count()
        forum_comments_count = await CommentDocument.find({"user_id": user_id}).count()
        
        # Partnership status
        has_active_partnership = await Partnership.find(
            {"$or": [{"user_id": user_id}, {"partner_user_id": user_id}], "status": "active"}
        ).count() > 0
        
        return {
            "days_since_last_login": days_since_last_login,
            "total_sessions": total_sessions,
            "transaction_count": transaction_count,
            "onboarding_completed": onboarding_completed,
            "badge_progress_count": badge_progress_count,
            "forum_posts_count": forum_posts_count,
            "forum_comments_count": forum_comments_count,
            "has_active_partnership": has_active_partnership
        }
    
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
        """Track user session"""
        # Biztosítjuk, hogy user_id string legyen
        user_id_str = str(user_id)
        session = UserSessionTracking(user_id=user_id_str)
        await session.save()

    @staticmethod
    async def track_feature_usage(user_id: str, feature_name: str) -> None:
        """Track feature usage"""
        # Biztosítjuk, hogy user_id string legyen
        user_id_str = str(user_id)
        usage = FeatureUsageTracking(user_id=user_id_str, feature_name=feature_name)
        await usage.save()