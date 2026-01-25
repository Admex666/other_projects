from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from app.dependencies import get_current_user
from app.db.crud import get_characters_by_user, create_character, update_character_visited_zones, get_item, add_character_item, remove_character_item, set_item_equipped, get_character_inventory, set_character_faction
from app.models.schemas import Character, CharacterClass, InventorySlot

router = APIRouter(prefix="/characters", tags=["characters"])

@router.get("", response_model=List[Character])
def get_my_characters(current_user: dict = Depends(get_current_user)):
    return get_characters_by_user(current_user["id"])

@router.post("/create", response_model=Character)
def create_new_character(character_class: CharacterClass, name: str, current_user: dict = Depends(get_current_user)):
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
