import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

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
            if websocket in self.active_connections[session_id]:
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
        
        for connection in list(self.active_connections[session_id]):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
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
            await asyncio.sleep(10)

manager = ConnectionManager()
