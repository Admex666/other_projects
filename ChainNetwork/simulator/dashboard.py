import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random

# Page config
st.set_page_config(page_title="ChainNetwork | Scenario Planner", layout="wide", page_icon="⚖️")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4150; }
    div[data-testid="stExpander"] { border: 1px solid #3e4150; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_full_data():
    conn = sqlite3.connect('simulator/chainnetwork.db')
    query = """
    SELECT t.*, u.test_group, u.name as user_name, u.joined_at, s.name as store_name, 
           ti.menu_item_id, mi.name as item_name, mi.category as item_category
    FROM transactions t
    JOIN users u ON t.user_id = u.id
    JOIN stores s ON t.store_id = s.id
    LEFT JOIN transaction_items ti ON t.id = ti.transaction_id
    LEFT JOIN menu_items mi ON ti.menu_item_id = mi.id
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    conn.close()
    return df

def run_advanced_rfm(df):
    now = df['timestamp'].max()
    rfm = df.groupby(['user_id', 'user_name', 'test_group']).agg({
        'timestamp': ['max', 'min', 'count', lambda x: x.sort_values().diff().dt.days.mean()],
        'total_amount': 'sum'
    }).reset_index()
    rfm.columns = ['user_id', 'user_name', 'test_group', 'last_visit', 'first_visit', 'freq_count', 'avg_gap', 'monetary']
    rfm['recency_days'] = (now - rfm['last_visit']).dt.days
    rfm['tenure'] = (now - rfm['first_visit']).dt.days + 1
    rfm['freq_density'] = rfm['freq_count'] / rfm['tenure']
    rfm['avg_gap'] = rfm['avg_gap'].fillna(30)
    rfm['recency_ratio'] = rfm['recency_days'] / rfm['avg_gap']
    
    rfm['F_Score'] = pd.qcut(rfm['freq_density'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    rfm['R_Score'] = pd.qcut(rfm['recency_ratio'].rank(method='first'), 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    
    rfm['Final_Score'] = (rfm['R_Score'].astype(int) * 0.4 + rfm['F_Score'].astype(int) * 0.4 + rfm['M_Score'].astype(int) * 0.2)
    
    def segment_advanced(score):
        if score >= 4.5: return 'Champion'
        if score >= 3.5: return 'Loyal'
        if score >= 2.5: return 'Casual'
        if score >= 1.5: return 'At Risk'
        return 'Lost'
    
    rfm['segment'] = rfm['Final_Score'].apply(segment_advanced)
    return rfm

# --- DATA LOADING ---
df_raw = load_full_data()

# --- SIDEBAR / SCENARIO PLANNER ---
st.sidebar.title("🍔 ChainNetwork Bio")
st.sidebar.markdown("---")
st.sidebar.subheader("📐 Scenario Parameters")

# Sliders for sensitivity analysis
retain_conv = st.sidebar.slider("Retention Conv. Rate (%)", 0, 100, 30) / 100
upsell_hit = st.sidebar.slider("Upsell Hit Rate (%)", 0, 100, 20) / 100
discount_amt = st.sidebar.slider("Average Discount (HUF)", 0, 2000, 500)
freq_lift = st.sidebar.slider("Frequency Lift Factor (%)", 0, 50, 15) / 100
basket_lift = st.sidebar.slider("Basket Lift Factor (%)", 0, 30, 8) / 100

st.sidebar.markdown("---")
min_date = df_raw['timestamp'].min().date()
max_date = df_raw['timestamp'].max().date()
date_range = st.sidebar.date_input("Analysis Period", [min_date, max_date], min_value=min_date, max_value=max_date)

# --- DATA FILTERING ---
mask = (
    (df_raw['timestamp'].dt.date >= date_range[0]) & 
    (df_raw['timestamp'].dt.date <= (date_range[1] if len(date_range) > 1 else date_range[0]))
)
df = df_raw[mask]

# --- MAIN DASHBOARD ---
st.title("Decision Engine | Interactive Business Planner")

# Calculate Dynamic Stats for A and B
stats = df_raw.groupby('test_group').agg({
    'id': 'count',
    'total_amount': 'sum',
    'user_id': 'nunique'
})
stats.columns = ['Orders', 'Revenue', 'Users']
stats['Avg Basket'] = stats['Revenue'] / stats['Orders']

# APPLY SCENARIO LOGIC TO B
# 1. Calculate Uplift based on sliders
orders_b = stats.loc['B', 'Orders'] * (1 + freq_lift * (retain_conv / 0.3)) # scaled by 30% baseline
avg_basket_b = stats.loc['B', 'Avg Basket'] * (1 + basket_lift * (upsell_hit / 0.2))

# 2. Add marketing cost (discount)
total_discount_cost = (orders_b * (retain_conv)) * discount_amt
final_rev_b = (orders_b * avg_basket_b) - total_discount_cost

stats.loc['B', 'Orders'] = orders_b
stats.loc['B', 'Avg Basket'] = avg_basket_b
stats.loc['B', 'Revenue'] = final_rev_b
stats.loc['B', 'ARPU'] = stats.loc['B', 'Revenue'] / stats.loc['B', 'Users']
stats.loc['A', 'ARPU'] = stats.loc['A', 'Revenue'] / stats.loc['A', 'Users']

uplift_pct = ((stats.loc['B', 'ARPU'] / stats.loc['A', 'ARPU']) - 1) * 100

# Top KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Current Scenario Revenue", f"{stats.loc['B', 'Revenue']:,.0f} HUF")
k2.metric("Projected Uplift", f"{uplift_pct:.1f}%", delta=f"{uplift_pct:.1f}%")
k3.metric("Discount Cost", f"-{total_discount_cost:,.0f} HUF", delta_color="inverse")
k4.metric("Net ROI", f"{(stats.loc['B', 'Revenue'] - stats.loc['A', 'Revenue']) / (total_discount_cost + 1):.1f}x")

# Tabs
tab_sim, tab_geo, tab_rfm = st.tabs(["📉 Sensitivity Analysis", "🌍 Geographical Performance", "🎯 Segmentation"])

with tab_sim:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("A/B Performance Comparison")
        comp_df = stats['ARPU'].reset_index()
        fig_comp = px.bar(comp_df, x='test_group', y='ARPU', color='test_group', 
                         template="plotly_dark", color_discrete_map={'A': '#555', 'B': '#00d2ff'})
        st.plotly_chart(fig_comp, use_container_width=True)
    
    with c2:
        st.subheader("Financial Breakdown")
        st.table(stats.style.format("{:,.0f}"))
        st.write("---")
        st.write(f"**Strategy Breakdown:**")
        st.write(f"🟢 Retention Impact: +{freq_lift * 100:.1f}% visits")
        st.write(f"🔵 Upsell Impact: +{basket_lift * 100:.1f}% size")

with tab_rfm:
    rfm_adv = run_advanced_rfm(df)
    col1, col2 = st.columns([1, 2])
    with col1:
        fig_pie = px.pie(rfm_adv, names='segment', template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        fig_scat = px.scatter(rfm_adv, x='freq_density', y='recency_ratio', color='segment', 
                              hover_name='user_name', template="plotly_dark")
        st.plotly_chart(fig_scat, use_container_width=True)

with tab_geo:
    st.subheader("Revenue by Store")
    store_agg = df.groupby('store_name')['total_amount'].sum().reset_index()
    fig_st = px.bar(store_agg, x='total_amount', y='store_name', orientation='h', template="plotly_dark")
    st.plotly_chart(fig_st, use_container_width=True)
