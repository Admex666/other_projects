# app/models/analytics.py
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_serializer
from beanie import Document, PydanticObjectId

class UserHealthScore(Document):
    user_id: PydanticObjectId
    overall_score: float = Field(..., ge=0, le=100, description="Overall health score 0-100")
    login_frequency_score: float = Field(..., ge=0, le=100)
    feature_usage_score: float = Field(..., ge=0, le=100) 
    engagement_score: float = Field(..., ge=0, le=100)
    
    # Serializer hozzáadása az ObjectId-k kezelésére
    @field_serializer('id', when_used='json')
    def serialize_id(self, value):
        return str(value) if value else None

    # Detailed metrics
    days_since_last_login: int = 0
    total_sessions: int = 0
    transaction_count: int = 0
    onboarding_completed: bool = False
    badge_progress_count: int = 0
    forum_posts_count: int = 0
    forum_comments_count: int = 0
    has_active_partnership: bool = False
    knowledge_activity_count: int = 0
    messages_activity_count: int = 0
    knowledge_lessons_completed: int = 0
    messages_sent_count: int = 0
    habits_activity_count: int = 0
    limits_active_count: int = 0
    pti_activity_count: int = 0
    badge_activity_count: int = 0
    
    # Meta
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    health_level: str = Field(default="fair")  # excellent, good, fair, poor
    
    class Settings:
        name = "user_health_scores"

class UserSessionTracking(Document):
    user_id: PydanticObjectId
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    features_used: list[str] = Field(default_factory=list)
    
    class Settings:
        name = "user_sessions"
        # HOZZÁADÁS: Index a gyorsabb lekérdezéshez
        indexes = [
            [("user_id", 1), ("session_start", -1)]
        ]

class FeatureUsageTracking(Document):
    user_id: PydanticObjectId
    feature_name: str
    used_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "feature_usage"

# Response models
class HealthScoreResponse(BaseModel):
    user_id: Optional[PydanticObjectId] = None
    overall_score: float
    login_frequency_score: float
    feature_usage_score: float
    engagement_score: float
    health_level: str
    calculated_at: datetime
    details: Dict[str, Any]
    recommendations: list[str] = []