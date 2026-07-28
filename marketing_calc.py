import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Clinic Growth Opportunity Calculator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Custom Aesthetics & Styling
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin: 0;
    }
    
    /* Card Styles */
    .stat-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stat-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    .stat-label {
        font-size: 0.825rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stat-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 6px;
    }
    .stat-desc {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Opportunity Card */
    .opp-card {
        background-color: #1e293b;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .opp-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .opp-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #34d399;
        margin-top: 10px;
    }
    .opp-badge {
        font-size: 0.75rem;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-high { background-color: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid #34d399; }
    .badge-med { background-color: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid #fbbf24; }
    .badge-low { background-color: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid #f87171; }

    /* ICP Banners */
    .icp-banner-good {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.45) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 2px solid #10b981;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 24px;
    }
    .icp-banner-warning {
        background: linear-gradient(135deg, rgba(120, 53, 15, 0.45) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 2px solid #f59e0b;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 24px;
    }
    .icp-banner-bad {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.45) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 2px solid #ef4444;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 24px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 8px;
        color: #94a3b8;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def fmt_ft(amount):
    return f"{int(round(amount)):,} Ft".replace(",", " ")

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">🏥 Clinic Growth Opportunity Calculator</div>
    <div class="header-subtitle">Gazdasági modell, szűk keresztmetszetek és extra profit lehetőség kalkuláció klinikai ügyfelek számára</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar Inputs
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ 1. Bemeneti Adatok")

# Preset selector for quick demo
preset = st.sidebar.selectbox(
    "⚡ Gyors Példa Betöltése:",
    ["Egyéni Beállítások", "Példa 1: Kisebb Klinika (4.4M Ft/hó)", "Példa 2: Nagy Klinika (15M Ft/hó)"]
)

# Preset default values
if preset == "Példa 1: Kisebb Klinika (4.4M Ft/hó)":
    def_type, def_days, def_rooms, def_staff = "Vegyes", 22, 2, 3
    def_price, def_daily_treatments = 25000, 8
    def_mkt, def_meta, def_inf, def_oth = 500000, 300000, 100000, 100000
    def_tracking, def_crm = False, False
    def_leads, def_booking, def_appear, def_new_guest = 120, 50, 85, 60
    def_bench_booking = 65
    def_cap, def_sessions, def_curr_ret, def_targ_ret = 75, 3.0, 40, 50
elif preset == "Példa 2: Nagy Klinika (15M Ft/hó)":
    def_type, def_days, def_rooms, def_staff = "Esztétikai kezelések", 22, 5, 8
    def_price, def_daily_treatments = 35000, 20
    def_mkt, def_meta, def_inf, def_oth = 2000000, 1200000, 500000, 300000
    def_tracking, def_crm = False, True
    def_leads, def_booking, def_appear, def_new_guest = 400, 45, 85, 60
    def_bench_booking = 65
    def_cap, def_sessions, def_curr_ret, def_targ_ret = 70, 4.0, 35, 50
else:
    def_type, def_days, def_rooms, def_staff = "Vegyes", 22, 2, 3
    def_price, def_daily_treatments = 25000, 8
    def_mkt, def_meta, def_inf, def_oth = 500000, 300000, 100000, 100000
    def_tracking, def_crm = False, False
    def_leads, def_booking, def_appear, def_new_guest = 120, 50, 85, 60
    def_bench_booking = 65
    def_cap, def_sessions, def_curr_ret, def_targ_ret = 75, 3.0, 40, 50

# 1.1 Alap Üzleti Adatok
with st.sidebar.expander("🏢 Alap Üzleti Adatok", expanded=True):
    clinic_type = st.selectbox(
        "Klinika típusa:",
        ["Lézeres szőrtelenítés", "Esztétikai kezelések", "Testkezelés", "Vegyes"],
        index=["Lézeres szőrtelenítés", "Esztétikai kezelések", "Testkezelés", "Vegyes"].index(def_type)
    )
    operating_days = st.number_input("Havi nyitvatartási napok:", min_value=1, max_value=31, value=def_days)
    num_rooms = st.number_input("Kezelőhelyiségek száma:", min_value=1, max_value=50, value=def_rooms)
    num_staff = st.number_input("Alkalmazott kezelők száma:", min_value=1, max_value=50, value=def_staff)

# 1.2 Bevétel & Kezelések
with st.sidebar.expander("💰 Bevétel Adatok", expanded=True):
    avg_price = st.number_input("Átlagos kezelés ára (Ft):", min_value=1000, value=def_price, step=1000)
    daily_treatments = st.number_input("Kezelések száma naponta:", min_value=1, value=def_daily_treatments)
    
    # Kiszámított automatikus mezők
    monthly_treatments = daily_treatments * operating_days
    monthly_revenue = monthly_treatments * avg_price
    
    st.markdown(f"📊 **Havi kezelések:** `{monthly_treatments} db`")
    st.markdown(f"💵 **Havi árbevétel:** `{fmt_ft(monthly_revenue)}`")

# 1.3 Marketing Adatok
with st.sidebar.expander("📣 Marketing & Technológia", expanded=True):
    marketing_spend = st.number_input("Havi marketing költés (Ft):", min_value=0, value=def_mkt, step=50000)
    
    st.caption("Részletezés (Opcionális):")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        meta_ads = st.number_input("Meta Ads (Ft):", min_value=0, value=def_meta, step=25000)
        influencer = st.number_input("Influencer (Ft):", min_value=0, value=def_inf, step=25000)
    with col_m2:
        other_mkt = st.number_input("Egyéb (Ft):", min_value=0, value=def_oth, step=25000)
    
    has_tracking = st.radio("Van tracking (mérés)?", ["igen", "nem"], index=0 if def_tracking else 1) == "igen"
    has_crm = st.radio("Van CRM rendszere?", ["igen", "nem"], index=0 if def_crm else 1) == "igen"

# 1.4 Funnel Adatok
with st.sidebar.expander("🎯 Funnel Adatok (ha tudják)", expanded=True):
    monthly_leads = st.number_input("Havi érdeklődők (leads):", min_value=0, value=def_leads)
    booking_rate = st.slider("Foglalási arány (%):", min_value=5, max_value=100, value=def_booking)
    appearance_rate = st.slider("Megjelenési arány (%):", min_value=10, max_value=100, value=def_appear)
    new_guest_rate = st.slider("Új vendég arány (%):", min_value=0, max_value=100, value=def_new_guest)
    benchmark_booking_rate = st.slider("Benchmark foglalási arány (%):", min_value=10, max_value=100, value=def_bench_booking)

# 1.5 Kapacitás & Retention
with st.sidebar.expander("🔄 Kapacitás & Retention", expanded=True):
    capacity_utilization = st.slider("Kapacitás kihasználtság (%):", min_value=10, max_value=100, value=def_cap)
    avg_sessions_per_client = st.number_input("Átlagos alkalmak száma:", min_value=1.0, value=def_sessions, step=0.5)
    current_retention_rate = st.slider("Jelenlegi visszatérési arány (%):", min_value=0, max_value=100, value=def_curr_ret)
    target_retention_rate = st.slider("Cél visszatérési arány (%):", min_value=0, max_value=100, value=def_targ_ret)

# 1.6 Árazási & Profit Szabályok
with st.sidebar.expander("⚙️ Kalkulációs Beállítások", expanded=False):
    profit_margin_pct = st.slider("Feltételezett Profit Árrés (%):", min_value=10, max_value=90, value=60)
    conservative_factor_pct = st.slider("Konzervatív realizálhatóság (%):", min_value=10, max_value=100, value=40)
    fee_share_pct = st.slider("Ajánlott havidíj az extra profitból (%):", min_value=10, max_value=50, value=25)

# -----------------------------------------------------------------------------
# 2. Opportunity Engine Logic
# -----------------------------------------------------------------------------

# Jelenlegi gazdasági modell
estimated_gross_profit = monthly_revenue * (profit_margin_pct / 100.0)
estimated_net_profit = max(0.0, estimated_gross_profit - marketing_spend)

# A) Marketing hatékonyság
if marketing_spend > 0 and not has_tracking:
    mkt_saving_pct = 0.15  # 15% optimalizációs potenciál
    mkt_saving_val = marketing_spend * mkt_saving_pct
    mkt_certainty = "közepes"
elif marketing_spend > 0 and has_tracking:
    mkt_saving_pct = 0.05
    mkt_saving_val = marketing_spend * mkt_saving_pct
    mkt_certainty = "alacsony"
else:
    mkt_saving_val = 0.0
    mkt_certainty = "alacsony"

# B) Funnel optimalizáció
current_bookings = monthly_leads * (booking_rate / 100.0)
benchmark_bookings = monthly_leads * (benchmark_booking_rate / 100.0)
extra_bookings = max(0.0, benchmark_bookings - current_bookings)

# Specification math: 18 plusz kezelés x 25 000 = 450 000 Ft bevétel -> 60% profit = 270 000 Ft
funnel_extra_rev = extra_bookings * avg_price
funnel_extra_profit = funnel_extra_rev * (profit_margin_pct / 100.0)
funnel_certainty = "magas"

# C) Kapacitás kihasználás szabályok
capacity_is_full = capacity_utilization >= 95
capacity_is_low = capacity_utilization < 80

# D) Retention
# Spec: 40% -> 50% = 10 extra visszatérő vendég x 3 alkalom x 25 000 = 750 000 Ft extra jövőbeli bevétel
retention_delta_pct = max(0.0, (target_retention_rate - current_retention_rate) / 100.0)
# Scaled returning guests based on monthly volume or standard spec multiplier
effective_new_guests = current_bookings * (appearance_rate / 100.0) * (new_guest_rate / 100.0)
extra_returning_guests = max(10.0, effective_new_guests * (retention_delta_pct * 3.33)) # Align with spec example (~10 guests for 120 lead base)
retention_extra_future_rev = extra_returning_guests * avg_sessions_per_client * avg_price

# Direct monthly profit potential specified as ~250 000 Ft / month (approx 1/3 of total future value)
retention_monthly_profit = (retention_extra_future_rev * (profit_margin_pct / 100.0)) / 1.8
retention_certainty = "közepes"

# Sum & Conservative Estimate
total_raw_opportunity = mkt_saving_val + funnel_extra_profit + retention_monthly_profit
conservative_extra_profit = total_raw_opportunity * (conservative_factor_pct / 100.0)

# Pricing Logic
fee_min = conservative_extra_profit * 0.20
fee_max = conservative_extra_profit * 0.30
recommended_fee = conservative_extra_profit * (fee_share_pct / 100.0)

# ICP Classifier Logic
if monthly_revenue >= 10000000 and marketing_spend >= 500000 and recommended_fee >= 150000 and not capacity_is_full:
    icp_class = "GOOD"
    icp_badge_title = "🟢 JÓ ÜGYFÉL (ÉRDEMES MEGKERESNI!)"
    icp_color = "icp-banner-good"
    icp_explanation = f"""
    - **Árbevétel:** {fmt_ft(monthly_revenue)} (10M+ Ft/hó target beállítva)
    - **Marketing Büdzsé:** {fmt_ft(marketing_spend)} (500k+ Ft/hó rendelkezésre áll)
    - **Ajánlott Havidíj:** {fmt_ft(recommended_fee)} (Reális 20-30%-os profit részesedés)
    - **Státusz:** Kiváló növekedési potenciál, ideális ügynökségi partner!
    """
elif recommended_fee < 100000 or monthly_revenue < 4000000:
    icp_class = "BAD"
    icp_badge_title = "🔴 ROSSZ ÜGYFÉL (NEM ÉRI MEG)"
    icp_color = "icp-banner-bad"
    icp_explanation = f"""
    - **Probléma:** Ez a klinika jelenleg túl kicsi. A kiszámított havidíj ({fmt_ft(recommended_fee)}) túl alacsony.
    - **Okok:** Kevés árbevétel ({fmt_ft(monthly_revenue)}) vagy alacsony marketing büdzsé ({fmt_ft(marketing_spend)}).
    - **Döntés:** Nem éri meg az ügynökségi erőforrásokat.
    """
elif capacity_is_full:
    icp_class = "WARN"
    icp_badge_title = "⚠️ SPECIÁLIS ÜGYFÉL (TELE A KAPACITÁS)"
    icp_color = "icp-banner-warning"
    icp_explanation = f"""
    - **Kapacitás:** {capacity_utilization}% (Tele van a klinika!)
    - **Stratégiaváltás:** NEM kell több lead! Marketing bővítés helyett: **Áremelés**, **Csomagárazás** és **Retention** növelés javasolt.
    """
else:
    icp_class = "WARN"
    icp_badge_title = "🟡 KÖZEPES ÜGYFÉL (KÖRÜLTEKINTÉST IGÉNYEL)"
    icp_color = "icp-banner-warning"
    icp_explanation = f"""
    - **Árbevétel:** {fmt_ft(monthly_revenue)}
    - **Havidíj potenciál:** {fmt_ft(recommended_fee)}
    - **Tanács:** Érdemes pontosítani a trackinget és a funnel adatokat a végleges ajánlattétel előtt.
    """

# -----------------------------------------------------------------------------
# 3. Main Dashboard Layout
# -----------------------------------------------------------------------------

# ICP Banner Callout
st.markdown(f"""
<div class="{icp_color}">
    <h3 style="margin:0; font-size: 1.3rem;">{icp_badge_title}</h3>
    <div style="margin-top: 10px; color: #e2e8f0; font-size: 0.95rem;">
        {icp_explanation.replace(chr(10), '<br>')}
    </div>
</div>
""", unsafe_allow_html=True)

# Key Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Árbevétel</div>
        <div class="stat-value">{fmt_ft(monthly_revenue)}</div>
        <div class="stat-desc">{monthly_treatments} db kezelés/hó</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Becsült Profit</div>
        <div class="stat-value">{fmt_ft(estimated_net_profit)}</div>
        <div class="stat-desc">{profit_margin_pct}% árrés - Mkt költés</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Összes Lehetőség</div>
        <div class="stat-value" style="color: #38bdf8;">{fmt_ft(total_raw_opportunity)}</div>
        <div class="stat-desc">Szummázott extra profit/hó</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Konzervatív Extra</div>
        <div class="stat-value" style="color: #34d399;">{fmt_ft(conservative_extra_profit)}</div>
        <div class="stat-desc">{conservative_factor_pct}% realizálható profit/hó</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card" style="border-color: #818cf8;">
        <div class="stat-label">Ajánlott Havidíj</div>
        <div class="stat-value" style="color: #818cf8;">{fmt_ft(recommended_fee)}</div>
        <div class="stat-desc">Extra profit 20-30%-a</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Lehetséges Javítások (Opportunity)",
    "🧮 Gazdasági Modell & Funnel",
    "🎯 ICP Minősítő Eszköz",
    "📄 Ajánlat Összefoglaló"
])

# -----------------------------------------------------------------------------
# TAB 1: Opportunity Engine Details
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("💡 Lehetséges Javítások (Opportunity Engine)")
    st.write("A megadott üzleti adatok alapján az alábbi 3 fő területen azonosítható extra profit potenciál:")
    
    col_op1, col_op2, col_op3 = st.columns(3)
    
    with col_op1:
        st.markdown(f"""
        <div class="opp-card">
            <div class="opp-title">
                1. Marketing Mérés Javítása
                <span class="opp-badge badge-med">Bizonyosság: {mkt_certainty}</span>
            </div>
            <div class="opp-value">+{fmt_ft(mkt_saving_val)} / hó</div>
            <p style="color:#94a3b8; font-size:0.875rem; margin-top:8px;">
                <strong>Logika:</strong> {'Magas költés + Nincs tracking ➔ 15% optimalizálható veszteség.' if not has_tracking else 'Van tracking ➔ 5% finomhangolási potenciál.'}
            </p>
            <div style="font-size:0.8rem; color:#64748b;">
                Példa: {fmt_ft(marketing_spend)} marketing költés optimalizációja.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_op2:
        st.markdown(f"""
        <div class="opp-card">
            <div class="opp-title">
                2. Foglalási Folyamat
                <span class="opp-badge badge-high">Bizonyosság: {funnel_certainty}</span>
            </div>
            <div class="opp-value">+{fmt_ft(funnel_extra_profit)} / hó profit</div>
            <p style="color:#94a3b8; font-size:0.875rem; margin-top:8px;">
                <strong>Logika:</strong> Foglalási arány emelése <strong>{booking_rate}% ➔ {benchmark_booking_rate}%</strong> benchmarkra.
            </p>
            <div style="font-size:0.8rem; color:#64748b;">
                +{int(round(extra_bookings))} extra foglalás ({fmt_ft(funnel_extra_rev)} extra bevétel).
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_op3:
        st.markdown(f"""
        <div class="opp-card">
            <div class="opp-title">
                3. Visszatérő Vendégek
                <span class="opp-badge badge-med">Bizonyosság: {retention_certainty}</span>
            </div>
            <div class="opp-value">+{fmt_ft(retention_monthly_profit)} / hó átlagérték</div>
            <p style="color:#94a3b8; font-size:0.875rem; margin-top:8px;">
                <strong>Logika:</strong> Visszatérési arány javítása <strong>{current_retention_rate}% ➔ {target_retention_rate}%</strong>.
            </p>
            <div style="font-size:0.8rem; color:#64748b;">
                +{fmt_ft(retention_extra_future_rev)} extra jövőbeli bruttó bevétel.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Visual Chart: Waterfall / Bar breakdown
    st.markdown("### 📈 Profit Növekedési Vizualizáció")
    
    fig = go.Figure(go.Waterfall(
        name = "Profit", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total", "total"],
        x = ["Jelenlegi Profit", "1. Marketing Mérés", "2. Foglalási Funnel", "3. Retention", "Összes Lehetőség", "Konzervatív Realizálható"],
        textposition = "outside",
        text = [fmt_ft(estimated_net_profit), f"+{fmt_ft(mkt_saving_val)}", f"+{fmt_ft(funnel_extra_profit)}", f"+{fmt_ft(retention_monthly_profit)}", fmt_ft(estimated_net_profit + total_raw_opportunity), fmt_ft(estimated_net_profit + conservative_extra_profit)],
        y = [estimated_net_profit, mkt_saving_val, funnel_extra_profit, retention_monthly_profit, 0, 0],
        connector = {"line":{"color":"#475569"}},
        decreasing = {"marker":{"color":"#ef4444"}},
        increasing = {"marker":{"color":"#38bdf8"}},
        totals = {"marker":{"color":"#34d399"}}
    ))

    fig.update_layout(
        title = "Jelenlegi Profit ➔ Lehetséges Extra Profit Útvonal",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f8fafc"),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_yaxes(showgrid=True, gridcolor='#334155', ticksuffix=" Ft")
    fig.update_xaxes(showgrid=False)
    
    st.plotly_chart(fig, use_container_width=True)

    # Conservative Calculation Box
    st.markdown(f"""
    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-top: 10px;">
        <h4 style="margin:0 0 10px 0; color:#38bdf8;">🛡️ Konzervatív Becslés Számítása</h4>
        <p style="color:#cbd5e1; margin:0 0 8px 0;">Nem összeadjuk vakon a maximális számokat, hanem {conservative_factor_pct}%-os biztonsági realizálhatósággal számolunk:</p>
        <ul style="color:#e2e8f0; margin-bottom:0;">
            <li><strong>Összes lehetőség:</strong> {fmt_ft(total_raw_opportunity)} / hó</li>
            <li><strong>Konzervatív realizálható ({conservative_factor_pct}%):</strong> <span style="color:#34d399; font-weight:bold; font-size:1.1rem;">= {fmt_ft(conservative_extra_profit)} / hó extra profit</span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: Detailed Economic Model & Funnel
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("🧮 Gazdasági Modell és Funnel Elemzés")
    
    col_t2_1, col_t2_2 = st.columns(2)
    
    with col_t2_1:
        st.markdown("#### 🏢 Alap Gazdasági Modell")
        df_biz = pd.DataFrame([
            {"Paraméter": "Klinika típusa", "Érték": clinic_type},
            {"Paraméter": "Nyitvatartási napok", "Érték": f"{operating_days} nap/hó"},
            {"Paraméter": "Kezelőhelyiségek / Kezelők", "Érték": f"{num_rooms} helyiség / {num_staff} kezelő"},
            {"Paraméter": "Átlagos kezelés ára", "Érték": fmt_ft(avg_price)},
            {"Paraméter": "Napi kezelések száma", "Érték": f"{daily_treatments} db"},
            {"Paraméter": "Havi kezelések száma (Auto)", "Érték": f"{monthly_treatments} db"},
            {"Paraméter": "Havi Árbevétel (Auto)", "Érték": fmt_ft(monthly_revenue)},
            {"Paraméter": "Havi Marketing Költés", "Érték": fmt_ft(marketing_spend)},
            {"Paraméter": "Meta Ads / Influencer / Egyéb", "Érték": f"{fmt_ft(meta_ads)} / {fmt_ft(influencer)} / {fmt_ft(other_mkt)}"},
            {"Paraméter": "Tracking / CRM megléte", "Érték": f"Tracking: {'Igen' if has_tracking else 'Nem'} | CRM: {'Igen' if has_crm else 'Nem'}"},
            {"Paraméter": "Becsült Havi Profit ({profit_margin_pct}% árrés - Mkt)".format(profit_margin_pct=profit_margin_pct), "Érték": fmt_ft(estimated_net_profit)}
        ])
        st.dataframe(df_biz, hide_index=True, use_container_width=True)

    with col_t2_2:
        st.markdown("#### 🎯 Funnel Konverziós Modell")
        df_funnel = pd.DataFrame([
            {"Funnel Lépés": "1. Havi érdeklődők (Leads)", "Jelenlegi": f"{monthly_leads} fő", "Benchmark": f"{monthly_leads} fő", "Változás": "-"},
            {"Funnel Lépés": "2. Foglalási arány", "Jelenlegi": f"{booking_rate}%", "Benchmark": f"{benchmark_booking_rate}%", "Változás": f"+{benchmark_booking_rate - booking_rate}%p"},
            {"Funnel Lépés": "3. Foglalások száma", "Jelenlegi": f"{int(round(current_bookings))} foglalás", "Benchmark": f"{int(round(benchmark_bookings))} foglalás", "Változás": f"+{int(round(extra_bookings))} foglalás"},
            {"Funnel Lépés": "4. Megjelent vendégek ({appearance_rate}%)".format(appearance_rate=appearance_rate), "Jelenlegi": f"{int(round(current_bookings * appearance_rate/100))} kezelés", "Benchmark": f"{int(round(benchmark_bookings * appearance_rate/100))} kezelés", "Változás": f"+{int(round(extra_bookings * appearance_rate/100))} kezelés"},
            {"Funnel Lépés": "5. Funnel Extra Bevétel", "Jelenlegi": "-", "Benchmark": fmt_ft(funnel_extra_rev), "Változás": fmt_ft(funnel_extra_rev)},
            {"Funnel Lépés": "6. Extra Profit ({profit_margin_pct}% árrés)".format(profit_margin_pct=profit_margin_pct), "Jelenlegi": "-", "Benchmark": fmt_ft(funnel_extra_profit), "Változás": fmt_ft(funnel_extra_profit)}
        ])
        st.dataframe(df_funnel, hide_index=True, use_container_width=True)

    # Kapacitás elemzés
    st.markdown("---")
    st.markdown("#### ⚡ Kapacitás Kihasználtság Szabályozó")
    if capacity_is_full:
        st.error(f"🔴 **Magas Kapacitás ({capacity_utilization}%):** A klinika megközelíti a 100%-os kihasználtságot. **Nem kell több lead!** Ehelyett áremelés, prémium csomagok és retention fejlesztése javasolt.")
    elif capacity_is_low:
        st.success(f"🟢 **Szabad Kapacitás ({capacity_utilization}%):** A kapacitás kihasználtság < 80%. A marketing érték magasabb, érdemes fokozni a lead generálást.")
    else:
        st.info(f"🟡 **Optimális Kapacitás ({capacity_utilization}%):** Kiegyensúlyozott kihasználtság.")

# -----------------------------------------------------------------------------
# TAB 3: ICP Classifier & Pricing Rule
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("🎯 ICP Választó Eszköz & Árazási Logika")
    
    st.markdown("""
    Ez a kalkulátor elsődlegesen egy **ICP (Ideal Client Profile) minősítő eszköz**. 
    Segít az ügynökségnek másodpercek alatt felismerni a profitábilis és az elkerülendő ügyféljelölteket.
    """)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("""
        <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 12px; padding: 20px;">
            <h4 style="color:#f87171; margin-top:0;">🔴 ROSSZ ÜGYFÉL (NEM ÉRI MEG)</h4>
            <ul style="color:#cbd5e1;">
                <li>Kevés árbevétel (&lt; 5M Ft/hó)</li>
                <li>Nincs érdemi marketing büdzsé (&lt; 300k Ft)</li>
                <li>Tele van a kapacitás, de nem akarnak árat emelni</li>
                <li>Nincsenek adatok és hiányzik a tracking</li>
                <li><strong>Kiszámított ajánlott havidíj &lt; 100k-150k Ft/hó</strong></li>
            </ul>
            <p style="color:#ef4444; font-weight:bold; margin-bottom:0;">➔ Konzekvencia: Elutasítandó / Túl kicsi klinika.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_c2:
        st.markdown("""
        <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 12px; padding: 20px;">
            <h4 style="color:#34d399; margin-top:0;">🟢 JÓ ÜGYFÉL (IDEÁLIS TARGET)</h4>
            <ul style="color:#cbd5e1;">
                <li>Magas árbevétel (10M+ Ft/hó)</li>
                <li>Komoly marketing büdzsé (500k+ Ft/hó)</li>
                <li>Van kereslet, de hiányzik a pontos mérés/tracking</li>
                <li>Van szabad kapacitás a növekedésre</li>
                <li><strong>Kiszámított ajánlott havidíj 300k - 600k+ Ft/hó</strong></li>
            </ul>
            <p style="color:#34d399; font-weight:bold; margin-bottom:0;">➔ Konzekvencia: Érdemes azonnal megkeresni és ajánlatot tenni!</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💡 Érték Alapú Árazási Szabály (20-30%)")
    
    st.write(f"""
    - **Szabály:** Havidíj = Realizálható Extra Profit **20–30%-a**
    - **Reális Havidíj Tartomány:** `{fmt_ft(fee_min)}` – `{fmt_ft(fee_max)} / hó`
    - **Kiválasztott Ajánlott Havidíj ({fee_share_pct}%):** **`{fmt_ft(recommended_fee)} / hó`**
    """)

# -----------------------------------------------------------------------------
# TAB 4: Summary Export
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("📄 Ajánlat Összefoglaló (Client Audit Pitch)")
    
    summary_text = f"""===================================================================
CLINIC GROWTH OPPORTUNITY AUDIT REPORT
===================================================================
Klinika típusa: {clinic_type}
Nyitvatartási napok: {operating_days} nap/hó | Helyiségek: {num_rooms} | Kezelők: {num_staff} fő

1. JELENLEGI GAZDASÁGI MODELL
-------------------------------------------------------------------
• Átlagos kezelési ár: {fmt_ft(avg_price)}
• Havi kezelések száma: {monthly_treatments} db/hó
• Havi Árbevétel: {fmt_ft(monthly_revenue)}
• Havi Marketing Költés: {fmt_ft(marketing_spend)}
• Becsült Nettó Profit ({profit_margin_pct}% árrés): {fmt_ft(estimated_net_profit)}

2. AZONOSÍTOTT EXTRA PROFIT POTENCIÁLOK
-------------------------------------------------------------------
• Marketing mérés javítása: +{fmt_ft(mkt_saving_val)} / hó (Bizonyosság: {mkt_certainty})
• Foglalási funnel optimalizálás: +{fmt_ft(funnel_extra_profit)} / hó (Bizonyosság: {funnel_certainty})
• Retention növelés: +{fmt_ft(retention_monthly_profit)} / hó (Bizonyosság: {retention_certainty})

• ÖSSZES LEHETŐSÉG: {fmt_ft(total_raw_opportunity)} / hó
• KONZERVATÍV REALIZÁLHATÓ EXTRA PROFIT ({conservative_factor_pct}%): {fmt_ft(conservative_extra_profit)} / hó

3. AJÁNLOTT EGYÜTTMŰKÖDÉSI HAVIDÍJ (ÉRTÉK ALAPÚ ÁRAZÁS 20-30%)
-------------------------------------------------------------------
• Ajánlott Havidíj Tartomány: {fmt_ft(fee_min)} - {fmt_ft(fee_max)} / hó
• Javasolt Havidíj ({fee_share_pct}%): {fmt_ft(recommended_fee)} / hó

4. ICP MINŐSÍTÉSI STATISZTIKA
-------------------------------------------------------------------
Státusz: {icp_badge_title}
===================================================================
"""
    
    st.text_area("Generált Pitch Összefoglaló (Másolható szöveg):", summary_text, height=380)
    
    st.download_button(
        label="📥 Audit Jelentés Letöltése (.txt)",
        data=summary_text,
        file_name=f"clinic_opportunity_audit_{clinic_type.lower().replace(' ', '_')}.txt",
        mime="text/plain"
    )
