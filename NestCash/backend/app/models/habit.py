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
    FINANCIAL = "financial"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    OTHER = "other"

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
            "title_key": "predefined_habits.financial.no_food_delivery.title",
            "description_key": "predefined_habits.financial.no_food_delivery.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.financial.shopping_list.title",
            "description_key": "predefined_habits.financial.shopping_list.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.financial.avoid_impulse_buying.title",
            "description_key": "predefined_habits.financial.avoid_impulse_buying.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.financial.daily_expense_tracking.title",
            "description_key": "predefined_habits.financial.daily_expense_tracking.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ],
    HabitCategory.SAVINGS: [
        {
            "title_key": "predefined_habits.savings.daily_savings.title",
            "description_key": "predefined_habits.savings.daily_savings.description",
            "tracking_type": TrackingType.NUMERIC,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.savings.coin_collection.title",
            "description_key": "predefined_habits.savings.coin_collection.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.savings.budget_rule.title",
            "description_key": "predefined_habits.savings.budget_rule.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ],
    HabitCategory.INVESTMENT: [
        {
            "title_key": "predefined_habits.investment.financial_news.title",
            "description_key": "predefined_habits.investment.financial_news.description",
            "tracking_type": TrackingType.NUMERIC,
            "frequency": FrequencyType.DAILY
        },
        {
            "title_key": "predefined_habits.investment.portfolio_review.title",
            "description_key": "predefined_habits.investment.portfolio_review.description",
            "tracking_type": TrackingType.BOOLEAN,
            "frequency": FrequencyType.DAILY
        }
    ]
}

# Fordítási szolgáltatás
class I18nService:
    def __init__(self):
        self.translations = {}
        self.default_language = "hu"
        self.supported_languages = ["hu", "en"]
        self._load_translations()
    
    def _load_translations(self):
        """Fordítási fájlok betöltése"""
        import json
        from pathlib import Path
        
        translations_dir = Path(__file__).parent.parent / "translations"
        
        for lang in self.supported_languages:
            translation_file = translations_dir / f"{lang}.json"
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {lang}.json: {e}")
                    self.translations[lang] = {}
            else:
                self.translations[lang] = {}
    
    def get_language_from_header(self, accept_language: str) -> str:
        """Accept-Language header alapján nyelv meghatározása"""
        if not accept_language:
            return self.default_language
            
        for lang in accept_language.split(','):
            lang_code = lang.strip().split('-')[0].split(';')[0].lower()
            if lang_code in self.supported_languages:
                return lang_code
        
        return self.default_language
    
    def translate(self, key: str, language: str) -> str:
        """Kulcs alapú fordítás"""
        if language not in self.translations:
            language = self.default_language
        
        # Nested key navigáció (pl. "predefined_habits.financial.title")
        keys = key.split('.')
        value = self.translations.get(language, {})
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Fallback to default language
                value = self.translations.get(self.default_language, {})
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return key  # Return key if translation not found
                break
        
        return value if isinstance(value, str) else key

# Globális i18n service instance
i18n_service = I18nService()

def get_localized_predefined_habits(language: str) -> dict:
    """Lokalizált predefined habits visszaadása"""
    localized_habits = {}
    
    for category, habits in PREDEFINED_HABITS.items():
        localized_habits[category] = []
        for habit in habits:
            localized_habit = {
                "title": i18n_service.translate(habit["title_key"], language),
                "description": i18n_service.translate(habit["description_key"], language),
                "tracking_type": habit["tracking_type"],
                "frequency": habit["frequency"]
            }
            localized_habits[category].append(localized_habit)
    
    return localized_habits