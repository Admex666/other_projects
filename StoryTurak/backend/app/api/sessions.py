from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from app.dependencies import get_current_user
from app.db.crud import db_create_session, db_join_session, get_user_sessions, execute_query

router = APIRouter(tags=["sessions"])

@router.post("/session/create")
def create_session_endpoint(campaign_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    # In original it used campaign_id and the body was the host player data
    session_id = str(uuid.uuid4())[:8].upper() # 8 char code
    db_create_session(session_id, current_user["id"], campaign_id)
    db_join_session(session_id, current_user["id"])
    return {"id": session_id, "code": session_id, "host_id": current_user["id"], "story_id": campaign_id, "status": "waiting"}

@router.post("/session/join")
def join_session_endpoint(data: dict, current_user: dict = Depends(get_current_user)):
    session_id = data.get("code")
    if not session_id:
        raise HTTPException(status_code=400, detail="Code required")
    
    # Check if session exists
    res = execute_query("SELECT id FROM sessions WHERE id = ?", (session_id,))
    if not res:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_join_session(session_id, current_user["id"])
    return {"id": session_id, "code": session_id, "status": "joined"}

@router.get("/session/{code}")
def get_session_endpoint(code: str, current_user: dict = Depends(get_current_user)):
    res = execute_query("SELECT * FROM sessions WHERE id = ?", (code,))
    if not res:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = dict(res[0])
    # Get players
    players = execute_query("SELECT user_id FROM session_players WHERE session_id = ?", (code,))
    session["players"] = [p["user_id"] for p in players]
    return session

@router.get("/users/{user_id}/sessions")
def get_user_sessions_endpoint(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["id"]:
         raise HTTPException(status_code=403, detail="Forbidden")
    return get_user_sessions(user_id)
