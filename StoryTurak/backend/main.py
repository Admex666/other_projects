import json
import asyncio
import hashlib
import uuid
import sys
import os
from pydantic import BaseModel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import init_db, get_user_by_username, create_user, save_progress, get_progress, db_create_session, db_join_session, get_user_sessions, db_update_session_status

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Optional
from datetime import timedelta

# ... imports ...
from auth import create_access_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, decode_access_token
from models_keldor import UserCreate, Token, Character, CharacterClass, PlayerState, Zone, Encounter, EncounterType, EncounterNodeType, EncounterChoice, EncounterNode, Item, ItemType, Quest, QuestObjective, QuestObjectiveType, QuestStatus, UserQuest, LootTable, LootEntry
from db import (
    init_db, get_user_by_username, create_user, save_progress, get_progress, 
    db_create_session, db_join_session, get_user_sessions, db_update_session_status,
    create_character, get_characters_by_user, update_character_inventory,
    create_quest, get_quest_by_id, get_user_quests, add_quest_to_user, update_user_quest_progress,
    create_item, get_item, create_loot_table, get_loot_table, update_character_visited_zones
)

app = FastAPI(title="Keldor Backend", version="2.0.0")
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
    # 1. inner City Ghost Quest
    q1 = {
        "id": "quest_opera_ghost",
        "title": "Az Operaház Fantomja",
        "description": "Keresd meg a ködben bujkáló szellemet.",
        "flavor_text": "Az Operaház árnyékában valami nem hagy nyugodni a lelkeket. Egy régi dal töredéke száll a szélben.",
        "image_url": "assets/mist_opera_phantom.png",
        "location": (47.502, 19.058),
        "min_level": 1,
        "objectives": [
            {
                "id": "obj_opera_01",
                "type": "complete_encounter",
                "target_id": "enc_poet_ghost",
                "count": 1,
                "description": "Beszélj a szellemmel"
            }
        ],
        "rewards_xp": 250,
        "starter_zone_id": "zone_belvaros"
    }
    # 2. Józsefváros Shadows
    q2 = {
        "id": "quest_eight_shadows",
        "title": "A Nyolcadik Kerület Árnyai",
        "description": "Tudd meg, miért gyülekeznek a Vámszedők.",
        "flavor_text": "A Józsefvárosi piac környékén sötét alakok suttognak. A Rend itt tehetetlen.",
        "image_url": "assets/mist_shadows_stairs.png",
        "location": (47.495, 19.075),
        "min_level": 2,
        "objectives": [
            {
                "id": "obj_eight_01",
                "type": "defeat_enemy",
                "target_id": "enemy_tax_collector",
                "count": 3,
                "description": "Győzz le 3 Vámszedőt"
            }
        ],
        "rewards_xp": 500,
        "starter_zone_id": "zone_nyolcker"
    }
    
    # Update q1/q2 to have start_location and empty stages for compatibility
    q1["start_location"] = q1.pop("location")
    q1["stages"] = []
    q2["start_location"] = q2.pop("location")
    q2["stages"] = []

    create_quest(q1)
    create_quest(q2)

# Dynamic Encounters Cache
dynamic_encounters = []

def sync_stories_to_quests():
    """
    Simulates the 'Quest' structures from the loaded JSON stories.
    This replaces the hardcoded seed_quests for Story-based content.
    """
    from db import create_quest, get_quest_by_id
    
    global dynamic_encounters
    dynamic_encounters = [] # Clear cache
    
    for story_id, story in STORY_DATA.items():
        # Check if this story is meant to be a Quest (has numeric rewards or map travel)
        if "rewards_xp" not in story and "estimated_distance_km" not in story:
            continue
            
        stages = []
        # Simple parser: Find all location_wait nodes and link them to the NEXT node as the encounter
        # This is a heuristic for the prototype to map Story -> Quest Stages
        
        # We need an ordered list of nodes. 
        # Since JSON is unordered map, we traverse next links starting from startNode
        current_node_id = story.get("startNode")
        visited = set()
        
        while current_node_id and current_node_id not in visited:
            visited.add(current_node_id)
            node = story["nodes"].get(current_node_id)
            if not node: break
            
            if node.get("type") == "location_wait":
                # Found a stage!
                # The encounter is effectively the node AFTER the arrival
                next_node_id = node.get("next")
                if next_node_id:
                    stage_encounter_id = f"{story_id}_{next_node_id}" # Synthetic ID
                    
                    stages.append({
                        "id": f"{story_id}_stage_{len(stages)+1}",
                        "description": node.get("description", node.get("text")[:50]+"..."),
                        "location": (node["targetLocation"]["lat"], node["targetLocation"]["lng"]),
                        "encounter_id": stage_encounter_id 
                    })
                    
                    # Create Logic Encounter Object for Map
                    # We wrap the whole story nodes but set the start_id to the stage's entry point
                    # This allows the encounter to play out using the Story Engine logic
                    
                    # Transform JSON nodes to EncounterNode objects
                    enc_nodes = {}
                    for nid, nops in story["nodes"].items():
                        # Map JSON node to EncounterNode
                        choices = []
                        if nops.get("choices"):
                            choices = [EncounterChoice(text=c["text"], next_node_id=c.get("next")) for c in nops["choices"]]
                            
                        enc_nodes[nid] = EncounterNode(
                            id=nid,
                            type=EncounterNodeType[nops.get("type", "narrative").upper()] if nops.get("type") != "location_wait" else EncounterNodeType.NARRATIVE,
                            text=nops.get("text", ""),
                            choices=choices if choices else None,
                            next_node_id=nops.get("next"),
                            image=nops.get("image")
                            # combat stats etc ignored for MVP sync
                        )
                    
                    # Create the Encounter Object
                    enc_obj = Encounter(
                        id=stage_encounter_id,
                        title=story.get("title") + " - " + node.get("description", "Stage"),
                        description=stages[-1]["description"],
                        type=EncounterType.STORY, # Trigger detailed view
                        start_node_id=next_node_id, 
                        location=stages[-1]["location"],
                        nodes=enc_nodes,
                        zone_id="zone_nyolcker" # Default
                    )
                    dynamic_encounters.append(enc_obj)
                
            current_node_id = node.get("next")
            # Handle choices? For linear path mapping we just take the first choice if navigation
            # But for simplicity let's stick to the 'next' attribute for the happy path
            if not current_node_id and node.get("choices"):
                current_node_id = node["choices"][0].get("next")

        # Create the Quest Object
        q_data = {
            "id": story_id,
            "title": story.get("title", "Untitled Story"),
            "description": story.get("description", "A mystery awaits..."),
            "flavor_text": story.get("flavor_text", ""),
            "image_url": story.get("image_url"),
            "start_location": tuple(stages[0]["location"]) if stages else (47.4979, 19.0402), 
            "stages": stages,
            "estimated_distance_km": story.get("estimated_distance_km", 1.0),
            "min_level": story.get("min_level", 1),
            "objectives": [],
            "rewards_xp": story.get("rewards_xp", 100),
            "rewards_items": story.get("rewards_items", []),
            "starter_zone_id": "zone_nyolcker" # Default/Mock
        }
        
        create_quest(q_data)
        logger.info(f" synced quest: {story_id} with {len(stages)} stages")

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

# Run init and seed on startup
init_db()
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
    load_stories()
    try:
        sync_stories_to_quests_v2() # Hydrate Quests from Stories (V2 with dynamic encounters)
        logger.info("✅ Quest sync completed")
    except Exception as e:
        logger.error(f"❌ Quest sync failed: {e}")
        import traceback
        traceback.print_exc()
    seed_loot()
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

# --- Keldor Endpoints ---

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

# Dynamic Encounters Cache
dynamic_encounters: List[Encounter] = []

# Define Encounters separately
encounters_db: List[Encounter] = [
    Encounter(
        id="enc_poet_ghost",
        title="Az Elfeledett Költő Szelleme",
        description="Egy halvány alak szaval a lámpaoszlop alatt.",
        type=EncounterType.STORY,
        start_node_id="start",
        location=(47.498, 19.040),
        nodes={
            "start": EncounterNode(
                id="start",
                type=EncounterNodeType.NARRATIVE,
                text="A szellem feléd fordul. Szemeiben a múlt fájdalma tükröződik. 'Emlékszel még a szavakra?' - suttogja.",
                image="assets/mist_walker_cover.png",
                next_node_id="choice_path"
            ),
            "choice_path": EncounterNode(
                id="choice_path",
                type=EncounterNodeType.CHOICE,
                text="Hogyan válaszolsz neki?",
                choices=[
                    EncounterChoice(text="Verssel felelek (Költő)", next_node_id="success_poet"),
                    EncounterChoice(text="Csendben hallgatom", next_node_id="success_listen"),
                    EncounterChoice(text="Fegyvert rántok", next_node_id="fail_fight")
                ]
            ),
            "success_poet": EncounterNode(
                id="success_poet",
                type=EncounterNodeType.NARRATIVE,
                text="A szellem elmosolyodik. 'A dal folytatódik.' Átnyújt neked egy poros tekercset.",
                next_node_id="end"
            ),
            "success_listen": EncounterNode(
                id="success_listen",
                type=EncounterNodeType.NARRATIVE,
                text="A csend néha többet mond. A szellem bólint és lassan elenyészik a ködben.",
                next_node_id="end"
            ),
            "fail_fight": EncounterNode(
                id="fail_fight",
                type=EncounterNodeType.FIGHT,
                text="A szellem haraggá válik! Meg kell küzdened az árnyékkal!",
                enemy_id="ghost_shadow",
                enemy_hp=20,
                next_node_id="end"
            ),
            "end": EncounterNode(
                id="end",
                type=EncounterNodeType.NARRATIVE,
                text="Az encounter véget ért. A köd egy pillanatra felszáll."
            )
        },
        zone_id="zone_belvaros",
        active_hours_start=20, active_hours_end=4
    ),
    Encounter(
        id="enc_mystic_merchant",
        title="A Józsefvárosi Titkos Árus",
        description="Egy gyanús alak babrál a kabátja belső zsebében egy sötét sikátorban.",
        type=EncounterType.STORY,
        start_node_id="start",
        location=(47.495, 19.065),
        nodes={
            "start": EncounterNode(
                id="start",
                type=EncounterNodeType.NARRATIVE,
                text="'Hé, te! Érdekel valami ritka? Valami, amit a Rend nem lát szívesen?'",
                next_node_id="choice"
            ),
            "choice": EncounterNode(
                id="choice",
                type=EncounterNodeType.CHOICE,
                text="Mit teszel?",
                choices=[
                    EncounterChoice(text="Megnézem az áruját", next_node_id="merchant_view"),
                    EncounterChoice(text="Továbbállok", next_node_id="merchant_leave")
                ]
            ),
             "merchant_view": EncounterNode(
                id="merchant_view",
                type=EncounterNodeType.NARRATIVE,
                text="Különös tárgyak csillannak meg a félhomályban. 'Csak tiszta aranyat fogadok el... vagy különös szívességeket.'",
                next_node_id="end"
            ),
            "merchant_leave": EncounterNode(
                id="merchant_leave",
                type=EncounterNodeType.NARRATIVE,
                text="Vállat ránt és elhúzódik az árnyékok közé.",
                next_node_id="end"
            ),
            "end": EncounterNode(
                id="end",
                type=EncounterNodeType.NARRATIVE,
                text="A találkozás befejeződött."
            )
        },
        zone_id="zone_nyolcker"
    ),
    Encounter(
        id="enc_nervous_gardener",
        title="Az Idegenszerű Kertész",
        description="Egy férfi izgatottan mutogat egy régi térképre a piac sarkában.",
        type=EncounterType.STORY,
        start_node_id="start",
        location=(47.486598, 19.106905),
        nodes={
            "start": EncounterNode(
                id="start",
                type=EncounterNodeType.NARRATIVE,
                text="'Kérlek, segíts! Elhagytam a Füvészkert titkos kulcsát. Ha a Rend megtalálja, mindennek vége!'",
                next_node_id="choice"
            ),
            "choice": EncounterNode(
                id="choice",
                type=EncounterNodeType.CHOICE,
                text="Mit válaszolsz?",
                choices=[
                    EncounterChoice(text="Segítek megkeresni", next_node_id="accept"),
                    EncounterChoice(text="Nincs időm ilyesmire", next_node_id="reject")
                ]
            ),
            "accept": EncounterNode(
                id="accept",
                type=EncounterNodeType.NARRATIVE,
                text="'Hála az égnek! Indulj el a Szigony utca felé, ott látták utoljára a tolvajt.'",
                next_node_id="end"
            ),
            "reject": EncounterNode(
                id="reject",
                type=EncounterNodeType.NARRATIVE,
                text="A férfi csalódottan eloldalog.",
                next_node_id="end"
            ),
            "end": EncounterNode(id="end", type=EncounterNodeType.NARRATIVE, text="A találkozás véget ért.")
        },
        zone_id="zone_nyolcker"
    ),
    Encounter(
        id="enc_rival_botanist",
        title="A Rivális Botanikus",
        description="Egy elegáns alak áll az utadba. Könyvet tart a kezében, de a szemeiben acélos hidegség.",
        type=EncounterType.STORY,
        start_node_id="start",
        location=(47.485, 19.095),
        nodes={
            "start": EncounterNode(
                id="start",
                type=EncounterNodeType.NARRATIVE,
                text="'Te is a kulcsot keresed? Kár érte... az már az enyém. Add át, amit tudsz, vagy készülj a következményekre!'",
                next_node_id="choice"
            ),
            "choice": EncounterNode(
                id="choice",
                type=EncounterNodeType.CHOICE,
                text="Hogyan döntesz?",
                choices=[
                    EncounterChoice(text="Megpróbálom lebeszélni (Meggyőzés)", next_node_id="persuade"),
                    EncounterChoice(text="Harcolok a kulcsért", next_node_id="fight")
                ]
            ),
            "persuade": EncounterNode(
                id="persuade",
                type=EncounterNodeType.NARRATIVE,
                text="A szavaid hatnak rá. 'Talán... talán igazad van. Vigyed, de vigyázz vele.'",
                next_node_id="end"
            ),
            "fight": EncounterNode(
                id="fight",
                type=EncounterNodeType.FIGHT,
                text="Pálcát ránt és különös növénymájgiával támad!",
                enemy_id="rival_botanist",
                enemy_hp=30,
                next_node_id="end"
            ),
            "end": EncounterNode(id="end", type=EncounterNodeType.NARRATIVE, text="Az út szabad.")
        },
        zone_id="zone_nyolcker"
    ),
    Encounter(
        id="enc_garden_gate",
        title="A Füvészkert Rejtett Kapuja",
        description="Egy borostyánnal benőtt vaskapu áll előtted. Nincs rajta kilincs, csak egy különös felirat.",
        type=EncounterType.STORY,
        start_node_id="start",
        location=(47.483809, 19.085603),
        nodes={
            "start": EncounterNode(
                id="start",
                type=EncounterNodeType.NARRATIVE,
                text="'Ami éjszaka nyílik, de nappal bezárul, a fény elől menekülve árnyékba burkol.' - Mi a jelszó?",
                next_node_id="input"
            ),
            "input": EncounterNode(
                id="input",
                type=EncounterNodeType.INPUT,
                text="Írd be a jelszót:",
                correct_answer="éjjeli hölgy",
                next_node_id="success_gate"
            ),
            "success_gate": EncounterNode(
                id="success_gate",
                type=EncounterNodeType.NARRATIVE,
                text="A kapu halkan nyikorogva kitárul. Belépsz a kertbe.",
                next_node_id="end"
            ),
            "end": EncounterNode(id="end", type=EncounterNodeType.NARRATIVE, text="Sikeresen bejutottál.")
        },
        zone_id="zone_nyolcker"
    ),
]

# Mock Player States
player_states: Dict[str, PlayerState] = {}

@app.post("/world/init_player")
def init_player(user_id: str, character_class: CharacterClass):
    state = PlayerState(user_id=user_id, character_class=character_class)
    player_states[user_id] = state
    return state

@app.get("/world/nearby")
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
    # Combined static + dynamic
    all_encounters = encounters_db + dynamic_encounters
    
    nearby_encounters = [
        e for e in all_encounters 
        if e.zone_id in active_zones
    ]

    return {
        "zones": nearby_zones,
        "encounters": nearby_encounters
    }

@app.get("/test/quests")
def test_quests():
    """Test endpoint to debug quest fetching"""
    from db import get_all_quests
    print("🧪 TEST: Calling get_all_quests()")
    quests = get_all_quests()
    print(f"🧪 TEST: Got {len(quests)} quests")
    return {"count": len(quests), "quests": quests}

@app.get("/quests")
def get_quests():
    from db import get_all_quests
    quests = get_all_quests()
    logger.info(f"📋 Returning {len(quests)} quests from /quests endpoint")
    return quests

@app.get("/quests/{quest_id}")
def get_quest(quest_id: str):
    from db import get_quest_by_id
    quest = get_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404)
    return quest

@app.get("/characters/{char_id}/quests")
def get_char_quests(char_id: str, current_user: dict = Depends(get_current_user)):
    from db import get_user_quests
    return get_user_quests(current_user["id"])

@app.post("/quests/{quest_id}/accept")
def accept_quest(quest_id: str, current_user: dict = Depends(get_current_user)):
    from db import add_quest_to_user, get_quest_by_id
    import uuid
    
    quest = get_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    uq_id = str(uuid.uuid4())
    uq_data = {
        "id": uq_id,
        "user_id": current_user["id"],
        "quest_id": quest_id,
        "status": "active",
        "current_stage_index": 0,
        "current_objective_index": 0,
        "current_count": 0
    }
    add_quest_to_user(uq_data)
    return uq_data

@app.delete("/user-quests/{user_quest_id}")
def abandon_quest(user_quest_id: str, current_user: dict = Depends(get_current_user)):
    """Abandon/delete a user's quest"""
    from db import execute_query
    
    # Verify the quest belongs to the user
    res = execute_query("SELECT user_id FROM user_quests WHERE id = ?", (user_quest_id,))
    if not res or res[0][0] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    # Delete the quest
    execute_query("DELETE FROM user_quests WHERE id = ?", (user_quest_id,))
    logger.info(f"🗑️ User {current_user['id']} abandoned quest {user_quest_id}")
    return {"status": "success", "message": "Quest abandoned"}

@app.post("/encounters/resolve")
def resolve_encounter(data: dict, current_user: dict = Depends(get_current_user)):
    from db import get_user_quests, get_quest_by_id, update_user_quest_progress
    
    enc_id = data.get("encounter_id")
    outcome = data.get("outcome") # Not used yet but good for logic
    
    logger.info(f"🔍 RESOLVE ENCOUNTER: enc_id={enc_id}, outcome={outcome}, user={current_user['id']}")
    
    # Check if this encounter is part of any active quest stage
    user_quests = get_user_quests(current_user["id"])
    active_uq = next((uq for uq in user_quests if uq["status"] == "active"), None)
    
    logger.info(f"🔍 Active quest: {active_uq}")
    
    if active_uq:
        quest = get_quest_by_id(active_uq["quest_id"])
        if quest and quest["stages"]:
            current_stage_idx = active_uq["current_stage_index"]
            if current_stage_idx < len(quest["stages"]):
                stage = quest["stages"][current_stage_idx]
                if stage["encounter_id"] == enc_id:
                    # Move to next stage!
                    new_stage_idx = current_stage_idx + 1
                    new_status = "active"
                    if new_stage_idx >= len(quest["stages"]):
                        new_status = "completed"
                    
                    update_user_quest_progress(
                        active_uq["id"], 
                        active_uq["current_count"], 
                        new_stage_index=new_stage_idx,
                        new_status=new_status
                    )
                    return {"status": "success", "message": "Quest stage progressed", "new_status": new_status}

    # If no active quest matches, check if this encounter starts any available quest
    from db import get_all_quests, add_quest_to_user
    import uuid
    all_quests = get_all_quests()
    for q in all_quests:
        # Check if user already has this quest (don't restart)
        if any(uq['quest_id'] == q['id'] for uq in user_quests):
            continue
            
        if q.get("stages") and q["stages"][0]["encounter_id"] == enc_id:
            # Automagically accept the quest!
            uq_id = str(uuid.uuid4())
            uq_data = {
                "id": uq_id,
                "user_id": current_user["id"],
                "quest_id": q["id"],
                "status": "active",
                "current_stage_index": 1, # Set to next stage (1) since we just did stage 0
                "current_objective_index": 0,
                "current_count": 0
            }
            add_quest_to_user(uq_data)
            return {"status": "success", "message": "Quest accepted and progressed", "new_status": "active"}

    return {"status": "success", "message": "Encounter resolved"}

def sync_stories_to_quests_v2():
    """
    Simulates the 'Quest' structures from the loaded JSON stories.
    This replaces the hardcoded seed_quests for Story-based content.
    """
    from db import create_quest, get_quest_by_id
    
    global dynamic_encounters
    dynamic_encounters = [] # Clear cache
    
    for story_id, story in STORY_DATA.items():
        # Check if this story is meant to be a Quest (has numeric rewards or map travel)
        if "rewards_xp" not in story and "estimated_distance_km" not in story:
            continue
            
        stages = []
        current_node_id = story.get("startNode")
        visited = set()
        
        while current_node_id and current_node_id not in visited:
            visited.add(current_node_id)
            node = story["nodes"].get(current_node_id)
            if not node: break
            
            if node.get("type") == "location_wait":
                # Found a stage!
                # The encounter is effectively the node AFTER the arrival
                next_node_id = node.get("next")
                if next_node_id:
                    stage_encounter_id = f"{story_id}_{next_node_id}" # Synthetic ID
                    
                    stages.append({
                        "id": f"{story_id}_stage_{len(stages)+1}",
                        "description": node.get("description", node.get("text")[:50]+"..."),
                        "location": (node["targetLocation"]["lat"], node["targetLocation"]["lng"]),
                        "encounter_id": stage_encounter_id 
                    })
                    
                    # Create Logic Encounter Object for Map
                    enc_nodes = {}
                    for nid, nops in story["nodes"].items():
                        choices = []
                        if nops.get("choices"):
                            choices = [EncounterChoice(text=c["text"], next_node_id=c.get("next")) for c in nops["choices"]]
                            
                        enc_nodes[nid] = EncounterNode(
                            id=nid,
                            type=EncounterNodeType[nops.get("type", "narrative").upper()] if nops.get("type") != "location_wait" else EncounterNodeType.NARRATIVE,
                            text=nops.get("text", ""),
                            choices=choices if choices else None,
                            next_node_id=nops.get("next"),
                            image=nops.get("image")
                        )
                    
                    # Create the Encounter Object
                    enc_obj = Encounter(
                        id=stage_encounter_id,
                        title=story.get("title") + " - " + node.get("description", "Stage"),
                        description=stages[-1]["description"],
                        type=EncounterType.STORY, # Trigger detailed view
                        start_node_id=next_node_id, 
                        location=stages[-1]["location"],
                        nodes=enc_nodes,
                        zone_id="zone_nyolcker" # Default
                    )
                    dynamic_encounters.append(enc_obj)
                
            current_node_id = node.get("next")
            if not current_node_id and node.get("choices"):
                current_node_id = node["choices"][0].get("next")

        # Create the Quest Object
        q_data = {
            "id": story_id,
            "title": story.get("title", "Untitled Story"),
            "description": story.get("description", "A mystery awaits..."),
            "flavor_text": story.get("flavor_text", ""),
            "image_url": story.get("image_url"),
            "start_location": tuple(stages[0]["location"]) if stages else (47.4979, 19.0402), 
            "stages": stages,
            "estimated_distance_km": story.get("estimated_distance_km", 1.0),
            "min_level": story.get("min_level", 1),
            "objectives": [],
            "rewards_xp": story.get("rewards_xp", 100),
            "rewards_items": story.get("rewards_items", []),
            "starter_zone_id": "zone_nyolcker" # Default/Mock
        }
        
        create_quest(q_data)
        logger.info(f" synced quest: {story_id} with {len(stages)} stages")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
