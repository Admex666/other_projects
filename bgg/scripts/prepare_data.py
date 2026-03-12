import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# --- 1. Load Data ---
print("Loading datasets...")
base_path = 'e:/Data/bgg/data/'
games = pd.read_csv(base_path + 'games.csv')
mechanics = pd.read_csv(base_path + 'mechanics.csv')
themes = pd.read_csv(base_path + 'themes.csv')

print(f"Games shape: {games.shape}")
print(f"Mechanics shape: {mechanics.shape}")
print(f"Themes shape: {themes.shape}")

# --- 2. Clean Core Features (games) ---
print("Handling missing values in games...")
# We drop rows where AvgRating is somehow missing (our target)
games = games.dropna(subset=['AvgRating'])

# Features we want to keep from games.csv
core_features = [
    'BGGId', 'YearPublished', 'GameWeight', 'MinPlayers', 'MaxPlayers', 
    'MfgPlaytime', 'MfgAgeRec', 'NumExpansions', 'Kickstarted', 'IsReimplementation', 
    'AvgRating' # Target
]
games_selected = games[core_features].copy()

# Fill missing numerical values with median (if any)
for col in ['YearPublished', 'GameWeight', 'MinPlayers', 'MaxPlayers', 'MfgPlaytime', 'MfgAgeRec', 'NumExpansions']:
    games_selected[col].fillna(games_selected[col].median(), inplace=True)

# --- 3. Process Sparse Binary Features (Mechanics & Themes) ---
print("Applying PCA to mechanics and themes...")
# PCA on Mechanics
mech_features = mechanics.drop(columns=['BGGId'])
scaler_mech = StandardScaler()
mech_scaled = scaler_mech.fit_transform(mech_features)
pca_mech = PCA(n_components=10, random_state=42) # Reduce to 10 principal components
mech_pca = pca_mech.fit_transform(mech_scaled)
mech_pca_df = pd.DataFrame(mech_pca, columns=[f'Mech_PC{i+1}' for i in range(10)])
mech_pca_df['BGGId'] = mechanics['BGGId']

# PCA on Themes
theme_features = themes.drop(columns=['BGGId'])
scaler_theme = StandardScaler()
theme_scaled = scaler_theme.fit_transform(theme_features)
pca_theme = PCA(n_components=10, random_state=42) # Reduce to 10 principal components
theme_pca = pca_theme.fit_transform(theme_scaled)
theme_pca_df = pd.DataFrame(theme_pca, columns=[f'Theme_PC{i+1}' for i in range(10)])
theme_pca_df['BGGId'] = themes['BGGId']

# --- 4. Merge Everything ---
print("Merging dataframes...")
final_df = pd.merge(games_selected, mech_pca_df, on='BGGId', how='left')
final_df = pd.merge(final_df, theme_pca_df, on='BGGId', how='left')

# Drop any rows that couldn't be joined with components 
# (although BGGId should match, just to be safe)
final_df = final_df.dropna()

print(f"Final prepared shape: {final_df.shape}")

# Inspect final columns
print("Final Columns:")
print(list(final_df.columns))

# --- 5. Save output ---
output_path = base_path + 'prepared_data.csv'
print(f"Saving prepared dataset to {output_path}...")
final_df.to_csv(output_path, index=False)
print("Done!")
