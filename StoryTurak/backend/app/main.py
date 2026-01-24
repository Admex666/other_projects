from fastapi import FastAPI
import asyncio
import logging

from app.db.database import init_db
from app.services.story_service import load_stories
from app.services.quest_service import sync_stories_to_quests_v2, seed_quests
from app.services.connection_manager import manager
from app.db.crud import create_item, create_loot_table

from app.api import auth, characters, quests, stories, ws, sessions, world, combat, economy, collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Keldor Backend", version="2.0.0")

# Include Routers
app.include_router(auth.router)
app.include_router(characters.router)
app.include_router(quests.router)
app.include_router(stories.router)
app.include_router(ws.router)
app.include_router(sessions.router)
app.include_router(world.router)
app.include_router(combat.router, prefix="/combat", tags=["combat"])
app.include_router(economy.router, tags=["economy"])
app.include_router(collections.router, tags=["collections"])

def seed_loot():
    potion = {
        "id": "item_healing_potion_minor",
        "name": "Kicsi Gyógyital",
        "description": "Enyhíti a fájdalmat. +5 HP.",
        "type": "consumable",
        "value": 10,
        "icon_code": "local_pharmacy",
        "stats": {"hp_restore": 5}
    }
    coin = {
        "id": "item_ancient_coin",
        "name": "Ősi Érme",
        "description": "Régi fizetőeszköz, a Gyűjtők szeretik.",
        "type": "misc",
        "value": 50,
        "icon_code": "monetization_on",
        "stats": {}
    }
    create_item(potion)
    create_item(coin)
    
    table = {
        "id": "loot_table_common",
        "entries": [
            {"item_id": "item_healing_potion_minor", "chance": 0.5, "min_qty": 1, "max_qty": 1},
            {"item_id": "item_ancient_coin", "chance": 0.3, "min_qty": 1, "max_qty": 2}
        ]
    }
    create_loot_table(table)

@app.on_event("startup")
async def startup_event():
    init_db()
    load_stories()
    try:
        sync_stories_to_quests_v2()
        logger.info("✅ Quest sync completed")
    except Exception as e:
        logger.error(f"❌ Quest sync failed: {e}")
    seed_quests()
    seed_loot()
    asyncio.create_task(manager.monitor_connections())

@app.get("/")
def health(): return {"status": "ok"}
