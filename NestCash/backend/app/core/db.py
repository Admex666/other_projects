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

load_dotenv()

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

async def init_db():
    """App startup-kor meghívva: kapcsolat + Beanie init."""
    global _client, _db
    mongo_uri = os.getenv("MONGODB_URI")
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client["nestcash"]
    # Csak azokat a modelleket inicializáljuk, amiket Beanie-vel kezelünk
    await init_beanie(
        database=_db, 
        document_models=[
            UserDocument, Item, Transaction, AllUserAccountsDocument, Category,
            KnowledgeCategory, Lesson, UserProgress,
            ForumPostDocument, CommentDocument, LikeDocument, FollowDocument,
            NotificationDocument, UserForumSettingsDocument, Limit 
            ]
            ) 

def get_db() -> AsyncIOMotorDatabase:
    """Használható route-okból; feltételezi, hogy init_db már lefutott."""
    if _db is None:
        raise RuntimeError("Database not initialized. Did startup run?")
    return _db