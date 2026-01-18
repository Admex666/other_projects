from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from app.dependencies import get_current_user
from app.db.crud import get_characters_by_user, create_character, update_character_visited_zones
from app.models.schemas import Character, CharacterClass

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
        "xp": 0,
        "max_hp": 10,
        "stats": {"strength": 5, "agility": 5} if character_class == CharacterClass.SOLDIER else {"strength": 2, "agility": 3},
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
