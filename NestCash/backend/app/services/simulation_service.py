# app/services/simulation_service.py
"""
What-If szimulációs szolgáltatások
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

class WhatIfSimulationService:
    """What-If szimulációs szolgáltatások"""
    
    @staticmethod
    def simulate_category_spending_change(
        transactions: List[Transaction], 
        category: str, 
        new_monthly_amount: float,
        months_to_simulate: int = 12
    ) -> Dict:
        """Kategória költés változtatásának szimulálása"""
        
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'category': t.kategoria or 'Egyéb',
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        expense_df = df[df['is_expense']].copy()
        
        # Eredeti kategória költés
        category_expenses = expense_df[expense_df['category'] == category]
        
        if len(category_expenses) == 0:
            original_monthly_avg = 0
        else:
            monthly_totals = category_expenses.groupby(category_expenses['date'].dt.to_period('M'))['amount'].sum()
            original_monthly_avg = abs(monthly_totals.mean()) if len(monthly_totals) > 0 else 0
        
        # Szimuláció
        monthly_change = new_monthly_amount - original_monthly_avg
        total_change_per_year = monthly_change * 12
        
        # Egyéb statisztikák
        total_monthly_expenses = abs(expense_df.groupby(expense_df['date'].dt.to_period('M'))['amount'].sum().mean())
        
        # Hatás számítása
        impact_percentage = (monthly_change / total_monthly_expenses * 100) if total_monthly_expenses > 0 else 0
        
        # Megtakarítási potenciál
        if monthly_change < 0:  # Csökkentés
            potential_savings = abs(monthly_change) * months_to_simulate
            savings_impact = "positive"
        else:  # Növelés
            potential_savings = -(monthly_change * months_to_simulate)
            savings_impact = "negative"
        
        return {
            "category": category,
            "original_monthly_avg": float(original_monthly_avg),
            "new_monthly_amount": float(new_monthly_amount),
            "monthly_change": float(monthly_change),
            "annual_change": float(total_change_per_year),
            "impact_percentage": float(impact_percentage),
            "potential_savings": float(potential_savings),
            "savings_impact": savings_impact,
            "months_simulated": months_to_simulate,
            "recommendation": WhatIfSimulationService._generate_category_recommendation(
                category, monthly_change, impact_percentage
            )
        }
    
    @staticmethod
    def simulate_multiple_changes(
        transactions: List[Transaction],
        changes: Dict[str, float],  # category -> new_monthly_amount
        months_to_simulate: int = 12
    ) -> Dict:
        """Több kategória egyidejű változtatásának szimulálása"""
        
        individual_results = []
        total_monthly_change = 0
        total_potential_savings = 0
        
        for category, new_amount in changes.items():
            result = WhatIfSimulationService.simulate_category_spending_change(
                transactions, category, new_amount, months_to_simulate
            )
            individual_results.append(result)
            total_monthly_change += result["monthly_change"]
            total_potential_savings += result["potential_savings"]
        
        # Összesített hatás
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        expense_df = df[df['is_expense']].copy()
        total_monthly_expenses = abs(expense_df.groupby(expense_df['date'].dt.to_period('M'))['amount'].sum().mean())
        
        overall_impact_percentage = (total_monthly_change / total_monthly_expenses * 100) if total_monthly_expenses > 0 else 0
        
        return {
            "individual_changes": individual_results,
            "total_monthly_change": float(total_monthly_change),
            "total_annual_change": float(total_monthly_change * 12),
            "total_potential_savings": float(total_potential_savings),
            "overall_impact_percentage": float(overall_impact_percentage),
            "months_simulated": months_to_simulate,
            "feasibility_score": WhatIfSimulationService._calculate_feasibility_score(
                individual_results, overall_impact_percentage
            ),
            "recommendations": WhatIfSimulationService._generate_multi_change_recommendations(
                individual_results, overall_impact_percentage
            )
        }
    
    @staticmethod
    def simulate_income_change(
        transactions: List[Transaction],
        new_monthly_income: float,
        months_to_simulate: int = 12
    ) -> Dict:
        """Bevétel változásának szimulálása"""
        
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'is_income': t.amount > 0,
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Eredeti bevétel
        income_df = df[df['is_income']].copy()
        if len(income_df) > 0:
            monthly_income_totals = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum()
            original_monthly_income = monthly_income_totals.mean()
        else:
            original_monthly_income = 0
        
        # Kiadások
        expense_df = df[df['is_expense']].copy()
        if len(expense_df) > 0:
            monthly_expense_totals = expense_df.groupby(expense_df['date'].dt.to_period('M'))['amount'].sum()
            avg_monthly_expenses = abs(monthly_expense_totals.mean())
        else:
            avg_monthly_expenses = 0
        
        # Változások számítása
        income_change = new_monthly_income - original_monthly_income
        
        # Új pénzügyi helyzet
        new_monthly_net = new_monthly_income - avg_monthly_expenses
        original_monthly_net = original_monthly_income - avg_monthly_expenses
        
        net_change = new_monthly_net - original_monthly_net
        
        # Megtakarítási ráta
        new_savings_rate = (new_monthly_net / new_monthly_income * 100) if new_monthly_income > 0 else 0
        original_savings_rate = (original_monthly_net / original_monthly_income * 100) if original_monthly_income > 0 else 0
        
        return {
            "original_monthly_income": float(original_monthly_income),
            "new_monthly_income": float(new_monthly_income),
            "income_change": float(income_change),
            "avg_monthly_expenses": float(avg_monthly_expenses),
            "new_monthly_net": float(new_monthly_net),
            "original_monthly_net": float(original_monthly_net),
            "net_change": float(net_change),
            "new_savings_rate": float(new_savings_rate),
            "original_savings_rate": float(original_savings_rate),
            "annual_net_change": float(net_change * 12),
            "months_simulated": months_to_simulate,
            "financial_health_improvement": WhatIfSimulationService._assess_financial_health_change(
                original_savings_rate, new_savings_rate, net_change
            )
        }
    
    @staticmethod
    def simulate_goal_achievement(
        transactions: List[Transaction],
        savings_goal: float,
        target_months: int,
        current_monthly_savings: Optional[float] = None
    ) -> Dict:
        """Megtakarítási cél elérésének szimulálása"""
        
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'is_income': t.amount > 0,
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Jelenlegi pénzügyi helyzet
        income_df = df[df['is_income']].copy()
        expense_df = df[df['is_expense']].copy()
        
        if len(income_df) > 0:
            monthly_income = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum().mean()
        else:
            monthly_income = 0
            
        if len(expense_df) > 0:
            monthly_expenses = abs(expense_df.groupby(expense_df['date'].dt.to_period('M'))['amount'].sum().mean())
        else:
            monthly_expenses = 0
        
        current_net = monthly_income - monthly_expenses
        
        if current_monthly_savings is None:
            current_monthly_savings = max(0, current_net)
        
        #