"""
Initialize database tables

Run this script to create all database tables:
    python init_db.py
"""

from database import Base, engine
from models import User, UserProfile, UserGoals, LearningProgress, Achievement, HandHistory, HandAnalysis

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print(f"Database location: pokerpro.db")

if __name__ == "__main__":
    init_database()
