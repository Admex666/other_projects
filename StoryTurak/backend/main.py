
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

app = FastAPI(title="StoryTurak Backend", version="1.1.0")

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

@app.post("/auth/register")
def register(req: AuthRequest):
    print(f"📝 Registration request for: {req.username}")
    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = str(uuid.uuid4())
    hashed = hash_password(req.password)
    create_user(user_id, req.username, hashed)
    return {"id": user_id, "username": req.username, "xp": 0}

@app.post("/auth/login")
def login(req: AuthRequest):
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": user["id"], "username": user["username"], "xp": user["xp"]}

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
