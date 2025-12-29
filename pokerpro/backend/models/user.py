from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class GameFormat(str, enum.Enum):
    CASH = "cash"
    MTT = "mtt"
    SNG = "sng"
    SPIN_AND_GO = "spin_and_go"


class GameVariant(str, enum.Enum):
    NLH = "nlh"
    PLO = "plo"


class PlayerGoal(str, enum.Enum):
    HOBBY_TO_WINNING = "hobby_to_winning"
    SEMI_PRO = "semi_pro"
    PROFESSIONAL = "professional"
    HIGH_STAKES = "high_stakes"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    goals = relationship("UserGoals", back_populates="user", uselist=False)
    progress = relationship("LearningProgress", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
    hand_histories = relationship("HandHistory", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Onboarding data
    skill_level = Column(Enum(SkillLevel), nullable=False)
    game_format = Column(Enum(GameFormat), nullable=False)
    game_variant = Column(Enum(GameVariant), nullable=False)
    
    # Stats
    total_hands_played = Column(Integer, default=0)
    total_study_hours = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class UserGoals(Base):
    __tablename__ = "user_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Goals
    player_goal = Column(Enum(PlayerGoal), nullable=False)
    target_bankroll = Column(Float, nullable=True)
    current_bankroll = Column(Float, nullable=True)
    weekly_hours = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")
