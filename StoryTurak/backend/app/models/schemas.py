from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

class CharacterClass(str, Enum):
    ARCHIVIST = "archivist" # Krónikás
    VIGILANTE = "vigilante" # Őrszem
    COLLECTOR = "collector" # Gyűjtő
    # Legacy / Backward Compatibility
    POET = "poet"
    SOLDIER = "soldier"
    TAX_COLLECTOR = "tax_collector"
    PILGRIM = "pilgrim"

class ItemType(str, Enum):
    WEAPON = "weapon"
    TOOL = "tool"
    RELIC = "relic"
    CONSUMABLE = "consumable"
    QUEST_ITEM = "quest_item"
    MISC = "misc"

class Item(BaseModel):
    id: str
    name: str
    description: str
    type: ItemType
    value: int = 0
    icon_code: str
    stats: Dict[str, int] = {}

class InventorySlot(BaseModel):
    item_id: str
    quantity: int = 1
    equipped: bool = False

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str = "player"
    steps: int = 0
    isReady: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class Character(BaseModel):
    id: str
    user_id: str
    name: str
    character_class: CharacterClass
    level: int = 1
    steps: int = 0
    weekly_steps: int = 0
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
    ORDER = "order"

class EncounterChoice(BaseModel):
    text: str
    next_node_id: Optional[str] = None
    condition: Optional[str] = None

class EncounterNode(BaseModel):
    id: str
    type: EncounterNodeType
    text: str
    image: Optional[str] = None
    choices: Optional[List[EncounterChoice]] = None
    next_node_id: Optional[str] = None
    enemy_id: Optional[str] = None
    enemy_hp: Optional[int] = None
    enemy_class: Optional[CharacterClass] = None # For Rock-Paper-Scissors
    weakness_item_id: Optional[str] = None # For Instant Win
    correct_answer: Optional[str] = None
    valid_answers: Optional[List[str]] = None
    success_node_id: Optional[str] = None
    failure_node_id: Optional[str] = None
    button_text: Optional[str] = None
    options: Optional[List[str]] = None
    
class Encounter(BaseModel):
    id: str
    title: str
    description: str
    type: EncounterType
    nodes: Dict[str, EncounterNode]
    start_node_id: str
    location: Tuple[float, float]
    zone_id: str
    active_hours_start: Optional[int] = None 
    active_hours_end: Optional[int] = None

class Zone(BaseModel):
    id: str
    name: str
    description: str
    boundary_points: List[Tuple[float, float]]
    difficulty_level: int = 1
    recommended_class: Optional[CharacterClass] = None
    active_encounters: List[Encounter] = []

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
    target_id: str
    count: int = 1
    description: str

class QuestStage(BaseModel):
    id: str
    description: str
    location: Tuple[float, float]
    encounter_id: Optional[str] = None

class Quest(BaseModel):
    id: str
    title: str
    description: str
    flavor_text: Optional[str] = None
    image_url: Optional[str] = None
    start_location: Tuple[float, float]
    stages: List[QuestStage]
    estimated_distance_km: float = 0.0
    estimated_duration_min: int = 30
    difficulty: str = "Közepes"
    min_level: int = 1
    intro_steps: List[str] = []
    objectives: List[QuestObjective]
    rewards_steps: int = 100
    rewards_items: Optional[List[str]] = None
    starter_zone_id: Optional[str] = None
    
class UserQuest(BaseModel):
    id: str
    user_id: str
    quest_id: str
    status: QuestStatus
    current_stage_index: int = 0
    current_objective_index: int = 0
    current_count: int = 0
    started_at: datetime = Field(default_factory=datetime.now)
    quest_title: Optional[str] = None
    quest_description: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class AuthRequest(BaseModel):
    username: str
    password: str

class JoinRequest(BaseModel):
    code: str
    user: User

class LootEntry(BaseModel):
    item_id: str
    chance: float
    min_qty: int = 1
    max_qty: int = 1

class LootTable(BaseModel):
    id: str
    entries: List[LootEntry]

class PlayerState(BaseModel):
    user_id: str
    character_class: CharacterClass
    level: int = 1
    inventory: List[Any] = []
    visited_zones: List[str] = []
    completed_encounters: List[str] = []
    last_location: Optional[Tuple[float, float]] = None
    updated_at: datetime = Field(default_factory=datetime.now)
