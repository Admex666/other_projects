from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Lesson tracking
    lesson_id = Column(String, nullable=False)  # e.g., "basic_math_01"
    lesson_category = Column(String, nullable=False)  # e.g., "theory", "strategy", "pro"
    
    # Progress
    completed = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    quiz_score = Column(Float, nullable=True)  # 0-100
    time_spent_minutes = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="progress")


class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Achievement details
    achievement_type = Column(String, nullable=False)  # e.g., "certification", "challenge", "milestone"
    achievement_id = Column(String, nullable=False)  # e.g., "nl10_ready", "100_hands_analyzed"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    earned_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, nullable=True)  # For certifications
    
    # Relationships
    user = relationship("User", back_populates="achievements")
