from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
import logging

from app.dependencies import get_current_user
from app.db.crud import (
    get_user_quests, get_quest_by_id, add_quest_to_user, 
    update_user_quest_progress, execute_query, get_all_quests,
    get_characters_by_user, update_character_inventory, update_user_steps, update_character_steps_and_level
)
from app.models.schemas import UserQuest, Quest, QuestStatus
from app.services.loot_service import roll_loot

logger = logging.getLogger(__name__)
router = APIRouter(tags=["quests"])

@router.get("/quests", response_model=List[UserQuest])
def get_my_quests(current_user: dict = Depends(get_current_user)):
    return get_user_quests(current_user["id"])

@router.get("/test/quests") 
def get_test_quests():
    quests = get_all_quests()
    return {"quests": quests}

@router.get("/characters/{character_id}/quests", response_model=List[UserQuest])
def get_character_quests(character_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    return get_user_quests(current_user["id"])

@router.get("/quests/available", response_model=List[Quest])
def get_available_quests_endpoint(current_user: dict = Depends(get_current_user)):
    my_quests = get_user_quests(current_user["id"])
    taken_ids = [q["quest_id"] for q in my_quests]
    
    available = []
    if "quest_starter_01" not in taken_ids:
        q = get_quest_by_id("quest_starter_01")
        if q:
            available.append(Quest(**q))
    
    all_db_quests = get_all_quests()
    for q in all_db_quests:
        if q["id"] not in taken_ids and q["id"] != "quest_starter_01":
             available.append(Quest(**q))
             
    return available

@router.post("/quests/{quest_id}/accept", response_model=UserQuest)
def accept_quest_endpoint(quest_id: str, current_user: dict = Depends(get_current_user)):
    quest = get_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
        
    my_quests = get_user_quests(current_user["id"])
    active_uq = next((q for q in my_quests if q["quest_id"] == quest_id), None)
    
    if active_uq:
        if active_uq["status"] == QuestStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Quest already active")
        else:
            # Allow replay: delete ALL old records for this quest for this user
            execute_query("DELETE FROM user_quests WHERE user_id = ? AND quest_id = ?", (current_user["id"], quest_id))

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

@router.delete("/user-quests/{user_quest_id}")
def abandon_quest(user_quest_id: str, current_user: dict = Depends(get_current_user)):
    res = execute_query("SELECT user_id FROM user_quests WHERE id = ?", (user_quest_id,))
    if not res or res[0]["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    execute_query("DELETE FROM user_quests WHERE id = ?", (user_quest_id,))
    return {"status": "success", "message": "Quest abandoned"}

@router.post("/encounters/resolve")
def resolve_encounter(data: dict, current_user: dict = Depends(get_current_user)):
    enc_id = data.get("encounter_id")
    outcome = data.get("outcome")
    
    user_quests = get_user_quests(current_user["id"])
    
    # NEW: Find a quest where the CURRENT stage matches this encounter
    matching_uq = None
    quest_def = None
    curr_stage_idx = 0
    
    for uq in user_quests:
        if uq["status"] != "active":
            continue
        q = get_quest_by_id(uq["quest_id"])
        if not q or not q.get("stages"):
            continue
        
        idx = uq.get("current_stage_index", 0)
        if idx < len(q["stages"]) and q["stages"][idx]["encounter_id"] == enc_id:
            matching_uq = uq
            quest_def = q
            curr_stage_idx = idx
            break

    if matching_uq:
        total_stages = len(quest_def["stages"])
        new_stage_idx = curr_stage_idx + 1
        new_status = "active"
        
        if new_stage_idx >= total_stages:
            new_status = "completed"
        
        update_user_quest_progress(
            matching_uq["id"], 
            matching_uq["current_count"], 
            new_stage_index=new_stage_idx,
            new_status=new_status
        )
        
        rewards = {"steps": 0, "items": []}
        if outcome == "success":
             steps_amount = 50 
             if new_status == "completed":
                 steps_amount += quest_def.get("rewards_steps", 0)
             rewards["steps"] = steps_amount
             
             table_id = "loot_table_common" 
             dropped_items = roll_loot(table_id)
             rewards["items"] = dropped_items
             
             chars = get_characters_by_user(current_user["id"])
             if chars:
                 char = chars[0]
                 current_inv = char["inventory"]
                 for item in dropped_items:
                     found = False
                     for slot in current_inv:
                         if slot["item_id"] == item["id"]:
                             slot["quantity"] += 1
                             found = True
                             break
                     if not found:
                         current_inv.append({"item_id": item["id"], "quantity": 1, "equipped": False})
                 
                 update_character_inventory(char["id"], current_inv)
                 update_user_steps(current_user["id"], steps_amount)
                 current_steps = char["steps"] + steps_amount
                 new_level = 1 + (current_steps // 1000) # 1km (1000 steps/points) = 1 Level
                 update_character_steps_and_level(char["id"], current_steps, new_level)
        
        return {
            "status": "success", 
            "message": "Quest stage progressed", 
            "new_status": new_status,
            "rewards": rewards
        }

    all_quests = get_all_quests()
    for q in all_quests:
        # NEW CRITICAL FIX: Check if they already have this quest (any status)
        already_taken = any(uq['quest_id'] == q['id'] for uq in user_quests)
        if already_taken:
            continue
            
        if q.get("stages") and q["stages"][0]["encounter_id"] == enc_id:
            uq_id = str(uuid.uuid4())
            new_status = "active"
            if 1 >= len(q["stages"]):
                new_status = "completed"
            uq_data = {
                "id": uq_id,
                "user_id": current_user["id"],
                "quest_id": q["id"],
                "status": new_status,
                "current_stage_index": 1, 
                "current_objective_index": 0,
                "current_count": 0
            }
            add_quest_to_user(uq_data)
            return {"status": "success", "message": f"Quest accepted and progressed to {new_status}", "new_status": new_status}

    return {"status": "success", "message": "Encounter resolved", "rewards": {"steps": 0, "items": []}}
