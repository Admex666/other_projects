import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Supabase Credentials loaded from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Meta Marketing API Credentials loaded from .env
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

@st.cache_data(ttl=10) # Cache data for 10 seconds to avoid API spamming
def load_data():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        st.error("Hiányzó Supabase kapcsolat! Ellenőrizd a .env fájlt.")
        return pd.DataFrame()
        
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
        st.error(f"Csatlakozási hiba (Supabase): {e}")
        return pd.DataFrame()

def clean_ad_account_id(acc_id):
    if not acc_id:
        return ""
    acc_id = acc_id.strip()
    if not acc_id.startswith("act_"):
        acc_id = f"act_{acc_id}"
    return acc_id

@st.cache_data(ttl=30) # Cache Meta insights for 30 seconds
def load_meta_data():
    if not META_AD_ACCOUNT_ID or not META_ACCESS_TOKEN:
        return None
    
    clean_id = clean_ad_account_id(META_AD_ACCOUNT_ID)
    url = f"https://graph.facebook.com/v19.0/{clean_id}/insights"
    
    params = {
        "fields": "spend,impressions,clicks,cpc,ctr",
        "date_preset": "lifetime",
        "access_token": META_ACCESS_TOKEN
    }
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json().get('data', [])
            if data:
                return data[0]
            else:
                # Fallback if no spending yet
                return {
                    "spend": "0",
                    "impressions": "0",
                    "clicks": "0",
                    "cpc": "0",
                    "ctr": "0"
                }
        else:
            err_msg = res.json().get('error', {}).get('message', 'Ismeretlen Meta hiba')
            st.sidebar.error(f"Meta API Hiba: {err_msg}")
            return None
    except Exception as e:
        st.sidebar.error(f"Meta csatlakozási hiba: {e}")
        return None

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

# Loading Supabase data
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

        # 3. Calculate Core KPIs (Supabase)
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
        
        # 4. Display Meta Ads Insights if credentials exist
        meta_data = load_meta_data()
        
        if meta_data:
            st.subheader("📢 Meta Ads Hirdetési Teljesítmény (Élő adatok)")
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            
            spend = float(meta_data.get('spend', 0))
            impressions = int(meta_data.get('impressions', 0))
            clicks = int(meta_data.get('clicks', 0))
            cpc = float(meta_data.get('cpc', 0))
            ctr = float(meta_data.get('ctr', 0))
            
            # Calculate Real CAC (Spend / Leads) live!
            real_cac = (spend / total_leads) if total_leads > 0 else 0.0
            
            with m_col1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Elköltött összeg", f"{int(spend):,} Ft".replace(",", " "))
                st.markdown("</div>", unsafe_allow_html=True)
                
            with m_col2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Megjelenések (Impressions)", f"{impressions:,} db".replace(",", " "))
                st.markdown("</div>", unsafe_allow_html=True)
                
            with m_col3:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Hirdetés kattintások", f"{clicks:,} fő")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with m_col4:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Átlagos CPC / CTR", f"{cpc:.1f} Ft / {ctr:.2f}%")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with m_col5:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                # Compare live CAC to the 2500 HUF target warning
                cac_label = "Valós Ügyfélszerzés (CAC)"
                if real_cac > 4000:
                    cac_status = f"{int(real_cac):,} Ft 🔴 (Túl magas)"
                elif 0 < real_cac <= 2500:
                    cac_status = f"{int(real_cac):,} Ft 🟢 (Nyereséges)"
                elif real_cac > 2500:
                    cac_status = f"{int(real_cac):,} Ft 🟡 (Magas)"
                else:
                    cac_status = "0 Ft"
                st.metric(cac_label, cac_status.replace(",", " "))
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.markdown("---")

        # 5. Display Supabase Conversion KPIs
        st.subheader("🛒 Weboldal Konverziós Mutatók (Tölcsér adatok)")
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

        # 6. Conversion Funnel & Time Series Plots
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
            st.subheader("📊 Látogatók (Session) Időbeli Megoszlása")
            
            # Map UTC timestamps to local Europe/Budapest timezone for precise reporting
            df_filtered['local_time'] = df_filtered['created_at_dt'].dt.tz_convert('Europe/Budapest')
            
            # Group sessions by local hour
            df_filtered['hour'] = df_filtered['local_time'].dt.strftime('%m.%d. %H:00')
            time_dist = df_filtered.groupby('hour')['session_id'].nunique().reset_index()
            time_dist.columns = ['Időszak (Óra)', 'Egyedi Látogatók (Session)']
            
            # Requested change: Interactive Bar Chart grouped hourly
            fig_time = px.bar(
                time_dist,
                x='Időszak (Óra)',
                y='Egyedi Látogatók (Session)',
                color_discrete_sequence=['#C3A479'] # Elegant Gold Bars
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
                    title="Egyedi Látogatók száma",
                    dtick=1 # Integer steps only
                )
            )
            st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("---")

        # 7. Detailed Leads table (B2C signup database)
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
