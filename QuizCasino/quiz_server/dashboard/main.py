import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Page config
st.set_page_config(page_title="KnowCoin Analytics", page_icon="📊", layout="wide")

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/quizcasino")

@st.cache_resource
def get_db():
    client = MongoClient(MONGODB_URI)
    try:
        # Try getting default from URI
        db = client.get_database()
        # Test if we can access it
        client.list_database_names()
        return db
    except Exception:
        # Fallback logic: check if 'quizcasino' or 'test' exists
        available = client.list_database_names()
        if 'quizcasino' in available:
            return client['quizcasino']
        return client['test']

db = get_db()
st.sidebar.success(f"Connected to DB: {db.name}")

st.title("KnowCoin Analytics Dashboard 📊")
st.markdown("---")

# Sidebar
st.sidebar.header("Navigation & Filters")
page = st.sidebar.radio("Go to", ["Global Overview", "Player Intelligence", "League Insights"])
days_to_check = st.sidebar.slider("Show data for last X days", 1, 30, 7)

# Load Data
@st.cache_data(ttl=60)
def load_matches(days):
    cutoff = datetime.now() - timedelta(days=days)
    matches = list(db.matches.find({"createdAt": {"$gte": cutoff}}))
    return matches

@st.cache_data(ttl=60)
def load_users():
    return list(db.users.find())

matches_raw = load_matches(days_to_check)
users_raw = load_users()

if not matches_raw or not users_raw:
    st.warning(f"Insufficient data found in database '{db.name}'.")
    st.info("💡 **Tipper:** Play some matches to see deep analytics!")
else:
    # Prepare DataFrames
    df_users = pd.DataFrame(users_raw)
    # Ensure hiddenElo exists, default to 1500 if missing
    if 'hiddenElo' not in df_users.columns:
        df_users['hiddenElo'] = 1500
    df_users['win_rate'] = (df_users['matchesWon'] / df_users['matchesPlayed'].replace(0, 1) * 100).round(1)
    
    real_players_df = df_users[~df_users['username'].str.startswith('bot_', na=False)]

    if page == "Global Overview":
        # 1. Key Metrics (Top Row)
        col1, col2, col3, col4 = st.columns(4)
        
        total_matches = len(matches_raw)
        total_users = len(real_players_df)
        
        df_matches = pd.DataFrame(matches_raw)
        df_matches['date'] = pd.to_datetime(df_matches['createdAt']).dt.date
        dau_data = df_matches.explode('players')
        dau_data = dau_data[dau_data['players'].apply(lambda x: not x.get('isBot', False))]
        dau_data['username'] = dau_data['players'].apply(lambda x: x['username'])
        daily_active = dau_data.groupby('date')['username'].nunique()

        col1.metric("Total Matches", total_matches)
        col2.metric("Total Users", total_users)
        col3.metric("Avg. Matches/Day", round(total_matches / days_to_check, 1))
        col4.metric("Avg. DAU", round(daily_active.mean(), 1) if not daily_active.empty else 0)

        st.markdown("---")
        st.subheader("Daily Active Users (DAU)")
        if not daily_active.empty:
            fig_dau = px.bar(daily_active, labels={'value': 'Unique Users', 'date': 'Date'}, 
                           color_discrete_sequence=[ '#00f2ff'])
            fig_dau.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_dau, use_container_width=True)

        st.markdown("---")
        st.subheader("Question Difficulty 🧠")
        rounds_data = []
        for m in matches_raw:
            for r in m.get('rounds', []):
                real_bets = [b for b in r.get('bets', []) if not b.get('isBot', False)]
                if real_bets:
                    correct = sum(1 for b in real_bets if b.get('isCorrect'))
                    rounds_data.append({'question': r['questionText'], 'success': correct / len(real_bets)})
        
        if rounds_data:
            df_q = pd.DataFrame(rounds_data).groupby('question')['success'].mean().reset_index().sort_values('success')
            col_l, col_r = st.columns(2)
            col_l.write("**Hardest Questions**")
            col_l.dataframe(df_q.head(5), hide_index=True)
            col_r.write("**Easiest Questions**")
            col_r.dataframe(df_q.tail(5), hide_index=True)

    elif page == "Player Intelligence":
        st.subheader("Player Identity Verification & Hidden Stats 🕵️")
        
        search_query = st.text_input("Search Operator ID (Username)", "").lower()
        
        display_df = real_players_df.copy()
        if search_query:
            display_df = display_df[display_df['username'].str.contains(search_query, case=False, na=False)]

        # Highlight Hidden ELO for balance detection
        cols_to_show = ['username', 'league', 'elo', 'hiddenElo', 'win_rate', 'gold', 'diamonds', 'matchesPlayed']
        st.dataframe(
            display_df[cols_to_show].sort_values('hiddenElo', ascending=False),
            column_config={
                "hiddenElo": st.column_config.NumberColumn("Hidden ELO 🛠️", help="Internal skill rating for matchmaking"),
                "win_rate": st.column_config.ProgressColumn("Win Rate", format="%.1f%%", min_value=0, max_value=100),
            },
            hide_index=True,
            use_container_width=True
        )

        if search_query and not display_df.empty:
            user_data = display_df.iloc[0]
            st.markdown(f"### Detailed Intel: {user_data['username']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Current League", user_data['league'].upper())
            c2.metric("Skill Delta (H-P)", int(user_data['hiddenElo'] - user_data['elo']))
            c3.metric("Placement Progress", f"{user_data.get('placementMatches', 0)}/5")

    elif page == "League Insights":
        st.subheader("League Ecosystem & Balance 🏆")
        
        l_col1, l_col2 = st.columns(2)
        
        # 1. Distribution
        league_counts = real_players_df['league'].value_counts()
        fig_dist = px.pie(values=league_counts.values, names=league_counts.index, 
                         title="Player Distribution by League", hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_dist.update_layout(template="plotly_dark")
        l_col1.plotly_chart(fig_dist, use_container_width=True)
        
        # 2. Performance by League
        league_stats = real_players_df.groupby('league').agg({
            'elo': 'mean',
            'hiddenElo': 'mean',
            'win_rate': 'mean'
        }).reset_index()
        
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Bar(name='Public ELO', x=league_stats['league'], y=league_stats['elo'], marker_color='#00FFE5'))
        fig_perf.add_trace(go.Bar(name='Hidden ELO', x=league_stats['league'], y=league_stats['hiddenElo'], marker_color='#991AFF'))
        fig_perf.update_layout(barmode='group', title="Avg ELO Levels per League", template="plotly_dark")
        l_col2.plotly_chart(fig_perf, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("System healthy. Data refreshed every 60s.")

