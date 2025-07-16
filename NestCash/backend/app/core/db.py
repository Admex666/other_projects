import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from app.models.item import Item  # későbbiekben több modelt is
from app.models.user import User

load_dotenv()

async def init_db():
    MONGO_URI = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["nestcash"]
    await init_beanie(database=db, document_models=[User, Item])
