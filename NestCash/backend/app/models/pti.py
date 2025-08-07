# app/models/pti.py
from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime, date
from enum import Enum

class PTIPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class RankingScope(str, Enum):
    PRIVATE = "private"      # Csak saját adatok
    FRIENDS = "friends"      # Barátok (követett felhasználók)
    GLOBAL = "global"        # Globális ranglista

class PTIScore(Document):
    """PTI pontszám tárolása időszakonként"""
    
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    period: PTIPeriod = Field(..., description="Időszak típusa")
    period_key: str = Field(..., description="Időszak azonosító (pl. 2025-W03, 2025-01, 2025)")
    
    # PTI komponensek
    learning_points: float = Field(default=0.0, description="Tanulási pontok")
    habit_score: float = Field(default=0.0, description="Szokáskövetés pontszám")
    badge_score: float = Field(default=0.0, description="Badge pontszám")
    limit_score: float = Field(default=0.0, description="Limit betartási pontszám")
    
    # Végső PTI értékek
    raw_pti: float = Field(default=0.0, description="Nyers PTI érték")
    normalized_pti: float = Field(default=0.0, description="Normalizált PTI (0-100)")
    
    # Ranking adatok
    global_rank: Optional[int] = Field(None, description="Globális rangsor")
    total_users: Optional[int] = Field(None, description="Összes felhasználó száma")
    
    # Meta adatok
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    is_anonymous: bool = Field(default=False, description="Anonimizált-e a ranglista számára")
    
    class Settings:
        name = "pti_scores"
        indexes = [
            "user_id",
            "period",
            "period_key",
            [("period", 1), ("period_key", 1), ("normalized_pti", -1)],  # Rangsor lekérdezéshez
            [("user_id", 1), ("period", 1)],
            "calculated_at"
        ]

class PTIHistory(Document):
    """PTI történet tárolása trendek számításához"""
    
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    date: str = Field(..., description="Dátum YYYY-MM-DD formátumban")
    
    # Napi komponensek
    learning_points_daily: float = Field(default=0.0)
    habit_completions_daily: int = Field(default=0)
    badges_earned_daily: int = Field(default=0)
    limit_violations_daily: int = Field(default=0)
    
    # Számított napi PTI
    daily_pti: float = Field(default=0.0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "pti_history"
        indexes = [
            "user_id",
            "date",
            [("user_id", 1), ("date", -1)]
        ]

class UserPTISettings(Document):
    """Felhasználó PTI beállításai"""
    
    user_id: PydanticObjectId = Field(..., description="Felhasználó ID")
    
    # Ranglistán való megjelenés
    show_in_global_ranking: bool = Field(default=True, description="Megjelenés globális ranglistán")
    show_in_friends_ranking: bool = Field(default=True, description="Megjelenés barátok ranglistáján")
    is_anonymous: bool = Field(default=False, description="Anonimizált megjelenés")
    anonymous_name: Optional[str] = Field(None, description="Anonimizált név")
    
    # Értesítési beállítások
    notify_rank_change: bool = Field(default=True, description="Értesítés rangsor változáskor")
    notify_weekly_summary: bool = Field(default=True, description="Heti összefoglaló")
    notify_achievements: bool = Field(default=True, description="PTI eredmények értesítése")
    
    # Célok
    weekly_pti_goal: Optional[float] = Field(None, description="Heti PTI cél")
    monthly_pti_goal: Optional[float] = Field(None, description="Havi PTI cél")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_pti_settings"
        indexes = ["user_id"]

# Response modellek
class PTIComponent(str, Enum):
    LEARNING = "learning"
    HABITS = "habits" 
    BADGES = "badges"
    LIMITS = "limits"
    TOTAL = "total"

    @property
    def value(self):
        """Enum érték visszaadása - Pydantic kompatibilitásért"""
        return self._value_

    @property
    def display_name(self):
        names = {
            "learning": "📚 Tanulás",
            "habits": "💪 Szokások", 
            "badges": "🏆 Kitűzők",
            "limits": "📊 Limitek",
            "total": "🏆 Összesített PTI"
        }
        return names.get(self.value, self.value)

# Komponens ranglista bejegyzés
ASCENDING = 1
DESCENDING = -1
class PTIComponentRanking(Document):
    period: str = Field(..., description="Időszak típusa (string formában)")  # Változás: str
    period_key: str
    component: str = Field(..., description="Komponens típusa (string formában)")  # Változás: str
    scope: str = Field(..., description="Rangsor scope (string formában)")  # Változás: str
    
    user_id: PydanticObjectId
    username: Optional[str] = None
    is_anonymous: bool = False
    anonymous_name: Optional[str] = None
    
    component_score: float
    rank: int
    total_participants: int
    percentile: float
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "pti_component_rankings"
        indexes = [
            [
                ("period", ASCENDING),
                ("period_key", ASCENDING),
                ("component", ASCENDING),
                ("scope", ASCENDING),
                ("rank", ASCENDING)
            ],
            [
                ("user_id", ASCENDING),
                ("period", ASCENDING),
                ("component", ASCENDING)
            ],
            [
                ("period", ASCENDING),
                ("period_key", ASCENDING),
                ("component", ASCENDING),
                ("component_score", DESCENDING)
            ]
        ]

class PTIComponentBreakdown(BaseModel):
    """PTI komponensek részletezése"""
    learning_points: float
    learning_weight: float = 0.30
    learning_contribution: float
    
    habit_score: float
    habit_weight: float = 0.30
    habit_contribution: float
    
    badge_score: float
    badge_weight: float = 0.20
    badge_contribution: float
    
    limit_score: float
    limit_weight: float = 0.20
    limit_contribution: float
    
    total_pti: float

class PTIRankingEntry(BaseModel):
    """Ranglista bejegyzés"""
    rank: int
    user_id: str
    username: Optional[str] = None  # Ha nem anonimizált
    anonymous_name: Optional[str] = None  # Ha anonimizált
    is_anonymous: bool
    pti_score: float
    components: PTIComponentBreakdown
    is_current_user: bool = False

class PTIRankingResponse(BaseModel):
    """Ranglista válasz"""
    period: PTIPeriod
    period_key: str
    scope: RankingScope
    rankings: List[PTIRankingEntry]
    user_rank: Optional[int] = None
    user_score: Optional[float] = None
    total_participants: int
    generated_at: datetime

class PTITrendData(BaseModel):
    """PTI trend adatok"""
    date: str
    pti_score: float
    learning_points: float
    habit_score: float
    badge_score: float
    limit_score: float

class PTIStatsResponse(BaseModel):
    """PTI statisztikák"""
    current_pti: PTIComponentBreakdown
    
    # Időszakos PTI értékek
    weekly_pti: Optional[float] = None
    monthly_pti: Optional[float] = None
    yearly_pti: Optional[float] = None
    
    # Rangsor adatok
    weekly_rank: Optional[int] = None
    monthly_rank: Optional[int] = None
    yearly_rank: Optional[int] = None
    
    # Trendek (utolsó 30 nap)
    trend_data: List[PTITrendData] = []
    
    # Javulási javaslatok
    improvement_suggestions: List[str] = []