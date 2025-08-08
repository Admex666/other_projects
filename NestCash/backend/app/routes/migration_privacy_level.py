# migration_privacy_level.py
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def migrate_privacy_levels():
    """Migrálja a 'friends' privacy_level értékeket 'mutual_following'-ra"""
    
    mongo_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["nestcash"]
    
    try:
        # Forum posts migrálás
        posts_result = await db.forum_posts.update_many(
            {"privacy_level": "friends"},
            {"$set": {"privacy_level": "mutual_following"}}
        )
        print(f"Forum posts migrated: {posts_result.modified_count}")
        
        # Forum user settings migrálás (ha van ilyen)
        settings_result = await db.forum_user_settings.update_many(
            {"default_privacy_level": "friends"},
            {"$set": {"default_privacy_level": "mutual_following"}}
        )
        print(f"User settings migrated: {settings_result.modified_count}")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_privacy_levels())