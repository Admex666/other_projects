from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user
from app.services.collection_service import get_character_collections
from app.db.crud import get_characters_by_user

router = APIRouter()

@router.get("/collections")
def get_collections(current_user: dict = Depends(get_current_user)):
    """
    Get collections for the active character (or first character for MVP).
    Ideally should accept character_id query param or header.
    For now, we fetch the user's first character.
    """
    user_id = current_user['id']
    chars = get_characters_by_user(user_id)
    if not chars:
        return []

    # Default to first character for MVP
    char_id = chars[0]["id"]
    
    return get_character_collections(char_id)
