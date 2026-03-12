import streamlit as st
import pandas as pd
import numpy as np
import os

# --- 1. Load Data ---
@st.cache_data
def load_data():
    base_path = 'e:/Data/bgg/data/'
    # Load the pre-calculated residuals and stats
    df = pd.read_csv(os.path.join(base_path, 'hidden_gems_cache.csv'))
    # Reconstruct playtime from log
    if 'Log_MfgPlaytime' in df.columns and 'MfgPlaytime' not in df.columns:
        df['MfgPlaytime'] = np.expm1(df['Log_MfgPlaytime'])
    return df

st.set_page_config(page_title="BGG Hidden Gems Finder", layout="wide", page_icon="💎")

st.title("💎 BoardGameGeek Hidden Gems Finder")
st.markdown("""
Welcome to the Hidden Gems Finder! This tool uses an advanced **XGBoost Machine Learning model** 
to predict a game's expected rating based on its stats (Complexity, Playtime, Player Counts, Mechanisms).

It then calculates the **Residual** (Actual Rating - Expected Rating). Games with the highest positive 
residuals are **Hidden Gems**: they massively outperform other similar games in their niche!
""")

data = load_data()

# --- 2. Sidebar Filters ---
st.sidebar.header("Filter Your Niche")

# GameWeight (Complexity)
min_weight, max_weight = st.sidebar.slider(
    "Complexity (GameWeight)", 
    min_value=1.0, max_value=5.0, 
    value=(1.0, 5.0), step=0.1
)

# Playtime
min_time, max_time = st.sidebar.slider(
    "Playtime (Minutes)", 
    min_value=0, max_value=int(data['MfgPlaytime'].quantile(0.99)), # Remove extreme outliers from slider
    value=(0, 240), step=15
)

# Player Counts
min_p = st.sidebar.number_input("Minimum Players", min_value=1, max_value=10, value=1)
max_p = st.sidebar.number_input("Maximum Players", min_value=1, max_value=99, value=4)

# --- 3. Apply Filters ---
filtered_data = data[
    (data['GameWeight'] >= min_weight) & (data['GameWeight'] <= max_weight) &
    (data['MfgPlaytime'] >= min_time) & (data['MfgPlaytime'] <= max_time) &
    (data['MinPlayers'] <= min_p) & (data['MaxPlayers'] >= max_p)
]

# --- 4. Main Display ---
st.subheader(f"Found {len(filtered_data)} games in this niche.")

if not filtered_data.empty:
    st.markdown("### 🏆 Top 10 Hidden Gems in your Niche")
    st.markdown("*Sorted by the 'Hidden Gem Score' (Residual). Higher is better!*")
    
    # Format the display table cleanly
    display_df = filtered_data[['Name', 'AvgRating', 'ExpectedRating', 'Residual', 'GameWeight', 'MfgPlaytime', 'YearPublished']].head(10).copy()
    
    # Clean up formatting
    display_df['AvgRating'] = display_df['AvgRating'].round(2)
    display_df['ExpectedRating'] = display_df['ExpectedRating'].round(2)
    display_df['Residual'] = display_df['Residual'].round(3)
    display_df['GameWeight'] = display_df['GameWeight'].round(2)
    display_df['MfgPlaytime'] = display_df['MfgPlaytime'].astype(int)
    display_df['YearPublished'] = display_df['YearPublished'].astype(int)
    
    display_df = display_df.rename(columns={
        'AvgRating': 'Actual Rating',
        'ExpectedRating': 'Model Expected Rating',
        'Residual': 'Hidden Gem Score (Residual)',
        'GameWeight': 'Complexity (Weight)',
        'MfgPlaytime': 'Playtime (Mins)',
        'YearPublished': 'Year'
    })
    
    # Display the dataframe with Streamlit
    st.dataframe(
        display_df,
        column_config={
            "Hidden Gem Score (Residual)": st.column_config.NumberColumn(
                format="%.3f",
                help="Actual Rating minus Expected Rating"
            ),
            "Actual Rating": st.column_config.NumberColumn(
                format="%.2f ⭐",
            )
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Optional: Expanders for the descriptions of the top 3
    st.markdown("### Top 3 Details")
    for i in range(min(3, len(filtered_data))):
        game = filtered_data.iloc[i]
        with st.expander(f"#{i+1}: {game['Name']} (Score: +{game['Residual']:.3f})"):
            st.write(f"**Published:** {int(game['YearPublished'])}")
            st.write(game['Description'][:500] + "..." if isinstance(game['Description'], str) else "No description available.")
            
else:
    st.warning("No games found matching these specific filters. Try loosening the requirements!")

st.markdown("---")
st.caption("Developed using XGBoost & Streamlit Data Pipeline.")
