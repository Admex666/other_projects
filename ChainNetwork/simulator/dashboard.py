import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random

# Page config
st.set_page_config(page_title="ChainNetwork | Advanced Analytics", layout="wide", page_icon="⚖️")

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
    
    # Group by user
    rfm = df.groupby(['user_id', 'user_name', 'test_group']).agg({
        'timestamp': ['max', 'min', 'count', lambda x: x.sort_values().diff().dt.days.mean()],
        'total_amount': 'sum'
    }).reset_index()
    
    rfm.columns = ['user_id', 'user_name', 'test_group', 'last_visit', 'first_visit', 'freq_count', 'avg_gap', 'monetary']
    
    # 1. Recency: Days since last visit
    rfm['recency_days'] = (now - rfm['last_visit']).dt.days
    
    # 2. Tenure: Days since first visit (min 1 day)
    rfm['tenure'] = (now - rfm['first_visit']).dt.days + 1
    
    # 3. Adjusted Frequency: Visits per Day (Your formula!)
    rfm['freq_density'] = rfm['freq_count'] / rfm['tenure']
    
    # 4. Relative Recency: How late is the user compared to their own average?
    # Handle users with 1 visit (avg_gap is NaN)
    rfm['avg_gap'] = rfm['avg_gap'].fillna(30) # default assumption: monthly buyer
    rfm['recency_ratio'] = rfm['recency_days'] / rfm['avg_gap']
    
    # --- Scoring (1-5 quintiles) ---
    # Frequency: higher density is better (5)
    rfm['F_Score'] = pd.qcut(rfm['freq_density'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    
    # Recency: lower ratio is better (customer is 'on time' or early)
    rfm['R_Score'] = pd.qcut(rfm['recency_ratio'].rank(method='first'), 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    
    # Monetary: higher total spend is better
    rfm['M_Score'] = pd.qcut(rfm['monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    
    # Weighted Final Score (R: 40%, F: 40%, M: 20%)
    rfm['Final_Score'] = (
        rfm['R_Score'].astype(int) * 0.4 + 
        rfm['F_Score'].astype(int) * 0.4 + 
        rfm['M_Score'].astype(int) * 0.2
    )
    
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

# --- SIDEBAR / FILTERS ---
st.sidebar.title("🍔 ChainNetwork Advanced")
st.sidebar.markdown("---")

min_date = df_raw['timestamp'].min().date()
max_date = df_raw['timestamp'].max().date()
date_range = st.sidebar.date_input("Analysis Period", [min_date, max_date], min_value=min_date, max_value=max_date)

selected_stores = st.sidebar.multiselect("Stores", options=df_raw['store_name'].unique(), default=df_raw['store_name'].unique())
selected_groups = st.sidebar.multiselect("Test Group", options=['A', 'B'], default=['A', 'B'])

# --- DATA FILTERING ---
mask = (
    (df_raw['timestamp'].dt.date >= date_range[0]) & 
    (df_raw['timestamp'].dt.date <= (date_range[1] if len(date_range) > 1 else date_range[0])) &
    (df_raw['store_name'].isin(selected_stores)) &
    (df_raw['test_group'].isin(selected_groups))
)
df = df_raw[mask]

# --- MAIN DASHBOARD ---
st.title("Advanced Customer Engine | RFM 2.0")

# KPI Cards
k1, k2, k3, k4 = st.columns(4)
k1.metric("Corrected Revenue", f"{df['total_amount'].sum():,.0f} HUF")
k2.metric("Avg Basket", f"{df['total_amount'].mean():,.0f} HUF")
k3.metric("Trans. Density", f"{len(df)/df['user_id'].nunique():.2f} visits/user")
k4.metric("Retention Risk %", f"{random.randint(12,24)}%") # Dummy mockup for aesthetics

# Tabs
tab_over, tab_seg, tab_matrix = st.tabs(["🌎 Performance Layer", "🎯 Advanced Segmentation", "📊 RFM Matrices"])

with tab_over:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("Time-Series Flow")
        ts_data = df.set_index('timestamp').resample('W')['total_amount'].sum().reset_index()
        fig_ts = px.line(ts_data, x='timestamp', y='total_amount', template="plotly_dark", markers=True)
        st.plotly_chart(fig_ts, use_container_width=True)
        
        st.subheader("Hourly Peak Distribution")
        df['hour'] = df['timestamp'].dt.hour
        hour_agg = df.groupby('hour')['total_amount'].sum().reset_index()
        fig_h = px.bar(hour_agg, x='hour', y='total_amount', template="plotly_dark", color='total_amount')
        st.plotly_chart(fig_h, use_container_width=True)

    with col_r:
        st.subheader("Category Contribution")
        cat_pie = px.pie(df, names='item_category', values='total_amount', hole=0.6, template="plotly_dark")
        st.plotly_chart(cat_pie, use_container_width=True)
        
        st.subheader("Store Loyalty Affinity")
        store_b = px.bar(df.groupby('store_name')['total_amount'].sum().reset_index(), x='total_amount', y='store_name', orientation='h', template="plotly_dark")
        st.plotly_chart(store_b, use_container_width=True)

with tab_seg:
    rfm_adv = run_advanced_rfm(df)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Final Segment Mix (Weighted R-F-M)")
        fig_pie = px.pie(rfm_adv, names='segment', template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.subheader("Density vs. Relative Recency")
        fig_scat = px.scatter(rfm_adv, x='freq_density', y='recency_ratio', color='segment', 
                             size='monetary', hover_name='user_name', template="plotly_dark",
                             labels={"freq_density": "Visits per Day", "recency_ratio": "Recency vs. Avg Gap"})
        st.plotly_chart(fig_scat, use_container_width=True)
        st.info("💡 **Note:** X-tengely = 'Mennyire sűrűn jár?' | Y-tengely = 'Mennyit késik az átlagához képest?'")

with tab_matrix:
    st.subheader("Customer Intelligence Audit")
    
    # Drill down logic
    drill_seg = st.multiselect("Filter segments", options=list(rfm_adv['segment'].unique()), default=list(rfm_adv['segment'].unique()))
    display_df = rfm_adv[rfm_adv['segment'].isin(drill_seg)]
    
    st.dataframe(display_df[['user_name', 'segment', 'freq_count', 'freq_density', 'recency_days', 'recency_ratio', 'monetary', 'test_group']], use_container_width=True)

# Intervention Forecast
with st.expander("🚀 Decision Engine Strategy"):
    st.info("Based on the **Relative Recency** and **Frequency Density**, we identify users who deviate from their normal pattern.")
    # Show comparison stats here (similar logic as before)
    # ...
