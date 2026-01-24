from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.services.combat_service import CombatService
from app.models.schemas import Character, CharacterClass
from app.db.crud import get_characters_by_user
# Mock Auth for now, or use real auth if available
# from app.api.auth import get_current_user

router = APIRouter()

class CombatPredictionRequest(BaseModel):
    character_id: str
    enemy_stance: str
    player_stance: str
    enemy_power: int = 1

@router.post("/predict")
def predict_combat(request: CombatPredictionRequest):
    """
    Predicts the outcome of a combat round.
    Used by the frontend to show projected results before committing? 
    Or acting as the actual turn resolution.
    """
    # 1. Fetch Character
    # DB lookup using provided ID
    from app.db.crud import get_character_with_details
    char_data = get_character_with_details(request.character_id)
    
    if not char_data:
        raise HTTPException(status_code=404, detail="Character not found")

    # Convert dict to Pydantic model
    # Ensure fields match
    try:
        real_char = Character(**char_data)
    except Exception as e:
        print(f"Error parsing character: {e}")
        # Fallback or re-raise
        raise HTTPException(status_code=500, detail=f"Character data error: {str(e)}")
    
    result = CombatService.calculate_combat_round(
        character=real_char,
        enemy_stance=request.enemy_stance,
        player_stance=request.player_stance,
        enemy_power=request.enemy_power
    )
    
    return result
