from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

class CharacterClass(str, Enum):
    SOLDIER = "soldier"
    POET = "poet"
    TAX_COLLECTOR = "tax_collector"
    PILGRIM = "pilgrim"

class ItemType(str, Enum):
    WEAPON = "weapon"
    CONSUMABLE = "consumable"
    QUEST_ITEM = "quest_item"
    MISC = "misc"

class Item(BaseModel):
    id: str
    name: str
    description: str
    type: ItemType
    value: int = 0
    icon_code: str # e.g., using Flutter Icons or assets
    stats: Dict[str, int] = {} # e.g., {"attack": 5, "defense": 2}

class InventorySlot(BaseModel):
    item_id: str
    quantity: int = 1
    equipped: bool = False

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str = "player" # player, admin
    created_at: datetime = Field(default_factory=datetime.now)

class Character(BaseModel):
    id: str
    user_id: str
    name: str
    character_class: CharacterClass
    level: int = 1
    xp: int = 0
    max_hp: int = 10
    current_hp: int = 10
    stats: Dict[str, int] = {"strength": 1, "agility": 1, "intellect": 1}
    inventory: List[InventorySlot] = []
    visited_zones: List[str] = []
    completed_quests: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)

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

# Quest System
class QuestStatus(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestObjectiveType(str, Enum):
    VISIT_ZONE = "visit_zone"
    DEFEAT_ENEMY = "defeat_enemy"
    COLLECT_ITEM = "collect_item"

class QuestObjective(BaseModel):
    id: str
    type: QuestObjectiveType
    target_id: str # zone_id, enemy_id, or item_id
    count: int = 1
    description: str

class Quest(BaseModel):
    id: str
    title: str
    description: str
    min_level: int = 1
    objectives: List[QuestObjective]
    rewards_xp: int = 100
    rewards_items: List[str] = [] # list of item_ids
    starter_zone_id: Optional[str] = None # Where to pick up
    
class UserQuest(BaseModel):
    id: str
    user_id: str
    quest_id: str
    status: QuestStatus
    current_objective_index: int = 0
    current_count: int = 0
    started_at: datetime = Field(default_factory=datetime.now)
    # Enriched fields (joined from quests table)
    quest_title: Optional[str] = None
    quest_description: Optional[str] = None

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# Loot System
class LootEntry(BaseModel):
    item_id: str
    chance: float # 0.0 to 1.0
    min_qty: int = 1
    max_qty: int = 1

class LootTable(BaseModel):
    id: str
    entries: List[LootEntry]

# Deprecated / Legacy Support (Migration in progress)
class LootItem(BaseModel):
    id: str
    name: str
    description: str
    effect: str 
    icon_code: str

class PlayerState(BaseModel):
    user_id: str
    character_class: CharacterClass
    level: int = 1
    inventory: List[LootItem] = []
    visited_zones: List[str] = []
    completed_encounters: List[str] = []
    last_location: Optional[Tuple[float, float]] = None
    updated_at: datetime = Field(default_factory=datetime.now)
