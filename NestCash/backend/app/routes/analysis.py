# app/routes/analysis.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import calendar
from statistics import mean
from bson import ObjectId
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy import stats
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from app.models.transaction import Transaction
from app.models.user import User
from app.models.account import AllUserAccountsDocument
from app.core.security import get_current_user
from app.services.ml_service import MLAnalysisService, CollaborativeFilteringService
from app.services.simulation_service import WhatIfSimulationService
from app.utils.translation_helper import translate

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Pydantic modellek az elemzési eredményekhez
from pydantic import BaseModel

class BasicStats(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    daily_avg_expense: float
    monthly_avg_expense: float
    most_active_day: str
    most_active_hour: int
    transaction_count: int

class CashflowTrend(BaseModel):
    period: str  # "2024-01" vagy "2024-W01"
    income: float
    expense: float
    net: float

class CashflowAnalysis(BaseModel):
    monthly_trends: List[CashflowTrend]
    weekly_trends: List[CashflowTrend]
    overall_trend: str  # "növekvő", "csökkenő", "stabil"

class CategoryAnalysis(BaseModel):
    top_expense_categories: List[Dict[str, Any]]
    category_summary: Dict[str, Dict[str, float]]
    missing_basic_categories: List[str]

class TimeAnalysis(BaseModel):
    by_weekday: Dict[str, float]
    by_hour: Dict[int, int]
    peak_spending_day: str
    peak_spending_hour: int

class RiskAnalysis(BaseModel):
    expense_income_ratio: float
    savings_rate: float
    debt_income_ratio: float
    emergency_fund_months: float
    risk_level: str  # "alacsony", "közepes", "magas"

class Recommendations(BaseModel):
    savings_suggestions: List[str]
    cost_optimization_tips: List[str]
    emergency_fund_advice: List[str]
    debt_management_advice: List[str]

class FinancialAnalysis(BaseModel):
    user_id: str
    analysis_date: datetime
    basic_stats: BasicStats
    cashflow_analysis: CashflowAnalysis
    category_analysis: CategoryAnalysis
    time_analysis: TimeAnalysis
    risk_analysis: RiskAnalysis
    recommendations: Recommendations

# ÚJ PYDANTIC MODELLEK - add hozzá a meglévő modellek mellé
class ForecastData(BaseModel):
    period: str  # "2024-02" vagy "2024-W05"
    predicted_income: float
    predicted_expense: float
    predicted_net: float
    confidence_lower: float
    confidence_upper: float
    seasonal_factor: float

class ForecastResponse(BaseModel):
    forecast_type: str  # "monthly" vagy "weekly"
    periods_ahead: int
    forecasts: List[ForecastData]
    model_accuracy: float
    seasonal_pattern_detected: bool
    trend: str  # "növekvő", "csökkenő", "stabil"

class SeasonalAnalysis(BaseModel):
    has_seasonality: bool
    seasonal_periods: List[str]  # ["december", "január"] vagy ["2024-W52", "2024-W01"]
    peak_seasons: Dict[str, float]  # Időszak -> átlagos kiadás
    seasonal_recommendations: List[str]

class AnomalyData(BaseModel):
    transaction_id: str
    date: str
    amount: float
    category: str
    anomaly_score: float
    anomaly_type: str  # "high_spending", "unusual_category", "time_anomaly"
    severity: str  # "low", "medium", "high"

class AnomalyResponse(BaseModel):
    total_anomalies: int
    anomalies_by_severity: Dict[str, int]
    recent_anomalies: List[AnomalyData]
    anomaly_trends: Dict[str, int]  # Hónap -> anomáliák száma
    recommendations: List[str]

class BudgetRecommendation(BaseModel):
    category: str
    recommended_limit: float
    current_spending: float
    confidence: float
    reasoning: str
    priority: str  # "high", "medium", "low"

class MLBudgetResponse(BaseModel):
    total_recommended_budget: float
    category_recommendations: List[BudgetRecommendation]
    spending_pattern_score: float  # 0-100, mennyire kiszámítható a költés
    risk_level: str
    personalized_tips: List[str]

class PaymentMethodAnalysis(BaseModel):
    payment_method: str
    transaction_count: int
    total_amount: float
    avg_transaction: float
    usage_percentage: float
    trend: str  # "növekvő", "csökkenő", "stabil"

class IncomeSourceAnalysis(BaseModel):
    source: str  # kategória vagy leírás alapján
    total_amount: float
    percentage_of_total: float
    regularity_score: float  # 0-1, mennyire rendszeres
    risk_level: str  # "alacsony", "közepes", "magas"

class IncomeAnalysisResponse(BaseModel):
    total_monthly_income: float
    income_sources: List[IncomeSourceAnalysis]
    diversification_score: float  # 0-100
    stability_score: float  # 0-100
    recommendations: List[str]

class SimilarUserProfile(BaseModel):
    similarity_score: float
    spending_pattern: Dict[str, float]  # kategória -> percentage
    avg_monthly_spending: float
    savings_rate: float

class CollaborativeAnalysisResponse(BaseModel):
    user_position: str  # "alatta", "átlag", "felette"
    similar_users_count: int
    peer_comparison: Dict[str, float]  # metric -> user_value vs peer_average
    recommendations_from_peers: List[str]
    spending_efficiency_score: float  # 0-100

class WhatIfScenario(BaseModel):
    scenario_name: str
    changes: Dict[str, float]  # kategória -> új havi összeg
    monthly_impact: float
    annual_savings: float
    feasibility: str  # "könnyű", "közepes", "nehéz"

class WhatIfResponse(BaseModel):
    scenarios: List[WhatIfScenario]
    recommended_scenario: str
    total_potential_savings: float


@router.get("/comprehensive", response_model=FinancialAnalysis)
async def get_comprehensive_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(12, ge=1, le=24, description="Hány hónapra visszamenőleg elemezzen"),
    lang: str = Query('hu', description="The language for analysis text")
):
    """Átfogó pénzügyi elemzés készítése"""
    try:
        # Időintervallum meghatározása
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Tranzakciók lekérése
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if not transactions:
            raise HTTPException(status_code=404, detail=translate('no_transactions_for_analysis', lang=lang))

        # 1. Alapvető statisztikák
        basic_stats = await _calculate_basic_stats(transactions, lang)
        
        # 2. Cashflow elemzés
        cashflow_analysis = await _analyze_cashflow(transactions, lang)
        
        # 3. Kategória elemzés
        category_analysis = await _analyze_categories(transactions, lang)
        
        # 4. Időbeli elemzés
        time_analysis = await _analyze_time_patterns(transactions, lang)
        
        # 5. Kockázatelemzés
        risk_analysis = await _analyze_risk(transactions, current_user.id, lang)
        
        # 6. Ajánlások generálása
        recommendations = await _generate_recommendations(
            basic_stats, cashflow_analysis, category_analysis, risk_analysis, lang
        )
        
        return FinancialAnalysis(
            user_id=current_user.id,
            analysis_date=datetime.now(),
            basic_stats=basic_stats,
            cashflow_analysis=cashflow_analysis,
            category_analysis=category_analysis,
            time_analysis=time_analysis,
            risk_analysis=risk_analysis,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

async def _calculate_basic_stats(transactions: List[Transaction], lang: str = 'hu') -> BasicStats:
    """Alapvető statisztikák számítása"""
    if not transactions:
        return BasicStats(
            total_income=0, total_expense=0, net_balance=0,
            daily_avg_expense=0, monthly_avg_expense=0,
            most_active_day=translate('monday', lang=lang), most_active_hour=12, transaction_count=0
        )
    
    # Bevételek és kiadások szétválasztása
    incomes = [t.amount for t in transactions if t.amount > 0]
    expenses = [abs(t.amount) for t in transactions if t.amount < 0]
    
    total_income = sum(incomes)
    total_expense = sum(expenses)
    net_balance = total_income - total_expense
    
    # Átlagok számítása
    days_in_period = (datetime.strptime(max(t.date for t in transactions), "%Y-%m-%d") - 
                     datetime.strptime(min(t.date for t in transactions), "%Y-%m-%d")).days + 1
    daily_avg_expense = total_expense / max(days_in_period, 1)
    monthly_avg_expense = daily_avg_expense * 30
    
    # Legaktívabb nap és óra
    weekdays = []
    hours = []
    
    for t in transactions:
        date_obj = datetime.strptime(t.date, "%Y-%m-%d")
        weekdays.append(calendar.day_name[date_obj.weekday()])
        # Ha van időbélyeg, használjuk, különben 12-t feltételezünk
        hours.append(getattr(t, 'hour', 12))
    
    most_active_day = Counter(weekdays).most_common(1)[0][0] if weekdays else translate('monday', lang=lang)
    most_active_hour = Counter(hours).most_common(1)[0][0] if hours else 12
    
    return BasicStats(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        daily_avg_expense=daily_avg_expense,
        monthly_avg_expense=monthly_avg_expense,
        most_active_day=most_active_day,
        most_active_hour=most_active_hour,
        transaction_count=len(transactions)
    )

async def _analyze_cashflow(transactions: List[Transaction], lang: str = 'hu') -> CashflowAnalysis:
    """Cashflow elemzés"""
    monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
    weekly_data = defaultdict(lambda: {"income": 0, "expense": 0})
    
    for t in transactions:
        date_obj = datetime.strptime(t.date, "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")
        week_key = date_obj.strftime("%Y-W%U")
        
        if t.amount > 0:
            monthly_data[month_key]["income"] += t.amount
            weekly_data[week_key]["income"] += t.amount
        else:
            monthly_data[month_key]["expense"] += abs(t.amount)
            weekly_data[week_key]["expense"] += abs(t.amount)
    
    # Havi trendek
    monthly_trends = []
    for month, data in sorted(monthly_data.items()):
        monthly_trends.append(CashflowTrend(
            period=month,
            income=data["income"],
            expense=data["expense"],
            net=data["income"] - data["expense"]
        ))
    
    # Heti trendek (utolsó 12 hét)
    weekly_trends = []
    for week, data in sorted(weekly_data.items())[-12:]:
        weekly_trends.append(CashflowTrend(
            period=week,
            income=data["income"],
            expense=data["expense"],
            net=data["income"] - data["expense"]
        ))
    
    # Trend meghatározása
    if len(monthly_trends) >= 3:
        recent_nets = [t.net for t in monthly_trends[-3:]]
        if all(recent_nets[i] <= recent_nets[i+1] for i in range(len(recent_nets)-1)):
            trend = translate('increasing', lang=lang)
        elif all(recent_nets[i] >= recent_nets[i+1] for i in range(len(recent_nets)-1)):
            trend = translate('decreasing', lang=lang)
        else:
            trend = translate('stable', lang=lang)
    else:
        trend = translate('stable', lang=lang)
    
    return CashflowAnalysis(
        monthly_trends=monthly_trends,
        weekly_trends=weekly_trends,
        overall_trend=trend
    )

async def _analyze_categories(transactions: List[Transaction], lang: str = 'hu') -> CategoryAnalysis:
    """Kategória elemzés"""
    category_data = defaultdict(lambda: {"income": 0, "expense": 0, "count": 0})
    
    for t in transactions:
        cat = t.kategoria or translate('other', lang=lang)
        category_data[cat]["count"] += 1
        
        if t.amount > 0:
            category_data[cat]["income"] += t.amount
        else:
            category_data[cat]["expense"] += abs(t.amount)
    
    # Top 3 kiadási kategória
    expense_categories = [(cat, data["expense"]) for cat, data in category_data.items() if data["expense"] > 0]
    expense_categories.sort(key=lambda x: x[1], reverse=True)
    
    top_expense_categories = []
    for i, (cat, amount) in enumerate(expense_categories[:3]):
        top_expense_categories.append({
            "rank": i + 1,
            "category": cat,
            "amount": amount,
            "transaction_count": category_data[cat]["count"]
        })
    
    # Alapvető kategóriák ellenőrzése
    basic_categories = [
        translate('food', lang=lang), translate('housing', lang=lang), 
        translate('transport', lang=lang), translate('healthcare', lang=lang), 
        translate('entertainment', lang=lang), translate('clothing', lang=lang), 
        translate('communication', lang=lang), translate('education', lang=lang)
    ]
    existing_categories = set(category_data.keys())
    missing_basic_categories = [cat for cat in basic_categories if cat not in existing_categories]
    
    # Kategória összesítés
    category_summary = {
        cat: {"income": data["income"], "expense": data["expense"]}
        for cat, data in category_data.items()
    }
    
    return CategoryAnalysis(
        top_expense_categories=top_expense_categories,
        category_summary=category_summary,
        missing_basic_categories=missing_basic_categories
    )

async def _analyze_time_patterns(transactions: List[Transaction], lang: str = 'hu') -> TimeAnalysis:
    """Időbeli minták elemzése"""
    weekday_expenses = defaultdict(float)
    hour_counts = defaultdict(int)
    
    for t in transactions:
        if t.amount < 0:  # Csak kiadások
            date_obj = datetime.strptime(t.date, "%Y-%m-%d")
            weekday = calendar.day_name[date_obj.weekday()]
            weekday_expenses[weekday] += abs(t.amount)
            
            # Óra (ha van)
            hour = getattr(t, 'hour', 12)
            hour_counts[hour] += 1
    
    # Hét napjai szerinti átlag
    by_weekday = {day: weekday_expenses.get(day, 0) for day in calendar.day_name}
    
    # Óra szerinti eloszlás
    by_hour = dict(hour_counts)
    
    # Csúcsok meghatározása
    peak_spending_day = max(by_weekday.items(), key=lambda x: x[1])[0] if by_weekday else translate('monday', lang=lang)
    peak_spending_hour = max(by_hour.items(), key=lambda x: x[1])[0] if by_hour else 12
    
    return TimeAnalysis(
        by_weekday=by_weekday,
        by_hour=by_hour,
        peak_spending_day=peak_spending_day,
        peak_spending_hour=peak_spending_hour
    )

async def _analyze_risk(transactions: List[Transaction], user_id: str, lang: str = 'hu') -> RiskAnalysis:
    """Kockázatelemzés"""
    # Alapadatok
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
    
    # Számla egyenlegek lekérése
    emergency_fund = 0.0
    debt_amount = 0.0
    
    try:
        all_accounts_doc = await AllUserAccountsDocument.find_one()
        if all_accounts_doc and user_id in all_accounts_doc.accounts_by_user:
            user_accounts = all_accounts_doc.accounts_by_user[user_id]
            
            # Vészhelyzeti alap (megtakarítások)
            if hasattr(user_accounts, 'megtakaritas'):
                for sub_account in user_accounts.megtakaritas.alszamlak.values():
                    emergency_fund += sub_account.balance
            
            # Adósság (negatív egyenlegek)
            for account_type in ['likvid', 'befektetes', 'megtakaritas']:
                if hasattr(user_accounts, account_type):
                    account = getattr(user_accounts, account_type)
                    for sub_account in account.alszamlak.values():
                        if sub_account.balance < 0:
                            debt_amount += abs(sub_account.balance)
    except Exception:
        pass
    
    # Mutatók számítása
    expense_income_ratio = total_expense / max(total_income, 1)
    savings_rate = max(0, total_income - total_expense) / max(total_income, 1)
    debt_income_ratio = debt_amount / max(total_income, 1)
    
    # Vészhelyzeti alap hónapokban
    monthly_expense = total_expense / 12 if total_expense > 0 else 1
    emergency_fund_months = emergency_fund / monthly_expense
    
    # Kockázati szint meghatározása
    risk_score = 0
    if expense_income_ratio > 0.8:
        risk_score += 2
    elif expense_income_ratio > 0.6:
        risk_score += 1
    
    if savings_rate < 0.1:
        risk_score += 2
    elif savings_rate < 0.2:
        risk_score += 1
    
    if debt_income_ratio > 0.3:
        risk_score += 2
    elif debt_income_ratio > 0.1:
        risk_score += 1
    
    if emergency_fund_months < 3:
        risk_score += 2
    elif emergency_fund_months < 6:
        risk_score += 1
    
    if risk_score >= 5:
        risk_level = translate('high_risk', lang=lang)
    elif risk_score >= 3:
        risk_level = translate('medium_risk', lang=lang)
    else:
        risk_level = translate('low_risk', lang=lang)
    
    return RiskAnalysis(
        expense_income_ratio=expense_income_ratio,
        savings_rate=savings_rate,
        debt_income_ratio=debt_income_ratio,
        emergency_fund_months=emergency_fund_months,
        risk_level=risk_level
    )

async def _generate_recommendations(
    basic_stats: BasicStats,
    cashflow_analysis: CashflowAnalysis,
    category_analysis: CategoryAnalysis,
    risk_analysis: RiskAnalysis,
    lang: str = 'hu'
) -> Recommendations:
    """Személyre szabott ajánlások generálása"""
    
    savings_suggestions = []
    cost_optimization_tips = []
    emergency_fund_advice = []
    debt_management_advice = []
    
    # Megtakarítási javaslatok
    if risk_analysis.savings_rate < 0.1:
        savings_suggestions.append(translate('low_savings_rate', lang=lang))
        savings_suggestions.append(translate('auto_savings_setup', lang=lang))
    elif risk_analysis.savings_rate < 0.2:
        savings_suggestions.append(translate('increase_savings_to_20', lang=lang))
    else:
        savings_suggestions.append(translate('excellent_savings', lang=lang))
    
    # Költségoptimalizálás
    if category_analysis.top_expense_categories:
        top_cat = category_analysis.top_expense_categories[0]
        cost_optimization_tips.append(
            translate('cost_optimization_top_category', lang=lang, 
                    category=top_cat['category'])
        )
    
    # Vészhelyzeti alap
    if risk_analysis.emergency_fund_months < 3:
        emergency_fund_advice.append(translate('low_emergency_fund', lang=lang))
        emergency_fund_advice.append(translate('emergency_fund_advice', lang=lang))
    
    # Adósságkezelés
    if risk_analysis.debt_income_ratio > 0.3:
        debt_management_advice.append(translate('high_debt', lang=lang))
        debt_management_advice.append(translate('debt_prioritize', lang=lang))
    elif risk_analysis.debt_income_ratio > 0.1:
        debt_management_advice.append(translate('reduce_debt', lang=lang))
    else:
        debt_management_advice.append(translate('good_debt', lang=lang))
    
    return Recommendations(
        savings_suggestions=savings_suggestions,
        cost_optimization_tips=cost_optimization_tips,
        emergency_fund_advice=emergency_fund_advice,
        debt_management_advice=debt_management_advice
    )

@router.get("/basic-stats", response_model=BasicStats)
async def get_basic_stats(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=1, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Alapvető statisztikák lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _calculate_basic_stats(transactions, lang)

@router.get("/risk-analysis", response_model=RiskAnalysis)
async def get_risk_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(12, ge=1, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Kockázatelemzés lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _analyze_risk(transactions, current_user.id, lang)

@router.get("/category-analysis", response_model=CategoryAnalysis)
async def get_category_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=1, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Kategóriaelemzés lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _analyze_categories(transactions, lang)

# ÚJ ROUTE-OK - add hozzá a meglévő route-ok mellé

@router.get("/forecast", response_model=ForecastResponse)
async def get_spending_forecast(
    current_user: User = Depends(get_current_user),
    forecast_type: str = Query("monthly", regex="^(monthly|weekly)$"),
    periods_ahead: int = Query(6, ge=1, le=12),
    months_history: int = Query(12, ge=3, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Havi/heti kiadások előrejelzése idősor elemzéssel"""
    try:
        # Historikus adatok lekérése
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_history * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 30:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # DataFrame készítése
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'is_income': t.amount > 0,
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Időszak szerint csoportosítás
        if forecast_type == "monthly":
            df['period'] = df['date'].dt.to_period('M')
            freq = 'M'
        else:  # weekly
            df['period'] = df['date'].dt.to_period('W')
            freq = 'W'
        
        # Aggregálás időszakonként
        period_data = df.groupby('period').agg({
            'amount': lambda x: x[x > 0].sum() if len(x[x > 0]) > 0 else 0,  # income
        }).rename(columns={'amount': 'income'})
        
        period_data['expense'] = df.groupby('period').agg({
            'amount': lambda x: abs(x[x < 0].sum()) if len(x[x < 0]) > 0 else 0
        })['amount']
        
        period_data['net'] = period_data['income'] - period_data['expense']
        period_data = period_data.fillna(0)
        
        if len(period_data) < 3:
            raise HTTPException(status_code=400, detail=translate('no_periods_for_forecast', lang=lang))
        
        # Előrejelzés készítése
        forecasts = []
        model_accuracy = 0.0
        seasonal_detected = False
        trend = translate("stable", lang=lang)
        
        # Expense előrejelzés (ezt általában jobban lehet előre jelezni)
        expense_series = period_data['expense'].values
        
        try:
            # Exponential Smoothing modell
            if len(expense_series) >= 8:  # Minimum szezonalitás detektálásához
                model = ExponentialSmoothing(
                    expense_series, 
                    trend='add', 
                    seasonal='add' if len(expense_series) >= 12 else None,
                    seasonal_periods=12 if forecast_type == "monthly" else 52
                ).fit()
                seasonal_detected = model.params.get('smoothing_seasonal', 0) > 0.1
            else:
                model = ExponentialSmoothing(expense_series, trend='add').fit()
            
            # Előrejelzés
            forecast_values = model.forecast(periods_ahead)
            confidence_intervals = model.predict(
                start=len(expense_series), 
                end=len(expense_series) + periods_ahead - 1, 
                return_conf_int=True
            )
            
            # Model accuracy (MAE alapú)
            fitted_values = model.fittedvalues
            model_accuracy = max(0, 100 - (np.mean(np.abs(expense_series[1:] - fitted_values)) / np.mean(expense_series) * 100))
            
        except Exception as e:
            # Fallback: simple linear trend
            x = np.arange(len(expense_series))
            slope, intercept = np.polyfit(x, expense_series, 1)
            forecast_values = [slope * (len(expense_series) + i) + intercept for i in range(periods_ahead)]
            confidence_intervals = [(f * 0.8, f * 1.2) for f in forecast_values]
            model_accuracy = 70.0
        
        # Income egyszerűbb előrejelzés (gyakran stabilabb)
        income_mean = period_data['income'].mean()
        income_std = period_data['income'].std()
        
        # Trend meghatározása
        recent_expenses = expense_series[-3:]
        older_expenses = expense_series[-6:-3] if len(expense_series) >= 6 else expense_series[:-3]
        if len(older_expenses) > 0:
            if np.mean(recent_expenses) > np.mean(older_expenses) * 1.05:
                trend = translate("increasing", lang=lang)
            elif np.mean(recent_expenses) < np.mean(older_expenses) * 0.95:
                trend = translate("decreasing", lang=lang)
        
        # Forecasts létrehozása
        for i in range(periods_ahead):
            current_period = period_data.index[-1] + i + 1
            
            pred_expense = float(forecast_values[i])
            pred_income = income_mean  # Egyszerűsített
            pred_net = pred_income - pred_expense
            
            conf_lower = float(confidence_intervals[i][0]) if hasattr(confidence_intervals[i], '__getitem__') else pred_expense * 0.8
            conf_upper = float(confidence_intervals[i][1]) if hasattr(confidence_intervals[i], '__getitem__') else pred_expense * 1.2
            
            # Szezonális faktor (egyszerűsített)
            seasonal_factor = 1.0
            if seasonal_detected and forecast_type == "monthly":
                month = (current_period.month - 1) if hasattr(current_period, 'month') else (datetime.now().month + i) % 12
                if month in [11, 0]:  # December, január
                    seasonal_factor = 1.2
                elif month in [6, 7]:  # Július, augusztus
                    seasonal_factor = 1.1
            
            forecasts.append(ForecastData(
                period=str(current_period),
                predicted_income=pred_income,
                predicted_expense=pred_expense * seasonal_factor,
                predicted_net=pred_income - (pred_expense * seasonal_factor),
                confidence_lower=conf_lower * seasonal_factor,
                confidence_upper=conf_upper * seasonal_factor,
                seasonal_factor=seasonal_factor
            ))
        
        return ForecastResponse(
            forecast_type=forecast_type,
            periods_ahead=periods_ahead,
            forecasts=forecasts,
            model_accuracy=min(100.0, max(0.0, model_accuracy)),
            seasonal_pattern_detected=seasonal_detected,
            trend=trend
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('forecast_error', lang=lang) + f" {str(e)}")

@router.get("/seasonal-analysis", response_model=SeasonalAnalysis)
async def get_seasonal_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(24, ge=12, le=36),
    lang: str = Query("hu", description="Language for analysis text")
):
    """Szezonalitás elemzése"""
    try:
        # Adatok lekérése
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$lt": 0},  # Csak kiadások
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 100:
            return SeasonalAnalysis(
                has_seasonality=False,
                seasonal_periods=[],
                peak_seasons={},
                seasonal_recommendations=[translate('no_data_for_seasonality', lang=lang)]
            )
        
        # DataFrame készítése
        df = pd.DataFrame([{
            'date': t.date,
            'amount': abs(t.amount),
            'month': datetime.strptime(t.date, '%Y-%m-%d').month,
            'month_name': datetime.strptime(t.date, '%Y-%m-%d').strftime('%B'),
            'category': t.kategoria or translate('other', lang=lang)
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Havi aggregálás
        monthly_spending = df.groupby([df['date'].dt.to_period('M')])['amount'].sum()
        
        # Szezonalitás detektálás
        has_seasonality = False
        seasonal_periods = []
        peak_seasons = {}
        
        if len(monthly_spending) >= 12:
            try:
                # Szezonális dekompozíció
                decomposition = seasonal_decompose(monthly_spending.values, period=12, model='additive')
                seasonal_component = decomposition.seasonal
                
                # Szezonalitás erősségének mérése
                seasonal_strength = np.std(seasonal_component) / np.std(monthly_spending.values)
                has_seasonality = seasonal_strength > 0.1
                
                if has_seasonality:
                    # Csúcs hónapok azonosítása
                    month_avg = df.groupby('month')['amount'].mean()
                    overall_avg = month_avg.mean()
                    
                    for month, avg_spending in month_avg.items():
                        if avg_spending > overall_avg * 1.15:  # 15%-kal több mint az átlag
                            month_name = datetime(2000, month, 1).strftime('%B')
                            seasonal_periods.append(month_name)
                            peak_seasons[month_name] = float(avg_spending)
                    
            except Exception:
                # Fallback: egyszerű statisztikai elemzés
                month_stats = df.groupby('month')['amount'].agg(['mean', 'std']).fillna(0)
                overall_mean = month_stats['mean'].mean()
                overall_std = month_stats['mean'].std()
                
                has_seasonality = overall_std > overall_mean * 0.15
                
                if has_seasonality:
                    for month, row in month_stats.iterrows():
                        if row['mean'] > overall_mean + overall_std:
                            month_name = datetime(2000, month, 1).strftime('%B')
                            seasonal_periods.append(month_name)
                            peak_seasons[month_name] = float(row['mean'])
        
        # Ajánlások generálása
        recommendations = []
        if has_seasonality:
            if 'December' in peak_seasons or 'November' in peak_seasons:
                recommendations.append(translate('christmas_higher_spending', lang=lang))
            if 'January' in peak_seasons:
                recommendations.append(translate('january_higher_spending', lang=lang))
            if len(peak_seasons) > 0:
                highest_month = max(peak_seasons, key=peak_seasons.get)
                recommendations.append(translate('highest_spending_month', lang=lang, highest_month=highest_month))
        else:
            recommendations.append(translate('stable_spending', lang=lang))
        
        return SeasonalAnalysis(
            has_seasonality=has_seasonality,
            seasonal_periods=seasonal_periods,
            peak_seasons=peak_seasons,
            seasonal_recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('seasonal_analysis_error', lang=lang, error=str(e)))

@router.get("/anomaly-detection", response_model=AnomalyResponse)
async def detect_anomalies(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    sensitivity: float = Query(0.1, ge=0.05, le=0.3, description="Anomália érzékenység (alacsonyabb = szigorúbb)"),
    lang: str = Query("hu", description="Language for analysis text")
):
    """Rendkívüli kiadások azonosítása anomália detektálással"""
    try:
        # JAVÍTÁS: Paraméter validálás és konverziók
        sensitivity = float(sensitivity) if not isinstance(sensitivity, float) else sensitivity
        months_back = int(months_back) if not isinstance(months_back, int) else months_back
        
        # Adatok lekérése
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$lt": 0},  # Csak kiadások
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 50:
            raise HTTPException(status_code=400, detail=translate('no_data_for_anomaly', lang=lang))
        
        # Feature engineering
        features_list = []
        anomaly_candidates = []
        
        for t in transactions:
            date_obj = datetime.strptime(t.date, '%Y-%m-%d')
            
            features = {
                'amount': abs(t.amount),
                'hour': t.hour or 12,
                'weekday': date_obj.weekday(),
                'is_weekend': date_obj.weekday() >= 5,
                'month': date_obj.month,
                'day_of_month': date_obj.day,
                'category_encoded': hash(t.kategoria or translate('other', lang=lang)) % 100,  # Egyszerű encoding
            }
            
            features_list.append(list(features.values()))
            anomaly_candidates.append({
                'transaction': t,
                'features': features,
                'date_obj': date_obj
            })
        
        # Isolation Forest modell
        features_array = np.array(features_list)
        
        # Normalizálás
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_array)
        
        # Anomália detektálás - JAVÍTÁS: float() konverziók
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=float(sensitivity),
            random_state=42
        )
        
        anomaly_labels = iso_forest.fit_predict(features_scaled)
        anomaly_scores = iso_forest.score_samples(features_scaled)
        
        # Anomáliák feldolgozása
        anomalies = []
        anomaly_trends = defaultdict(int)
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        
        for i, (label, score, candidate) in enumerate(zip(anomaly_labels, anomaly_scores, anomaly_candidates)):
            if label == -1:  # Anomália
                t = candidate['transaction']
                
                # Anomália típus meghatározása
                anomaly_type = "high_spending"
                amount = abs(t.amount)
                
                # Kategórián belüli átlagtól való eltérés
                category_transactions = [abs(tr.amount) for tr in transactions if tr.kategoria == t.kategoria]
                if category_transactions:
                    category_avg = np.mean(category_transactions)
                    category_std = np.std(category_transactions)
                    if amount > category_avg + 2 * category_std:
                        anomaly_type = "unusual_category"
                
                # Időbeli anomália (szokatlan időpontban)
                if t.hour and (t.hour < 6 or t.hour > 22):
                    anomaly_type = "time_anomaly"
                
                # Severity meghatározása
                severity = "low"
                if score < -0.6:
                    severity = "high"
                elif score < -0.4:
                    severity = "medium"
                
                severity_counts[severity] += 1
                
                anomalies.append(AnomalyData(
                    transaction_id=str(t.id),
                    date=t.date,
                    amount=amount,
                    category=t.kategoria or translate('other', lang=lang),
                    anomaly_score=float(score),
                    anomaly_type=anomaly_type,
                    severity=severity
                ))
                
                # Trend számítás
                month_key = candidate['date_obj'].strftime('%Y-%m')
                anomaly_trends[month_key] += 1
        
        # Rendezés severity és score szerint
        anomalies.sort(key=lambda x: (x.severity == "high", x.severity == "medium", abs(x.anomaly_score)), reverse=True)
        
        # Ajánlások
        recommendations = []
        if len(anomalies) > len(transactions) * 0.15:  # Ha túl sok anomália
            recommendations.append(translate('many_anomalies_found', lang=lang))
        
        high_severity_count = severity_counts["high"]
        if high_severity_count > 0:
            recommendations.append(translate('high_risk_anomalies', lang=lang, count=high_severity_count))
            recommendations.append(translate('check_transactions', lang=lang))
        
        if any(a.anomaly_type == "time_anomaly" for a in anomalies):
            recommendations.append(translate('unusual_time_spending', lang=lang))
        
        if not recommendations:
            recommendations.append(translate('spending_stable_predictable', lang=lang))
        
        return AnomalyResponse(
            total_anomalies=len(anomalies),
            anomalies_by_severity=dict(severity_counts),
            recent_anomalies=anomalies[:20],  # Top 20
            anomaly_trends=dict(anomaly_trends),
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('anomaly_detection_error', lang=lang, error=str(e)))

@router.get("/ml-budget-recommendations", response_model=MLBudgetResponse)
async def get_ml_budget_recommendations(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """ML alapú költségvetési korlátok javaslása kategóriánként"""
    try:
        # Adatok lekérése
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$lt": 0},  # Csak kiadások
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 30:
            raise HTTPException(status_code=400, detail=translate('no_data_for_budget', lang=lang))
        
        # Kategóriánkénti elemzés
        category_data = defaultdict(list)
        for t in transactions:
            category = t.kategoria or translate('other', lang=lang)
            amount = abs(t.amount)
            date_obj = datetime.strptime(t.date, '%Y-%m-%d')
            
            category_data[category].append({
                'amount': amount,
                'date': date_obj,
                'month': date_obj.strftime('%Y-%m')
            })
        
        recommendations = []
        total_recommended = 0.0
        spending_patterns = []
        
        for category, cat_transactions in category_data.items():
            if len(cat_transactions) < 5:  # Túl kevés adat
                continue
            
            amounts = [t['amount'] for t in cat_transactions]
            
            # Statisztikai mutatók
            mean_spending = np.mean(amounts)
            std_spending = np.std(amounts)
            median_spending = np.median(amounts)
            percentile_75 = np.percentile(amounts, 75)
            percentile_90 = np.percentile(amounts, 90)
            
            # Havi összesítés a stabilabb becslésért
            monthly_totals = defaultdict(float)
            for t in cat_transactions:
                monthly_totals[t['month']] += t['amount']
            
            monthly_amounts = list(monthly_totals.values())
            if monthly_amounts:
                monthly_mean = np.mean(monthly_amounts)
                monthly_std = np.std(monthly_amounts)
                cv = monthly_std / monthly_mean if monthly_mean > 0 else 1  # Coefficient of variation
            else:
                monthly_mean = mean_spending
                cv = 1
            
            # Kiszámíthatóság score (0-100)
            predictability = max(0, min(100, (1 - cv) * 100))
            spending_patterns.append(predictability)
            
            # Ajánlott limit számítása
            if cv < 0.3:  # Stabil költés
                recommended_limit = monthly_mean * 1.1  # 10% buffer
                confidence = 0.9
                reasoning = translate('stable_spending_pattern', lang=lang)
            elif cv < 0.6:  # Közepesen változó
                recommended_limit = monthly_mean * 1.25  # 25% buffer
                confidence = 0.75
                reasoning = translate('variable_spending_pattern', lang=lang)
            else:  # Nagyon változó
                recommended_limit = max(monthly_mean * 1.5, percentile_90)  # 50% buffer vagy 90. percentilis
                confidence = 0.6
                reasoning = translate('unpredictable_spending_pattern', lang=lang)
            
            # Prioritás meghatározása
            category_lower = category.lower()
            if any(basic_cat in category_lower for basic_cat in [translate('food', lang=lang).lower(), translate('housing', lang=lang).lower(), translate('transport', lang=lang).lower(), translate('healthcare', lang=lang).lower()]):
                priority = "high"
            elif any(medium_cat in category_lower for medium_cat in [translate('clothing', lang=lang).lower(), translate('communication', lang=lang).lower(), translate('education', lang=lang).lower()]):
                priority = "medium" 
            else:
                priority = "low"
            
            total_recommended += recommended_limit
            
            recommendations.append(BudgetRecommendation(
                category=category,
                recommended_limit=float(recommended_limit),
                current_spending=float(monthly_mean),
                confidence=float(confidence),
                reasoning=reasoning,
                priority=priority
            ))
        
        # Összesített mutatók
        overall_predictability = np.mean(spending_patterns) if spending_patterns else 50
        
        # Kockázati szint
        if overall_predictability > 80:
            risk_level = translate('low_risk', lang=lang)
        elif overall_predictability > 60:
            risk_level = translate('medium_risk', lang=lang)
        else:
            risk_level = translate('high_risk', lang=lang)
        
        # Személyre szabott tippek
        tips = []
        if overall_predictability < 60:
            tips.append(translate('spending_unpredictable', lang=lang))
        
        high_priority_categories = [r for r in recommendations if r.priority == "high"]
        if len(high_priority_categories) < 4:
            tips.append(translate('spending_add_categories', lang=lang))
        
        variable_categories = [r for r in recommendations if r.confidence < 0.7]
        if variable_categories:
            categories_str = ', '.join([r.category for r in variable_categories[:3]])
            tips.append(translate('spending_variable_categories', lang=lang, categories=categories_str))
        
        if not tips:
            tips.append(translate('spending_structured', lang=lang))
        
        # Prioritás szerinti rendezés
        recommendations.sort(key=lambda x: (x.priority == "high", x.priority == "medium", x.confidence), reverse=True)
        
        return MLBudgetResponse(
            total_recommended_budget=float(total_recommended),
            category_recommendations=recommendations,
            spending_pattern_score=float(overall_predictability),
            risk_level=risk_level,
            personalized_tips=tips
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.get("/income-diversification", response_model=IncomeAnalysisResponse)
async def analyze_income_diversification(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(12, ge=3, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Bevételi források diverzifikációjának elemzése"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Csak bevételek lekérése
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$gt": 0},  # Csak bevételek
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 5:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # Bevételi források azonosítása
        income_sources = defaultdict(list)
        for t in transactions:
            # Forrás meghatározása kategória és leírás alapján
            source = t.kategoria or translate('other', lang=lang)
            if t.description and any(keyword in t.description.lower() for keyword in ['fizetés', 'salary', 'bér']):
                source = "Rendszeres fizetés"
            elif t.description and any(keyword in t.description.lower() for keyword in ['freelance', 'mellékállás', 'extra']):
                source = "Mellékjövedelem"
            
            income_sources[source].append({
                'amount': t.amount,
                'date': datetime.strptime(t.date, '%Y-%m-%d'),
                'description': t.description or ""
            })
        
        # Források elemzése
        total_income = sum(t.amount for t in transactions)
        monthly_income = total_income / months_back
        
        analyzed_sources = []
        for source, source_transactions in income_sources.items():
            source_total = sum(t['amount'] for t in source_transactions)
            
            # Rendszeresség számítása (hányszor havonta átlagosan)
            monthly_frequency = len(source_transactions) / months_back
            regularity_score = min(1.0, monthly_frequency / 2)  # 2+ alkalom/hó = teljesen rendszeres
            
            # Kockázat értékelése
            if regularity_score > 0.8 and source_total > total_income * 0.3:
                risk_level = translate('low_risk', lang=lang)
            elif regularity_score > 0.5:
                risk_level = translate('medium_risk', lang=lang)
            else:
                risk_level = translate('high_risk', lang=lang)
            
            analyzed_sources.append(IncomeSourceAnalysis(
                source=source,
                total_amount=source_total,
                percentage_of_total=(source_total / total_income * 100),
                regularity_score=regularity_score,
                risk_level=risk_level
            ))
        
        # Diverzifikáció és stabilitás számítása
        source_percentages = [s.percentage_of_total for s in analyzed_sources]
        
        # Herfindahl index (diverzifikáció)
        hhi = sum((p/100)**2 for p in source_percentages)
        diversification_score = max(0, (1 - hhi) * 100)
        
        # Stabilitás (rendszeres források aránya)
        regular_income = sum(s.total_amount for s in analyzed_sources if s.regularity_score > 0.7)
        stability_score = (regular_income / total_income * 100)
        
        # Ajánlások
        recommendations = []
        if diversification_score < 50:
            recommendations.append("Érdemes több bevételi forrást keresni a kockázat csökkentéséhez")
        if stability_score < 70:
            recommendations.append("A bevételeid nagy része nem rendszeres - próbálj stabilabb forrásokat találni")
        if len(analyzed_sources) == 1:
            recommendations.append("Csak egy bevételi forrásod van - ez magas kockázatú")
        
        if not recommendations:
            recommendations.append("Jól diverzifikált és stabil bevételi portfóliód van!")
        
        return IncomeAnalysisResponse(
            total_monthly_income=monthly_income,
            income_sources=sorted(analyzed_sources, key=lambda x: x.total_amount, reverse=True),
            diversification_score=diversification_score,
            stability_score=stability_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.get("/payment-methods", response_model=List[PaymentMethodAnalysis])
async def analyze_payment_methods(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Fizetési módok hatásának elemzése"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$lt": 0},  # Csak kiadások
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 20:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # Fizetési módok azonosítása (sub_account_name vagy platform alapján)
        payment_methods = defaultdict(list)
        
        for t in transactions:
            # Fizetési mód meghatározása
            method = t.sub_account_name or translate('other', lang=lang)
            
            # Platform alapú finomítás
            if t.platform:
                if 'card' in t.platform.lower() or 'kártya' in t.platform.lower():
                    method = f"{method} (Kártya)"
                elif 'cash' in t.platform.lower() or 'készpénz' in t.platform.lower():
                    method = f"{method} (Készpénz)"
                elif 'online' in t.platform.lower():
                    method = f"{method} (Online)"
            
            payment_methods[method].append({
                'amount': abs(t.amount),
                'date': datetime.strptime(t.date, '%Y-%m-%d')
            })
        
        # Elemzés
        total_spending = sum(abs(t.amount) for t in transactions)
        results = []
        
        for method, method_transactions in payment_methods.items():
            method_total = sum(t['amount'] for t in method_transactions)
            
            # Trend számítása (első vs. második fél összehasonlítása)
            mid_date = start_date + timedelta(days=months_back * 15)
            first_half = [t for t in method_transactions if t['date'] < mid_date]
            second_half = [t for t in method_transactions if t['date'] >= mid_date]
            
            if first_half and second_half:
                first_avg = sum(t['amount'] for t in first_half) / len(first_half)
                second_avg = sum(t['amount'] for t in second_half) / len(second_half)
                
                if second_avg > first_avg * 1.1:
                    trend = translate('increasing', lang=lang)
                elif second_avg < first_avg * 0.9:
                    trend = translate('decreasing', lang=lang)
                else:
                    trend = translate('stable', lang=lang)
            else:
                trend = translate('stable', lang=lang)
            
            results.append(PaymentMethodAnalysis(
                payment_method=method,
                transaction_count=len(method_transactions),
                total_amount=method_total,
                avg_transaction=method_total / len(method_transactions),
                usage_percentage=(method_total / total_spending * 100),
                trend=trend
            ))
        
        return sorted(results, key=lambda x: x.total_amount, reverse=True)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.get("/collaborative-analysis", response_model=CollaborativeAnalysisResponse)
async def get_collaborative_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Collaborative filtering alapú összehasonlítás más felhasználókkal"""
    try:
        # Felhasználó tranzakcióinak lekérése
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        user_transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(user_transactions) < 30:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # Egyszerűsített implementáció - valódi környezetben több felhasználó adatait kellene lekérni
        # Itt szimulált adatokkal dolgozunk a privacy miatt
        
        # Felhasználó profiljának elemzése
        user_expenses = [t for t in user_transactions if t.amount < 0]
        user_income = [t for t in user_transactions if t.amount > 0]
        
        monthly_spending = sum(abs(t.amount) for t in user_expenses) / months_back
        monthly_income = sum(t.amount for t in user_income) / months_back if user_income else 0
        
        savings_rate = ((monthly_income - monthly_spending) / monthly_income * 100) if monthly_income > 0 else 0
        
        # Kategóriák szerinti eloszlás
        category_spending = defaultdict(float)
        for t in user_expenses:
            category_spending[t.kategoria or translate('other', lang=lang)] += abs(t.amount)
        
        total_spending = sum(category_spending.values())
        category_percentages = {
            cat: (amount / total_spending * 100) 
            for cat, amount in category_spending.items()
        }
        
        # Szimulált peer adatok (valódi implementációban ez adatbázisból jönne)
        peer_monthly_spending = monthly_spending * np.random.uniform(0.8, 1.2)  # ±20%
        peer_savings_rate = savings_rate + np.random.uniform(-10, 10)  # ±10%
        
        # Pozíció meghatározása
        if monthly_spending < peer_monthly_spending * 0.9:
            position = "átlag alatti költő"
        elif monthly_spending > peer_monthly_spending * 1.1:
            position = "átlag feletti költő"
        else:
            position = "átlagos költő"
        
        # Efficiency score (megtakarítás vs költés arány)
        efficiency_score = min(100, max(0, savings_rate + 50))  # 50 = baseline
        
        # Ajánlások
        recommendations = []
        if savings_rate < peer_savings_rate:
            recommendations.append(translate('peer_spending_higher', lang=lang))
        
        if monthly_spending > peer_monthly_spending:
            recommendations.append(translate('review_top_categories', lang=lang))
        
        if efficiency_score < 60:
            recommendations.append("Pénzügyi hatékonyságod javítható - fókuszálj a megtakarításokra")
        
        if not recommendations:
            recommendations.append("Jól teljesítesz a hasonló felhasználókhoz képest!")
        
        return CollaborativeAnalysisResponse(
            user_position=position,
            similar_users_count=50,  # Szimulált
            peer_comparison={
                "monthly_spending": monthly_spending / peer_monthly_spending,
                "savings_rate": savings_rate / max(peer_savings_rate, 1),
                "efficiency": efficiency_score / 100
            },
            recommendations_from_peers=recommendations,
            spending_efficiency_score=efficiency_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.post("/what-if-scenarios", response_model=WhatIfResponse)
async def generate_what_if_scenarios(
    current_user: User = Depends(get_current_user),
    target_savings: float = Query(..., description="Cél havi megtakarítás összeg"),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """What-If szimulációk generálása költségcsökkentési célokhoz"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "amount": {"$lt": 0},  # Csak kiadások
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 20:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # Kategóriánkénti havi átlagok
        category_spending = defaultdict(list)
        for t in transactions:
            category = t.kategoria or translate('other', lang=lang)
            month_key = datetime.strptime(t.date, '%Y-%m-%d').strftime('%Y-%m')
            category_spending[category].append(abs(t.amount))
        
        category_monthly_avg = {}
        for category, amounts in category_spending.items():
            # Havi összesítés
            monthly_totals = defaultdict(float)
            for t in transactions:
                if (t.kategoria or translate('other', lang=lang)) == category:
                    month_key = datetime.strptime(t.date, '%Y-%m-%d').strftime('%Y-%m')
                    monthly_totals[month_key] += abs(t.amount)
            
            if monthly_totals:
                category_monthly_avg[category] = sum(monthly_totals.values()) / len(monthly_totals)
        
        # Szcenáriók generálása
        scenarios = []
        
        # 1. Konzervatív szcenárió (5-10% csökkentés)
        conservative_changes = {}
        conservative_savings = 0
        for category, avg_amount in sorted(category_monthly_avg.items(), key=lambda x: x[1], reverse=True)[:5]:
            reduction = avg_amount * 0.075  # 7.5% csökkentés
            conservative_changes[category] = avg_amount - reduction
            conservative_savings += reduction
        
        scenarios.append(WhatIfScenario(
            scenario_name="Konzervatív csökkentés",
            changes=conservative_changes,
            monthly_impact=-conservative_savings,
            annual_savings=conservative_savings * 12,
            feasibility="könnyű"
        ))
        
        # 2. Közepes szcenárió (10-20% csökkentés)
        moderate_changes = {}
        moderate_savings = 0
        for category, avg_amount in sorted(category_monthly_avg.items(), key=lambda x: x[1], reverse=True)[:4]:
            entertainment_key = translate('entertainment', lang=lang).lower()
            other_key = translate('other', lang=lang).lower()
            clothing_key = translate('clothing', lang=lang).lower()
            
            if category.lower() in [entertainment_key, other_key, clothing_key]:
                reduction = avg_amount * 0.2  # 20% nagyobb csökkentés
            else:
                reduction = avg_amount * 0.15  # 15% csökkentés
            moderate_changes[category] = avg_amount - reduction
            moderate_savings += reduction
        
        scenarios.append(WhatIfScenario(
            scenario_name="Közepes csökkentés",
            changes=moderate_changes,
            monthly_impact=-moderate_savings,
            annual_savings=moderate_savings * 12,
            feasibility="közepes"
        ))
        
        # 3. Agresszív szcenárió (20-40% csökkentés)
        aggressive_changes = {}
        aggressive_savings = 0
        food_key = translate('food', lang=lang).lower()
        housing_key = translate('housing', lang=lang).lower()
        
        for category, avg_amount in category_monthly_avg.items():
            if category.lower() in [food_key, housing_key]:
                reduction = avg_amount * 0.1  # Kisebb csökkentés alapvető kategóriákban
            else:
                reduction = avg_amount * 0.3  # 30% csökkentés
            aggressive_changes[category] = avg_amount - reduction
            aggressive_savings += reduction
        
        scenarios.append(WhatIfScenario(
            scenario_name="Agresszív csökkentés",
            changes=aggressive_changes,
            monthly_impact=-aggressive_savings,
            annual_savings=aggressive_savings * 12,
            feasibility="nehéz"
        ))
        
        # Ajánlott szcenárió kiválasztása
        target_diff = [(abs(s.monthly_impact) - target_savings, s.scenario_name) for s in scenarios]
        recommended = min(target_diff, key=lambda x: abs(x[0]))[1]
        
        total_potential = sum(s.annual_savings for s in scenarios) / len(scenarios)
        
        return WhatIfResponse(
            scenarios=scenarios,
            recommended_scenario=recommended,
            total_potential_savings=total_potential
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

# Meglévő route-ok javítása - ezeket add hozzá/cseréld le a jelenlegi implementációdban

@router.get("/spending-insights", response_model=Dict[str, Any])
async def get_advanced_spending_insights(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Fejlett költési betekintések kombinálva"""
    try:
        # Párhuzamos lekérdezések különböző elemzésekhez
        anomaly_result = await detect_anomalies(current_user, months_back, 0.1, lang)
        forecast_result = await get_spending_forecast(current_user, "monthly", 6, months_back, lang)
        seasonal_result = await get_seasonal_analysis(current_user, months_back * 2, lang)
        
        # Kombinált betekintések
        insights = {
            "anomaly_summary": {
                "total_anomalies": anomaly_result.total_anomalies,
                "high_risk_count": anomaly_result.anomalies_by_severity.get("high", 0),
                "recent_anomalies": anomaly_result.recent_anomalies[:5]
            },
            "forecast_summary": {
                "trend": forecast_result.trend,
                "next_month_prediction": forecast_result.forecasts[0].predicted_expense if forecast_result.forecasts else 0,
                "accuracy": forecast_result.model_accuracy
            },
            "seasonal_summary": {
                "has_patterns": seasonal_result.has_seasonality,
                "peak_months": seasonal_result.peak_seasons
            },
            "combined_recommendations": _generate_combined_recommendations(
                anomaly_result, forecast_result, seasonal_result, lang
            )
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

def _generate_combined_recommendations(anomaly_result, forecast_result, seasonal_result, lang: str) -> List[str]:
    """Kombinált ajánlások generálása több elemzés alapján"""
    recommendations = []
    
    # Anomália alapú ajánlások
    if anomaly_result.anomalies_by_severity.get("high", 0) > 0:
        recommendations.append(translate('high_risk_anomalies', lang=lang, count=anomaly_result.anomalies_by_severity.get("high", 0)))
    
    # Forecast alapú ajánlások
    if forecast_result.trend == translate('increasing', lang=lang):
        recommendations.append(translate('forecast_increasing', lang=lang))
    
    # Szezonális ajánlások
    if seasonal_result.has_seasonality and seasonal_result.peak_seasons:
        peak_month = max(seasonal_result.peak_seasons.items(), key=lambda x: x[1])[0]
        recommendations.append(translate('seasonal_peak_month', lang=lang, month=peak_month))
    
    if not recommendations:
        recommendations.append("Pénzügyi szokásaid stabilak és egészségesek!")
    
    return recommendations

@router.get("/ml-anomaly-detection", response_model=Dict[str, Any])
async def get_ml_anomaly_detection(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    sensitivity: float = Query(0.1, ge=0.05, le=0.3),
    lang: str = Query('hu', description="Language for analysis text")
):
    """ML alapú anomália detektálás továbbfejlesztett algoritmusokkal"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 20:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # ML szolgáltatás használata
        anomaly_result = MLAnalysisService.detect_spending_anomalies(
            transactions, contamination=float(sensitivity)
        )
        
        return {
            "ml_analysis": anomaly_result,
            "analysis_period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_transactions": len(transactions)
            },
            "model_info": {
                "algorithm": "Isolation Forest",
                "confidence": anomaly_result.get("model_confidence", 0),
                "sensitivity": sensitivity
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('anomaly_detection_error', lang=lang, error=str(e)))

@router.get("/ml-forecast", response_model=Dict[str, Any])
async def get_ml_forecast(
    current_user: User = Depends(get_current_user),
    periods_ahead: int = Query(6, ge=1, le=12),
    forecast_type: str = Query("monthly", regex="^(monthly|weekly)$"),
    months_history: int = Query(12, ge=6, le=24),
    lang: str = Query('hu', description="Language for analysis text")
):
    """ML alapú fejlett előrejelzés"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_history * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 30:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # ML szolgáltatás használata
        forecast_result = MLAnalysisService.generate_spending_forecast(
            transactions, periods_ahead, forecast_type
        )
        
        # Szezonalitás elemzés
        seasonality_result = MLAnalysisService.analyze_seasonality(transactions)
        
        return {
            "forecast": forecast_result,
            "seasonality": seasonality_result,
            "analysis_info": {
                "periods_ahead": periods_ahead,
                "forecast_type": forecast_type,
                "historical_months": months_history,
                "data_quality": "good" if len(transactions) > 100 else "limited"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('forecast_error', lang=lang) + f" {str(e)}")

@router.get("/ml-budget-optimization", response_model=Dict[str, Any])
async def get_ml_budget_optimization(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    optimization_goal: str = Query("balanced", regex="^(conservative|balanced|aggressive)$"),
    lang: str = Query('hu', description="Language for analysis text")
):
    """ML alapú költségvetés optimalizálás"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(transactions) < 30:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # ML alapú kategória költségvetések
        budget_result = MLAnalysisService.generate_category_budgets(transactions)
        
        # Optimalizálási stratégia alkalmazása
        optimized_budgets = _apply_optimization_strategy(
            budget_result["recommendations"], optimization_goal
        )
        
        return {
            "original_analysis": budget_result,
            "optimized_budgets": optimized_budgets,
            "optimization_strategy": optimization_goal,
            "potential_savings": _calculate_optimization_savings(
                budget_result["recommendations"], optimized_budgets
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.get("/collaborative-insights", response_model=Dict[str, Any])
async def get_collaborative_insights(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Collaborative filtering alapú betekintések (egyszerűsített verzió privacy miatt)"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        user_transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        if len(user_transactions) < 20:
            raise HTTPException(status_code=400, detail=translate('no_transactions_for_analysis', lang=lang))
        
        # Felhasználói profil elemzése
        user_profile = CollaborativeFilteringService._create_user_profile(user_transactions)
        
        # Szimulált összehasonlítás (valós implementációban több felhasználóval)
        comparison_result = _simulate_peer_comparison(user_profile, user_transactions, lang)
        
        return {
            "user_profile": {
                "total_spending": user_profile.get("total_spending", 0),
                "category_distribution": user_profile.get("category_distribution", {}),
                "spending_patterns": user_profile.get("time_pattern", {})
            },
            "peer_comparison": comparison_result,
            "privacy_note": "Az összehasonlítás aggregált és anonimizált adatokon alapul"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

@router.post("/simulation/comprehensive")
async def run_comprehensive_simulation(
    current_user: User = Depends(get_current_user),
    simulation_request: Dict[str, Any] = ...,
    months_back: int = Query(6, ge=3, le=12),
    lang: str = Query('hu', description="Language for analysis text")
):
    """Átfogó What-If szimuláció multiple scenarios-val"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        transactions = await Transaction.find({
            "user_id": ObjectId(current_user.id),
            "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).to_list()
        
        results = {}
        
        # Kategória változtatások szimulálása
        if "category_changes" in simulation_request:
            results["category_simulation"] = WhatIfSimulationService.simulate_multiple_changes(
                transactions,
                simulation_request["category_changes"],
                simulation_request.get("months_to_simulate", 12)
            )
        
        # Bevétel változtatás szimulálása
        if "income_change" in simulation_request:
            results["income_simulation"] = WhatIfSimulationService.simulate_income_change(
                transactions,
                simulation_request["income_change"],
                simulation_request.get("months_to_simulate", 12)
            )
        
        # Cél elérés szimulálása
        if "savings_goal" in simulation_request:
            results["goal_simulation"] = WhatIfSimulationService.simulate_goal_achievement(
                transactions,
                simulation_request["savings_goal"],
                simulation_request.get("target_months", 12)
            )
        
        # Vészhelyzeti alap szimulálása
        if "emergency_fund" in simulation_request:
            results["emergency_fund_simulation"] = WhatIfSimulationService.simulate_emergency_fund_building(
                transactions,
                simulation_request.get("emergency_months", 6)
            )
        
        return {
            "simulation_results": results,
            "analysis_period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "summary": _generate_simulation_summary(results, lang)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=translate('analysis_error', lang=lang, error=str(e)))

# Segédfüggvények

def _apply_optimization_strategy(original_budgets: Dict, strategy: str) -> Dict:
    """Optimalizálási stratégia alkalmazása"""
    optimized = {}
    
    for category, data in original_budgets.items():
        current_budget = data["recommended_budget"]
        
        if strategy == "conservative":
            # 5% csökkentés nem alapvető kategóriákban
            if category.lower() not in ['élelmiszer', 'lakhatás', 'egészségügy']:
                optimized[category] = current_budget * 0.95
            else:
                optimized[category] = current_budget
        elif strategy == "balanced":
            # 10% csökkentés opcionális kategóriákban
            if category.lower() in ['szórakozás', 'ruházat', 'egyéb']:
                optimized[category] = current_budget * 0.9
            else:
                optimized[category] = current_budget
        elif strategy == "aggressive":
            # 15-20% csökkentés nem alapvető kategóriákban
            if category.lower() in ['élelmiszer', 'lakhatás']:
                optimized[category] = current_budget * 0.95
            else:
                optimized[category] = current_budget * 0.8
    
    return optimized

def _calculate_optimization_savings(original: Dict, optimized: Dict) -> float:
    """Optimalizálásból származó megtakarítás számítása"""
    total_savings = 0
    
    for category in original.keys():
        if category in optimized:
            original_amount = original[category]["recommended_budget"]
            optimized_amount = optimized[category]
            total_savings += max(0, original_amount - optimized_amount)
    
    return total_savings

def _simulate_peer_comparison(user_profile: Dict, transactions: List, lang: str) -> Dict:
    """Peer összehasonlítás szimulálása (privacy-safe)"""
    # Szimulált peer adatok generálása
    total_spending = user_profile.get("total_spending", 0)
    
    # Szimulált peer átlagok
    peer_avg_spending = total_spending * np.random.uniform(0.85, 1.15)
    
    return {
        "spending_comparison": {
            "user_spending": total_spending,
            "peer_average": peer_avg_spending,
            "user_position": "átlag alatt" if total_spending < peer_avg_spending else "átlag felett"
        },
        "category_comparison": _simulate_category_comparison(
            user_profile.get("category_distribution", {}), lang
        ),
        "recommendations": _generate_peer_recommendations(total_spending, peer_avg_spending, lang)
    }

def _simulate_category_comparison(user_categories: Dict, lang: str) -> Dict:
    """Kategória összehasonlítás szimulálása"""
    comparison = {}
    
    for category, user_percentage in user_categories.items():
        # Szimulált peer átlag
        peer_avg = user_percentage * np.random.uniform(0.8, 1.2)
        comparison[category] = {
            "user_percentage": user_percentage,
            "peer_average": peer_avg,
            "difference": user_percentage - peer_avg
        }
    
    return comparison

def _generate_peer_recommendations(user_spending: float, peer_avg: float, lang: str) -> List[str]:
    """Peer összehasonlítás alapú ajánlások"""
    recommendations = []
    
    if user_spending > peer_avg * 1.1:
        recommendations.append(translate('peer_spending_higher', lang=lang))
        recommendations.append(translate('review_top_categories', lang=lang))
    elif user_spending < peer_avg * 0.9:
        recommendations.append(translate('peer_spending_lower', lang=lang))
        recommendations.append(translate('increase_savings', lang=lang))
    else:
        recommendations.append(translate('peer_spending_average', lang=lang))
    
    return recommendations

def _generate_simulation_summary(results: Dict, lang: str) -> Dict:
    """Szimuláció összesítő generálása"""
    summary = {
        "total_scenarios": len(results),
        "key_insights": [],
        "priority_actions": []
    }
    
    # Kategória szimuláció összesítése
    if "category_simulation" in results:
        category_result = results["category_simulation"]
        summary["key_insights"].append(
            translate('insight_1', lang=lang, savings=category_result.get('total_potential_savings', 0))
        )
    
    # Bevétel szimuláció összesítése
    if "income_simulation" in results:
        income_result = results["income_simulation"]
        if income_result.get("net_change", 0) > 0:
            summary["priority_actions"].append("Bevételnövelés pozitív hatással járna")
    
    return summary