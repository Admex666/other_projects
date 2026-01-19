from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from app.dependencies import get_current_user
from app.db.crud import get_characters_by_user, create_character, update_character_visited_zones, get_item, update_character_inventory
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
    char = next((c for c in chars if c["id"] == character_id), None)
    if not char:
        raise HTTPException(status_code=403, detail="Not your character")
    
    # Verify item exists
    item = get_item(item_id)
    if not item:
       raise HTTPException(status_code=404, detail="Item not found")

    current_inv = char["inventory"]
    found = False
    for slot in current_inv:
        if slot["item_id"] == item_id:
            slot["quantity"] += quantity
            found = True
            break
    
    if not found:
        # We need to structure this as a dict compatible with InventorySlot
        current_inv.append({"item_id": item_id, "quantity": quantity, "equipped": False})
    
    update_character_inventory(character_id, current_inv)
    return {"status": "item_added", "inventory": current_inv}

@router.post("/{character_id}/inventory/remove")
def remove_item_from_inventory(character_id: str, item_id: str, quantity: int = 1, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    char = next((c for c in chars if c["id"] == character_id), None)
    if not char:
        raise HTTPException(status_code=403, detail="Not your character")

    current_inv = char["inventory"]
    found = False
    new_inv = []
    
    for slot in current_inv:
        if slot["item_id"] == item_id:
            found = True
            if slot["quantity"] > quantity:
                slot["quantity"] -= quantity
                new_inv.append(slot)
            elif slot["quantity"] == quantity:
                # Remove slot completely
                pass
            else:
                 raise HTTPException(status_code=400, detail="Not enough items to remove")
        else:
            new_inv.append(slot)
            
    if not found:
        raise HTTPException(status_code=404, detail="Item not in inventory")

    update_character_inventory(character_id, new_inv)
    return {"status": "item_removed", "inventory": new_inv}

@router.post("/{character_id}/inventory/equip")
def equip_item(character_id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    char = next((c for c in chars if c["id"] == character_id), None)
    if not char:
        raise HTTPException(status_code=403, detail="Not your character")
    
    current_inv = char["inventory"]
    found = False
    
    for slot in current_inv:
        if slot["item_id"] == item_id:
            slot["equipped"] = True
            found = True
            # Ideally verify item type and unequip others of same type, but keeping simple for now
        else:
             # If we enforce single weapon slot etc., logic goes here.
             pass
             
    if not found:
        raise HTTPException(status_code=404, detail="Item not in inventory")
        
    update_character_inventory(character_id, current_inv)
    return {"status": "equipped", "inventory": current_inv}

@router.post("/{character_id}/inventory/unequip")
def unequip_item(character_id: str, item_id: str, current_user: dict = Depends(get_current_user)):
    chars = get_characters_by_user(current_user["id"])
    char = next((c for c in chars if c["id"] == character_id), None)
    if not char:
        raise HTTPException(status_code=403, detail="Not your character")
    
    current_inv = char["inventory"]
    
    for slot in current_inv:
        if slot["item_id"] == item_id:
            slot["equipped"] = False
            
    update_character_inventory(character_id, current_inv)
    return {"status": "unequipped", "inventory": current_inv}
