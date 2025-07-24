# app/routes/analysis.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import calendar
from statistics import mean
from bson import ObjectId

from app.models.transaction import Transaction
from app.models.user import User
from app.models.account import AllUserAccountsDocument
from app.core.security import get_current_user

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

@router.get("/comprehensive", response_model=FinancialAnalysis)
async def get_comprehensive_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(12, ge=1, le=24, description="Hány hónapra visszamenőleg elemezzen")
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
            raise HTTPException(status_code=404, detail="Nincs elegendő tranzakció az elemzéshez")

        # 1. Alapvető statisztikák
        basic_stats = await _calculate_basic_stats(transactions)
        
        # 2. Cashflow elemzés
        cashflow_analysis = await _analyze_cashflow(transactions)
        
        # 3. Kategória elemzés
        category_analysis = await _analyze_categories(transactions)
        
        # 4. Időbeli elemzés
        time_analysis = await _analyze_time_patterns(transactions)
        
        # 5. Kockázatelemzés
        risk_analysis = await _analyze_risk(transactions, current_user.id)
        
        # 6. Ajánlások generálása
        recommendations = await _generate_recommendations(
            basic_stats, cashflow_analysis, category_analysis, risk_analysis
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
        raise HTTPException(status_code=500, detail=f"Elemzési hiba: {str(e)}")

async def _calculate_basic_stats(transactions: List[Transaction]) -> BasicStats:
    """Alapvető statisztikák számítása"""
    if not transactions:
        return BasicStats(
            total_income=0, total_expense=0, net_balance=0,
            daily_avg_expense=0, monthly_avg_expense=0,
            most_active_day="Hétfő", most_active_hour=12, transaction_count=0
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
    
    most_active_day = Counter(weekdays).most_common(1)[0][0] if weekdays else "Hétfő"
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

async def _analyze_cashflow(transactions: List[Transaction]) -> CashflowAnalysis:
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
            trend = "növekvő"
        elif all(recent_nets[i] >= recent_nets[i+1] for i in range(len(recent_nets)-1)):
            trend = "csökkenő"
        else:
            trend = "stabil"
    else:
        trend = "stabil"
    
    return CashflowAnalysis(
        monthly_trends=monthly_trends,
        weekly_trends=weekly_trends,
        overall_trend=trend
    )

async def _analyze_categories(transactions: List[Transaction]) -> CategoryAnalysis:
    """Kategória elemzés"""
    category_data = defaultdict(lambda: {"income": 0, "expense": 0, "count": 0})
    
    for t in transactions:
        cat = t.kategoria or "Egyéb"
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
        "Élelmiszer", "Lakhatás", "Közlekedés", "Egészségügy", 
        "Szórakozás", "Ruházat", "Kommunikáció", "Oktatás"
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

async def _analyze_time_patterns(transactions: List[Transaction]) -> TimeAnalysis:
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
    peak_spending_day = max(by_weekday.items(), key=lambda x: x[1])[0] if by_weekday else "Hétfő"
    peak_spending_hour = max(by_hour.items(), key=lambda x: x[1])[0] if by_hour else 12
    
    return TimeAnalysis(
        by_weekday=by_weekday,
        by_hour=by_hour,
        peak_spending_day=peak_spending_day,
        peak_spending_hour=peak_spending_hour
    )

async def _analyze_risk(transactions: List[Transaction], user_id: str) -> RiskAnalysis:
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
        risk_level = "magas"
    elif risk_score >= 3:
        risk_level = "közepes"
    else:
        risk_level = "alacsony"
    
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
    risk_analysis: RiskAnalysis
) -> Recommendations:
    """Személyre szabott ajánlások generálása"""
    
    savings_suggestions = []
    cost_optimization_tips = []
    emergency_fund_advice = []
    debt_management_advice = []
    
    # Megtakarítási javaslatok
    if risk_analysis.savings_rate < 0.1:
        savings_suggestions.append("Próbálj meg legalább 10%-ot megtakarítani a bevételeidből")
        savings_suggestions.append("Állíts be automatikus megtakarítást minden hónap elején")
    elif risk_analysis.savings_rate < 0.2:
        savings_suggestions.append("Remek! Próbáld növelni a megtakarítási rátád 20%-ra")
    else:
        savings_suggestions.append("Kiváló megtakarítási szokásaid vannak!")
    
    # Költségoptimalizálás
    if category_analysis.top_expense_categories:
        top_cat = category_analysis.top_expense_categories[0]
        cost_optimization_tips.append(f"A legnagyobb kiadásod: {top_cat['category']}. Érdemes átnézni ezeket a költségeket")
    
    if basic_stats.daily_avg_expense > basic_stats.total_income / 365:
        cost_optimization_tips.append("Napi kiadásaid magasak a bevételeidhez képest")
        cost_optimization_tips.append("Készíts költségvetést és kövesd a napi kiadásaidat")
    
    # Vészhelyzeti alap
    if risk_analysis.emergency_fund_months < 3:
        emergency_fund_advice.append("Építs fel legalább 3 havi kiadásnak megfelelő vészhelyzeti alapot")
        emergency_fund_advice.append("Havonta tegyél félre egy kisebb összeget erre a célra")
    elif risk_analysis.emergency_fund_months < 6:
        emergency_fund_advice.append("Jó úton vagy! Próbáld növelni 6 hónapra a vészhelyzeti alapot")
    else:
        emergency_fund_advice.append("Kiváló vészhelyzeti alapod van!")
    
    # Adósságkezelés
    if risk_analysis.debt_income_ratio > 0.3:
        debt_management_advice.append("Adósságaid magasak a bevételeidhez képest")
        debt_management_advice.append("Prioritást adj az adósságok törlesztésének")
        debt_management_advice.append("Fontolj meg adósság-konszolidációt")
    elif risk_analysis.debt_income_ratio > 0.1:
        debt_management_advice.append("Törekedj az adósságok fokozatos csökkentésére")
    else:
        debt_management_advice.append("Jól kezeled az adósságaidat!")
    
    return Recommendations(
        savings_suggestions=savings_suggestions,
        cost_optimization_tips=cost_optimization_tips,
        emergency_fund_advice=emergency_fund_advice,
        debt_management_advice=debt_management_advice
    )

@router.get("/basic-stats", response_model=BasicStats)
async def get_basic_stats(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=1, le=24)
):
    """Alapvető statisztikák lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _calculate_basic_stats(transactions)

@router.get("/risk-analysis", response_model=RiskAnalysis)
async def get_risk_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(12, ge=1, le=24)
):
    """Kockázatelemzés lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _analyze_risk(transactions, current_user.id)

@router.get("/category-analysis", response_model=CategoryAnalysis)
async def get_category_analysis(
    current_user: User = Depends(get_current_user),
    months_back: int = Query(6, ge=1, le=24)
):
    """Kategóriaelemzés lekérése"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    
    transactions = await Transaction.find({
        "user_id": ObjectId(current_user.id),
        "date": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }).to_list()
    
    return await _analyze_categories(transactions)