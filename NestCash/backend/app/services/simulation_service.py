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
        
        # A meglévő simulation_service.py folytatása - add hozzá a fájl végéhez

        # Szükséges havi megtakarítás a cél eléréséhez
        required_monthly_savings = savings_goal / target_months
        
        # Jelenlegi helyzet vs. cél
        savings_gap = required_monthly_savings - current_monthly_savings
        
        # Szcenáriók elemzése
        scenarios = []
        
        if savings_gap <= 0:
            # Már elérhető a cél
            scenarios.append({
                "name": "Jelenlegi ütemben",
                "required_change": 0,
                "probability": "magas",
                "description": "Jelenlegi megtakarítási ütemben elérhető a cél"
            })
        else:
            # Kiadások csökkentése szükséges
            current_expense_ratio = monthly_expenses / monthly_income if monthly_income > 0 else 1
            
            # Konzervatív: 5% kiadáscsökkentés
            conservative_reduction = monthly_expenses * 0.05
            if conservative_reduction >= savings_gap:
                scenarios.append({
                    "name": "Konzervatív kiadáscsökkentés",
                    "required_change": -conservative_reduction,
                    "probability": "magas",
                    "description": f"5% kiadáscsökkentéssel ({conservative_reduction:.0f} Ft/hó)"
                })
            
            # Közepes: 10% kiadáscsökkentés
            moderate_reduction = monthly_expenses * 0.10
            if moderate_reduction >= savings_gap:
                scenarios.append({
                    "name": "Közepes kiadáscsökkentés",
                    "required_change": -moderate_reduction,
                    "probability": "közepes",
                    "description": f"10% kiadáscsökkentéssel ({moderate_reduction:.0f} Ft/hó)"
                })
            
            # Agresszív: 20% kiadáscsökkentés
            aggressive_reduction = monthly_expenses * 0.20
            scenarios.append({
                "name": "Agresszív kiadáscsökkentés",
                "required_change": -aggressive_reduction,
                "probability": "alacsony" if aggressive_reduction < savings_gap else "közepes",
                "description": f"20% kiadáscsökkentéssel ({aggressive_reduction:.0f} Ft/hó)"
            })
            
            # Bevétel növelés
            required_income_increase = savings_gap
            scenarios.append({
                "name": "Bevételnövelés",
                "required_change": required_income_increase,
                "probability": "változó",
                "description": f"Havi bevétel növelése {required_income_increase:.0f} Ft-tal"
            })
        
        # Időbecslés különböző szcenáriókra
        time_estimates = {}
        for scenario in scenarios:
            if scenario["required_change"] == 0:
                time_estimates[scenario["name"]] = target_months
            else:
                # Egyszerűsített számítás
                new_monthly_savings = current_monthly_savings + abs(scenario["required_change"])
                estimated_months = savings_goal / max(new_monthly_savings, 1)
                time_estimates[scenario["name"]] = int(estimated_months)
        
        return {
            "savings_goal": float(savings_goal),
            "target_months": target_months,
            "current_monthly_income": float(monthly_income),
            "current_monthly_expenses": float(monthly_expenses),
            "current_monthly_savings": float(current_monthly_savings),
            "required_monthly_savings": float(required_monthly_savings),
            "savings_gap": float(savings_gap),
            "scenarios": scenarios,
            "time_estimates": time_estimates,
            "goal_achievable": any(s["probability"] in ["magas", "közepes"] for s in scenarios),
            "recommendations": WhatIfSimulationService._generate_goal_recommendations(
                savings_gap, current_expense_ratio, monthly_income
            )
        }
    
    @staticmethod
    def simulate_emergency_fund_building(
        transactions: List[Transaction],
        target_months: int = 6,
        monthly_expenses: Optional[float] = None
    ) -> Dict:
        """Vészhelyzeti alap felépítésének szimulálása"""
        
        df = pd.DataFrame([{
            'date': t.date,
            'amount': t.amount,
            'is_income': t.amount > 0,
            'is_expense': t.amount < 0
        } for t in transactions])
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Havi kiadások átlaga
        if monthly_expenses is None:
            expense_df = df[df['is_expense']].copy()
            if len(expense_df) > 0:
                monthly_expense_totals = expense_df.groupby(expense_df['date'].dt.to_period('M'))['amount'].sum()
                monthly_expenses = abs(monthly_expense_totals.mean())
            else:
                monthly_expenses = 0
        
        # Cél összeg
        target_amount = monthly_expenses * target_months
        
        # Jelenlegi megtakarítási kapacitás
        income_df = df[df['is_income']].copy()
        if len(income_df) > 0:
            monthly_income_totals = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum()
            monthly_income = monthly_income_totals.mean()
        else:
            monthly_income = 0
        
        # Nettó megtakarítási kapacitás
        net_monthly_capacity = monthly_income - monthly_expenses
        
        # Különböző megtakarítási stratégiák
        strategies = []
        
        # 1. Jelenlegi kapacitás alapján
        if net_monthly_capacity > 0:
            months_needed = target_amount / net_monthly_capacity
            strategies.append({
                "strategy": "Jelenlegi nettó kapacitás",
                "monthly_amount": float(net_monthly_capacity),
                "months_to_complete": int(months_needed),
                "total_saved": float(target_amount),
                "feasibility": "reális" if months_needed <= 24 else "hosszú távú"
            })
        
        # 2. 10% megtakarítási ráta
        ten_percent_savings = monthly_income * 0.1
        if ten_percent_savings > 0:
            months_needed = target_amount / ten_percent_savings
            strategies.append({
                "strategy": "10% megtakarítási ráta",
                "monthly_amount": float(ten_percent_savings),
                "months_to_complete": int(months_needed),
                "total_saved": float(target_amount),
                "feasibility": "közepes" if months_needed <= 36 else "kihívás"
            })
        
        # 3. 20% megtakarítási ráta
        twenty_percent_savings = monthly_income * 0.2
        if twenty_percent_savings > 0:
            months_needed = target_amount / twenty_percent_savings
            strategies.append({
                "strategy": "20% megtakarítási ráta",
                "monthly_amount": float(twenty_percent_savings),
                "months_to_complete": int(months_needed),
                "total_saved": float(target_amount),
                "feasibility": "agresszív" if months_needed <= 24 else "nagyon nehéz"
            })
        
        # Ajánlott stratégia
        if strategies:
            recommended = min(strategies, key=lambda x: abs(x["months_to_complete"] - target_months * 2))
        else:
            recommended = None
        
        return {
            "target_emergency_fund": float(target_amount),
            "target_months_coverage": target_months,
            "monthly_expenses": float(monthly_expenses),
            "monthly_income": float(monthly_income),
            "current_savings_capacity": float(net_monthly_capacity),
            "strategies": strategies,
            "recommended_strategy": recommended,
            "priority_level": WhatIfSimulationService._assess_emergency_fund_priority(
                target_amount, net_monthly_capacity, monthly_expenses
            )
        }
    
    @staticmethod
    def _generate_category_recommendation(category: str, monthly_change: float, impact_percentage: float) -> str:
        """Kategória-specifikus ajánlás generálása"""
        if monthly_change < 0:  # Csökkentés
            if abs(impact_percentage) > 20:
                return f"Nagy hatású csökkentés a {category} kategóriában - alaposan tervezd meg!"
            elif category.lower() in ['élelmiszer', 'lakhatás']:
                return f"Óvatosan csökkentsd a {category} kiadásokat - ezek alapvető szükségletek"
            else:
                return f"Reális csökkentés a {category} kategóriában"
        else:  # Növelés
            return f"A {category} kategória növelése {monthly_change:.0f} Ft-tal havonta"
    
    @staticmethod
    def _calculate_feasibility_score(individual_results: List[Dict], overall_impact: float) -> float:
        """Megvalósíthatósági pontszám számítása"""
        base_score = 100
        
        # Nagy változások csökkentik a megvalósíthatóságot
        for result in individual_results:
            change_magnitude = abs(result["impact_percentage"])
            if change_magnitude > 30:
                base_score -= 20
            elif change_magnitude > 20:
                base_score -= 10
            elif change_magnitude > 10:
                base_score -= 5
        
        # Túl sok változás nehezebb
        if len(individual_results) > 5:
            base_score -= 15
        elif len(individual_results) > 3:
            base_score -= 10
        
        # Összesített hatás
        if abs(overall_impact) > 30:
            base_score -= 20
        elif abs(overall_impact) > 20:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    @staticmethod
    def _generate_multi_change_recommendations(individual_results: List[Dict], overall_impact: float) -> List[str]:
        """Több kategória változtatásához ajánlások"""
        recommendations = []
        
        # Összesített hatás alapján
        if overall_impact < -30:
            recommendations.append("Nagy költségcsökkentést tervezel - fokozatosan vezess be!")
        elif overall_impact > 30:
            recommendations.append("Jelentős költségnövekedés - ellenőrizd a fedezetet!")
        
        # Kategóriák száma alapján
        if len(individual_results) > 5:
            recommendations.append("Sok kategóriát érintesz egyszerre - kezdj a legfontosabbakkal!")
        
        # Megvalósíthatóság alapján
        high_impact_changes = [r for r in individual_results if abs(r["impact_percentage"]) > 20]
        if high_impact_changes:
            recommendations.append(f"{len(high_impact_changes)} nagy hatású változtatást tervezel")
        
        if not recommendations:
            recommendations.append("Reális változtatásokat tervezel!")
        
        return recommendations
    
    @staticmethod
    def _assess_financial_health_change(original_rate: float, new_rate: float, net_change: float) -> Dict:
        """Pénzügyi egészség változásának értékelése"""
        improvement = {
            "savings_rate_change": new_rate - original_rate,
            "monthly_net_change": net_change,
            "overall_assessment": "unchanged"
        }
        
        if new_rate > original_rate + 5:
            improvement["overall_assessment"] = "jelentős javulás"
        elif new_rate > original_rate + 2:
            improvement["overall_assessment"] = "javulás"
        elif new_rate < original_rate - 5:
            improvement["overall_assessment"] = "romlás"
        elif new_rate < original_rate - 2:
            improvement["overall_assessment"] = "enyhe romlás"
        
        # Ajánlások
        recommendations = []
        if new_rate < 10:
            recommendations.append("Megtakarítási rátád még mindig alacsony")
        elif new_rate > 30:
            recommendations.append("Kiváló megtakarítási ráta!")
        
        if net_change > 0:
            recommendations.append("Pozitív pénzügyi változás!")
        
        improvement["recommendations"] = recommendations
        return improvement
    
    @staticmethod
    def _generate_goal_recommendations(savings_gap: float, expense_ratio: float, monthly_income: float) -> List[str]:
        """Cél elérési ajánlások"""
        recommendations = []
        
        if savings_gap <= 0:
            recommendations.append("Jelenlegi ütemben elérhető a cél!")
        else:
            gap_percentage = (savings_gap / monthly_income * 100) if monthly_income > 0 else 100
            
            if gap_percentage < 5:
                recommendations.append("Kis kiigazítással elérhető a cél")
            elif gap_percentage < 15:
                recommendations.append("Közepes erőfeszítéssel elérhető")
            else:
                recommendations.append("Jelentős változtatások szükségesek")
            
            # Konkrét javaslatok
            if expense_ratio > 0.8:
                recommendations.append("Magas a kiadási arányod - fókuszálj a költségcsökkentésre")
            else:
                recommendations.append("Bevételnövelés is segíthet a cél elérésében")
        
        return recommendations
    
    @staticmethod
    def _assess_emergency_fund_priority(target: float, capacity: float, expenses: float) -> str:
        """Vészhelyzeti alap prioritásának értékelése"""
        if capacity <= 0:
            return "kritikus - nincs megtakarítási kapacitás"
        
        months_to_complete = target / capacity
        
        if months_to_complete <= 12:
            return "magas - gyorsan felépíthető"
        elif months_to_complete <= 24:
            return "közepes - reális időkeretben"
        else:
            return "alacsony - hosszú távú cél"