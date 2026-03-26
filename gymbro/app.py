import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from analytics import get_dashboard_metrics, get_churn_risk_data, get_upsell_candidates, get_winback_candidates
from generator import generate_mock_data

# Page Config
st.set_page_config(page_title="GymBro - Profit & Retention AI", layout="wide")

# Helpers for Formatting
def fmt_huf(val):
    if val is None: return "0 HUF"
    formatted = "{:,.0f}".format(val).replace(',', ' ').replace('.', ',').replace(' ', '.')
    return f"{formatted} HUF"

def fmt_pct(val):
    if val is None: return "0,0%"
    return "{:.1f}%".format(val * 100).replace('.', ',')

def fmt_num(val):
    if isinstance(val, (int, float)):
        if val == int(val):
            return "{:,.0f}".format(val).replace(',', ' ').replace('.', ',').replace(' ', '.')
        return "{:,.2f}".format(val).replace(',', ' ').replace('.', ',').replace(' ', '.')
    return val

COLUMN_MAP = {
    'member_id': 'Tag ID',
    'tag_neve': 'Név',
    'registration_date': 'Regisztráció',
    'age': 'Életkor',
    'gender': 'Nem',
    'berlet_neve': 'Bérlet típusa',
    'plan_id': 'Bérlet ID',
    'name': 'Megnevezés',
    'type': 'Típus',
    'duration_days': 'Időtartam (nap)',
    'entries_allowed': 'Max alkalmak',
    'price': 'Ár (HUF)',
    'purchase_date': 'Vásárlás dátuma',
    'expiry_date': 'Lejárat dátuma',
    'entries_used': 'Elhasznált alkalmak',
    'risk_score': 'Kockázati pont',
    'visits_last_30': 'Látogatás (utolsó 30 nap)',
    'visits_prev_30': 'Látogatás (előző 30 nap)',
    'current_plan': 'Jelenlegi bérlet',
    'total_visits': 'Összes látogatás',
    'visits_per_week': 'Heti átlag látogatás',
    'last_visit': 'Utolsó látogatás',
    'last_purchase': 'Utolsó vásárlás',
    'check_in_time': 'Belépés ideje',
    'duration_minutes': 'Időtartam (perc)',
    'subscription_id': 'Bérlet vásárlás ID'
}

def translate_and_style(df):
    translated = df.rename(columns=COLUMN_MAP)
    # Apply formatting to numeric columns
    formats = {}
    for col in translated.columns:
        if "Ár" in col or "HUF" in col:
            formats[col] = lambda x: "{:,.0f}".format(x).replace(',', ' ').replace('.', ',').replace(' ', '.') + " HUF"
        elif "Kockázati" in col:
            formats[col] = lambda x: "{:.2f}".format(x).replace('.', ',')
        elif "átlag" in col:
            formats[col] = lambda x: "{:.1f}".format(x).replace('.', ',')
        elif translated[col].dtype in ['float64', 'int64']:
            # For other numbers, use thousands separator but no decimal if it's an integer
            formats[col] = lambda x: "{:,.0f}".format(x).replace(',', ' ').replace('.', ',').replace(' ', '.') if x == int(x) else "{:,.2f}".format(x).replace(',', ' ').replace('.', ',').replace(' ', '.')
    
    return translated.style.format(formats, na_rep="-")

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; color: #00d4ff; }
    .stButton>button { background-color: #00d4ff; color: #000; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Paraméterek")
st.sidebar.markdown("Állítsd be a terem hírnevét:")

member_count = st.sidebar.slider("Tagok száma", 50, 1000, 300)
avg_churn_input = st.sidebar.slider("Célzott Churn Rate (%)", 5, 50, 20) / 100

if st.sidebar.button("SZIMULÁCIÓ INDÍTÁSA"):
    with st.spinner("Adatok generálása a megadott paraméterek alapján..."):
        generate_mock_data(num_members=member_count, avg_churn=avg_churn_input)
    st.sidebar.success("Adatbázis sikeresen frissítve!")

# Main Header
st.title("🏋️‍♂️ GymBro: Adatvezérelt Profit Optimalizáló")
st.markdown("---")

# Metrics Dashboard
metrics = get_dashboard_metrics()
col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])

with col1:
    st.metric("Összes Bevétel (LTV)", fmt_huf(metrics["Total Revenue"]))
with col2:
    st.metric("Összes Tag", metrics["Total Members"])
with col3:
    st.metric("Inaktivitás", fmt_pct(metrics["Inactivity Rate"]), help="Azon tagok aránya, akiknek jelenleg nincs érvényes bérletük.")
with col4:
    st.metric("Lemorzsolódási arány", fmt_pct(metrics["Churn Rate"]), delta="-2,1%", delta_color="inverse", help="Havi szintű lemorzsolódás: Az előző hónapban aktív tagok hány százaléka nem újított bérletet.")

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📉 Lemorzsolódás", "💎 Felülértékesítés & Újraaktiválás", "📅 Bérlet Lejárat", "📦 Bérlet Típusok", "🗄️ Nyers Adatok"])

with tab1:
    st.subheader("Veszélyeztetett Tagok (Lemorzsolódás Kezelés)")
    st.info("A rendszer összeveti a tagok jelenlegi aktivitását a korábbi átlagukkal.")
    
    churn_df = get_churn_risk_data()
    if not churn_df.empty:
        fig = px.histogram(churn_df, x="risk_score", nbins=10, 
                           title="Lemorzsolódási Kockázat Eloszlás",
                           labels={'risk_score': 'Kockázati Index (0-1)'},
                           color_discrete_sequence=['#ff4b4b'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Azonnali teendőt igénylő tagok")
        st.dataframe(translate_and_style(churn_df[['member_id', 'tag_neve', 'risk_score', 'visits_last_30', 'visits_prev_30']]), use_container_width=True)
    else:
        st.write("Jelenleg nincs kiugróan veszélyeztetett tag.")

with tab2:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("💎 Felülértékesítési Lehetőségek")
        st.write("Tagok, akik heti 2+ alkalommal jönnek alkalmi bérlettel.")
        upsell_df = get_upsell_candidates()
        st.dataframe(translate_and_style(upsell_df), use_container_width=True)
    with col_right:
        st.subheader("🔄 Újraaktiválási Kampány")
        st.write("Tagok, akik 14+ napja nem jártak.")
        winback_df = get_winback_candidates()
        st.dataframe(translate_and_style(winback_df), use_container_width=True)

with tab3:
    st.subheader("📅 Közeledő Lejáratok")
    conn = sqlite3.connect("gym_data.db")
    expiry_query = """
    SELECT m.member_id, p.name, s.expiry_date, s.entries_used, p.entries_allowed
    FROM Subscriptions s
    JOIN Members m ON s.member_id = m.member_id
    JOIN MembershipPlans p ON s.plan_id = p.plan_id
    WHERE s.expiry_date BETWEEN DATE('now', '-7 days') AND DATE('now', '+30 days')
    OR (p.entries_allowed IS NOT NULL AND s.entries_used >= p.entries_allowed - 2)
    """
    expiry_df = pd.read_sql_query(expiry_query, conn)
    st.dataframe(translate_and_style(expiry_df), use_container_width=True)
    conn.close()

with tab4:
    st.subheader("📦 Bérlet Konstrukciók Szerkesztése")
    conn = sqlite3.connect("gym_data.db")
    
    # List existing plans
    plans_df = pd.read_sql_query("SELECT * FROM MembershipPlans", conn)
    st.dataframe(translate_and_style(plans_df), use_container_width=True)
    
    st.divider()
    st.markdown("### Új bérlet hozzáadása")
    with st.form("new_plan_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_name = st.text_input("Bérlet neve", placeholder="Pl: 20 alkalmas")
            p_price = st.number_input("Ár (HUF)", min_value=0, step=500, value=15000)
        with c2:
            p_type = st.selectbox("Típus", ["Monthly", "Occasional"])
            p_dur = st.number_input("Érvényesség (nap)", min_value=1, value=30)
        with c3:
            p_ent = st.number_input("Alkalmak száma (0 ha korlátlan)", min_value=0, value=0)
            submitted = st.form_submit_button("Mentés")
            
        if submitted:
            cursor = conn.cursor()
            ent_val = p_ent if p_ent > 0 else None
            cursor.execute("INSERT INTO MembershipPlans (name, type, duration_days, entries_allowed, price) VALUES (?, ?, ?, ?, ?)",
                           (p_name, p_type, p_dur, ent_val, p_price))
            conn.commit()
            st.success(f"'{p_name}' bérlet hozzáadva!")
            st.rerun()

    if not plans_df.empty:
        st.markdown("### Bérlet törlése")
        del_name = st.selectbox("Válaszd ki a törölni kívánt bérletet", plans_df['name'].tolist())
        if st.button("TÖRLÉS", type="primary"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM MembershipPlans WHERE name = ?", (del_name,))
            conn.commit()
            st.warning(f"'{del_name}' törölve.")
            st.rerun()
    conn.close()

with tab5:
    st.subheader("Raw Data Inspector")
    table = st.selectbox("Válassz táblát", ["Members", "Subscriptions", "Visits", "MembershipPlans"])
    conn = sqlite3.connect("gym_data.db")
    df_raw = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 100", conn)
    st.dataframe(translate_and_style(df_raw), use_container_width=True)
    conn.close()
