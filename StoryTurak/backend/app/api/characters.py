from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List
import uuid

from app.dependencies import get_current_user
from app.db.crud import get_characters_by_user, create_character, update_character_visited_zones, get_item, add_character_item, remove_character_item, set_item_equipped, get_character_inventory, set_character_faction, update_character_loadout, get_quest_history
from app.models.schemas import Character, CharacterClass, InventorySlot

router = APIRouter(prefix="/characters", tags=["characters"])

@router.get("", response_model=List[Character])
def get_my_characters(current_user: dict = Depends(get_current_user)):
    return get_characters_by_user(current_user["id"])

@router.post("/create", response_model=Character)
def create_new_character(
    character_class: CharacterClass, 
    name: str, 
    lat: float = 47.4979,  # Default to Budapest center if not provided
    lon: float = 19.0402,
    current_user: dict = Depends(get_current_user)
):
    char_id = str(uuid.uuid4())
    new_char = {
        "id": char_id,
        "user_id": current_user["id"],
        "name": name,
        "character_class": character_class,
        "level": 1,
        "level": 1,
        "steps": 0,
        "weekly_steps": 0,
        "max_hp": 10,
        "stats": {
            "strength": 5 if character_class == CharacterClass.VIGILANTE else 2,
            "agility": 5 if character_class == CharacterClass.COLLECTOR else 3,
            "intellect": 5 if character_class == CharacterClass.ARCHIVIST else 3
        },
        "inventory": [],
        "visited_zones": [],
        "completed_quests": []
    }
    create_character(new_char)
    
    # Create and auto-accept tutorial quest with random location near character spawn
    try:
        from app.services.quest_service import create_dynamic_tutorial_quest, dynamic_encounters
        from app.db.crud import accept_quest, create_encounter
        from app.db.crud import execute_query
        from app.models.schemas import Encounter, EncounterNode, EncounterType, EncounterNodeType
        
        # Create tutorial quest with character's spawn location
        quest_data, enc_def = create_dynamic_tutorial_quest(lat, lon)
        
        # Save quest to database
        execute_query(
            "INSERT OR REPLACE INTO quests (id, title, description, definition) VALUES (?, ?, ?, ?)",
            (quest_data["id"], quest_data["title"], quest_data["description"], str(quest_data))
        )
        
        # Save encounter to database
        create_encounter(enc_def)
        
        # CRITICAL: Add to dynamic_encounters so /world/nearby returns it
        enc_obj = Encounter(
            id=enc_def["id"],
            title=enc_def["title"],
            description=enc_def["description"],
            type=EncounterType.STORY,
            start_node_id=enc_def["definition"]["start_node_id"],
            location=[enc_def["location_lat"], enc_def["location_lon"]],
            nodes={
                nid: EncounterNode(
                    id=nid,
                    type=EncounterNodeType.NARRATIVE,
                    text=node["text"],
                    button_text=node.get("buttonText")
                ) for nid, node in enc_def["definition"]["nodes"].items()
            },
            zone_id=enc_def["zone_id"]
        )
        dynamic_encounters.append(enc_obj)
        
        # Auto-accept the quest
        accept_quest(current_user["id"], "quest_tutorial_01")
        
    except Exception as e:
        # Log but don't fail character creation if tutorial quest creation fails
        import logging
        logging.getLogger(__name__).warning(f"Failed to create/accept tutorial quest: {e}")
    
    return Character(**new_char)

@router.post("/{character_id}/visit-zone")
def visit_zone_endpoint(character_id: str, zone_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    update_character_visited_zones(character_id, zone_id)
    return {"status": "ok"}

@router.post("/{character_id}/inventory/add")
def add_item_to_inventory(character_id: str, item_id: str, quantity: int = 1, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    # Verify item exists
    item = get_item(item_id)
    if not item:
       raise HTTPException(status_code=404, detail="Item not found")

    add_character_item(character_id, item_id, quantity)
    
    new_inv = get_character_inventory(character_id)
    return {"status": "item_added", "inventory": new_inv}

@router.post("/{character_id}/inventory/remove")
def remove_item_from_inventory(character_id: str, item_id: str, quantity: int = 1, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")

    remove_character_item(character_id, item_id, quantity)
    
    new_inv = get_character_inventory(character_id)
    return {"status": "item_removed", "inventory": new_inv}

@router.post("/{character_id}/inventory/equip")
def equip_item(character_id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    set_item_equipped(character_id, item_id, True)
    
    new_inv = get_character_inventory(character_id)
    return {"status": "equipped", "inventory": new_inv}

@router.post("/{character_id}/inventory/unequip")
def unequip_item(character_id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    set_item_equipped(character_id, item_id, False)

    new_inv = get_character_inventory(character_id)
    return {"status": "unequipped", "inventory": new_inv}

@router.post("/{character_id}/faction")
def update_faction_endpoint(character_id: str, faction: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
        
    set_character_faction(character_id, faction)
    return {"status": "ok", "faction": faction}

@router.post("/{character_id}/loadout")
def update_loadout_endpoint(character_id: str, item_ids: List[str] = Body(...), current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    try:
        update_character_loadout(character_id, item_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    new_inv = get_character_inventory(character_id)
    return {"status": "loadout_updated", "inventory": new_inv}

@router.get("/{character_id}/quest_history")
def get_quest_history_endpoint(character_id: str, current_user: dict = Depends(get_current_user)):
    # Verify character ownership (optional, but good practice if we scope quests to chars later)
    # Since quests are user-wide currently, we just return user quests.
    chars = get_characters_by_user(current_user["id"])
    if not any(c["id"] == character_id for c in chars):
        raise HTTPException(status_code=403, detail="Not your character")
    
    debug_history = get_quest_history(current_user["id"])
    print(f"DEBUG API: Quest History for {current_user['id']}: {debug_history}")
    return debug_history
