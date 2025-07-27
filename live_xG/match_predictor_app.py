import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pickle
import joblib  # Ha joblib-et használtál
import os

# FONTOS: Import a közös predictor osztályból
from predictor import RobustMatchPredictor

# Page config
st.set_page_config(
    page_title="⚽ Live Match Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (ugyanaz marad)
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .outcome-home {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        text-align: center;
        color: white;
    }
    .outcome-draw {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        text-align: center;
        color: white;
    }
    .outcome-away {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        text-align: center;
        color: white;
    }
    .insight-box {
        background: #f0f2f6;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .error-box {
        background: #ffebee;
        padding: 1rem;
        border-left: 4px solid #f44336;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #c62828;
    }
</style>
""", unsafe_allow_html=True)

# FRISSÍTETT: Valódi predictor betöltése
@st.cache_resource
def load_predictor():
    """
    Betöltjük a valódi betanított modellt
    """
    st.write(f"Current working directory: {os.getcwd()}") #
    st.write(f"Files in current directory: {os.listdir('.')}") #
    model_path = 'live_xG/trained_predictor.pkl'
    
    if not os.path.exists(model_path):
        st.error(f"❌ Model fájl nem található: {model_path}")
        st.info("Kérlek, futtasd le először a training scriptet!")
        return None
    
    try:
        # Próbáljuk pickle-lel
        with open(model_path, 'rb') as f:
            predictor = pickle.load(f)
        st.success("✅ Model sikeresen betöltve (pickle)")
        return predictor
    except:
        try:
            # Ha pickle nem működik, próbáljuk joblib-el
            predictor = joblib.load(model_path)
            st.success("✅ Model sikeresen betöltve (joblib)")
            return predictor
        except Exception as e:
            st.error(f"❌ Hiba a model betöltésekor: {e}")
            return None

# ÚJ: Helper függvény a Streamlit input-okból shots DataFrame készítéséhez
def create_shots_dataframe(home_team, away_team, home_goals, away_goals, 
                          home_xg, away_xg, home_shots, away_shots, current_minute):
    """
    Létrehoz egy mock shots DataFrame-et a Streamlit input-okból
    A valódi predictor által várt formátumban
    """
    shots_data = []
    
    # Generálunk mock shot adatokat a megadott statisztikák alapján
    # Home team shots
    if home_shots > 0:
        xg_per_shot_home = home_xg / home_shots if home_shots > 0 else 0
        goals_made_home = 0
        
        for i in range(home_shots):
            shot_minute = np.random.uniform(1, current_minute)
            is_goal = goals_made_home < home_goals
            if is_goal:
                goals_made_home += 1
            
            shots_data.append({
                'team_name': home_team,
                'minute': shot_minute,
                'shot_statsbomb_xg': xg_per_shot_home,
                'outcome_name': 'Goal' if is_goal else 'Saved'
            })
    
    # Away team shots
    if away_shots > 0:
        xg_per_shot_away = away_xg / away_shots if away_shots > 0 else 0
        goals_made_away = 0
        
        for i in range(away_shots):
            shot_minute = np.random.uniform(1, current_minute)
            is_goal = goals_made_away < away_goals
            if is_goal:
                goals_made_away += 1
            
            shots_data.append({
                'team_name': away_team,
                'minute': shot_minute,
                'shot_statsbomb_xg': xg_per_shot_away,
                'outcome_name': 'Goal' if is_goal else 'Saved'
            })
    
    return pd.DataFrame(shots_data)

# Main App
def main():
    st.markdown('<h1 class="main-header">⚽ Live Match Predictor</h1>', unsafe_allow_html=True)
    st.markdown("### Real-time football match outcome prediction using advanced ML")
    
    # Betöltjük a modellt
    predictor = load_predictor()
    
    if predictor is None:
        st.markdown("""
        ## ⚠️ Model nem elérhető
        
        A predikciós model jelenleg nem érhető el. Lehetséges okok:
        
        1. **Még nem lett betanítva** - Futtasd le a `mpl_ml_testing.py` scriptet
        2. **Fájl nem található** - Ellenőrizd, hogy a `trained_predictor.pkl` ugyanabban a mappában van
        3. **Betöltési hiba** - Ellenőrizd a model fájl integritását
        
        ### 🔧 Megoldás:
        ```bash
        python mpl_ml_testing.py  # Betanítja és elmenti a modellt
        streamlit run match_predictor_app.py  # Elindítja az appot
        ```
        """)
        return
    
    # Model információk megjelenítése
    if hasattr(predictor, 'is_fitted') and predictor.is_fitted:
        st.sidebar.success("✅ Model betöltve és kész")
        if hasattr(predictor, 'selected_features'):
            st.sidebar.info(f"📊 Használt features: {len(predictor.selected_features)}")
    
    # Sidebar for inputs
    st.sidebar.header("🎯 Match Information")
    
    # Team names
    home_team = st.sidebar.text_input("🏠 Home Team", value="Arsenal", placeholder="Enter home team name")
    away_team = st.sidebar.text_input("✈️ Away Team", value="Chelsea", placeholder="Enter away team name")
    
    st.sidebar.markdown("---")
    st.sidebar.header("⏱️ Match State")
    
    # Current minute
    current_minute = st.sidebar.slider("Current Minute", 1, 90, 45, help="Current match minute")
    
    # Current score
    col1, col2 = st.sidebar.columns(2)
    with col1:
        home_goals = st.number_input("🏠 Goals", min_value=0, max_value=10, value=1, key="home_goals")
    with col2:
        away_goals = st.number_input("✈️ Goals", min_value=0, max_value=10, value=0, key="away_goals")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Match Statistics")
    
    # xG values
    col1, col2 = st.sidebar.columns(2)
    with col1:
        home_xg = st.number_input("🏠 xG", min_value=0.0, max_value=5.0, value=1.2, step=0.1, key="home_xg")
    with col2:
        away_xg = st.number_input("✈️ xG", min_value=0.0, max_value=5.0, value=0.8, step=0.1, key="away_xg")
    
    # Shots
    col1, col2 = st.sidebar.columns(2)
    with col1:
        home_shots = st.number_input("🏠 Shots", min_value=0, max_value=30, value=8, key="home_shots")
    with col2:
        away_shots = st.number_input("✈️ Shots", min_value=0, max_value=30, value=5, key="away_shots")
    
    # Validation
    validation_errors = []
    if home_goals > home_shots:
        validation_errors.append("🏠 Goals cannot exceed shots")
    if away_goals > away_shots:
        validation_errors.append("✈️ Goals cannot exceed shots")
    if home_shots > 0 and home_xg == 0:
        validation_errors.append("🏠 xG should be > 0 if shots > 0")
    if away_shots > 0 and away_xg == 0:
        validation_errors.append("✈️ xG should be > 0 if shots > 0")
    
    if validation_errors:
        for error in validation_errors:
            st.sidebar.error(error)
    
    # Prediction button
    st.sidebar.markdown("---")
    predict_button = st.sidebar.button(
        "🔮 Predict Match Outcome", 
        type="primary", 
        use_container_width=True,
        disabled=len(validation_errors) > 0
    )
    
    # Main content area
    if predict_button and predictor is not None:
        try:
            # Létrehozzuk a shots DataFrame-et
            shots_df = create_shots_dataframe(
                home_team, away_team, home_goals, away_goals,
                home_xg, away_xg, home_shots, away_shots, current_minute
            )
            
            # Make prediction VALÓDI MODELLEL
            with st.spinner("🧠 Analyzing match data with trained ML model..."):
                prediction = predictor.predict_live(shots_df, current_minute, home_team, away_team)
                insights = predictor.get_insights(prediction, current_minute, home_team, away_team)
            
            # Display results
            st.success("✅ Prediction Complete!")
            
            # Match header
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.markdown(f"### 🏠 {home_team}")
            with col2:
                st.markdown(f"### {home_goals} - {away_goals}")
                st.markdown(f"**{current_minute}'**")
            with col3:
                st.markdown(f"### {away_team} ✈️")
            
            st.markdown("---")
            
            # Prediction results
            col1, col2, col3 = st.columns(3)
            
            probs = prediction['probabilities']
            
            with col1:
                st.markdown(f"""
                <div class="outcome-home">
                    <h3>1 - Home Win</h3>
                    <h2>{probs['home']:.1%}</h2>
                    <p>{home_team} Victory</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="outcome-draw">
                    <h3>X - Draw</h3>
                    <h2>{probs['draw']:.1%}</h2>
                    <p>Match Tied</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="outcome-away">
                    <h3>2 - Away Win</h3>
                    <h2>{probs['away']:.1%}</h2>
                    <p>{away_team} Victory</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Prediction confidence
            st.markdown(f"""
            <div class="prediction-card">
                <h3>🎯 Most Likely Outcome</h3>
                <h2>{prediction['predicted_outcome'].upper()}</h2>
                <p>Confidence: {prediction['confidence']:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Probability chart
            st.markdown("### 📈 Probability Distribution")
            
            # Create probability chart
            outcomes = ['Home Win', 'Draw', 'Away Win']
            probabilities = [probs['home'], probs['draw'], probs['away']]
            colors = ['#4CAF50', '#FF9800', '#f44336']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=outcomes,
                    y=probabilities,
                    marker_color=colors,
                    text=[f"{p:.1%}" for p in probabilities],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Match Outcome Probabilities (Trained ML Model)",
                yaxis_title="Probability",
                showlegend=False,
                height=400,
                yaxis=dict(tickformat='.1%')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights
            if insights['key_insights']:
                st.markdown("### 💡 Key Insights (AI-Generated)")
                for insight in insights['key_insights']:
                    st.markdown(f"""
                    <div class="insight-box">
                        <strong>•</strong> {insight}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Model Features használva
            if hasattr(predictor, 'selected_features'):
                with st.expander("🔍 Model Details"):
                    st.write("**Selected Features:**")
                    st.write(predictor.selected_features)
                    
                    current_features = prediction['current_features']
                    st.write("**Current Match Features:**")
                    
                    feature_df = pd.DataFrame([
                        {"Feature": k, "Value": f"{v:.3f}" if isinstance(v, float) else str(v)}
                        for k, v in current_features.items()
                    ])
                    st.dataframe(feature_df, use_container_width=True)
            
            # Match statistics visualization (ugyanaz marad)
            st.markdown("### 📊 Match Statistics Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # xG comparison
                fig_xg = go.Figure()
                fig_xg.add_trace(go.Bar(
                    name=home_team,
                    x=['Expected Goals'],
                    y=[home_xg],
                    marker_color='#4CAF50'
                ))
                fig_xg.add_trace(go.Bar(
                    name=away_team,
                    x=['Expected Goals'],
                    y=[away_xg],
                    marker_color='#f44336'
                ))
                fig_xg.update_layout(
                    title="Expected Goals (xG)",
                    yaxis_title="xG",
                    barmode='group',
                    height=300
                )
                st.plotly_chart(fig_xg, use_container_width=True)
            
            with col2:
                # Shots comparison
                fig_shots = go.Figure()
                fig_shots.add_trace(go.Bar(
                    name=home_team,
                    x=['Total Shots'],
                    y=[home_shots],
                    marker_color='#4CAF50'
                ))
                fig_shots.add_trace(go.Bar(
                    name=away_team,
                    x=['Total Shots'],
                    y=[away_shots],
                    marker_color='#f44336'
                ))
                fig_shots.update_layout(
                    title="Total Shots",
                    yaxis_title="Shots",
                    barmode='group',
                    height=300
                )
                st.plotly_chart(fig_shots, use_container_width=True)
            
            # Advanced metrics
            st.markdown("### 🔍 Advanced Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Goal Difference", 
                    value=f"{home_goals - away_goals:+d}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="xG Difference", 
                    value=f"{home_xg - away_xg:+.2f}",
                    delta=None
                )
            
            with col3:
                game_tempo = (home_shots + away_shots) / max(current_minute, 1)
                st.metric(
                    label="Game Tempo", 
                    value=f"{game_tempo:.2f}",
                    help="Shots per minute"
                )
            
            with col4:
                total_xg = home_xg + away_xg
                home_dominance = home_xg / max(total_xg, 0.001) if total_xg > 0 else 0.5
                st.metric(
                    label="Home xG%", 
                    value=f"{home_dominance:.1%}",
                    help="Home team's share of total xG"
                )
                
        except Exception as e:
            st.error(f"❌ Hiba a predikció során: {e}")
            st.markdown(f"""
            <div class="error-box">
                <strong>Részletes hiba információ:</strong><br>
                {str(e)}
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Welcome screen (ugyanaz marad)
        st.markdown("""
        ## 🚀 How to Use
        
        1. **Enter Team Names** in the sidebar
        2. **Set Current Match State** (minute, score)
        3. **Input Match Statistics** (xG, shots)
        4. **Click 'Predict Match Outcome'** to get predictions
        
        ## 🧠 What This Predicts
        
        - **1 (Home Win)** - Probability of home team victory
        - **X (Draw)** - Probability of match ending in a draw  
        - **2 (Away Win)** - Probability of away team victory
        
        ## 📊 Features
        
        - **Real trained ML model** using professional football data
        - Advanced feature engineering with xG and temporal data
        - **Interactive visualizations** with real-time updates
        - **AI-generated insights** and recommendations
        
        ---
        **Data Sources**: Euro 2024, Bundesliga, Ligue 1 matches
        **Model**: Random Forest with feature selection and cross-validation
        """)

# Footer
def add_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        ⚽ Live Match Predictor | Powered by Trained ML Model<br>
        Built with Streamlit & Python | Professional Football Data Analytics
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    add_footer()