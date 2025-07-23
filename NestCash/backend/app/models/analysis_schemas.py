# app/models/analysis_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class TimePeriod(BaseModel):
    start: str
    end: str

class BasicStats(BaseModel):
    user_income: float
    user_expenses: float
    user_net: float
    user_savings_rate: float
    benchmark_income: float
    benchmark_expenses: float
    benchmark_savings_rate: float
    user_rank_income: float
    user_rank_savings: float

class Cashflow(BaseModel):
    monthly_flow: Dict[str, float]
    trend: Optional[float]
    trend_msg: Optional[str]

class SpendingPattern(BaseModel):
    spending_types: Dict[str, float]
    total_expenses: float
    user_impulse_pct: float
    profile_impulse_pct: float
    fixed_costs: float
    variable_costs: float
    fixed_ratio: float
    variable_ratio: float

class CategoryItem(BaseModel):
    name: str
    amount: float
    percentage: float

class CategoryAnalysis(BaseModel):
    user_categories: Dict[str, float]
    top_category: Dict[str, CategoryItem]
    missing_essentials: List[str]
    profile_avg_categories: Dict[str, float]

class TemporalAnalysis(BaseModel):
    weekly_spending: Dict[str, float]
    max_day: Dict[str, Any]
    min_day: Dict[str, Any]
    weekday_avg: float
    weekend_avg: float
    weekend_spending_ratio: float

class RiskAnalysis(BaseModel):
    expense_ratio: float
    debt_to_income: float
    emergency_fund_months: float
    risk_level: str
    debt_to_income_comparison: str
    emergency_fund_comparison: str

class Recommendation(BaseModel):
    category: str
    advice: str
    priority: str

class FinancialAnalysisResponse(BaseModel):
    user_id: str
    profile: str
    time_period: TimePeriod
    transaction_count: int
    basic_stats: BasicStats
    cashflow: Cashflow
    spending_patterns: SpendingPattern
    category_analysis: CategoryAnalysis
    temporal_analysis: TemporalAnalysis
    risk_analysis: RiskAnalysis
    recommendations: List[Recommendation]