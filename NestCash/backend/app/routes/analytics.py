# app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import timedelta, datetime

from app.core.security import get_current_user
from app.models.user import User, UserDocument
from app.models.analytics import HealthScoreResponse
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
        # Get latest health scores for all users
        pipeline = [
            {"$sort": {"user_id": 1, "calculated_at": -1}},
            {"$group": {
                "_id": "$user_id",
                "latest_score": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_score"}}
        ]
        
        health_scores = await UserHealthScore.aggregate(pipeline).to_list()
        
        # Get user details for each score
        result = []
        for score_dict in health_scores:  # score_dict most dict, nem UserHealthScore object
            user = await UserDocument.find_one({"_id": score_dict["user_id"]})
            if user:
                result.append({
                    "user_id": score_dict["user_id"],
                    "username": user.username,
                    "email": user.email,
                    "overall_score": score_dict["overall_score"],
                    "health_level": score_dict["health_level"],
                    "calculated_at": score_dict["calculated_at"],
                    "login_frequency_score": score_dict["login_frequency_score"],
                    "feature_usage_score": score_dict["feature_usage_score"],
                    "engagement_score": score_dict["engagement_score"],
                    "details": {
                        "days_since_last_login": score_dict["days_since_last_login"],
                        "total_sessions": score_dict["total_sessions"],
                        "transaction_count": score_dict["transaction_count"],
                        "onboarding_completed": score_dict["onboarding_completed"],
                        "badge_progress_count": score_dict["badge_progress_count"],
                        "forum_posts_count": score_dict["forum_posts_count"],
                        "forum_comments_count": score_dict["forum_comments_count"],
                        "has_active_partnership": score_dict["has_active_partnership"]
                    }
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health scores: {str(e)}")


@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_admin_stats(current_user: User = Depends(get_current_user)):
    """Get overall app statistics (admin only)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Total users
        total_users = await UserDocument.find_all().count()
        
        # Active users (last 7 days) - egyszerűsített verzió
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_sessions = await UserSessionTracking.find(
            {"session_start": {"$gte": seven_days_ago}}
        ).to_list()
        active_users_count = len(set([session.user_id for session in active_sessions]))
        
        # Health distribution - aggregation pipeline használata
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
        
        # Average scores - aggregation pipeline használata
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
            "average_scores": average_scores
        }
        
    except Exception as e:
        print(f"Error in get_admin_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {str(e)}")