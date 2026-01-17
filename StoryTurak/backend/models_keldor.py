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
    QUEST = "quest"
    RANDOM = "random"
    STORY = "story"

class EncounterNodeType(str, Enum):
    NARRATIVE = "narrative"
    CHOICE = "choice"
    FIGHT = "fight"
    INPUT = "input"

class EncounterChoice(BaseModel):
    text: str
    next_node_id: str
    condition: Optional[str] = None # e.g. "level >= 2"

class EncounterNode(BaseModel):
    id: str
    type: EncounterNodeType
    text: str
    image: Optional[str] = None
    choices: Optional[List[EncounterChoice]] = None
    next_node_id: Optional[str] = None
    # Combat specific
    enemy_id: Optional[str] = None
    enemy_hp: Optional[int] = None
    # Puzzle/Input specific
    correct_answer: Optional[str] = None
    
class Encounter(BaseModel):
    id: str
    title: str
    description: str
    type: EncounterType
    nodes: Dict[str, EncounterNode]
    start_node_id: str
    location: Tuple[float, float] # (lat, lon)
    zone_id: str
    active_hours_start: Optional[int] = None 
    active_hours_end: Optional[int] = None

class Zone(BaseModel):
    # ... (remains same)
    id: str
    name: str
    description: str
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
    COMPLETE_ENCOUNTER = "complete_encounter"

class QuestObjective(BaseModel):
    id: str
    type: QuestObjectiveType
    target_id: str # zone_id, enemy_id, item_id, or encounter_id
    count: int = 1
    description: str

class QuestStage(BaseModel):
    id: str
    description: str
    location: Tuple[float, float]
    encounter_id: Optional[str] = None # The encounter that resolves this stage

class Quest(BaseModel):
    id: str
    title: str
    description: str
    flavor_text: Optional[str] = None
    image_url: Optional[str] = None
    start_location: Tuple[float, float]
    stages: List[QuestStage]
    estimated_distance_km: float = 0.0
    min_level: int = 1
    objectives: List[QuestObjective] # Legacy, might keep for compatibility or summary
    rewards_xp: int = 100
    rewards_items: Optional[List[str]] = None # list of item_ids
    starter_zone_id: Optional[str] = None # Where to pick up
    
class UserQuest(BaseModel):
    id: str
    user_id: str
    quest_id: str
    status: QuestStatus
    current_stage_index: int = 0
    current_objective_index: int = 0 # Legacy
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
