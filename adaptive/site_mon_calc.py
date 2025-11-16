import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Adaptive Media - Bevétel Becslő",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Inicializálás
if 'scenario_1' not in st.session_state:
    st.session_state.scenario_1 = {}
if 'scenario_2' not in st.session_state:
    st.session_state.scenario_2 = {}
if 'scenario_3' not in st.session_state:
    st.session_state.scenario_3 = {}

# Makrogazdasági tényezők (fix)
MACRO_FACTORS = {
    2026: {
        'inflacio': 1.035,
        'gdp': 1.042,
        'reklamkoltes': 1.11,
        'cookieless': 0.92,
        'ai': 1.12
    },
    2027: {
        'inflacio': 1.03,
        'gdp': 1.033,
        'reklamkoltes': 1.12,
        'cookieless': 0.91,
        'ai': 1.10
    }
}

def calculate_macro_multiplier(year):
    factors = MACRO_FACTORS[year]
    return factors['inflacio'] * factors['gdp'] * factors['reklamkoltes'] * factors['cookieless'] * factors['ai']

def calculate_brand_safety_index(szenztiv, karos, user_elegedettseg):
    return (szenztiv + karos + user_elegedettseg) / 3

def calculate_weboldal_multiplier(markaertek, brand_safety, szezonalitas, sulyok):
    w_marka, w_bs, w_szezon = sulyok
    brand_safety_multiplier = 0.8 + brand_safety*0.4 
    return (markaertek * w_marka + brand_safety_multiplier * w_bs + szezonalitas * w_szezon)

def calculate_impressions(real_users, pageviews, mobil_arany, desktop_arany, mobil_zones, desktop_zones):
    avg_zones = (mobil_arany/100 * mobil_zones) + (desktop_arany/100 * desktop_zones)
    return real_users * pageviews * avg_zones

def calculate_revenue(inputs):
    results = {}
    
    for year in [2026]:
        # Impressions
        total_impressions = calculate_impressions(
            inputs['real_users'],
            inputs['pageviews'],
            inputs['mobil_arany'],
            inputs['desktop_arany'],
            inputs['mobil_zones'],
            inputs['desktop_zones']
        )

        monetizable = total_impressions * (inputs['fill_rate'] / 100)

        # Brand Safety Index
        bs_key = f'bs_{year}'
        brand_safety = calculate_brand_safety_index(
            inputs[f'{bs_key}_szenzitiv'],
            inputs[f'{bs_key}_karos'],
            inputs[f'{bs_key}_user']
        )
        
        # Multiplikátorok
        macro_mult = calculate_macro_multiplier(year)
        macro_mult = 1
        weboldal_mult = calculate_weboldal_multiplier(
            inputs['markaertek'],
            brand_safety,
            inputs['szezonalitas'],
            (inputs['suly_marka']/100, inputs['suly_bs']/100, inputs['suly_szezon']/100)
        )
        weboldal_mult = 1
        
        total_multiplier = macro_mult * weboldal_mult
        
        # Kategóriák
        categories = {
            'Időalapú': {'ratio': inputs['inv_idoalapu'], 'base_cpm': 1700},
            'AV alapú': {'ratio': inputs['inv_av'], 'base_cpm': 2100},
            'CT': {'ratio': inputs['inv_ct'], 'base_cpm': 300},
            'PMP Display': {'ratio': inputs['inv_pmp_display'], 'base_cpm': 850},
            'Open Display': {'ratio': inputs['inv_open_display'], 'base_cpm': 175},
            'PMP Video': {'ratio': inputs['inv_pmp_video'], 'base_cpm': 2000},
            'Open Video': {'ratio': inputs['inv_open_video'], 'base_cpm': 600},
            'Üres': {'ratio': inputs['inv_ures'], 'base_cpm': 0}
        }

        category_revenues = {}
        for cat_name, cat_data in categories.items():
            impressions = monetizable * (cat_data['ratio'] / 100)
            cpm = cat_data['base_cpm'] * total_multiplier
            revenue = (impressions * cpm) / 1000
            category_revenues[cat_name] = {
                'impressions': impressions,
                'cpm': cpm,
                'revenue': revenue
            }
        
        total_monthly = sum([v['revenue'] for v in category_revenues.values()])
        total_yearly = total_monthly * 12
        adaptive_share = total_yearly * 0.5
        
        results[year] = {
            'total_impressions': total_impressions,
            'monetizable': monetizable,
            'macro_mult': macro_mult,
            'weboldal_mult': weboldal_mult,
            'brand_safety': brand_safety,
            'categories': category_revenues,
            'total_monthly': total_monthly,
            'total_yearly': total_yearly,
            'adaptive_share': adaptive_share
        }
    
    return results

def render_inputs(prefix="main"):
    cols = st.columns([2, 3])
    
    with cols[0]:
        st.subheader("📊 Forgalmi jellemzők")
        real_users = st.number_input("Havi Real Users", min_value=0, value=400000, step=10000, key=f"{prefix}_users")
        pageviews = st.number_input("Oldalmegtekintés/user/hó", min_value=1, value=3, step=1, key=f"{prefix}_pv")
        
        col1, col2 = st.columns(2)
        with col1:
            mobil_arany = st.number_input("Mobil arány (%)", min_value=0, max_value=100, value=75, key=f"{prefix}_mobil")
        with col2:
            desktop_arany = 100 - mobil_arany
            st.metric("Desktop arány (%)", desktop_arany)
        
        col1, col2 = st.columns(2)
        with col1:
            mobil_zones = st.number_input("Banner zónák (mobil)", min_value=1, value=5, key=f"{prefix}_mz")
        with col2:
            desktop_zones = st.number_input("Banner zónák (desktop)", min_value=1, value=3, key=f"{prefix}_dz")
        
        fill_rate = st.slider("Fill Rate (%)", min_value=0, max_value=100, value=70, key=f"{prefix}_fill")
        
        st.subheader("📦 Inventory kategorizálás")
        st.caption("Összesen: 100%")
        
        inv_idoalapu = st.slider("Időalapú (%)", 0, 100, 10, key=f"{prefix}_inv1")
        inv_av = st.slider("AV alapú (%)", 0, 100, 10, key=f"{prefix}_inv2")
        inv_ct = st.slider("CT (%)", 0, 100, 0, key=f"{prefix}_inv3")
        inv_pmp_display = st.slider("PMP Display (%)", 0, 100, 7, key=f"{prefix}_inv4")
        inv_open_display = st.slider("Open Display (%)", 0, 100, 25, key=f"{prefix}_inv5")
        inv_pmp_video = st.slider("PMP Video (%)", 0, 100, 3, key=f"{prefix}_inv6")
        inv_open_video = st.slider("Open Video (%)", 0, 100, 15, key=f"{prefix}_inv7")
        inv_ures = st.slider("Üres (%)", 0, 100, 30, key=f"{prefix}_inv8")
        
        total_inv = inv_idoalapu + inv_av + inv_ct + inv_pmp_display + inv_open_display + inv_pmp_video + inv_open_video + inv_ures
        if total_inv != 100:
            st.error(f"⚠️ Az inventory kategóriák összege: {total_inv}% (kellene: 100%)")
        else:
            st.success("✅ Inventory kategóriák összege: 100%")
        
        st.subheader("🎯 Márkaérték")
        markaertek_options = {
            "Induló Website": 0.8,
            "Rosszul pozicionált márka": 0.9,
            "Jól pozicionált márka": 1.1
        }
        markaertek_choice = st.selectbox("Válassz márkaértéket:", list(markaertek_options.keys()), index=2, key=f"{prefix}_marka")
        markaertek = markaertek_options[markaertek_choice]
        
        st.subheader("🛡️ Brand Safety Index komponensek")
        col1, col2, col3 = st.columns(3)
        with col1:
            bs_2026_szenzitiv = st.slider("Szenzitív", 0.0, 1.0, 0.9, 0.1, key=f"{prefix}_bs26_s")
        with col2:
            bs_2026_karos = st.slider("Káros", 0.0, 1.0, 0.9, 0.1, key=f"{prefix}_bs26_k")
        with col3:
            bs_2026_user = st.slider("User elég.", 0.0, 1.0, 0.9, 0.1, key=f"{prefix}_bs26_u")
        
        st.subheader("⚖️ Weboldal jellemzők súlyai")
        st.caption("Összesen: 100%")
        suly_marka = st.slider("Márkaérték súlya (%)", 0, 100, 30, key=f"{prefix}_w1")
        suly_bs = st.slider("Brand Safety szorzó súlya (%)", 0, 100, 20, key=f"{prefix}_w2")
        suly_szezon = st.slider("Szezonalitás súlya (%)", 0, 100, 50, key=f"{prefix}_w3")
        
        total_suly = suly_marka + suly_bs + suly_szezon
        if total_suly != 100:
            st.error(f"⚠️ Súlyok összege: {total_suly}% (kellene: 100%)")
        else:
            st.success("✅ Súlyok összege: 100%")
        
        szezonalitas = st.slider("Szezonalitás értéke", 0.5, 2.0, 1.5, 0.1, key=f"{prefix}_szezon")
    
    return {
        'real_users': real_users,
        'pageviews': pageviews,
        'mobil_arany': mobil_arany,
        'desktop_arany': desktop_arany,
        'mobil_zones': mobil_zones,
        'desktop_zones': desktop_zones,
        'fill_rate': fill_rate,
        'inv_idoalapu': inv_idoalapu,
        'inv_av': inv_av,
        'inv_ct': inv_ct,
        'inv_pmp_display': inv_pmp_display,
        'inv_open_display': inv_open_display,
        'inv_pmp_video': inv_pmp_video,
        'inv_open_video': inv_open_video,
        'inv_ures': inv_ures,
        'markaertek': markaertek,
        'bs_2026_szenzitiv': bs_2026_szenzitiv,
        'bs_2026_karos': bs_2026_karos,
        'bs_2026_user': bs_2026_user,
        'suly_marka': suly_marka,
        'suly_bs': suly_bs,
        'suly_szezon': suly_szezon,
        'szezonalitas': szezonalitas
    }

def render_results(results, inputs):
    # KPI Cards
    col1, col2 = st.columns(2)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Adaptive éves részesedése</div>
            <div class="kpi-value">{results[2026]['adaptive_share']/1_000_000:.2f}M Ft</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col1:
        avg_gross = results[2026]['total_yearly']
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Bruttó éves bevétel</div>
            <div class="kpi-value">{avg_gross/1_000_000:.2f}M Ft</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts - 2x2 grid
    
    # 1. Inventory vs Revenue Mix (side-by-side bar)
    st.subheader("Inventory vs Bevétel Összetétel")
    cat_data = results[2026]['categories']
    categories = [k for k, v in cat_data.items() if k != 'Üres']
    
    # Inventory arányok
    total_impressions = sum([v['impressions'] for v in cat_data.values()])
    inv_ratios = [(cat_data[c]['impressions'] / total_impressions * 100) for c in categories]
    
    # Bevétel arányok
    total_revenue = sum([v['revenue'] for k, v in cat_data.items() if k != 'Üres'])
    rev_ratios = [(cat_data[c]['revenue'] / total_revenue * 100) for c in categories]
    
    fig_mix = go.Figure(data=[
        go.Bar(name='Inventory arány (%)', x=categories, y=inv_ratios, marker_color='#8B5CF6'),
        go.Bar(name='Bevétel arány (%)', x=categories, y=rev_ratios, marker_color='#10B981')
    ])
    fig_mix.update_layout(
        barmode='group',
        height=350,
        yaxis_title="Arány (%)",
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_mix, use_container_width=True)

    # 2. Marginális Hatás Elemzés - Horizontal Bar Chart
    st.subheader("Marginális Hatás Elemzés")
    st.caption("1%-os paraméter változás hatása az éves bevételre")
    
    # Baseline bevétel
    baseline = results[2026]['adaptive_share']
    
    # Helper function - tesztelünk 1%-os változást
    from copy import deepcopy
    
    def test_marginal(param_name, param_value, is_percentage=False):
        test_inputs = deepcopy(inputs)
        if is_percentage:
            # Ha százalékos érték (pl. Fill Rate), akkor +1 százalékpont
            test_inputs[param_name] = (param_value/100) * 1.01
        else:
            # Ha abszolút érték, akkor +1%
            test_inputs[param_name] = param_value * 1.01
        test_result = calculate_revenue(test_inputs)
        change = test_result[2026]['adaptive_share'] - baseline
        return change
    
    # Paraméterek tesztelése
    marginal_impacts = []
    
    # Forgalmi paraméterek
    marginal_impacts.append({
        'label': 'Real Users / Fill Rate / Pageviews (+1%)',
        'impact': test_marginal('real_users', inputs['real_users']),
        'current': f"{inputs['real_users']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'Időalapú arány (+1%)',
        'impact': test_marginal('inv_idoalapu', inputs['inv_idoalapu']),
        'current': f"{inputs['inv_idoalapu']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'AV alapú arány (+1%)',
        'impact': test_marginal('inv_av', inputs['inv_av']),
        'current': f"{inputs['inv_av']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'CT arány (+1%)',
        'impact': test_marginal('inv_ct', inputs['inv_ct']),
        'current': f"{inputs['inv_ct']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'PMP Display arány (+1%)',
        'impact': test_marginal('inv_pmp_display', inputs['inv_pmp_display']),
        'current': f"{inputs['inv_pmp_display']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'Open Display arány (+1%)',
        'impact': test_marginal('inv_open_display', inputs['inv_open_display']),
        'current': f"{inputs['inv_open_display']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'PMP Video arány (+1%)',
        'impact': test_marginal('inv_pmp_video', inputs['inv_pmp_video']),
        'current': f"{inputs['inv_pmp_video']:,.0f}"
    })

    marginal_impacts.append({
        'label': 'Open Video arány (+1%)',
        'impact': test_marginal('inv_open_video', inputs['inv_open_video']),
        'current': f"{inputs['inv_open_video']:,.0f}"
    })
    
    # Rendezés impact szerint (abszolút értékben)
    marginal_impacts.sort(key=lambda x: abs(x['impact']), reverse=True)
    
    # Bar chart
    labels = [m['label'] for m in marginal_impacts]
    impacts = [m['impact'] / 1000 for m in marginal_impacts]  # ezer Ft-ban
    colors = ['#10b981' if i > 0 else '#ef4444' for i in impacts]
    
    # Tooltip text
    hover_texts = [
        f"{m['label']}<br>Jelenlegi: {m['current']}<br>Hatás: {m['impact']:,.0f} Ft/év"
        for m in marginal_impacts
    ]
    
    fig_marginal = go.Figure(data=[
        go.Bar(
            x=impacts,
            y=labels,
            orientation='h',
            marker=dict(color=colors),
            text=[f"{v:,.0f}k Ft" for v in impacts],
            textposition='auto',
            hovertext=hover_texts,
            hoverinfo='text'
        )
    ])
    
    fig_marginal.update_layout(
        height=450,
        xaxis_title="Éves bevétel változás (ezer Ft)",
        showlegend=False,
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='#cbd5e1')
    )
    st.plotly_chart(fig_marginal, use_container_width=True)

    col3, col4 = st.columns(2)

    # 3. Inventory Utilization Gauge
    with col3:
        st.subheader("Inventory Kihasználtság")
        # Fill rate százalék
        fill_pct = (results[2026]['monetizable'] / results[2026]['total_impressions']) * 100
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fill_pct,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Fill Rate", 'font': {'size': 24}},
            delta={'reference': 65, 'suffix': '%'},
            gauge={
                'axis': {'range': [None, 100], 'ticksuffix': '%'},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 45], 'color': "#fee2e2"},
                    {'range': [45, 65], 'color': "#fef3c7"},
                    {'range': [65, 100], 'color': "#d1fae5"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 65
                }
            }
        ))
        fig_gauge.update_layout(height=350)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # 4. Multiplikátor Breakdown
    with col4:
        st.subheader("Weboldal Jellemzőinek Hatása")
        
        # Számoljuk ki a komponenseket az inputokból
        macro_mult = results[2026]['macro_mult']
        weboldal_mult = results[2026]['weboldal_mult']
        brand_safety = results[2026]['brand_safety']
        
        # Súlyok (normalizálva 0-1 közé)
        w_marka = inputs['suly_marka'] / 100
        w_bs = inputs['suly_bs'] / 100
        w_szezon = inputs['suly_szezon'] / 100
        
        # Komponensek hozzájárulása
        marka_contribution = inputs['markaertek'] * w_marka
        brand_safety_multiplier = 0.8 + brand_safety * 0.4  # Ugyanaz a formula mint a calculate_weboldal_multiplier-ben
        bs_contribution = brand_safety_multiplier * w_bs
        szezon_contribution = inputs['szezonalitas'] * w_szezon
        
        components = ['Márkaérték', 
                      'Brand Safety szorzó', 
                      'Szezonalitás', 
                      'Összesen']
        values = [marka_contribution, bs_contribution, szezon_contribution, weboldal_mult]
        
        colors = ['#8B5CF6', '#EC4899', '#F59E0B', '#667eea']
        
        fig_components = go.Figure(data=[
            go.Bar(
                x=values,
                y=components,
                orientation='h',
                marker=dict(color=colors),
                text=[f"{v:.3f}" for v in values],
                textposition='auto',
            )
        ])
        fig_components.update_layout(
            height=350,
            xaxis_title="Hozzájárulás értéke",
            showlegend=False,
            xaxis=dict(range=[0, max(values) * 1.2])
        )
        st.plotly_chart(fig_components, use_container_width=True)
    
# MAIN APP
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("adaptive.png", width=100)
with col_title:
    st.markdown('<h1 class="main-header">Bevétel Becslő Dashboard</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎯 Kalkulátor", "🔄 Szcenárió Összehasonlítás"])

with tab1:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.header("⚙️ Paraméterek")
        
        # Forgalmi jellemzők
        with st.expander("📊 Forgalmi jellemzők", expanded=True):
            real_users = st.number_input("Havi Real Users", min_value=0, value=400000, step=10000, key="main_users")
            pageviews = st.number_input("Oldalmegtekintés/user/hó", min_value=1, value=3, step=1, key="main_pv")
            
            col1, col2 = st.columns(2)
            with col1:
                mobil_arany = st.number_input("Mobil arány (%)", min_value=0, max_value=100, value=75, key="main_mobil")
            with col2:
                desktop_arany = 100 - mobil_arany
                st.metric("Desktop arány (%)", desktop_arany)
            
            col1, col2 = st.columns(2)
            with col1:
                mobil_zones = st.number_input("Banner zónák (mobil)", min_value=1, value=5, key="main_mz")
            with col2:
                desktop_zones = st.number_input("Banner zónák (desktop)", min_value=1, value=3, key="main_dz")
            
            fill_rate = st.slider("Fill Rate (%)", min_value=0, max_value=100, value=70, key="main_fill")
        
        # Inventory kategorizálás
        with st.expander("📦 Inventory kategorizálás", expanded=True):
            st.caption("Összesen: 100%")
            
            inv_idoalapu = st.slider("Időalapú (%)", 0, 100, 10, key="main_inv1")
            inv_av = st.slider("AV alapú (%)", 0, 100, 10, key="main_inv2")
            inv_ct = st.slider("CT (%)", 0, 100, 0, key="main_inv3")
            inv_pmp_display = st.slider("PMP Display (%)", 0, 100, 7, key="main_inv4")
            inv_open_display = st.slider("Open Display (%)", 0, 100, 25, key="main_inv5")
            inv_pmp_video = st.slider("PMP Video (%)", 0, 100, 3, key="main_inv6")
            inv_open_video = st.slider("Open Video (%)", 0, 100, 15, key="main_inv7")
            inv_ures = (1 - fill_rate/100)*100
            st.text(f"Üres: {inv_ures:.0f}%")
            
            total_inv = inv_idoalapu + inv_av + inv_ct + inv_pmp_display + inv_open_display + inv_pmp_video + inv_open_video + inv_ures
            if total_inv != 100:
                st.error(f"⚠️ Összeg: {total_inv}% (kellene: 100%)")
            else:
                st.success("✅ Összeg: 100%")
        
        # Márkaérték
        with st.expander("🎯 Márkaérték", expanded=True):
            markaertek_options = {
                "Induló Website": 0.8,
                "Rosszul pozicionált márka": 0.9,
                "Jól pozicionált márka": 1.1
            }
            markaertek_choice = st.selectbox("Válassz márkaértéket:", list(markaertek_options.keys()), index=2, key="main_marka")
            markaertek = markaertek_options[markaertek_choice]
        
        # Brand Safety Index
        with st.expander("🛡️ Brand Safety Index", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                bs_2026_szenzitiv = st.slider("Szenzitív", 0.0, 1.0, 0.9, 0.1, key="main_bs26_s")
            with col2:
                bs_2026_karos = st.slider("Káros", 0.0, 1.0, 0.9, 0.1, key="main_bs26_k")
            with col3:
                bs_2026_user = st.slider("User elég.", 0.0, 1.0, 0.9, 0.1, key="main_bs26_u")
            
        # Weboldal jellemzők súlyai
        with st.expander("⚖️ Weboldal jellemzők súlyai", expanded=False):
            st.caption("Összesen: 100%")
            suly_marka = st.slider("Márkaérték súlya (%)", 0, 100, 30, key="main_w1")
            suly_bs = st.slider("Brand Safety szorzó súlya (%)", 0, 100, 20, key="main_w2")
            suly_szezon = st.slider("Szezonalitás súlya (%)", 0, 100, 50, key="main_w3")
            
            total_suly = suly_marka + suly_bs + suly_szezon
            if total_suly != 100:
                st.error(f"⚠️ Súlyok összege: {total_suly}% (kellene: 100%)")
            else:
                st.success("✅ Súlyok összege: 100%")
            
            szezonalitas = st.slider("Szezonalitás értéke", 0.5, 2.0, 1.5, 0.1, key="main_szezon")
        
        # Összes input összegyűjtése
        inputs = {
            'real_users': real_users,
            'pageviews': pageviews,
            'mobil_arany': mobil_arany,
            'desktop_arany': desktop_arany,
            'mobil_zones': mobil_zones,
            'desktop_zones': desktop_zones,
            'fill_rate': fill_rate,
            'inv_idoalapu': inv_idoalapu,
            'inv_av': inv_av,
            'inv_ct': inv_ct,
            'inv_pmp_display': inv_pmp_display,
            'inv_open_display': inv_open_display,
            'inv_pmp_video': inv_pmp_video,
            'inv_open_video': inv_open_video,
            'inv_ures': inv_ures,
            'markaertek': markaertek,
            'bs_2026_szenzitiv': bs_2026_szenzitiv,
            'bs_2026_karos': bs_2026_karos,
            'bs_2026_user': bs_2026_user,
            'suly_marka': suly_marka,
            'suly_bs': suly_bs,
            'suly_szezon': suly_szezon,
            'szezonalitas': szezonalitas
        }
    
    # A tab1-ben ahol hívod:
with col_right:
    st.header("📊 Eredmények")
    results = calculate_revenue(inputs)
    render_results(results, inputs) 

with tab2:
    st.subheader("Szcenárió összehasonlítás")
    st.caption("Hasonlítsd össze különböző paraméterekkel a bevételi eredményeket")
    
    col1, col2, col3 = st.columns(3)
    
    scenarios_inputs = []
    
    for i, col in enumerate([col1, col2, col3], 1):
        with col:
            st.markdown(f"### Szcenárió {i}")
            
            # Forgalmi jellemzők
            with st.expander("📊 Forgalom", expanded=False):
                real_users = st.number_input("Havi Real Users", min_value=0, value=400000, step=10000, key=f"scen{i}_users")
                pageviews = st.number_input("Pageview/user/hó", min_value=1, value=3, step=1, key=f"scen{i}_pv")
                mobil_arany = st.number_input("Mobil arány (%)", min_value=0, max_value=100, value=75, key=f"scen{i}_mobil")
                mobil_zones = st.number_input("Banner (mobil)", min_value=1, value=5, key=f"scen{i}_mz")
                desktop_zones = st.number_input("Banner (desktop)", min_value=1, value=3, key=f"scen{i}_dz")
                fill_rate = st.slider("Fill Rate (%)", 0, 100, 70, key=f"scen{i}_fill")
            
            # Inventory
            with st.expander("📦 Inventory", expanded=False):
                inv_idoalapu = st.slider("Időalapú (%)", 0, 100, 10, key=f"scen{i}_inv1")
                inv_av = st.slider("AV alapú (%)", 0, 100, 10, key=f"scen{i}_inv2")
                inv_ct = st.slider("CT (%)", 0, 100, 0, key=f"scen{i}_inv3")
                inv_pmp_display = st.slider("PMP Display (%)", 0, 100, 7, key=f"scen{i}_inv4")
                inv_open_display = st.slider("Open Display (%)", 0, 100, 25, key=f"scen{i}_inv5")
                inv_pmp_video = st.slider("PMP Video (%)", 0, 100, 3, key=f"scen{i}_inv6")
                inv_open_video = st.slider("Open Video (%)", 0, 100, 15, key=f"scen{i}_inv7")
                inv_ures = st.slider("Üres (%)", 0, 100, 30, key=f"scen{i}_inv8")
            
            # Márkaérték
            with st.expander("🎯 Márkaérték", expanded=False):
                markaertek_options = {
                    "Induló Website": 0.8,
                    "Rosszul pozicionált márka": 0.9,
                    "Jól pozicionált márka": 1.1
                }
                markaertek_choice = st.selectbox("Márkaérték:", list(markaertek_options.keys()), index=2, key=f"scen{i}_marka")
                markaertek = markaertek_options[markaertek_choice]
            
            # Brand Safety
            with st.expander("🛡️ Brand Safety", expanded=False):
                bs_2026_szenzitiv = st.slider("Szenzitív", 0.0, 1.0, 0.9, 0.1, key=f"scen{i}_bs26_s")
                bs_2026_karos = st.slider("Káros", 0.0, 1.0, 0.9, 0.1, key=f"scen{i}_bs26_k")
                bs_2026_user = st.slider("User elég.", 0.0, 1.0, 0.9, 0.1, key=f"scen{i}_bs26_u")

            # Súlyok
            with st.expander("⚖️ Súlyok", expanded=False):
                suly_marka = st.slider("Márkaérték (%)", 0, 100, 30, key=f"scen{i}_w1")
                suly_bs = st.slider("Brand Safety (%)", 0, 100, 20, key=f"scen{i}_w2")
                suly_szezon = st.slider("Szezonalitás (%)", 0, 100, 50, key=f"scen{i}_w3")
                szezonalitas = st.slider("Szezonalitás értéke", 0.5, 2.0, 1.5, 0.1, key=f"scen{i}_szezon")
            
            # Inputok összegyűjtése
            scen_inputs = {
                'real_users': real_users,
                'pageviews': pageviews,
                'mobil_arany': mobil_arany,
                'desktop_arany': 100 - mobil_arany,
                'mobil_zones': mobil_zones,
                'desktop_zones': desktop_zones,
                'fill_rate': fill_rate,
                'inv_idoalapu': inv_idoalapu,
                'inv_av': inv_av,
                'inv_ct': inv_ct,
                'inv_pmp_display': inv_pmp_display,
                'inv_open_display': inv_open_display,
                'inv_pmp_video': inv_pmp_video,
                'inv_open_video': inv_open_video,
                'inv_ures': inv_ures,
                'markaertek': markaertek,
                'bs_2026_szenzitiv': bs_2026_szenzitiv,
                'bs_2026_karos': bs_2026_karos,
                'bs_2026_user': bs_2026_user,
                'suly_marka': suly_marka,
                'suly_bs': suly_bs,
                'suly_szezon': suly_szezon,
                'szezonalitas': szezonalitas
            }
            
            scenarios_inputs.append(scen_inputs)
            
            # Eredmények
            st.markdown("---")
            scen_results = calculate_revenue(scen_inputs)
            
            st.metric("💰 Adaptive", f"{scen_results[2026]['adaptive_share']/1_000_000:.2f}M Ft")

st.markdown("---")
st.caption("© 2025 Brindzik Dorina, Jakus Ádám, Koltai Dóra, Lefánti Vilmos, Nagy Boglárka, Szerényi Petra")