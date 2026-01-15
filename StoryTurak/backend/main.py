
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import asyncio
import hashlib
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import init_db, get_user_by_username, create_user, save_progress, get_progress, db_create_session, db_join_session, get_user_sessions, db_update_session_status

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Optional
from datetime import timedelta

# ... imports ...
from auth import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, decode_access_token
from models_geolixo import UserCreate, Token, Character, CharacterClass, PlayerState, Zone, Encounter, EncounterType, Item, ItemType, Quest, QuestObjective, QuestObjectiveType, QuestStatus, UserQuest, LootTable, LootEntry
from db import (
    init_db, get_user_by_username, create_user, save_progress, get_progress, 
    db_create_session, db_join_session, get_user_sessions, db_update_session_status,
    create_character, get_characters_by_user, update_character_inventory,
    create_quest, get_quest_by_id, get_user_quests, add_quest_to_user, update_user_quest_progress,
    create_item, get_item, create_loot_table, get_loot_table, update_character_visited_zones
)

app = FastAPI(title="Geolixo Backend", version="2.0.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
         raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- Auth Endpoints ---

@app.post("/auth/register", response_model=Token)
def register(user: UserCreate):
    db_user = get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user_id = str(uuid.uuid4())
    hashed_pw = get_password_hash(user.password)
    create_user(user_id, user.username, hashed_pw)
    
    # Auto-login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Character Endpoints ---

@app.get("/characters", response_model=List[Character])
def get_my_characters(current_user: dict = Depends(get_current_user)):
    return get_characters_by_user(current_user["id"])

@app.post("/characters/create", response_model=Character)
def create_new_character(character_class: CharacterClass, name: str, current_user: dict = Depends(get_current_user)):
    char_id = str(uuid.uuid4())
    new_char = {
        "id": char_id,
        "user_id": current_user["id"],
        "name": name,
        "character_class": character_class,
        "level": 1,
        "xp": 0,
        "max_hp": 10,
        "stats": {"strength": 5, "agility": 5} if character_class == CharacterClass.SOLDIER else {"strength": 2, "agility": 3},
        "inventory": [],
        "visited_zones": [],
        "completed_quests": []
    }
    create_character(new_char)
    # Return as object matching model
    return Character(**new_char)

@app.post("/characters/{character_id}/visit-zone")
def visit_zone_endpoint(character_id: str, zone_id: str, current_user: dict = Depends(get_current_user)):
    # Verify character belongs to user
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    update_character_visited_zones(character_id, zone_id)
    return {"status": "ok"}

# --- Quest Endpoints ---

@app.get("/quests", response_model=List[UserQuest])
def get_my_quests(current_user: dict = Depends(get_current_user)):
    return get_user_quests(current_user["id"])

@app.get("/quests/available", response_model=List[Quest])
def get_available_quests_endpoint(current_user: dict = Depends(get_current_user)):
    # In a real app, filter by level, prerequisites, etc.
    # For MVP, we return our hardcoded quest #1 if not already taken
    
    # Check if already taken
    my_quests = get_user_quests(current_user["id"])
    taken_ids = [q["quest_id"] for q in my_quests]
    
    available = []
    # Hardcoded check for our seed quest
    if "quest_starter_01" not in taken_ids:
        q = get_quest_by_id("quest_starter_01")
        if q:
            available.append(Quest(**q))
            
    return available

@app.post("/quests/{quest_id}/accept", response_model=UserQuest)
def accept_quest_endpoint(quest_id: str, current_user: dict = Depends(get_current_user)):
    # Validation
    quest = get_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    my_quests = get_user_quests(current_user["id"])
    if any(q["quest_id"] == quest_id for q in my_quests):
        raise HTTPException(status_code=400, detail="Quest already accepted")

    user_quest_id = str(uuid.uuid4())
    new_uq = {
        "id": user_quest_id,
        "user_id": current_user["id"],
        "quest_id": quest_id,
        "status": QuestStatus.ACTIVE,
        "current_objective_index": 0,
        "current_count": 0
    }
    add_quest_to_user(new_uq)
    return UserQuest(**new_uq)


class EncounterResolution(BaseModel):
    encounter_id: str
    outcome: str # success, failure, escape
    
@app.post("/encounters/resolve")
def resolve_encounter(resolution: EncounterResolution, current_user: dict = Depends(get_current_user)):
    # 1. Validation (Verify encounter exists, etc. - skipping for MVP)
    
    rewards = {"xp": 0, "items": []}
    
    if resolution.outcome == "success":
        # Base XP
        rewards["xp"] = 50
        
        # simple Loot Logic (Mocked table ID for now)
        # In prod, get table_id from Encounter definition
        table_id = "loot_table_common" 
        dropped_items = roll_loot(table_id)
        
        # Update Character Inventory
        # For simplicity, we update the first character of the user
        chars = get_characters_by_user(current_user["id"])
        if chars:
            char = chars[0] # Active character
            current_inv = char["inventory"] # List of dicts
            
            # Add items
            for item in dropped_items:
                # Check stackability
                found = False
                for slot in current_inv:
                    if slot["item_id"] == item["id"]:
                        slot["quantity"] += 1
                        found = True
                        break
                if not found:
                    current_inv.append({"item_id": item["id"], "quantity": 1, "equipped": False})
            
            # Save
            update_character_inventory(char["id"], current_inv)
            
            # Populate response
            rewards["items"] = dropped_items
            
            # Give XP to Character
            from db import update_user_xp, update_character_xp_and_level
            
            # 1. Update Global User XP (Legacy/Profile)
            update_user_xp(current_user["id"], rewards["xp"])

            # 2. Update Active Character XP & Level
            current_xp = char["xp"] + rewards["xp"]
            current_level = char["level"]
            # Simple level curve: Level * 100 XP to advance
            xp_to_next = current_level * 100
            
            if current_xp >= xp_to_next:
                current_level += 1
                current_xp -= xp_to_next # Rollover or Keep total? usually total in many games, but here let's stick to total accumulation model
                # Wait, if we use total accumulation, the check is different.
                # Let's use simple accumulation: Level = floor(sqrt(XP/100)) or just increment
                # For MVP: Accumulate XP. If XP > threshold, Level Up.
                # Let's say: 0-99 = Lvl 1, 100-299 = Lvl 2, etc.
                # Actually, simplest is just increment level if threshold passed.
                pass 
            
            # Let's just blindly add XP and recalc level
            # Level formula: Level = 1 + int((TotalXP / 100) ** 0.5) ? No, too slow.
            # Linear: Level = 1 + TotalXP // 100
            new_level = 1 + (current_xp // 100)
            
            update_character_xp_and_level(char["id"], current_xp, new_level)

    return rewards

def roll_loot(table_id: str):
    import random
    table = get_loot_table(table_id)
    drops = []
    if table:
        for entry in table["entries"]: # list of dicts from JSON
            if random.random() <= entry["chance"]:
                # Drop!
                item = get_item(entry["item_id"])
                if item:
                    drops.append(item)
    return drops

# Seed Data (Quick & Dirty)
def seed_quests():
    q1 = {
        "id": "quest_starter_01",
        "title": "A Kezdetek",
        "description": "Menj el a Belvárosba, és keress nyomokat.",
        "min_level": 1,
        "objectives": [
            {
                "id": "obj_01",
                "type": "visit_zone",
                "target_id": "zone_belvaros",
                "count": 1,
                "description": "Látogasd meg a Belvárost"
            }
        ],
        "rewards_xp": 150,
        "starter_zone_id": None # Available globally
    }
    create_quest(q1)

def seed_loot():
    # Items
    potion = {
        "id": "item_healing_potion_minor",
        "name": "Kicsi Gyógyital",
        "description": "Enyhíti a fájdalmat. +5 HP.",
        "type": "consumable",
        "value": 10,
        "icon_code": "local_pharmacy", # Flutter Icon name
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
    
    # Loot Table
    table = {
        "id": "loot_table_common",
        "entries": [
            {"item_id": "item_healing_potion_minor", "chance": 0.5, "min_qty": 1, "max_qty": 1},
            {"item_id": "item_ancient_coin", "chance": 0.3, "min_qty": 1, "max_qty": 2} # Qty logic not impl yet, assume 1
        ]
    }
    create_loot_table(table)

# Run seed on startup (safe to run multiple times due to INSERT OR IGNORE)
seed_quests()
seed_loot()

# --- In-Memory Database (Mock) ---
sessions: Dict[str, dict] = {}

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.last_seen: Dict[WebSocket, float] = {}
        self.user_map: Dict[WebSocket, str] = {} # WebSocket -> userId

    async def connect(self, session_id: str, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        self.last_seen[websocket] = asyncio.get_event_loop().time()
        self.user_map[websocket] = user_id

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
        if websocket in self.last_seen:
            del self.last_seen[websocket]
        if websocket in self.user_map:
            del self.user_map[websocket]

    def update_heartbeat(self, websocket: WebSocket):
        self.last_seen[websocket] = asyncio.get_event_loop().time()

    async def broadcast(self, session_id: str, message: dict):
        if session_id not in self.active_connections:
            return
        
        # Use a copy of the list to avoid "size changed during iteration" errors
        for connection in list(self.active_connections[session_id]):
            try:
                await connection.send_json(message)
            except:
                self.disconnect(session_id, connection)

    async def monitor_connections(self):
        while True:
            now = asyncio.get_event_loop().time()
            for session_id, connections in list(self.active_connections.items()):
                for ws in list(connections):
                    if now - self.last_seen.get(ws, 0) > 30: # 30s timeout
                        user_id = self.user_map.get(ws)
                        logger.info(f"User {user_id} timed out in session {session_id}")
                        await self.broadcast(session_id, {
                            "type": "USER_STATUS",
                            "userId": user_id,
                            "status": "AWAY"
                        })
                        # Optional: self.disconnect(session_id, ws) or just mark AWAY
            await asyncio.sleep(10)

manager = ConnectionManager()

# --- Models ---
class User(BaseModel):
    id: str
    username: str
    xp: int = 0
    isReady: bool = False

class AuthRequest(BaseModel):
    username: str
    password: str

class JoinRequest(BaseModel):
    code: str
    user: User

# --- Utility Functions ---
def hash_password(password: str) -> str:
    # Adding a static salt for prototype simplicity. In production use bcrypt/argon2.
    salt = "storyturak_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# --- Data Loading ---
STORY_DATA = {}
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_stories():
    STORY_DATA.clear()
    
    # Get absolute path to the data directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found at {data_dir}")
        return

    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            p = os.path.join(data_dir, filename)
            try:
                with open(p, "r", encoding="utf-8") as f:
                    story = json.load(f)
                    STORY_DATA[story["id"]] = story
                    logger.info(f"Successfully loaded story: {story['id']} from {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    if not STORY_DATA:
        logger.warning("No stories were loaded!")

load_stories()

@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(manager.monitor_connections())

# --- API Endpoints ---

@app.get("/")
def health(): return {"status": "ok"}

@app.get("/stories")
def get_stories():
    load_stories() # Hot-reload stories for development
    return list(STORY_DATA.values())

@app.get("/stories/{story_id}")
def get_story(story_id: str):
    load_stories() # Hot-reload stories for development
    if story_id not in STORY_DATA:
        raise HTTPException(status_code=404)
    return STORY_DATA[story_id]


@app.get("/progress/{user_id}/{story_id}")
def get_user_story_progress(user_id: str, story_id: str):
    prog = get_progress(user_id, story_id)
    if not prog:
        return {"nodeId": None, "variables": {}}
    return prog

@app.post("/progress/{user_id}/{story_id}")
def update_user_story_progress(user_id: str, story_id: str, data: dict):
    # data expects { "nodeId": "...", "variables": {...} }
    save_progress(user_id, story_id, data["nodeId"], data["variables"])
    return {"status": "saved"}

@app.post("/progress/{user_id}/{story_id}/xp")
def add_xp(user_id: str, amount: int):
    from db import update_user_xp
    update_user_xp(user_id, amount)
    return {"status": "xp_added"}

@app.post("/analytics/log")
def log_event(data: dict):
    from db import execute_query
    import json
    execute_query("INSERT INTO analytics (user_id, event_type, data) VALUES (?, ?, ?)", 
                  (data.get("userId"), data.get("type"), json.dumps(data.get("payload", {}))))
    return {"status": "logged"}

@app.get("/users/{user_id}/sessions")
def list_user_sessions(user_id: str):
    return get_user_sessions(user_id)

@app.post("/session/create")
def create_session(campaign_id: str, host: User):
    import random, string
    session_id = ''.join(random.choices(string.ascii_uppercase, k=4))
    sessions[session_id] = {
        "id": session_id,
        "hostId": host.id,
        "campaignId": campaign_id,
        "players": [host.dict()],
        "status": "waiting"
    }
    db_create_session(session_id, host.id, campaign_id)
    return sessions[session_id]

@app.post("/session/join")
def join_session(req: JoinRequest):
    if req.code not in sessions:
        # Try to load from DB? (Skipping for now to keep it simple, sessions usually short-lived)
        raise HTTPException(status_code=404)
    session = sessions[req.code]
    if not any(p['id'] == req.user.id for p in session['players']):
        session['players'].append(req.user.dict())
        db_join_session(req.code, req.user.id)
    return session

@app.get("/session/{code}")
def get_session(code: str):
    if code not in sessions:
        # Try to load from DB? (Skipping for now to keep it simple, sessions usually short-lived)
        raise HTTPException(status_code=404)
    return sessions[code]

# --- WebSocket Logic ---

@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_handler(websocket: WebSocket, session_id: str, user_id: str):
    await manager.connect(session_id, websocket, user_id)
    try:
        # Broadcast full player list on join
        if session_id in sessions:
            await manager.broadcast(session_id, {
                "type": "SESSION_UPDATE",
                "session": sessions[session_id]
            })
        
        while True:
            data = await websocket.receive_json()
            # Expecting: { "type": "POSITION", "lat": X, "lng": Y } or { "type": "STORY_ADVANCE", "nodeId": X, "variables": {...}, "storyId": "..." }
            data["userId"] = user_id # Add sender info
            
            if data.get("type") == "GAME_START" and session_id in sessions:
                sessions[session_id]["status"] = "active"
                db_update_session_status(session_id, "active")

            if data.get("type") == "HEARTBEAT":
                manager.update_heartbeat(websocket)
                continue

            if data.get("type") == "STORY_ADVANCE" and "storyId" in data:
                save_progress(user_id, data["storyId"], data["nodeId"], data.get("variables", {}))
                # Fall through to broadcast

            if data.get("type") == "USER_READY" and session_id in sessions:
                for p in sessions[session_id]['players']:
                    if p['id'] == user_id:
                        p['isReady'] = data.get('ready', False)
                await manager.broadcast(session_id, {
                    "type": "SESSION_UPDATE",
                    "session": sessions[session_id]
                })
                continue # Already broadcasted

            await manager.broadcast(session_id, data)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        await manager.broadcast(session_id, {
            "type": "USER_LEFT",
            "userId": user_id
        })

# --- Geolixo Endpoints ---
from models_geolixo import Zone, Encounter, CharacterClass, PlayerState, EncounterType

# Mock Active Zones (Budapest)
active_zones: Dict[str, Zone] = {
    # 1. District V (Inner City)
    "zone_belvaros": Zone(
        id="zone_belvaros",
        name="Belváros - A Ködös Utcák",
        description="A régi Pest szíve. Itt a legerősebb a Rend őreinek jelenléte, de a földalatti járatokban más világ uralkodik.",
        boundary_points=[
            (47.498, 19.040), (47.502, 19.050),
            (47.495, 19.060), (47.490, 19.045)
        ],
        difficulty_level=1,
        active_encounters=[]
    ),
    # 2. District VIII (Józsefváros)
    "zone_nyolcker": Zone(
        id="zone_nyolcker",
        name="VIII. Kerület - A Sötét Parkok",
        description="A senki földje. Kereskedők, csempészek és bukott költők tanyája. Veszélyes, de nagy kincseket rejt.",
        boundary_points=[
            (47.495, 19.065), (47.498, 19.080),
            (47.485, 19.085), (47.485, 19.070)
        ],
        difficulty_level=3,
        active_encounters=[]
    )
}

# Define Encounters separately
encounters_db: List[Encounter] = [
    Encounter(
        id="enc_poet_ghost",
        title="Az Elfeledett Költő Szelleme",
        description="Egy halvány alak szaval a lámpaoszlop alatt. Szavai mintha fizikai súllyal nehezednének a válladra.",
        type=EncounterType.NARRATIVE,
        options=[], # Narrative only
        zone_id="zone_belvaros",
        active_hours_start=20, active_hours_end=4
    ),
    Encounter(
        id="enc_tax_collector_ambush",
        title="Vámszedő Rajtaütés",
        description="Két marcona alak állja utadat. 'Itt minden lépés adóköteles', mordulnak rád.",
        type=EncounterType.FIGHT,
        options=[], # Logic handled in resolving
        zone_id="zone_nyolcker",
        active_hours_start=0, active_hours_end=24
    ),
    Encounter(
        id="enc_mystic_merchant",
        title="A Ködárus",
        description="Egy köpenyes alak kínál üvegcséket. A tartalmuk folyamatosan kavarog.",
        type=EncounterType.SHOP,
        options=[],
        zone_id="zone_belvaros",
        active_hours_start=18, active_hours_end=6
    ),
]

# Mock Player States
player_states: Dict[str, PlayerState] = {}

@app.post("/geolixo/init_player")
def init_player(user_id: str, character_class: CharacterClass):
    state = PlayerState(user_id=user_id, character_class=character_class)
    player_states[user_id] = state
    return state

@app.get("/geolixo/world/nearby")
def get_nearby_world(lat: float, lon: float, radius: int = 1000):
    """
    Returns zones and encounters within 'radius' meters of (lat, lon).
    For MVP, we just return the fixed Belvaros zone if close enough.
    """
    # Simple distance check logic would go here.
    # returning all for MVP testing
    # Filter zones for MVP (just returning all)
    nearby_zones = list(active_zones.values())
    
    # Filter encounters for these zones
    nearby_encounters = [
        e for e in encounters_db 
        if e.zone_id in active_zones
    ]

    return {
        "zones": nearby_zones,
        "encounters": nearby_encounters
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
