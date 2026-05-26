import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from utils.data_fetchers import (
    fetch_polymarket_markets,
    fetch_live_assets,
    get_preset_markets,
    get_historical_data
)
from utils.correlation import (
    calculate_pearson_correlation,
    get_correlation_interpretation
)

# Page Setup
st.set_page_config(
    page_title="SentIndex - Polymarket Sentiment Dashboard",
    page_icon="🔮",
    layout="wide"
)

# Load Custom CSS (Minimal styling only)
styles_path = os.path.join(os.path.dirname(__file__), 'styles.css')
if os.path.exists(styles_path):
    with open(styles_path, 'r', encoding='utf-8') as f:
        custom_css = f.read()
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# App Header
st.markdown('<div class="main-title">🔮 SentIndex</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Polymarket várakozások és a pénzügyi piacok korrelációja</div>', unsafe_allow_html=True)

# Fetch Live Prices (Cached for Session)
@st.cache_data(ttl=60)
def get_cached_assets():
    return fetch_live_assets()

live_assets = get_cached_assets()

# Sidebar: Simple, native tickers and settings
st.sidebar.title("📈 Élő Árfolyamok")
for asset, val in live_assets.items():
    st.sidebar.metric(label=asset, value=f"{val:,}")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Beállítások")
history_days = st.sidebar.slider("Időtáv (napok)", min_value=15, max_value=90, value=30, step=5)

# --- SECTION 1: Globális SentIndex ---
st.subheader("🔮 Globális SentIndex Hangulat")

# We dynamically calculate the index based on preset markets
presets = get_preset_markets()
total_weight = 0
weighted_sentiment = 0

for p in presets:
    weighted_sentiment += (p["yes_prob"] * p["weight"])
    total_weight += abs(p["weight"])

raw_score = (weighted_sentiment / total_weight) + 50
normalized_score = max(0, min(100, round(raw_score, 1)))

# Determine label and color
if normalized_score > 60:
    sentiment_label = "+ Kockázatvállaló (Risk-On)"
    sentiment_color = "normal"
elif normalized_score < 40:
    sentiment_label = "- Kockázatkerülő (Risk-Off)"
    sentiment_color = "normal"
else:
    sentiment_label = "Semleges (Neutral)"
    sentiment_color = "off"

col1, col2 = st.columns([1, 2])

with col1:
    # Use native Streamlit metrics and progress bar instead of custom SVG elements
    st.metric(
        label="Aktuális Globális SentIndex",
        value=f"{normalized_score}%",
        delta=sentiment_label,
        delta_color=sentiment_color
    )
    st.progress(normalized_score / 100.0)

with col2:
    st.info(
        f"A **SentIndex** a Polymarket legfontosabb globális predikcióinak (geopolitika, gazdaság, tech) súlyozott hangulati mutatója. "
        f"A geopolitikai feszültségek (pl. közel-keleti helyzet eszkalációja) növelik a kockázatkerülést (Risk-Off), ami "
        f"történelmileg gyengíti a forintot (USD/HUF emelkedés) és erősíti a menedék-eszközöket."
    )

st.markdown("---")

# --- SECTION 2: Asset Correlation Playground ---
st.subheader("📊 Korrelációs Elemző (Correlation Playground)")

# Selectbox inputs for comparisons
col_sel_1, col_sel_2 = st.columns(2)
preset_options = [p["question"] for p in presets]

with col_sel_1:
    selected_market = st.selectbox("Válassz egy predikciós piacot:", preset_options)
with col_sel_2:
    selected_asset = st.selectbox("Válassz egy összehasonlítandó árfolyamot / devizát:", list(live_assets.keys()))

# Generate Aligned Historical Data
df_hist = get_historical_data(selected_market, selected_asset, days=history_days)

# Calculate Correlation
corr_coeff = calculate_pearson_correlation(df_hist)
interpretation = get_correlation_interpretation(corr_coeff, selected_market, selected_asset)

# Create Dual-Axis Plotly Chart
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add Probability Trace (Left Y-Axis)
fig.add_trace(
    go.Scatter(
        x=df_hist["Date"],
        y=df_hist["Probability"],
        name="Polymarket Valószínűség (%)",
        line=dict(color="#00f2fe", width=2),
        mode="lines+markers"
    ),
    secondary_y=False
)

# Add Asset Price Trace (Right Y-Axis)
fig.add_trace(
    go.Scatter(
        x=df_hist["Date"],
        y=df_hist["AssetPrice"],
        name=f"{selected_asset} Árfolyam",
        line=dict(color="#8a4fff", width=2),
        mode="lines+markers"
    ),
    secondary_y=True
)

fig.update_layout(
    xaxis=dict(title="Dátum"),
    yaxis=dict(title="Polymarket Valószínűség (%)", ticksuffix="%", range=[0, 105]),
    yaxis2=dict(title=f"{selected_asset} Árfolyam"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40),
    hovermode="x unified",
    height=400
)

col_chart, col_details = st.columns([2, 1])

with col_chart:
    st.plotly_chart(fig, use_container_width=True)

with col_details:
    corr_class = "corr-positive" if corr_coeff > 0.2 else ("corr-negative" if corr_coeff < -0.2 else "corr-neutral")
    st.markdown(
        f'''
        <div style="background: rgba(255,255,255,0.02); padding: 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); height: 100%;">
            <h4 style="margin: 0 0 10px 0; color: #ffffff;">Korrelációs mutató</h4>
            <div class="correlation-value {corr_class}">{corr_coeff}</div>
            <p style="text-align: center; font-size: 0.9rem; font-weight: bold; color: #ffffff; margin-bottom: 15px;">
                Típus: {interpretation["strength"]} {interpretation["direction"]} korreláció
            </p>
            <div style="font-size: 0.85rem; line-height: 1.4; color: #bbbbcc;">
                {interpretation["explanation"]}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

st.markdown("---")

# --- SECTION 3: Live Polymarket Explorer ---
st.subheader("🔍 Élő Polymarket Kereső")

col_search_1, col_search_2 = st.columns([3, 1])
with col_search_1:
    search_query = st.text_input("Keresés kulcsszó alapján:", placeholder="pl. war, election, rate, crypto...")
with col_search_2:
    category_filter = st.selectbox("Szűrés kategóriára:", ["Összes", "Geopolitics", "Crypto", "Economy", "AI", "Other"])

# Call live api
live_markets = fetch_polymarket_markets(search_query)

# Filter by category if selected
if category_filter != "Összes":
    live_markets = [m for m in live_markets if m["category"].lower() == category_filter.lower() or (category_filter == "Other" and m["category"] not in ["Geopolitics", "Crypto", "Economy", "AI"])]

if live_markets:
    # Display in columns natively managed by Streamlit (guarantees perfect grid alignment)
    cols_per_row = 3
    for i in range(0, len(live_markets[:12]), cols_per_row):
        row_markets = live_markets[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, market in enumerate(row_markets):
            with cols[idx]:
                st.markdown(
                    f'''
                    <div class="market-card">
                        <div class="market-category">{market["category"]}</div>
                        <div class="market-title">{market["question"]}</div>
                        <div class="market-odds-container">
                            <div class="odds-badge odds-yes">YES: {market["yes_prob"]:.1f}%</div>
                            <div class="odds-badge odds-no">NO: {market["no_prob"]:.1f}%</div>
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
else:
    st.info("Nem található aktív piac a keresési feltételekkel. Kérlek, próbálj más kifejezést!")
