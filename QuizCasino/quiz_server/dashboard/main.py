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
st.sidebar.header("Filters")
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

if not matches_raw:
    st.warning(f"No match data found in database '{db.name}' for the selected period ({days_to_check} days).")
    st.info("💡 **Tipper:** Restart your server and play a full match to record data!")
else:
    # 1. Key Metrics (Top Row)
    col1, col2, col3, col4 = st.columns(4)
    
    total_matches = len(matches_raw)
    real_players = [u for u in users_raw if not u['username'].startswith('bot_')]
    total_users = len(real_players)
    
    # Calculate DAU
    df_matches = pd.DataFrame(matches_raw)
    df_matches['date'] = pd.to_datetime(df_matches['createdAt']).dt.date
    dau = df_matches.explode('players')
    # Extract username from nested player object
    dau['username'] = dau['players'].apply(lambda x: x['username'])
    # Filter out bots from DAU
    dau = dau[dau['players'].apply(lambda x: not x.get('isBot', False))]
    daily_active = dau.groupby('date')['username'].nunique()

    col1.metric("Total Matches", total_matches)
    col2.metric("Total Users", total_users)
    col3.metric("Avg. Matches/Day", round(total_matches / days_to_check, 1))
    col4.metric("Avg. DAU", round(daily_active.mean(), 1) if not daily_active.empty else 0)

    st.markdown("---")

    # 2. Daily Activity Chart
    st.subheader("Daily Active Users (DAU)")
    if not daily_active.empty:
        fig_dau = px.bar(daily_active, labels={'value': 'Unique Users', 'date': 'Date'}, 
                       color_discrete_sequence=[ '#00f2ff'])
        fig_dau.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_dau, use_container_width=True)

    # 3. Question Difficulty Analysis
    st.markdown("---")
    st.subheader("Question Difficulty Analysis 🧠")
    
    rounds_data = []
    for m in matches_raw:
        for r in m.get('rounds', []):
            # Filter out bots (using isBot flag OR Bot name prefix for older records)
            real_bets = [b for b in r.get('bets', []) 
                         if not b.get('isBot', False) and not b.get('username', '').startswith('Bot')]
            
            if not real_bets:
                continue
                
            correct_bets = sum(1 for b in real_bets if b.get('isCorrect'))
            total_bets = len(real_bets)
            rounds_data.append({
                'question': r['questionText'],
                'correct_ratio': correct_bets / total_bets,
                'total_attempts': total_bets
            })
    
    if rounds_data:
        df_rounds = pd.DataFrame(rounds_data)
        q_stats = df_rounds.groupby('question').agg({
            'correct_ratio': 'mean',
            'total_attempts': 'sum'
        }).reset_index()
        
        q_stats = q_stats.sort_values('correct_ratio')
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.write("**Hardest Questions (Lowest Success rate)**")
            st.dataframe(q_stats.head(10)[['question', 'correct_ratio']].style.format({'correct_ratio': '{:.1%}'}), 
                        hide_index=True, use_container_width=True)
            
        with col_right:
            st.write("**Easiest Questions (Highest Success rate)**")
            st.dataframe(q_stats.tail(10).sort_values('correct_ratio', ascending=False)[['question', 'correct_ratio']].style.format({'correct_ratio': '{:.1%}'}), 
                        hide_index=True, use_container_width=True)

    # 4. Economy Tracker
    st.markdown("---")
    st.subheader("Economy & Coin Flow 💰")
    
    economy_data = []
    for m in matches_raw:
        for p in m.get('players', []):
            if not p['isBot']:
                economy_data.append({
                    'date': pd.to_datetime(m['createdAt']).date(),
                    'change': p['endStack'] - p['startStack']
                })
    
    if economy_data:
        df_eco = pd.DataFrame(economy_data)
        daily_eco = df_eco.groupby('date')['change'].sum().reset_index()
        
        fig_eco = px.line(daily_eco, x='date', y='change', title="Net Coin Change (Daily)",
                         color_discrete_sequence=['#ffd700'])
        fig_eco.add_hline(y=0, line_dash="dash", line_color="white")
        fig_eco.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_eco, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("Data updates every 60 seconds.")
