"""
Financial modeling for real estate investments.

This module provides classes for loan calculations, investment analysis,
and risk simulation (Monte Carlo).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class LoanDetails:
    """Data class for loan details."""
    amount: float
    interest_rate: float  # Annual interest rate (e.g., 0.08 for 8%)
    term_years: int
    monthly_payment: float
    total_payment: float
    total_interest: float


class LoanCalculator:
    """Calculator for mortgage loans."""
    
    @staticmethod
    def calculate_loan(amount: float, interest_rate: float, term_years: int) -> LoanDetails:
        """
        Calculate loan details.
        
        Args:
            amount: Loan principal amount
            interest_rate: Annual interest rate (0.0 - 1.0)
            term_years: Loan term in years
            
        Returns:
            LoanDetails object
        """
        if amount <= 0:
            return LoanDetails(0, 0, 0, 0, 0, 0)
        
        monthly_rate = interest_rate / 12
        num_payments = term_years * 12
        
        if monthly_rate == 0:
            monthly_payment = amount / num_payments
        else:
            monthly_payment = (amount * monthly_rate * (1 + monthly_rate)**num_payments) / \
                              ((1 + monthly_rate)**num_payments - 1)
        
        total_payment = monthly_payment * num_payments
        total_interest = total_payment - amount
        
        return LoanDetails(
            amount=amount,
            interest_rate=interest_rate,
            term_years=term_years,
            monthly_payment=monthly_payment,
            total_payment=total_payment,
            total_interest=total_interest
        )


class InvestmentAnalyzer:
    """Analyzer for real estate investment returns."""
    
    def __init__(
        self,
        purchase_price: float,
        monthly_rent: float,
        renovation_cost: float = 0,
        stamp_duty_rate: float = 0.04,
        monthly_expenses: float = 0,
        vacancy_rate: float = 0.05,
        loan_details: LoanDetails = None
    ):
        """
        Initialize investment analyzer.
        
        Args:
            purchase_price: Property purchase price
            monthly_rent: Speculated monthly rent
            renovation_cost: Cost of renovation
            stamp_duty_rate: Stamp duty percentage (usually 4%)
            monthly_expenses: Common cost, insurance, tax, maintenance
            vacancy_rate: Expected vacancy rate (0.0 - 1.0)
            loan_details: LoanDetails object (optional)
        """
        self.purchase_price = purchase_price
        self.monthly_rent = monthly_rent
        self.renovation_cost = renovation_cost
        self.stamp_duty = purchase_price * stamp_duty_rate
        self.total_investment = purchase_price + renovation_cost + self.stamp_duty
        
        self.monthly_expenses = monthly_expenses
        self.vacancy_loss = monthly_rent * vacancy_rate
        
        self.loan = loan_details
        
        # Calculate own cash invested (Equity)
        if self.loan:
            self.own_cash = self.total_investment - self.loan.amount
        else:
            self.own_cash = self.total_investment
            
    def calculate_metrics(self) -> Dict:
        """
        Calculate key financial metrics.
        
        Returns:
            Dictionary with metrics (Cashflow, ROI, Yield, etc.)
        """
        # Income
        effective_gross_income = (self.monthly_rent - self.vacancy_loss) * 12
        
        # Expenses
        annual_expenses = self.monthly_expenses * 12
        net_operating_income = effective_gross_income - annual_expenses
        
        # Debt Service
        annual_debt_service = (self.loan.monthly_payment * 12) if self.loan else 0
        
        # Cashflow
        annual_cashflow = net_operating_income - annual_debt_service
        monthly_cashflow = annual_cashflow / 12
        
        # Returns
        gross_yield = (self.monthly_rent * 12) / self.purchase_price
        cap_rate = net_operating_income / self.purchase_price # Capitalization Rate
        
        # Cash on Cash Return (ROI)
        if self.own_cash > 0:
            cash_on_cash_return = annual_cashflow / self.own_cash
        else:
            cash_on_cash_return = 0
            
        return {
            "own_cash_invested": self.own_cash,
            "total_cost": self.total_investment,
            "monthly_cashflow": monthly_cashflow,
            "annual_cashflow": annual_cashflow,
            "gross_yield_percent": gross_yield * 100,
            "cap_rate_percent": cap_rate * 100,
            "cash_on_cash_roi_percent": cash_on_cash_return * 100,
            "break_even_point_years": (self.own_cash / annual_cashflow) if annual_cashflow > 0 else float('inf')
        }


class RiskSimulator:
    """Monte Carlo simulator for investment risk analysis."""
    
    def __init__(self, analyzer: InvestmentAnalyzer):
        self.base_analyzer = analyzer
    
    def run_simulation(self, n_simulations: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation varying key parameters.
        
        Varies:
        - Vacancy rate (Beta distribution)
        - Monthly rent (Normal distribution)
        - Expenses (Normal distribution)
        - Appreciation (Normal distribution)
        
        Returns:
            Simulation results summary
        """
        results_roi = []
        results_cashflow = []
        
        base_rent = self.base_analyzer.monthly_rent
        base_vacancy = 0.05
        base_expenses = self.base_analyzer.monthly_expenses
        
        for _ in range(n_simulations):
            # 1. Randomize Rent (+/- 10%)
            sim_rent = np.random.normal(base_rent, base_rent * 0.1)
            
            # 2. Randomize Vacancy (skewed towards 0-10%)
            # Alpha=2, Beta=20 gives mean around ~0.09
            sim_vacancy = np.random.beta(2, 20) 
            
            # 3. Randomize Expenses (+/- 20%)
            sim_expenses = np.random.normal(base_expenses, base_expenses * 0.2)
            
            # Create temp analyzer
            analyzer = InvestmentAnalyzer(
                purchase_price=self.base_analyzer.purchase_price,
                monthly_rent=sim_rent,
                renovation_cost=self.base_analyzer.renovation_cost,
                monthly_expenses=sim_expenses,
                vacancy_rate=sim_vacancy,
                loan_details=self.base_analyzer.loan
            )
            
            metrics = analyzer.calculate_metrics()
            results_roi.append(metrics["cash_on_cash_roi_percent"])
            results_cashflow.append(metrics["monthly_cashflow"])
            
        results_roi = np.array(results_roi)
        results_cashflow = np.array(results_cashflow)
        
        return {
            "roi_mean": np.mean(results_roi),
            "roi_median": np.median(results_roi),
            "roi_std": np.std(results_roi),
            "roi_5th_percentile": np.percentile(results_roi, 5),  # Worst case
            "roi_95th_percentile": np.percentile(results_roi, 95), # Best case
            
            "cashflow_mean": np.mean(results_cashflow),
            "probability_positive_cashflow": np.sum(results_cashflow > 0) / n_simulations * 100
        }
