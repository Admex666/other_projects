import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import random
import os
import networkx as nx

# Page config
st.set_page_config(page_title="ChainNetwork | Social Decision Engine", layout="wide", page_icon="🕸️")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0b0d11; color: #e0e0e0; }
    .stMetric { background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
    h1, h2, h3 { color: #00d2ff; }
    </style>
    """, unsafe_allow_html=True)

# Database path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'chainnetwork.db')

@st.cache_data
def load_baseline():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT t.*, u.name as user_name, u.age_group, u.lifestyle_tag, 
           ti.menu_item_id, mi.price as unit_price, mi.cost as unit_cost, ti.quantity
    FROM transactions t
    JOIN users u ON t.user_id = u.id
    JOIN transaction_items ti ON t.id = ti.transaction_id
    JOIN menu_items mi ON ti.menu_item_id = mi.id
    WHERE u.test_group = 'A'
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['total_cost'] = df['unit_cost'] * df['quantity']
    df['revenue'] = df['unit_price'] * df['quantity']
    conn.close()
    
    df_tx = df.groupby(['id', 'user_id', 'user_name', 'timestamp', 'total_amount', 'age_group', 'lifestyle_tag']).agg({
        'total_cost': 'sum',
        'revenue': 'sum'
    }).reset_index()
    df_tx['profit'] = df_tx['revenue'] - df_tx['total_cost']
    return df_tx

@st.cache_data
def get_social_data():
    conn = sqlite3.connect(DB_PATH)
    connections = pd.read_sql_query("SELECT * FROM connections", conn)
    referrals = pd.read_sql_query("SELECT * FROM referrals", conn)
    users_spending = pd.read_sql_query("""
        SELECT u.id, u.name, u.lifestyle_tag, SUM(t.total_amount) as total_spent
        FROM users u
        LEFT JOIN transactions t ON u.id = t.user_id
        GROUP BY u.id
    """, conn)
    conn.close()
    return connections, referrals, users_spending

def synthesize_engine_effect(df_a, retain_conv, upsell_hit, social_boost, panic_mode):
    df_b = df_a.copy()
    df_b['is_synthetic'] = False
    df_b['intervention_type'] = 'None'
    if panic_mode: return df_b
        
    new_records = []
    for uid in df_b['user_id'].unique():
        user_tx = df_b[df_b['user_id'] == uid].sort_values('timestamp')
        if len(user_tx) == 0: continue
        last_visit = user_tx.iloc[-1]
        
        if random.random() < (retain_conv * 0.5):
            new_ts = last_visit['timestamp'] + timedelta(days=random.randint(7, 14))
            if new_ts > datetime.now(): continue
            
            new_records.append({
                'id': 999000 + len(new_records), 'user_id': uid, 'user_name': last_visit['user_name'],
                'timestamp': new_ts, 'total_amount': last_visit['total_amount'], 'age_group': last_visit['age_group'],
                'lifestyle_tag': last_visit['lifestyle_tag'], 'total_cost': last_visit['total_cost'],
                'revenue': last_visit['revenue'], 'profit': last_visit['profit'], 'is_synthetic': True,
                'intervention_type': 'Churn Save'
            })
            
            if random.random() < social_boost:
                for _ in range(random.randint(1, 2)):
                    new_records.append({
                        'id': 999000 + len(new_records), 'user_id': 0, 'user_name': 'Friend of ' + last_visit['user_name'],
                        'timestamp': new_ts, 'total_amount': last_visit['total_amount'] * 0.9,
                        'age_group': last_visit['age_group'], 'lifestyle_tag': last_visit['lifestyle_tag'],
                        'total_cost': last_visit['total_cost'],
                        'revenue': last_visit['revenue'] * 0.9, 'profit': last_visit['profit'] * 0.85,
                        'is_synthetic': True, 'intervention_type': 'Social/Group Referral'
                    })
    if new_records:
        df_b = pd.concat([df_b, pd.DataFrame(new_records)], ignore_index=True)
    return df_b

# --- SIDEBAR ---
st.sidebar.title("🕸️ Social Decision Engine")

public_calc_mode = st.sidebar.toggle("🌐 Public Loss Calculator", value=False)

if public_calc_mode:
    st.title("💸 Rejtett Veszteség Kalkulátor Éttermeknek")
    st.markdown("Számold ki 30 másodperc alatt, mennyi profitot hagysz az asztalon minden hónapban a lemorzsolódás és az elmaradt upsell miatt.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Étterem Adatai")
        orders = st.number_input("Havi rendelésszám (db)", min_value=100, value=8000, step=100)
        avg_ticket = st.number_input("Átlagos kosárérték (Ft)", min_value=1000, value=4500, step=100)
        margin = st.slider("Becsült Haszonkulcs (%)", 0, 100, 35) / 100
        churn_rate = st.slider("Lemorzsolódás (30 nap után elvesztett vendégek) (%)", 0, 100, 15) / 100
        
        st.subheader("❓ Jelenlegi folyamatok")
        track_churn = st.checkbox("Követitek a vendégeitek fogyasztását a lemorzsolódás megelőzésére?")
        has_upsell = st.checkbox("Van aktív és mért upsell stratégiátok?")
        track_referrals = st.checkbox("Ösztönzitek a csoportos fogyasztást és az ajánlásokat?")
        
    with col2:
        # Kalkulációk (csak ha NINCS megoldva)
        monthly_rev = orders * avg_ticket
        
        # Y = Churn Gap
        churn_gap = (orders * churn_rate) * avg_ticket * margin if not track_churn else 0
        
        # Z = Upsell Gap
        upsell_gap = (orders * 0.40) * 800 * margin if not has_upsell else 0
        
        # W = Network Gap
        network_gap = (orders / 2) * 0.10 * avg_ticket * margin if not track_referrals else 0
        
        total_loss = churn_gap + upsell_gap + network_gap
        
        st.subheader("🚨 Elszalasztott Nettó Profit")
        st.metric(label="Havi Veszteség", value=f"{total_loss:,.0f} Ft")
        st.metric(label="Éves Veszteség", value=f"{(total_loss * 12):,.0f} Ft")
        
        st.markdown("---")
        st.markdown("**Miből tevődik ez össze?**")
        st.markdown(f"📉 **{churn_gap:,.0f} Ft**: Elvesztett törzsvendégek, akiket egy automatikus üzenettel visszahozhattunk volna.")
        st.markdown(f"🍔 **{upsell_gap:,.0f} Ft**: Elmaradt extra köretek/italok, mert a személyzet nem ajánlotta fel következetesen.")
        st.markdown(f"🕸️ **{network_gap:,.0f} Ft**: Elmaradt baráti meghívások, mert nem ösztönöztük a csoportos étkezést.")
        
    st.markdown("---")
    st.success("Tudjuk, hogyan állítsd meg ezt a veszteséget emberi beavatkozás nélkül. Érdekel a megoldás?")
    if st.button("Kérem a személyre szabott stratégiát (Demo) 🚀", use_container_width=True):
        st.balloons()
        st.info("Ezen a ponton kérnénk be az e-mail címet vagy egy Calendly időpontfoglalást a landing page-en!")
        
    st.stop() # Megállítja a dashboard többi részének betöltését

pitch_mode = st.sidebar.toggle("🚀 Enterprise Mode", value=True)

if pitch_mode:
    client_name = st.sidebar.text_input("Brand Name", "Bamba Marha")
    m_rev = st.sidebar.number_input("Monthly Revenue (HUF)", value=40000000)
else:
    client_name = "Simulation Base"

st.sidebar.subheader("🕹️ Strategy Parameters")
retain_conv = st.sidebar.slider("Intervention Success (%)", 5, 100, 25) / 100
upsell_hit = st.sidebar.slider("Upsell Hit Rate (%)", 0, 100, 15) / 100
social_boost = st.sidebar.slider("Viral/Social Factor (%)", 0, 100, 30) / 100

st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Controls")
panic = st.sidebar.button("🛑 STOP ALL MARKETING", use_container_width=True)
st.session_state['panic_active'] = panic if panic else st.session_state.get('panic_active', False)

# --- DATA PROCESSING ---
df_a = load_baseline()
df_b = synthesize_engine_effect(df_a, retain_conv, upsell_hit, social_boost, st.session_state['panic_active'])

# Scaling
if pitch_mode:
    scale = m_rev / df_a['revenue'].sum()
    df_a['revenue'] *= scale; df_a['profit'] *= scale
    df_b['revenue'] *= scale; df_b['profit'] *= scale

base_profit = df_a['profit'].sum()
new_profit = df_b['profit'].sum()
viral_rev = df_b[df_b['intervention_type'] == 'Social/Group Referral']['revenue'].sum()

# --- MAIN UI ---
st.title(f"{client_name} | Network Influence Suite")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Net Profit", f"{new_profit:,.0f} Ft", delta=f"{((new_profit/base_profit)-1)*100:.1f}%")
k2.metric("Viral Revenue", f"+{viral_rev:,.0f} Ft")
k3.metric("Viral Coefficient (K)", f"{social_boost * 1.5:.2f}")
k4.metric("Avg User Lifetime Value", f"{(new_profit/df_b['user_id'].nunique()):,.0f} Ft")

st.markdown("---")

tabs = st.tabs(["📊 Performance", "🕸️ Social Network", "🎯 Referral ROI", "🕒 Journey", "🔬 A/B Test"])

with tabs[1]:
    st.subheader("Social Graph: Node Size = Total Spending")
    conn_df, ref_df, users_df = get_social_data()
    
    G = nx.Graph()
    # Limit nodes but ensure hubs are included
    top_spenders = users_df.sort_values('total_spent', ascending=False).head(200)
    for _, user in top_spenders.iterrows():
        G.add_node(user['id'], name=user['name'], lifestyle=user['lifestyle_tag'], spent=user['total_spent'])
    
    for _, edge in conn_df.iterrows():
        if edge['user_a'] in G.nodes and edge['user_b'] in G.nodes:
            G.add_edge(edge['user_a'], edge['user_b'])
            
    pos = nx.spring_layout(G, k=0.4, iterations=50)
    
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#444'), hoverinfo='none', mode='lines')

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    colors = {'Office': '#00d2ff', 'Student': '#2ecc71', 'Family': '#f1c40f', 'Tourist': '#e74c3c'}
    
    max_spent = top_spenders['total_spent'].max()

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x); node_y.append(y)
        spent = G.nodes[node]['spent'] if not pd.isna(G.nodes[node]['spent']) else 0
        
        # Calculate Network Info
        neighbors = list(G.neighbors(node))
        network_reach_count = len(neighbors)
        network_reach_value = sum([G.nodes[n]['spent'] for n in neighbors if not pd.isna(G.nodes[n]['spent'])])
        
        node_text.append(
            f"<b>{G.nodes[node]['name']}</b><br>" +
            f"Personal Spending: {spent:,.0f} Ft<br>" +
            f"Connections: {network_reach_count}<br>" +
            f"Network Reach Value: {network_reach_value:,.0f} Ft<br>" +
            f"Lifestyle: {G.nodes[node]['lifestyle']}"
        )
        node_color.append(colors.get(G.nodes[node]['lifestyle'], '#888'))
        # Scaling size: base 10 + proportional to spending
        node_size.append(5 + (spent / max_spent) * 25)

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_text,
        marker=dict(color=node_color, size=node_size, line=dict(width=1, color='white'))
    )

    fig_graph = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='Network Hubs by Spending (Nodes colored by Lifestyle)',
                    showlegend=False, template="plotly_dark",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    st.plotly_chart(fig_graph, width='stretch')
    
    st.info("💡 **Insights:** Larger bubbles are high-value customers. Network Reach Value shows the total spending of their direct circle.")

# (Other tabs logic remains consistent)
with tabs[0]:
    st.subheader("Monthly Profit Uplift Bridge")
    churn_gain = df_b[df_b['intervention_type'] == 'Churn Save']['profit'].sum()
    social_gain = df_b[df_b['intervention_type'] == 'Social/Group Referral']['profit'].sum()
    upsell_gain = new_profit - base_profit - churn_gain - social_gain
    fig = go.Figure(go.Waterfall(
        x = ["Baseline", "Retention", "Social/Viral", "Upsell", "Total (B)"],
        y = [base_profit, churn_gain, social_gain, upsell_gain, new_profit],
        measure = ["absolute", "relative", "relative", "relative", "total"],
        increasing = {"marker":{"color":"#2ecc71"}},
        totals = {"marker":{"color":"#00d2ff"}}
    ))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, width='stretch')

with tabs[2]:
    st.subheader("Referral Program ROI")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Social Distribution**")
        group_dist = df_b.groupby('intervention_type').size().reset_index(name='count')
        st.plotly_chart(px.pie(group_dist, names='intervention_type', values='count', template="plotly_dark"), width='stretch')
    with c2:
        st.write("**Network Value Analysis**")
        st.write(f"- **Viral Revenue Contribution:** {(viral_rev/df_b['revenue'].sum())*100:.1f}%")

with tabs[3]:
    st.subheader("Social Journey Proof")
    user_list = df_a['user_name'].unique()[:10]
    selected_u = st.selectbox("Select Customer", user_list)
    u_data = df_b[(df_b['user_name'] == selected_u) | (df_b['user_name'] == 'Friend of ' + selected_u)].sort_values('timestamp')
    st.dataframe(u_data[['timestamp', 'user_name', 'profit', 'is_synthetic', 'intervention_type']].style.map(lambda x: 'color: #00d2ff' if x==True else 'color: white', subset=['is_synthetic']))

with tabs[4]:
    st.subheader("Scientific Delta Proof")
    comp_df = pd.DataFrame({
        'Group': ['Control (A)', 'Social Engine (B)'],
        'Profit/User': [base_profit / df_a['user_id'].nunique(), new_profit / df_b['user_id'].nunique()]
    })
    st.plotly_chart(px.bar(comp_df, x='Group', y='Profit/User', color='Group', template="plotly_dark"), width='stretch')
