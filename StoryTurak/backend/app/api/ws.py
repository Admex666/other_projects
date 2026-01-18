from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import asyncio

from app.services.connection_manager import manager
from app.db.crud import save_progress, db_update_session_status

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

# We'll use a local session store for now, or move it to a service if it grows
sessions = {} 

@router.websocket("/ws/{session_id}/{user_id}")
async def websocket_handler(websocket: WebSocket, session_id: str, user_id: str):
    await manager.connect(session_id, websocket, user_id)
    try:
        # Note: In the full app, sessions should be managed more robustly
        while True:
            data = await websocket.receive_json()
            data["userId"] = user_id
            
            if data.get("type") == "GAME_START":
                db_update_session_status(session_id, "active")

            if data.get("type") == "HEARTBEAT":
                manager.update_heartbeat(websocket)
                continue

            if data.get("type") == "STORY_ADVANCE" and "storyId" in data:
                save_progress(user_id, data["storyId"], data["nodeId"], data.get("variables", {}))

            if data.get("type") == "USER_READY":
                # Implementation would require access to the sessions dict
                pass

            await manager.broadcast(session_id, data)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        await manager.broadcast(session_id, {
            "type": "USER_LEFT",
            "userId": user_id
        })
