from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from app.dependencies import get_current_user
from app.services.story_service import get_all_stories, get_story_by_id, load_stories
from app.db.crud import get_progress, save_progress, update_user_xp, execute_query, get_user_quests, get_all_quests
import json

from app.models.schemas import Zone
from app.services.quest_service import dynamic_encounters

logger = logging.getLogger(__name__)

# Mock data for zones
active_zones = [
    {
        "id": "zone_belvaros",
        "name": "Belváros - A Ködös Utcák",
        "description": "A régi Pest szíve.",
        "boundary_points": [[47.498, 19.040], [47.502, 19.050], [47.495, 19.060], [47.49, 19.045]],
        "difficulty_level": 1
    },
    {
        "id": "zone_nyolcker",
        "name": "VIII. Kerület - A Sötét Parkok",
        "description": "A senki földje.",
        "boundary_points": [[47.495, 19.065], [47.498, 19.080], [47.485, 19.085], [47.485, 19.070]],
        "difficulty_level": 3
    }
]

router = APIRouter(tags=["stories"])

@router.get("/world/nearby")
def get_nearby_world(lat: float, lon: float, current_user: dict = Depends(get_current_user)):
    user_quests = get_user_quests(current_user["id"])
    active_map = {uq["quest_id"]: uq for uq in user_quests}
    all_db_quests = get_all_quests()
    
    # Map encounter_id to its quest stage info
    enc_to_quest = {}
    for q in all_db_quests:
        for idx, stage in enumerate(q.get("stages", [])):
            eid = stage.get("encounter_id")
            if eid:
                enc_to_quest[eid] = (q["id"], idx)

    visible_encounters = []
    for enc in dynamic_encounters:
        if enc.id in enc_to_quest:
            q_id, s_idx = enc_to_quest[enc.id]
            
            # If user has this quest active
            if q_id in active_map:
                uq = active_map[q_id]
                if uq["status"] == "active" and uq.get("current_stage_index", 0) == s_idx:
                    visible_encounters.append(enc)
            else:
                # User hasn't started this quest, show only the 1st stage
                if s_idx == 0:
                    visible_encounters.append(enc)
        else:
            # Independent encounters (not part of a quest) - show them for now
            visible_encounters.append(enc)
            
    return {
        "zones": active_zones,
        "encounters": [e.dict() for e in visible_encounters]
    }

@router.get("/stories")
def get_stories():
    load_stories()
    return get_all_stories()

@router.get("/stories/{story_id}")
def get_story(story_id: str):
    load_stories()
    story = get_story_by_id(story_id)
    if not story:
        raise HTTPException(status_code=404)
    return story

@router.get("/progress/{user_id}/{story_id}")
def get_user_story_progress(user_id: str, story_id: str):
    prog = get_progress(user_id, story_id)
    if not prog:
        return {"nodeId": None, "variables": {}}
    return prog

@router.post("/progress/{user_id}/{story_id}")
def update_user_story_progress(user_id: str, story_id: str, data: dict):
    save_progress(user_id, story_id, data["nodeId"], data["variables"])
    return {"status": "saved"}

@router.post("/progress/{user_id}/{story_id}/xp")
def add_xp(user_id: str, amount: int):
    update_user_xp(user_id, amount)
    return {"status": "xp_added"}

@router.post("/analytics/log")
def log_event(data: dict):
    execute_query("INSERT INTO analytics (user_id, event_type, data) VALUES (?, ?, ?)", 
                  (data.get("userId"), data.get("type"), json.dumps(data.get("payload", {}))))
    return {"status": "logged"}
