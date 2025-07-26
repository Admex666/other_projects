# app/models/habit_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, date
from app.models.habit import TrackingType, FrequencyType, HabitCategory

# === HABIT SCHEMAS ===

class HabitCreate(BaseModel):
    title: str = Field(..., description="Szokás neve")
    description: Optional[str] = Field(None, description="Szokás leírása")
    category: HabitCategory = Field(default=HabitCategory.OTHER)
    tracking_type: TrackingType = Field(default=TrackingType.BOOLEAN)
    frequency: FrequencyType = Field(default=FrequencyType.DAILY)
    
    # Cél beállítások
    has_goal: bool = Field(default=False)
    target_value: Optional[int] = Field(None)
    goal_period: Optional[FrequencyType] = Field(None)
    
    @validator('target_value')
    def validate_target_value(cls, v, values):
        if values.get('has_goal') and v is None:
            raise ValueError('Cél beállításakor a target_value kötelező')
        if v is not None and v <= 0:
            raise ValueError('A cél értéknek pozitívnak kell lennie')
        return v

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[HabitCategory] = None
    tracking_type: Optional[TrackingType] = None
    frequency: Optional[FrequencyType] = None
    
    # Cél beállítások
    has_goal: Optional[bool] = None
    target_value: Optional[int] = None
    goal_period: Optional[FrequencyType] = None
    
    is_active: Optional[bool] = None

class HabitRead(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    category: HabitCategory
    tracking_type: TrackingType
    frequency: FrequencyType
    
    # Cél beállítások
    has_goal: bool
    target_value: Optional[int]
    goal_period: Optional[FrequencyType]
    daily_target: Optional[float]
    
    # Állapot
    is_active: bool
    
    # Statisztikák
    streak_count: int
    best_streak: int
    last_completed: Optional[str]
    
    # Kiszámított mezők (opcionális, runtime-ban állítódnak be)
    current_usage: Optional[float] = None
    usage_percentage: Optional[float] = None
    is_completed_today: Optional[bool] = None
    
    # Timestampek
    created_at: datetime
    updated_at: Optional[datetime]

# === HABIT LOG SCHEMAS ===

class HabitLogCreate(BaseModel):
    completed: bool = Field(default=False)
    value: Optional[float] = Field(None, description="Érték numerikus követésnél")
    notes: Optional[str] = Field(None, description="Jegyzetek")
    date: Optional[str] = Field(None, description="Dátum YYYY-MM-DD formátumban (alapértelmezett: ma)")
    
    @validator('date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('A dátumnak YYYY-MM-DD formátumúnak kell lennie')
        return v

class HabitLogUpdate(BaseModel):
    completed: Optional[bool] = None
    value: Optional[float] = None
    notes: Optional[str] = None

class HabitLogRead(BaseModel):
    id: str
    user_id: str
    habit_id: str
    date: str
    completed: bool
    value: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

# === RESPONSE SCHEMAS ===

class HabitListResponse(BaseModel):
    habits: List[HabitRead]
    total_count: int
    active_count: int
    archived_count: int

class HabitLogListResponse(BaseModel):
    logs: List[HabitLogRead]
    total_count: int
    habit_title: str

# === STATS SCHEMAS ===

class HabitProgressStats(BaseModel):
    total_days: int
    completed_days: int
    completion_rate: float  # százalék
    current_streak: int
    best_streak: int
    average_value: Optional[float] = None  # numerikus szokásoknál

class HabitWeeklyStats(BaseModel):
    week_start: str  # YYYY-MM-DD
    week_end: str    # YYYY-MM-DD
    completed_days: int
    total_value: Optional[float] = None

class HabitMonthlyStats(BaseModel):
    month: str  # YYYY-MM
    completed_days: int
    total_days: int
    completion_rate: float
    total_value: Optional[float] = None

class HabitStatsResponse(BaseModel):
    habit_id: str
    habit_title: str
    overall: HabitProgressStats
    weekly_stats: List[HabitWeeklyStats]
    monthly_stats: List[HabitMonthlyStats]

class UserHabitOverview(BaseModel):
    total_habits: int
    active_habits: int
    archived_habits: int
    completed_today: int
    current_average_streak: float
    best_overall_streak: int
    categories_breakdown: Dict[str, int]  # kategória -> szokások száma

# === PREDEFINED HABITS ===

class PredefinedHabitResponse(BaseModel):
    category: HabitCategory
    habits: List[Dict[str, str]]  # title, description, tracking_type, frequency

# === BULK OPERATIONS ===

class HabitBulkCreate(BaseModel):
    habits: List[HabitCreate]

class HabitBulkCreateResponse(BaseModel):
    created_count: int
    created_habits: List[HabitRead]
    errors: List[str] = []