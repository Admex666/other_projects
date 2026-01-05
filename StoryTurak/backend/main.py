
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import asyncio

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
    name: str

class JoinRequest(BaseModel):
    code: str
    user: User

# --- Data Loading ---
STORY_DATA = {}
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_stories():
    STORY_DATA.clear()
    
    # Get absolute path to the directory where main.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Potential paths to check
    possible_paths = [
        os.path.join(base_dir, "data", "mist_walker.json"),
        os.path.join(base_dir, "..", "backend", "data", "mist_walker.json"),
        os.path.join(os.getcwd(), "backend", "data", "mist_walker.json"),
        os.path.join(os.getcwd(), "data", "mist_walker.json"),
    ]
    
    loaded = False
    for p in possible_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    story = json.load(f)
                    STORY_DATA[story["id"]] = story
                    logger.info(f"Successfully loaded story: {story['id']} from {p}")
                    loaded = True
            except Exception as e:
                logger.error(f"Error loading story from {p}: {e}")
    
    if not loaded:
        logger.warning("No stories were loaded! Checked paths: " + ", ".join(possible_paths))

load_stories()

# --- API Endpoints ---

@app.get("/")
def health(): return {"status": "ok"}

@app.get("/stories/{story_id}")
def get_story(story_id: str):
    if story_id not in STORY_DATA:
        raise HTTPException(status_code=404)
    return STORY_DATA[story_id]

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

# --- WebSocket Logic ---

@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_handler(websocket: WebSocket, session_id: str, user_id: str):
    await manager.connect(session_id, websocket)
    try:
        # Initial broadcast: User joined
        await manager.broadcast(session_id, {
            "type": "USER_JOINED",
            "userId": user_id
        })
        
        while True:
            data = await websocket.receive_json()
            # Expecting: { "type": "POSITION", "lat": X, "lng": Y } or { "type": "STORY_ADVANCE", "nodeId": X }
            data["userId"] = user_id # Add sender info
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
