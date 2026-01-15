from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

class CharacterClass(str, Enum):
    SOLDIER = "soldier"
    POET = "poet"
    TAX_COLLECTOR = "tax_collector"
    PILGRIM = "pilgrim"

class LootItem(BaseModel):
    id: str
    name: str
    description: str
    effect: str  # e.g., "passive_stealth", "key_item"
    icon_code: str

class EncounterType(str, Enum):
    FIGHT = "fight"       # Quick reflex/choice sequence
    PUZZLE = "puzzle"     # Observation based
    NARRATIVE = "narrative" # Pure story/lore
    SHOP = "shop" # Trade

class EncounterOption(BaseModel):
    text: str
    required_class: Optional[CharacterClass] = None
    required_item_id: Optional[str] = None
    success_chance: float = 1.0  # 0.0 to 1.0
    outcome_success_text: str
    outcome_fail_text: Optional[str] = None
    loot_reward_id: Optional[str] = None

class Encounter(BaseModel):
    id: str
    title: str
    description: str
    type: EncounterType
    options: List[EncounterOption]
    zone_id: str
    # Logic for appearing (e.g., only at night)
    active_hours_start: Optional[int] = None 
    active_hours_end: Optional[int] = None

class Zone(BaseModel):
    id: str
    name: str
    description: str
    # Polygon points: List of [lat, lon]
    boundary_points: List[Tuple[float, float]]
    difficulty_level: int = 1
    recommended_class: Optional[CharacterClass] = None
    active_encounters: List[Encounter] = []

class PlayerState(BaseModel):
    user_id: str
    character_class: CharacterClass
    level: int = 1
    inventory: List[LootItem] = []
    visited_zones: List[str] = []
    completed_encounters: List[str] = []
    last_location: Optional[Tuple[float, float]] = None
    updated_at: datetime = Field(default_factory=datetime.now)
