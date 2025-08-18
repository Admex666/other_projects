# app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import timedelta, datetime

from app.core.security import get_current_user
from app.models.user import User, UserDocument
from app.models.analytics import HealthScoreResponse, FeatureUsageTracking
from app.services.health_score_service import HealthScoreService, UserHealthScore, UserSessionTracking

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/health-score", response_model=HealthScoreResponse)
async def get_health_score(current_user: User = Depends(get_current_user)):
    """Get user's health score"""
    try:
        health_score = await HealthScoreService.calculate_health_score(current_user.id)
        return health_score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate health score: {str(e)}")

@router.post("/track-session")
async def track_session(current_user: User = Depends(get_current_user)):
    """Track user session"""
    try:
        await HealthScoreService.track_session(current_user.id)
        return {"message": "Session tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track session: {str(e)}")

@router.post("/track-feature/{feature_name}")
async def track_feature_usage(
    feature_name: str,
    current_user: User = Depends(get_current_user)
):
    """Track feature usage"""
    try:
        await HealthScoreService.track_feature_usage(current_user.id, feature_name)
        return {"message": "Feature usage tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track feature usage: {str(e)}")
    
@router.get("/admin/all-health-scores", response_model=List[Dict[str, Any]])
async def get_all_health_scores(current_user: User = Depends(get_current_user)):
    """Get all users' health scores (admin only)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get all users
        all_users = await UserDocument.find_all().to_list()
        
        result = []
        for user in all_users:
            try:
                # Get latest health score for user
                latest_score = await UserHealthScore.find_one(
                    {"user_id": user.id}, 
                    sort=[("calculated_at", -1)]
                )
                
                # If no score exists or score is older than 24 hours, calculate new one
                should_calculate = (
                    latest_score is None or 
                    (datetime.utcnow() - latest_score.calculated_at).total_seconds() > 86400  # 24 hours
                )
                
                if should_calculate:
                    print(f"Calculating health score for user: {user.username}")
                    # Calculate new health score
                    health_score_response = await HealthScoreService.calculate_health_score(user.id)
                    
                    # Get the saved record from database
                    latest_score = await UserHealthScore.find_one(
                        {"user_id": user.id}, 
                        sort=[("calculated_at", -1)]
                    )
                
                if latest_score:
                    result.append({
                        "user_id": str(latest_score.user_id),  # Explicit string konverzió
                        "username": user.username,
                        "email": user.email,
                        "overall_score": latest_score.overall_score,
                        "health_level": latest_score.health_level,
                        "calculated_at": latest_score.calculated_at,
                        "login_frequency_score": latest_score.login_frequency_score,
                        "feature_usage_score": latest_score.feature_usage_score,
                        "engagement_score": latest_score.engagement_score,
                        "details": {
                            "days_since_last_login": latest_score.days_since_last_login,
                            "total_sessions": latest_score.total_sessions,
                            "transaction_count": latest_score.transaction_count,
                            "onboarding_completed": latest_score.onboarding_completed,
                            "badge_progress_count": latest_score.badge_progress_count,
                            "forum_posts_count": latest_score.forum_posts_count,
                            "forum_comments_count": latest_score.forum_comments_count,
                            "has_active_partnership": latest_score.has_active_partnership,
                            "knowledge_activity_count": latest_score.knowledge_activity_count,
                            "messages_activity_count": latest_score.messages_activity_count,
                            "knowledge_lessons_completed": latest_score.knowledge_lessons_completed,
                            "messages_sent_count": latest_score.messages_sent_count,
                            "habits_activity_count": latest_score.habits_activity_count,
                            "limits_active_count": latest_score.limits_active_count,
                            "pti_activity_count": latest_score.pti_activity_count,
                            "badge_activity_count": latest_score.badge_activity_count
                        }
                    })
            except Exception as e:
                print(f"Error calculating health score for user {user.username}: {str(e)}")
                # Skip this user but continue with others
                continue
        
        return result
    except Exception as e:
        print(f"Error in get_all_health_scores: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get health scores: {str(e)}")

@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_admin_stats(current_user: User = Depends(get_current_user)):
    """Get overall app statistics (admin only)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Total users
        all_users = await UserDocument.find_all().to_list()
        total_users = len(all_users)

        # Inaktív felhasználók számítása
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        inactive_users_count = 0
        for user in all_users:
            latest_session = await UserSessionTracking.find_one(
                {"user_id": user.id},
                sort=[("session_start", -1)]
            )
            if latest_session and latest_session.session_start < thirty_days_ago:
                inactive_users_count += 1
        
        inactive_user_rate = 0.0
        if total_users > 0:
            inactive_user_rate = (inactive_users_count / total_users) * 100
        
        # Active users (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_sessions = await UserSessionTracking.find(
            {"session_start": {"$gte": seven_days_ago}}
        ).to_list()
        active_users_count = len(set([session.user_id for session in active_sessions]))
        
        # TTV és Onboarding Completion Rate számítása
        completed_onboarding_users_count = 0
        ttv_durations_seconds = []

        # Ensure we have recent health scores for statistics
        # Get all users and make sure they have recent health scores
        for user in all_users:
            try:
                latest_score = await UserHealthScore.find_one(
                    {"user_id": user.id}, 
                    sort=[("calculated_at", -1)]
                )
                
                # Calculate if no score or score is old
                if (latest_score is None or 
                    (datetime.utcnow() - latest_score.calculated_at).total_seconds() > 86400):
                    print(f"Calculating health score for stats - user: {user.username}")
                    await HealthScoreService.calculate_health_score(user.id)
            except Exception as e:
                print(f"Error ensuring health score for {user.username}: {e}")
                continue

            if user.onboarding_completed:
                completed_onboarding_users_count += 1

                # Keresd meg a TTV eseményt (onboarding befejezés)
                ttv_event = await FeatureUsageTracking.find_one(
                    {"user_id": user.id, "feature_name": "onboarding_full_completion"},
                    sort=[("used_at", 1)]
                )

                if ttv_event and user.registration_date:
                    ttv_duration = (ttv_event.used_at - user.registration_date).total_seconds()
                    ttv_durations_seconds.append(ttv_duration)
        
        onboarding_completion_rate = 0.0
        if total_users > 0:
            onboarding_completion_rate = (completed_onboarding_users_count / total_users) * 100

        average_ttv_seconds = 0
        if ttv_durations_seconds:
            average_ttv_seconds = sum(ttv_durations_seconds) / len(ttv_durations_seconds)
        average_ttv_minutes = average_ttv_seconds / 60

        # Health distribution
        health_distribution_pipeline = [
            {"$sort": {"user_id": 1, "calculated_at": -1}},
            {"$group": {
                "_id": "$user_id",
                "latest_health_level": {"$first": "$health_level"}
            }},
            {"$group": {
                "_id": "$latest_health_level",
                "count": {"$sum": 1}
            }}
        ]
        
        health_dist_result = await UserHealthScore.aggregate(health_distribution_pipeline).to_list()
        health_distribution = {item["_id"]: item["count"] for item in health_dist_result}
        
        # Average scores
        avg_scores_pipeline = [
            {"$sort": {"user_id": 1, "calculated_at": -1}},
            {"$group": {
                "_id": "$user_id",
                "latest_overall": {"$first": "$overall_score"},
                "latest_login": {"$first": "$login_frequency_score"},
                "latest_feature": {"$first": "$feature_usage_score"},
                "latest_engagement": {"$first": "$engagement_score"}
            }},
            {"$group": {
                "_id": None,
                "avg_overall": {"$avg": "$latest_overall"},
                "avg_login": {"$avg": "$latest_login"},
                "avg_feature": {"$avg": "$latest_feature"},
                "avg_engagement": {"$avg": "$latest_engagement"}
            }}
        ]
        
        avg_result = await UserHealthScore.aggregate(avg_scores_pipeline).to_list()
        
        if avg_result:
            averages = avg_result[0]
            average_scores = {
                "overall": round(averages.get("avg_overall", 0), 1),
                "login_frequency": round(averages.get("avg_login", 0), 1),
                "feature_usage": round(averages.get("avg_feature", 0), 1),
                "engagement": round(averages.get("avg_engagement", 0), 1)
            }
        else:
            average_scores = {
                "overall": 0.0,
                "login_frequency": 0.0,
                "feature_usage": 0.0,
                "engagement": 0.0
            }

        return {
            "total_users": total_users,
            "active_users": active_users_count,
            "health_distribution": health_distribution,
            "average_scores": average_scores,
            "onboarding_completion_rate": round(onboarding_completion_rate, 1),
            "average_ttv_minutes": round(average_ttv_minutes, 1) if average_ttv_minutes > 0 else 0.0,
            "inactive_user_rate": round(inactive_user_rate, 2),
        }
        
    except Exception as e:
        print(f"Error in get_admin_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {str(e)}")
    
@router.post("/admin/recalculate-all-health-scores")
async def recalculate_all_health_scores(current_user: User = Depends(get_current_user)):
    """Recalculate health scores for all users (admin only)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get all users
        all_users = await UserDocument.find_all().to_list()
        
        success_count = 0
        error_count = 0
        
        for user in all_users:
            try:
                await HealthScoreService.calculate_health_score(user.id)
                success_count += 1
                print(f"Recalculated health score for: {user.username}")
            except Exception as e:
                error_count += 1
                print(f"Failed to calculate health score for {user.username}: {str(e)}")
        
        return {
            "message": "Health score recalculation completed",
            "total_users": len(all_users),
            "success_count": success_count,
            "error_count": error_count
        }
        
    except Exception as e:
        print(f"Error in recalculate_all_health_scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to recalculate health scores: {str(e)}")