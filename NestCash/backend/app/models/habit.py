# app/models/habit.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal
from datetime import datetime, date
from enum import Enum

class TrackingType(str, Enum):
    BOOLEAN = "boolean"
    NUMERIC = "numeric"

class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class HabitCategory(str, Enum):
    FINANCIAL = "Pénzügyi"
    SAVINGS = "Megtakarítás"
    INVESTMENT = "Befektetés"
    OTHER = "Egyéb"

class Habit(Document):
    user_id: PydanticObjectId = Field(..., description="A szokást létrehozó felhasználó azonosítója")
    title: str = Field(..., description="Szokás neve")
    description: Optional[str] = Field(None, description="Szokás leírása")
    category: HabitCategory = Field(default=HabitCategory.OTHER, description="Szokás kategóriája")
    
    # Követés beállítások
    tracking_type: TrackingType = Field(default=TrackingType.BOOLEAN, description="Követés típusa")
    frequency: FrequencyType = Field(default=FrequencyType.DAILY, description="Gyakoriság")
    
    # Cél beállítások (opcionális)
    has_goal: bool = Field(default=False, description="Van-e cél beállítva")
    target_value: Optional[int] = Field(None, description="Cél érték")
    goal_period: Optional[FrequencyType] = Field(None, description="Cél időszaka")
    daily_target: Optional[float] = Field(None, description="Napi cél (automatikusan számított)")
    
    # Állapot
    is_active: bool = Field(default=True, description="Aktív-e a szokás")
    
    # Statisztikák
    streak_count: int = Field(default=0, description="Jelenlegi sorozat")
    best_streak: int = Field(default=0, description="Legjobb sorozat")
    last_completed: Optional[str] = Field(None, description="Utoljára teljesítve (YYYY-MM-DD)")
    
    # Timestampek
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    
    @validator('target_value')
    def validate_target_value(cls, v, values):
        """Cél érték validálása"""
        if values.get('has_goal') and v is None:
            raise ValueError('Cél beállításakor a target_value kötelező')
        if v is not None and v <= 0:
            raise ValueError('A cél értéknek pozitívnak kell lennie')
        return v
    
    @validator('goal_period')
    def validate_goal_period(cls, v, values):
        """Cél időszak validálása"""
        if values.get('has_goal') and v is None:
            raise ValueError('Cél beállításakor a goal_period kötelező')
        return v
    
    def calculate_daily_target(self) -> Optional[float]:
        """Napi cél számítása a gyakoriság alapján"""
        if not self.has_goal or not self.target_value:
            return None
            
        if self.goal_period == FrequencyType.DAILY:
            return float(self.target_value)
        elif self.goal_period == FrequencyType.WEEKLY:
            return self.target_value / 7.0
        elif self.goal_period == FrequencyType.MONTHLY:
            return self.target_value / 30.0
        return None
    
    async def save(self, **kwargs):
        """Mentés előtt daily_target és updated_at frissítése"""
        self.daily_target = self.calculate_daily_target()
        self.updated_at = datetime.utcnow()
        return await super().save(**kwargs)
    
    class Settings:
        name = "habits"
        indexes = [
            "user_id",
            "is_active",
            "category",
            [("user_id", 1), ("is_active", 1)],
            [("user_id", 1), ("category", 1)]
        ]

class HabitLog(Document):
    user_id: PydanticObjectId = Field(..., description="Felhasználó azonosítója")
    habit_id: PydanticObjectId = Field(..., description="Szokás azonosítója")
    date: str = Field(..., description="Dátum YYYY-MM-DD formátumban")
    
    # Teljesítés adatok
    completed: bool = Field(default=False, description="Teljesítve-e")
    value: Optional[float] = Field(None, description="Érték numerikus követésnél")
    notes: Optional[str] = Field(None, description="Jegyzetek")
    
    # Timestampek
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    
    @validator('date')
    def validate_date_format(cls, v):
        """Dátum formátum ellenőrzése"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('A dátumnak YYYY-MM-DD formátumúnak kell lennie')
    
    async def save(self, **kwargs):
        """Mentés előtt updated_at frissítése"""
        self.updated_at = datetime.utcnow()
        return await super().save(**kwargs)
    
    class Settings:
        name = "habit_logs"
        indexes = [
            "user_id",
            "habit_id",
            "date",
            [("user_id", 1), ("habit_id", 1), ("date", -1)],
            [("user_id", 1), ("date", -1)]
        ]

# Előre definiált szokások
PREDEFINED_HABITS = {
    HabitCategory.FINANCIAL: [
        {
            "title": "Nem rendeltem ételt",
            "description": "Nem rendeltem ételt házhozszállítással",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "Bevásárló lista alapján vásároltam",
            "description": "Csak a listán szereplő dolgokat vettem meg",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "Impulzusvásárlás kerülése",
            "description": "Nem vásároltam spontán módon",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "Napi költés nyomon követése",
            "description": "Minden kiadást rögzítettem",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ],
    HabitCategory.SAVINGS: [
        {
            "title": "Napi megtakarítás",
            "description": "Minden nap tettem félre valamennyit",
            "tracking_type": TrackingType.NUMERIC,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "Aprópénz gyűjtés",
            "description": "Az aprópénzt külön gyűjtöttem",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "50/30/20 szabály",
            "description": "Betartottam a 50/30/20 költségvetési szabályt",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ],
    HabitCategory.INVESTMENT: [
        {
            "title": "Befektetési hírek olvasása",
            "description": "Minimum 10 percet töltöttem pénzügyi hírek olvasásával",
            "tracking_type": TrackingType.NUMERIC,
            "frequency": FrequencyType.DAILY
        },
        {
            "title": "Portfólió áttekintése",
            "description": "Ellenőriztem a befektetéseim teljesítményét",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ]
}