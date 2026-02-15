import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.financial import InvestmentAnalyzer, LoanCalculator

st.set_page_config(page_title="Ingatlanos Gyilkos v3.1", page_icon="🚀", layout="wide")

def format_huf(value):
    return f"{int(value):,}".replace(",", " ") if not np.isnan(value) else "0"

def calculator_page():
    st.header("🚀 PRO Ingatlan Kalkulátor (v3.1)")
    
    with st.sidebar:
        st.subheader("🛠️ Piaci Dinamika")
        appreciation_rate = st.slider("Éves értéknövekedés (%)", 0.0, 15.0, 5.0, 0.5)
        rent_growth_rate = st.slider("Bérleti díj növekedés (%)", 0.0, 15.0, 4.0, 0.5)
        inflation_rate = st.slider("Infláció / Diszkontráta (%)", 0.0, 20.0, 8.0, 0.5)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Alapadatok")
        with st.expander("🏠 Ingatlan", expanded=True):
            price_m = st.number_input("Vételár (M Ft)", min_value=0, value=50)
            size = st.number_input("Méret (m²)", min_value=0, value=50)
            rent_k = st.number_input("Havi bérlet (eFt)", min_value=0, value=250)
            price, rent = price_m * 1e6, rent_k * 1e3
            
        with st.expander("💰 Finanszírozás", expanded=True):
            own_cash_m = st.number_input("Saját tőke (M Ft)", min_value=1, value=15)
            interest_rate = st.slider("Hitelkamat (%)", 0.0, 15.0, 6.5, 0.1)
            loan_term = st.slider("Futamidő (év)", 5, 30, 20)
            own_cash = own_cash_m * 1e6

        with st.expander("⚙️ Költségek", expanded=False):
            renovation_m = st.number_input("Felújítás (M Ft)", value=2)
            monthly_exp_k = st.number_input("Havi költség (eFt)", value=30)
            renovation, monthly_exp = renovation_m * 1e6, monthly_exp_k * 1e3

    # Initial Setup
    stamp_duty = price * 0.04
    total_entry_cost = price + renovation + stamp_duty
    loan_amt = max(0.0, total_entry_cost - own_cash)
    loan_calc = LoanCalculator.calculate_loan(loan_amt, interest_rate/100, loan_term)
    monthly_payment = loan_calc.monthly_payment
    
    # 10 Year Projection
    years = np.arange(0, 11)
    projection = []
    
    curr_price = price + renovation
    curr_rent = rent
    remaining_loan = loan_amt
    cumulative_cashflow = 0
    
    # Yearly amortization calculation
    monthly_rate = (interest_rate/100) / 12
    
    for year in years:
        if year > 0:
            # 12 months of operations
            annual_cashflow = 0
            for month in range(12):
                # Monthly operations
                m_income = curr_rent * 0.95 # 5% vacancy
                m_profit = m_income - monthly_exp - monthly_payment
                annual_cashflow += m_profit
                
                # Loan amortization
                interest_payment = remaining_loan * monthly_rate
                principal_payment = monthly_payment - interest_payment
                remaining_loan = max(0, remaining_loan - principal_payment)
            
            # End of year adjustments
            curr_price *= (1 + appreciation_rate/100)
            curr_rent *= (1 + rent_growth_rate/100)
            cumulative_cashflow += annual_cashflow
        
        # Total Wealth Calculation
        # Net Wealth = Property Value - Loan Balance + Cash in pocket
        future_wealth = curr_price - remaining_loan + cumulative_cashflow
        
        # Discounting to Today's Value
        discount_factor = (1 + inflation_rate/100)**year
        pv_wealth = future_wealth / discount_factor
        
        # Real Profit (Discounted Wealth - Initial Investment)
        real_profit = pv_wealth - own_cash
        
        projection.append({
            "Year": year,
            "Real_Value": curr_price,
            "Loan_Balance": remaining_loan,
            "Net_Equity": curr_price - remaining_loan,
            "Cum_Cashflow": cumulative_cashflow,
            "Future_Total_Wealth": future_wealth,
            "Discounted_Total_Wealth": pv_wealth,
            "Real_Discounted_Profit": real_profit
        })
    
    df_proj = pd.DataFrame(projection)
    final = df_proj.iloc[-1]
    
    with col2:
        tab1, tab2 = st.tabs(["💰 Vagyonépülés & Profit", "📅 Éves Cashflow"])
        
        with tab1:
            st.subheader("Teljes Profit (Mai értéken diszkontálva)")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("10 Éves Reál Profit", f"{format_huf(final['Real_Discounted_Profit'])} Ft", help="Mennyi pénzt kerestél tisztán az infláció felett, mai értéken.")
            m2.metric("Vagyon 10 év múlva", f"{format_huf(final['Future_Total_Wealth'])} Ft", help="Ingatlan értéke + összeggyűjtött cashflow - maradék hitel.")
            m3.metric("Reál Megtérülés", f"{((final['Discounted_Total_Wealth']/own_cash)-1)*100:.1f}%", help="Az infláció feletti tiszta hozam a saját tőkédre vetítve.")

            # Chart: Cumulative Real Wealth vs Investment
            fig_wealth = go.Figure()
            fig_wealth.add_trace(go.Scatter(x=df_proj['Year'], y=df_proj['Discounted_Total_Wealth'], 
                                           name="Diszkontált Összvagyon (Reál érték)", 
                                           fill='tozeroy', line=dict(color='#00CC96', width=4)))
            fig_wealth.add_hline(y=own_cash, line_dash="dot", line_color="gray", annotation_text="Kezdeti befektetés")
            fig_wealth.update_layout(title="Hogyan növekszik a vagyonod az inflációt is beleszámolva?", xaxis_title="Év", yaxis_title="Ft")
            st.plotly_chart(fig_wealth, use_container_width=True)
            
            st.info(f"💡 **Elemzés:** 10 év alatt a befektetett {own_cash_m} M Ft-ból mai értéken {format_huf(final['Discounted_Total_Wealth'])} Ft lesz. Ebben benne van az ingatlan drágulása, a hiteled fogyása és a bérleti díj emelkedése is.")

        with tab2:
            st.subheader("Havi Cashflow alakulása (Nominál)")
            # Display yearly nominal cashflow
            df_proj['Yearly_CF'] = df_proj['Cum_Cashflow'].diff().fillna(0)
            fig_cf = px.bar(df_proj[df_proj['Year'] > 0], x="Year", y="Yearly_CF", 
                           title="Éves tiszta bevétel (nem diszkontálva)",
                           labels={"Yearly_CF": "M Ft / év"})
            st.plotly_chart(fig_cf, use_container_width=True)

    # Market Data
    st.divider()
    st.markdown("### 🔎 Piacvizsgálat (Összehasonlító adatok)")
    try:
        sales = pd.read_csv("data/processed/zenga_sales_data.csv")
        st.dataframe(sales[['kerület', 'price', 'area_m2', 'address']].head(10), use_container_width=True)
    except:
        st.info("Futtasd a scrape-et a piaci adatokhoz!")

if __name__ == "__main__":
    calculator_page()
