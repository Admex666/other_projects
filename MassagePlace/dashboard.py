import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration with premium brand styling
st.set_page_config(
    page_title="ZenSlot Live Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Premium CSS injection matching the ZenSlot glassmorphism & spa design system
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .main {
        background-color: #0f1412;
        color: #f5f5f5;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Elegant titles */
    h1, h2, h3 {
        color: #c3a479 !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metrics glassmorphism card styling */
    div[data-testid="stMetricValue"] {
        color: #c3a479 !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #a0a8a3 !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
    }
    
    /* Custom container padding and cards */
    .metric-card {
        background: rgba(15, 20, 18, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 1.5rem;
    }
    
    /* Header layout styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 1rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Supabase Credentials
SUPABASE_URL = "https://vggmrmgctzanoutabvvl.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZnZ21ybWdjdHphbm91dGFidnZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzODIzMzgsImV4cCI6MjA5NDk1ODMzOH0.xg7g-o0l9V5kskL_ebVRJtYiFfGrDFeHMa9ng-WYWnU"

@st.cache_data(ttl=10) # Cache data for 10 seconds to avoid API spamming
def load_data():
    url = f"{SUPABASE_URL}/rest/v1/fake_door_leads?select=*"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
        else:
            st.error(f"Hiba a Supabase elérésekor: {res.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Csatlakozási hiba: {e}")
        return pd.DataFrame()

# Main Title & Header Layout
st.markdown("""
    <div class='header-container'>
        <div style='display: flex; align-items: center; gap: 15px;'>
            <h1 style='margin: 0;'>🌿 ZenSlot Élő Kampány Analytics</h1>
        </div>
        <div style='color: #a0a8a3; font-size: 0.95rem; text-align: right;'>
            Budapesti Last-Minute Wellness Validáció
        </div>
    </div>
""", unsafe_allow_html=True)

# Loading data
df = load_data()

if df.empty:
    st.info("Várakozás az első Supabase adatok betöltődésére... ⏳")
else:
    # 1. Parse timestamps and handle datetime parsing safely
    df['created_at_dt'] = pd.to_datetime(df['created_at'])
    
    # 2. Strict Filter: ONLY show data after 2026-05-23 19:00 CET (which is 17:00 UTC)
    filter_time_utc = pd.to_datetime('2026-05-23 17:00:00').tz_localize('UTC')
    df_filtered = df[df['created_at_dt'] >= filter_time_utc].copy()
    
    if df_filtered.empty:
        st.warning("⚠️ Nincs rögzített adat a hivatalos kampányindítás (2026.05.23. 19:00 CET) óta.")
        st.info("Amint elindulnak a Meta hirdetések és az első látogatók megnyitják a weblapot, itt fognak megjelenni a valós idejű statisztikák. Frissíts az alábbi gombbal!")
        if st.button("Adatok frissítése 🔄"):
            st.rerun()
    else:
        # Columns normalization/guarantees
        if 'total_aov' not in df_filtered.columns:
            df_filtered['total_aov'] = 0
        df_filtered['total_aov'] = pd.to_numeric(df_filtered['total_aov']).fillna(0)

        # 3. Calculate Core KPIs
        # Total Unique Sessions
        total_sessions = df_filtered['session_id'].nunique()
        
        # Total Leads (waitlist submissions)
        leads_df = df_filtered[df_filtered['event_name'] == 'waitlist_submitted']
        total_leads = leads_df['session_id'].nunique()
        
        # Conversion Rate (CVR)
        cvr = (total_leads / total_sessions * 100) if total_sessions > 0 else 0.0
        
        # Average Order Value (AOV) from waitlist submitted leads
        lead_aov_df = leads_df[leads_df['total_aov'] > 0]
        if lead_aov_df.empty:
            # Fallback to any step with value
            lead_aov_df = df_filtered[df_filtered['total_aov'] > 0]
        avg_aov = lead_aov_df['total_aov'].mean() if not lead_aov_df.empty else 0.0
        
        # Estimated commission (20% take rate of submitted leads)
        est_commission = (leads_df['total_aov'].sum() * 0.20) if not leads_df.empty else 0.0
        
        # 4. KPI Layout in Columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Összes Látogató (Session)", f"{total_sessions} fő")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Sikeres Feliratkozó (Lead)", f"{total_leads} fő")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Konverziós Arány (CVR)", f"{cvr:.2f} %")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Átlagos Kosárérték (AOV)", f"{int(avg_aov):,} Ft".replace(",", " "))
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col5:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Becsült Bevétel (20% jutalék)", f"{int(est_commission):,} Ft".replace(",", " "))
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 5. Conversion Funnel & Time Series Plots
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🎯 Konverziós Tölcsér (Funnel)")
            
            # Calculate unique sessions at each step of the fake door process
            funnel_data = pd.DataFrame({
                'Lépés': [
                    '1. Oldalmegnyitás (PageView)',
                    '2. Kezelés választás',
                    '3. Aromaterápia választás',
                    '4. Gyakoriság megadás',
                    '5. Sikeres Lead feliratkozás'
                ],
                'Látogatók (Fő)': [
                    total_sessions,
                    df_filtered[df_filtered['treatment'].notna()]['session_id'].nunique(),
                    df_filtered[df_filtered['upsell'].notna()]['session_id'].nunique(),
                    df_filtered[df_filtered['frequency'].notna()]['session_id'].nunique(),
                    total_leads
                ]
            })
            
            # Beautiful spa brand color theme for the funnel
            funnel_colors = ["#2C352F", "#3B4D41", "#5C7364", "#829D8B", "#C3A479"]
            
            fig_funnel = go.Figure(go.Funnel(
                y=funnel_data['Lépés'],
                x=funnel_data['Látogatók (Fő)'],
                textposition="inside",
                textinfo="value+percent initial",
                marker={"color": funnel_colors},
                connector={"line": {"color": "rgba(255, 255, 255, 0.15)", "width": 1.5}}
            ))
            
            fig_funnel.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#F5F5F5',
                margin=dict(l=20, r=20, t=20, b=20),
                height=350
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

        with col_right:
            st.subheader("📈 Látogatók (Session) Időbeli Megoszlása")
            
            # Map UTC timestamps to local Europe/Budapest timezone for precise reporting
            df_filtered['local_time'] = df_filtered['created_at_dt'].dt.tz_convert('Europe/Budapest')
            
            # Group sessions by local hour
            df_filtered['hour'] = df_filtered['local_time'].dt.strftime('%m.%d. %H:00')
            time_dist = df_filtered.groupby('hour')['session_id'].nunique().reset_index()
            time_dist.columns = ['Időszak (Óra)', 'Egyedi Látogatók (Session)']
            
            # Smooth area line chart with brand colors
            fig_time = px.area(
                time_dist,
                x='Időszak (Óra)',
                y='Egyedi Látogatók (Session)',
                color_discrete_sequence=['#C3A479'] # Elegant Gold Line
            )
            
            fig_time.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#F5F5F5',
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
                xaxis=dict(
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    title=""
                ),
                yaxis=dict(
                    gridcolor='rgba(255, 255, 255, 0.05)',
                    title="Egyedi Látogatók száma"
                )
            )
            st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("---")

        # 6. Detailed Leads table (B2C signup database)
        st.subheader("📋 Zárt Béta Feliratkozók (Valós Leadek)")
        
        # Extract unique leads with their choices, ordered by newest first
        leads_list_df = leads_df.drop_duplicates(subset=['session_id']).sort_values(by='created_at_dt', ascending=False)
        
        # Localize time for display
        leads_list_df['local_time_str'] = leads_list_df['created_at_dt'].dt.tz_convert('Europe/Budapest').dt.strftime('%Y.%m.%d. %H:%M')
        
        # Map treatments and upselly to elegant Hungarian texts
        treatment_map = {
            'sved_60': '60 perces svédmasszázs',
            'thai_90': '90 perces thai masszázs'
        }
        leads_list_df['Választott Kezelés'] = leads_list_df['treatment'].map(treatment_map).fillna(leads_list_df['treatment'])
        leads_list_df['Aromaterápia'] = leads_list_df['upsell'].apply(lambda x: 'Kérte 🌸' if x == 'yes' else 'Nem kérte ❌')
        
        # Present clean display table
        display_leads = leads_list_df[[
            'local_time_str', 'name', 'email', 'Választott Kezelés', 'Aromaterápia', 'total_aov', 'ip_address'
        ]].copy()
        
        display_leads.columns = [
            'Dátum (Helyi)', 'Név', 'Email cím', 'Kezelés', 'Aromaterápia', 'Kosárérték (Ft)', 'IP cím'
        ]
        
        st.dataframe(display_leads, use_container_width=True, hide_index=True)
        
        # Quick Excel/CSV download button
        csv = display_leads.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Leadek letöltése CSV formátumban 📥",
            data=csv,
            file_name=f"zenslot_leads_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Adatok manuális frissítése 🔄", key="footer_refresh"):
            st.rerun()
