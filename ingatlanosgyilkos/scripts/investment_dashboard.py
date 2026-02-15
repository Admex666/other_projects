#!/usr/bin/env python3
"""
Generate comprehensive investment analysis dashboard (Report).

This script combines sales and rental data, performs financial modeling,
and generates a readable report on the best investment opportunities.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.financial import InvestmentAnalyzer, LoanCalculator, RiskSimulator
from src.market_analysis import MarketAnalyzer


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Real Estate Investment Dashboard")
    parser.add_argument('--rent-data', type=Path, default=Path('data/raw/zenga_rentals_details.csv'), help='Rental data CSV')
    parser.add_argument('--sales-data', type=Path, default=Path('data/raw/zenga_sales_details.csv'), help='Sales data CSV')
    parser.add_argument('--own-cash', type=float, default=20000000, help='Own cash available (Ft)')
    parser.add_argument('--loan-rate', type=float, default=0.07, help='Loan interest rate (e.g. 0.07 for 7%)')
    parser.add_argument('--loan-term', type=int, default=20, help='Loan term in years')
    parser.add_argument('--output', type=Path, default=Path('results/investment_report.md'), help='Output report file')
    return parser.parse_args()


def calculate_price_per_m2_safe(df):
    """Safely calculate price per m2 if missing."""
    # Ensure numeric types
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['area_m2'] = pd.to_numeric(df['area_m2'], errors='coerce')
    
    if 'price_per_m2' not in df.columns:
        df['price_per_m2'] = df['price'] / df['area_m2']
    return df


def main():
    args = parse_args()
    
    # 1. Load Data
    print("📂 Loading data...")
    if not args.rent_data.exists():
        print(f"❌ Rental data not found at {args.rent_data}")
        # Fallback for demonstration if file missing (user might not have scraped yet)
        print("⚠️  Creating dummy data for demonstration purposes...")
        rentals = pd.DataFrame({
            'kerület': [6, 6, 8, 8, 13, 13],
            'price': [250000, 300000, 180000, 200000, 220000, 240000],
            'area_m2': [40, 55, 35, 45, 40, 50],
            'location': ['VI. kerület', 'VI. kerület', 'VIII. kerület', 'VIII. kerület', 'XIII. kerület', 'XIII. kerület']
        })
    else:
        rentals = pd.read_csv(args.rent_data)
        if 'size_sqm' in rentals.columns: rentals.rename(columns={'size_sqm': 'area_m2'}, inplace=True)
        if 'district' in rentals.columns: rentals.rename(columns={'district': 'kerület'}, inplace=True)
        
    if not args.sales_data.exists():
        print(f"⚠️  Sales data not found at {args.sales_data}. Using rental data to estimate sales prices (Yield approximation).")
        # Estimate sales price based on yield 5% (Rent * 12 * 20) just for demo
        sales = rentals.copy()
        sales['price'] = sales['price'] * 12 * 20  # ~5% yield assumption reversed
        sales['url'] = 'dummy_url'
    else:
        sales = pd.read_csv(args.sales_data)
        if 'size_sqm' in sales.columns: sales.rename(columns={'size_sqm': 'area_m2'}, inplace=True)
        if 'district' in sales.columns: sales.rename(columns={'district': 'kerület'}, inplace=True)
        
    # Precalc fields
    rentals = calculate_price_per_m2_safe(rentals)
    sales = calculate_price_per_m2_safe(sales)
    
    # 2. Market Analysis
    print("📈 Analyzing market trends...")
    analyzer = MarketAnalyzer(rentals, sales)
    summary = analyzer.aggregate_market_data(group_by=['kerület', 'size_cat'])
    top_opportunities = analyzer.find_best_investment_areas(top_n=10)
    
    # 3. Financial Simulation for Top Opportunities
    print("💰 Simulating financials...")
    
    if top_opportunities.empty:
        print("⚠️ No opportunities found matching the criteria (need sales AND rentals in same area/size).")
        print("💡 Suggestion: Scrape rental data to find matches.")
        # Create output dir just in case
        args.output.parent.mkdir(parents=True, exist_ok=True)
        return
    
    report_lines = []
    report_lines.append("# 🏢 Ingatlanbefektetési Elemzés\n")
    report_lines.append(f"**Saját tőke:** {args.own_cash:,.0f} Ft | **Hitelkamat:** {args.loan_rate*100}% | **Futamidő:** {args.loan_term} év\n")
    
    report_lines.append("## 🏆 Top 10 Befektetési Lehetőség (Yield alapján)\n")
    report_lines.append("| Kerület | Méret | Átlagár (M Ft) | Bérleti Díj (eFt) | Gross Yield | Cashflow (becsült) |")
    report_lines.append("|---|---|---|---|---|---|")
    
    for _, row in top_opportunities.iterrows():
        avg_price = row['avg_sales_price']
        avg_rent = row['avg_rent']
        
        # Loan Calculation
        loan_amount = max(0, avg_price - args.own_cash)
        loan = LoanCalculator.calculate_loan(loan_amount, args.loan_rate, args.loan_term)
        
        # Investment Analysis
        inv = InvestmentAnalyzer(
            purchase_price=avg_price,
            monthly_rent=avg_rent,
            loan_details=loan,
            monthly_expenses=20000 # Estimate
        )
        metrics = inv.calculate_metrics()
        
        cashflow = metrics['monthly_cashflow']
        cashflow_str = f"✅ +{cashflow:,.0f}" if cashflow > 0 else f"🔻 {cashflow:,.0f}"
        
        report_lines.append(f"| {row['kerület']} | {row['size_cat']} | {avg_price/1e6:.1f}M | {avg_rent/1e3:.0f}e | **{row['gross_yield_percent']:.1f}%** | {cashflow_str} |")
        
    # 4. Detailed Simulation for the #1 Opportunity
    best = top_opportunities.iloc[0]
    report_lines.append(f"\n## ⭐️ Részletes Elemzés: {best['kerület']}. kerület, {best['size_cat']}\n")
    
    # Run Monte Carlo
    # Re-instantiate calculator for best option
    loan_amount = max(0, best['avg_sales_price'] - args.own_cash)
    loan = LoanCalculator.calculate_loan(loan_amount, args.loan_rate, args.loan_term)
    inv_best = InvestmentAnalyzer(
        purchase_price=best['avg_sales_price'],
        monthly_rent=best['avg_rent'],
        loan_details=loan,
        monthly_expenses=25000
    )
    
    risk_sim = RiskSimulator(inv_best)
    sim_results = risk_sim.run_simulation()
    
    report_lines.append(f"- **Vételár:** {best['avg_sales_price']:,.0f} Ft")
    report_lines.append(f"- **Hitel összeg:** {loan_amount:,.0f} Ft ({loan_amount/best['avg_sales_price']*100:.0f}% LTV)")
    report_lines.append(f"- **Havi törlesztő:** {loan.monthly_payment:,.0f} Ft")
    report_lines.append(f"- **Várható Cashflow:** {inv_best.calculate_metrics()['monthly_cashflow']:,.0f} Ft/hó")
    report_lines.append(f"- **ROI (Cash-on-Cash):** {inv_best.calculate_metrics()['cash_on_cash_roi_percent']:.1f}%")
    
    report_lines.append("\n### 🎲 Kockázatelemzés (Monte Carlo, 10,000 eset)")
    report_lines.append(f"- **Pozitív Cashflow valószínűsége:** {sim_results['probability_positive_cashflow']:.1f}%")
    report_lines.append(f"- **Várható ROI:** {sim_results['roi_mean']:.1f}% (±{sim_results['roi_std']:.1f}%)")
    report_lines.append(f"- **Worst Case (5%):** {sim_results['roi_5th_percentile']:.1f}% ROI")
    
    # Save Report
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"\n✅ Report generated: {output_path}")
    print("\n------------------------------------------------")
    print("\n".join(report_lines[:20])) # Show preview
    print("...")


if __name__ == "__main__":
    main()
