# app/core/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from dotenv import load_dotenv

from app.models.user import UserDocument
from app.models.item import Item
from app.models.transaction import Transaction
from app.models.account import AllUserAccountsDocument
from app.models.category import Category
from app.models.knowledge import KnowledgeCategory, Lesson, UserProgress
from app.models.forum_models import (
    ForumPostDocument, CommentDocument, LikeDocument, FollowDocument,
    UserForumSettingsDocument
)
from app.models.notification import NotificationDocument
from app.models.limit import Limit
from app.models.challenge import ChallengeDocument, UserChallengeDocument
from app.models.badge import BadgeType, UserBadge, BadgeProgress
from app.models.habit import Habit, HabitLog
from app.models.pti import PTIScore, PTIHistory, UserPTISettings
from app.models.subscription import UserSubscriptionDocument
from app.models.message_models import MessageDocument, ConversationDocument
from app.models.accountability_models import AccountabilityProfile, Partnership, CheckIn

load_dotenv()

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

async def init_db():
    """App startup-kor meghívva: kapcsolat + Beanie init."""
    global _client, _db
    mongo_uri = os.getenv("MONGODB_URI")
    print(f"MongoDB URI (first 20 chars): {mongo_uri[:20] if mongo_uri else 'None'}")  # Debug log
    
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable is not set")
    
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client["nestcash"]
    
    # Kapcsolat tesztelése
    try:
        await _client.admin.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        raise
    
    # Csak azokat a modelleket inicializáljuk, amiket Beanie-vel kezelünk
    await init_beanie(
        database=_db, 
        document_models=[
            UserDocument, Item, Transaction, AllUserAccountsDocument, Category,
            KnowledgeCategory, Lesson, UserProgress,
            ForumPostDocument, CommentDocument, LikeDocument, FollowDocument,
            NotificationDocument, UserForumSettingsDocument, Limit,
            ChallengeDocument, UserChallengeDocument,
            BadgeType, UserBadge, BadgeProgress,
            Habit, HabitLog,
            PTIScore, PTIHistory, UserPTISettings,
            UserSubscriptionDocument,
            MessageDocument, ConversationDocument,
            AccountabilityProfile, Partnership, CheckIn
            ]
            ) 

def get_db() -> AsyncIOMotorDatabase:
    """Használható route-okból; feltételezi, hogy init_db már lefutott."""
    if _db is None:
        raise RuntimeError("Database not initialized. Did startup run?")
    return _db