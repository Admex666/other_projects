# app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.user import User
from app.models.analytics import HealthScoreResponse
from app.services.health_score_service import HealthScoreService

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