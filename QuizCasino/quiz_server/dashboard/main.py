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
    
    # Create granular rank-division label
    df_users['full_league'] = df_users['league'].str.upper() + " " + df_users['division'].fillna('')
    
    # Enrich matches with finishing positions
    match_performances = []
    for m in matches_raw:
        m_players = sorted(m.get('players', []), key=lambda x: x.get('stack', 0), reverse=True)
        for i, p in enumerate(m_players):
            if not p.get('isBot', False):
                match_performances.append({
                    'username': p['username'],
                    'position': i + 1,
                    'total_players': len(m_players),
                    'normalized_pos': (i + 1) / len(m_players)
                })
    
    df_perf = pd.DataFrame(match_performances)
    if not df_perf.empty:
        avg_pos = df_perf.groupby('username')['position'].mean().reset_index()
        df_users = df_users.merge(avg_pos, on='username', how='left')
    
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
        cols_to_show = ['username', 'full_league', 'elo', 'hiddenElo', 'win_rate', 'position', 'gold', 'diamonds', 'matchesPlayed']
        st.dataframe(
            display_df[cols_to_show].sort_values('hiddenElo', ascending=False),
            column_config={
                "hiddenElo": st.column_config.NumberColumn("Hidden ELO 🛠️", help="Internal skill rating for matchmaking"),
                "win_rate": st.column_config.ProgressColumn("Win Rate", format="%.1f%%", min_value=0, max_value=100),
                "position": st.column_config.NumberColumn("Avg. Pos", format="%.1f"),
                "full_league": "League/Division"
            },
            hide_index=True,
            use_container_width=True
        )

        if search_query and not display_df.empty:
            user_data = display_df.iloc[0]
            st.markdown(f"### Detailed Intel: {user_data['username']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("League/Division", user_data['full_league'])
            c2.metric("Skill Delta (H-P)", int(user_data['hiddenElo'] - user_data['elo']))
            c3.metric("Avg. Finish Pos", f"#{user_data.get('position', 0):.1f}")
            c4.metric("Win Rate", f"{user_data['win_rate']}%")

    elif page == "League Insights":
        st.subheader("League Ecosystem & Balance 🏆")
        
        l_col1, l_col2 = st.columns(2)
        
        # 1. Distribution
        league_counts = real_players_df['full_league'].value_counts()
        fig_dist = px.pie(values=league_counts.values, names=league_counts.index, 
                         title="Player Distribution by League & Division", hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Bold)
        fig_dist.update_layout(template="plotly_dark")
        l_col1.plotly_chart(fig_dist, use_container_width=True)
        
        # 2. Answer Success & Position by League
        # Collect round success by league
        league_success = []
        for m in matches_raw:
            # Find a real player to determine the room's average league
            real_p = next((p for p in m.get('players', []) if not p.get('isBot', False)), None)
            if real_p:
                # Map name to league via df_users
                p_info = df_users[df_users['username'] == real_p['username']]
                if not p_info.empty:
                    lg = p_info.iloc[0]['league']
                    for r in m.get('rounds', []):
                        correct = sum(1 for b in r.get('bets', []) if b.get('isCorrect') and not b.get('isBot', False))
                        total = sum(1 for b in r.get('bets', []) if not b.get('isBot', False))
                        if total > 0:
                            league_success.append({'league': lg, 'success': correct / total})
        
        df_lg_success = pd.DataFrame(league_success).groupby('league')['success'].median().reset_index()
        
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Bar(name='Median Success Rate', x=df_lg_success['league'], y=df_lg_success['success'] * 100, marker_color='#00FFE5'))
        fig_perf.update_layout(title="Typical Answer Success % per Rank", template="plotly_dark", yaxis_title="Success %")
        l_col2.plotly_chart(fig_perf, use_container_width=True)

        st.markdown("---")
        # 3. Hidden vs Public ELO per League-Division
        st.subheader("Granular Skill Balance (League + Division)")
        granular_stats = real_players_df.groupby('full_league').agg({
            'elo': 'mean',
            'hiddenElo': 'mean'
        }).reset_index().sort_values('hiddenElo')
        
        fig_gran = px.line(granular_stats, x='full_league', y=['elo', 'hiddenElo'], 
                          title="ELO Calibration Curve", markers=True,
                          color_discrete_map={"elo": "#00f2ff", "hiddenElo": "#9d00ff"})
        fig_gran.update_layout(template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig_gran, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("System healthy. Data refreshed every 60s.")
