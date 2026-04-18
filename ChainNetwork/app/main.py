import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import networkx as nx
from datetime import datetime

# Add parent directory to path to import simulator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.engine import SimulationEngine

st.set_page_config(page_title="ChainNetwork | Digital Twin Simulator", layout="wide")

st.title("ChainNetwork: Bottom-Up Decision Simulator")
st.markdown("""
Ez a rendszer nem feltetelezest, hanem **adat-rekonstrukciot** hasznal. 
Eloszor legeneralunk egy nyers tranzakcios multat, majd abbol **visszafejtjuk** a social halozatot.
""")

# --- Persistent State ---
if 'engine' not in st.session_state:
    st.session_state.engine = SimulationEngine()
    st.session_state.history_generated = False

# --- Sidebar ---
st.sidebar.header("1. History Generation")
hist_months = st.sidebar.slider("Historical Period (months)", 1, 12, 6)
base_users = st.sidebar.number_input("Base Population", 100, 2000, 1000)

if st.sidebar.button("Generate Raw History"):
    st.session_state.engine = SimulationEngine(num_users=base_users)
    st.session_state.engine.generate_past(months=hist_months)
    st.session_state.history_generated = True
    st.success("Generated history and analytical profiles.")

# --- Main Logic ---
if st.session_state.history_generated:
    tab1, tab2 = st.tabs(["Discovery", "Projection"])
    engine = st.session_state.engine
    
    with tab1:
        st.header("Raw Data Analysis (Historical)")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        summary = engine.analyzer.get_summary_stats()
        col_m1.metric("Total History Revenue", f"{summary['total_revenue']:,.0f} Ft")
        col_m2.metric("Identified Fans %", f"{summary['identified_percentage']:.1f}%")
        col_m3.metric("Avg Group Size", f"{summary['avg_group_size']:.2f}")

        st.subheader("Raw Transaction Log")
        st.dataframe(engine.df_history.sort_values('timestamp', ascending=False).head(50), use_container_width=True)

        st.divider()
        st.subheader("User Intelligence Table")
        # Ensure we use the correct column names from analyzer.py
        display_stats = engine.user_stats.copy()
        if 'influence_score' in display_stats.columns:
            display_stats = display_stats.sort_values('influence_score', ascending=False)
            
        # Add a churn warning column for display
        display_stats['Status'] = display_stats['churn_risk'].apply(lambda x: "⚠️ Churn Risk" if x == 1 else "✅ Active")

        st.dataframe(
            display_stats[['user_id', 'Status', 'total_spend', 'visit_count', 'influence_score', 'connections', 'days_since_last']].style.format({
                'total_spend': '{:,.0f} Ft',
                'influence_score': '{:.3f}',
                'connections': '{:.0f}'
            }), 
            use_container_width=True
        )

        st.divider()
        st.subheader("🎯 Strategic Opportunities")
        
        o_col1, o_col2 = st.columns(2)
        
        with o_col1:
            st.markdown("**Lookalike Influencers (Anonymous Leaders)**")
            lookalike_count = engine.analyzer.lookalikes['session_id'].nunique()
            st.metric("Detected Potential Influencers", lookalike_count)
            st.info(f"Olyan anonim vendegek, akik rendszeresen 3+ fős társasággal esznek. Ha sikerülne őket regisztrálni, a hálózatod {lookalike_count * 5:.0f} új éllel bővülne.")

        with o_col2:
            st.markdown("**Revenue by Group Size**")
            # Calculate revenue per group size from history
            group_rev = engine.df_history.groupby('session_id').size().value_counts().reset_index()
            group_rev.columns = ['Group Size', 'Frequency']
            fig_rev = px.bar(group_rev, x='Group Size', y='Frequency', color='Frequency', title="Tranzakciók csoportméret szerint")
            st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()
        st.subheader("Social Graph Reconstruction")
        
        # Filter for top influencers to visualize
        if 'influence_score' in engine.user_stats.columns:
            top_u = engine.user_stats.sort_values('influence_score', ascending=False).head(40)['user_id'].tolist()
            sub = engine.graph.subgraph(top_u)
            pos = nx.spring_layout(sub, k=0.5)
            
            edge_x, edge_y = [], []
            for edge in sub.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.7, color='#BBB'), hoverinfo='none', mode='lines')
            node_x, node_y, node_text, node_size = [], [], [], []
            
            for node in sub.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                # Fetch metrics for the node
                row = engine.user_stats[engine.user_stats['user_id'] == node].iloc[0]
                inf = row['influence_score']
                conn = row['connections']
                
                node_text.append(f"User: {node}<br>Influence: {inf:.3f}<br>Connections: {conn}")
                node_size.append(inf * 300 + 10)

            node_trace = go.Scatter(
                x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_text,
                marker=dict(showscale=True, colorscale='Viridis', size=node_size, color=node_size, line_width=2)
            )
            
            fig = go.Figure(data=[edge_trace, node_trace], 
                            layout=go.Layout(showlegend=False, hovermode='closest', margin=dict(b=0,l=0,r=0,t=0),
                                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("Future Simulation (Projection)")
        st.sidebar.header("2. Simulation Config")
        fut_days = st.sidebar.slider("Horizon (days)", 30, 365, 90)
        boost = st.sidebar.slider("Influencer Boost", 1.0, 2.0, 1.3)
        cost = st.sidebar.slider("Reward Cost %", 1, 10, 5) / 100

        if st.button("Run Future Projection"):
            df_b, df_o = engine.run_projection(days=fut_days, influencer_retention_boost=boost, reward_cost_pct=cost)
            
            rev_b = df_b['spend'].sum()
            rev_o = df_o['spend'].sum()
            profit_o = rev_o - df_o['cost'].sum()
            uplift = (profit_o / rev_b - 1) * 100
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Projected Baseline Revenue", f"{rev_b:,.0f} Ft")
            mc2.metric("Projected ChainNetwork Revenue", f"{rev_o:,.0f} Ft")
            mc3.metric("Net Profit Uplift", f"{uplift:.1f}%")
            
            daily_b = df_b.groupby('date')['spend'].sum().reset_index()
            daily_o = df_o.groupby('date')['spend'].sum().reset_index()
            
            f_fig = go.Figure()
            f_fig.add_trace(go.Scatter(x=daily_b['date'], y=daily_b['spend'], name='Baseline', line=dict(color='gray')))
            f_fig.add_trace(go.Scatter(x=daily_o['date'], y=daily_o['spend'], name='ChainNetwork', line=dict(color='#00CC96', width=3)))
            st.plotly_chart(f_fig, use_container_width=True)

else:
    st.info("Kezdeshez generalj multbeli adatokat a sidebaron!")
