
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import asyncio
import hashlib
import uuid
from db import init_db, get_user_by_username, create_user, save_progress, get_progress

app = FastAPI(title="StoryTurak Backend", version="1.1.0")

# --- In-Memory Database (Mock) ---
sessions: Dict[str, dict] = {}

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

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

@app.post("/session/create")
def create_session(campaign_id: str, host: User):
    import random, string
    session_id = ''.join(random.choices(string.ascii_uppercase, k=4))
    sessions[session_id] = {
        "id": session_id,
        "campaignId": campaign_id,
        "hostId": host.id,
        "players": [host.dict()],
        "status": "waiting"
    }
    return sessions[session_id]

@app.post("/session/join")
def join_session(req: JoinRequest):
    if req.code not in sessions:
        raise HTTPException(status_code=404)
    session = sessions[req.code]
    if not any(p['id'] == req.user.id for p in session['players']):
        session['players'].append(req.user.dict())
    return session

@app.get("/session/{code}")
def get_session(code: str):
    if code not in sessions:
        raise HTTPException(status_code=404)
    return sessions[code]

# --- WebSocket Logic ---

@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_handler(websocket: WebSocket, session_id: str, user_id: str):
    await manager.connect(session_id, websocket)
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

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
