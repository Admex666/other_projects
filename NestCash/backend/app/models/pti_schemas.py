# app/models/pti_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from app.models.pti import PTIPeriod, RankingScope, PTIComponentBreakdown, PTIRankingEntry

# Request modellek
class PTISettingsUpdate(BaseModel):
    """PTI beállítások frissítése"""
    show_in_global_ranking: Optional[bool] = None
    show_in_friends_ranking: Optional[bool] = None
    is_anonymous: Optional[bool] = None
    anonymous_name: Optional[str] = Field(None, max_length=50)
    
    notify_rank_change: Optional[bool] = None
    notify_weekly_summary: Optional[bool] = None
    notify_achievements: Optional[bool] = None
    
    weekly_pti_goal: Optional[float] = Field(None, ge=0, le=100)
    monthly_pti_goal: Optional[float] = Field(None, ge=0, le=100)
    
    @validator('anonymous_name')
    def validate_anonymous_name(cls, v, values):
        if values.get('is_anonymous') and not v:
            raise ValueError('Anonimizált megjelenés esetén meg kell adni az anonimizált nevet')
        return v

class PTICalculationRequest(BaseModel):
    """PTI számítás kérés (admin/teszt célra)"""
    user_id: Optional[str] = None  # Ha nincs megadva, akkor az aktuális felhasználó
    period: PTIPeriod = PTIPeriod.WEEKLY
    force_recalculate: bool = False

# Response modellek
class PTIUserSettings(BaseModel):
    """Felhasználó PTI beállításai"""
    user_id: str
    show_in_global_ranking: bool
    show_in_friends_ranking: bool
    is_anonymous: bool
    anonymous_name: Optional[str]
    
    notify_rank_change: bool
    notify_weekly_summary: bool
    notify_achievements: bool
    
    weekly_pti_goal: Optional[float]
    monthly_pti_goal: Optional[float]
    
    created_at: datetime
    updated_at: datetime

class PTIScoreResponse(BaseModel):
    """PTI pontszám válasz"""
    user_id: str
    period: PTIPeriod
    period_key: str
    
    components: PTIComponentBreakdown
    pti_score: float
    
    rank: Optional[int] = None
    total_users: Optional[int] = None
    percentile: Optional[float] = None  # Hányadik percentilis
    
    calculated_at: datetime

class PTIRankingRequest(BaseModel):
    """Ranglista lekérés kérés"""
    period: PTIPeriod = PTIPeriod.WEEKLY
    scope: RankingScope = RankingScope.GLOBAL
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    include_user: bool = True  # Tartalmazza-e a felhasználót ha nincs a top listában

class PTIComparisonResponse(BaseModel):
    """PTI összehasonlítás (pl. előző időszakkal)"""
    current_period: PTIScoreResponse
    previous_period: Optional[PTIScoreResponse] = None
    
    # Változások
    pti_change: Optional[float] = None
    rank_change: Optional[int] = None
    
    improvements: List[str] = []  # Javulások listája
    declines: List[str] = []      # Romlások listája

class PTILeaderboardStats(BaseModel):
    """Ranglista statisztikák"""
    period: PTIPeriod
    period_key: str
    
    # Általános stats
    total_participants: int
    average_pti: float
    median_pti: float
    highest_pti: float
    lowest_pti: float
    
    # Komponens átlagok
    avg_learning_points: float
    avg_habit_score: float
    avg_badge_score: float
    avg_limit_score: float
    
    # Top teljesítők
    top_learners: List[PTIRankingEntry] = []  # Top 3 tanulásban
    top_habit_trackers: List[PTIRankingEntry] = []  # Top 3 szokáskövetésben
    most_badges: List[PTIRankingEntry] = []  # Top 3 badge-ben
    best_limit_keepers: List[PTIRankingEntry] = []  # Top 3 limit betartásban

class PTIDashboardResponse(BaseModel):
    """PTI dashboard összes adat"""
    current_pti: PTIScoreResponse
    
    # Rangsorok
    weekly_ranking: Optional[PTIRankingEntry] = None
    monthly_ranking: Optional[PTIRankingEntry] = None
    yearly_ranking: Optional[PTIRankingEntry] = None
    
    # Trendek
    last_7_days: List[Dict[str, float]] = []  # Utolsó 7 nap PTI értékei
    last_4_weeks: List[Dict[str, float]] = []  # Utolsó 4 hét
    last_12_months: List[Dict[str, float]] = []  # Utolsó 12 hónap
    
    # Célok teljesítése
    weekly_goal_progress: Optional[float] = None  # %
    monthly_goal_progress: Optional[float] = None  # %
    
    # Javaslatok
    next_actions: List[str] = []  # Mit tegyen legközelebb a PTI javításához

class PTIAchievement(BaseModel):
    """PTI eredmény/achievement"""
    type: str  # "rank_improvement", "pti_milestone", "component_mastery"
    title: str
    description: str
    achieved_at: datetime
    points_earned: Optional[int] = None
    
class PTINotificationData(BaseModel):
    """PTI értesítés adatok"""
    type: str  # "weekly_summary", "rank_change", "achievement"
    title: str
    message: str
    data: Dict = {}  # További adatok (pl. új rangsor, PTI érték)
    
class PTIAnalyticsResponse(BaseModel):
    """PTI elemzés válasz (fejlett statisztikák)"""
    user_id: str
    analysis_period: str  # pl. "last_30_days"
    
    # Komponens teljesítmény
    strongest_component: str
    weakest_component: str
    most_improved_component: str
    
    # Trendek
    overall_trend: str  # "improving", "declining", "stable"
    trend_percentage: float  # Mennyivel változott %
    
    # Benchmark adatok
    user_vs_average: Dict[str, float]  # Felhasználó vs átlag komponensenként
    user_vs_friends: Optional[Dict[str, float]] = None  # Ha vannak barátai
    
    # Javaslatok prioritási sorrendben
    improvement_recommendations: List[Dict[str, str]] = []