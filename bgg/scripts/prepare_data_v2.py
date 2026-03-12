import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os

base_path = 'e:/Data/bgg/data/'

def load_and_pca(filename, prefix, n_components=10):
    print(f"Loading {filename} for PCA...")
    df = pd.read_csv(os.path.join(base_path, filename))
    features = df.drop(columns=['BGGId'])
    
    # Standardize
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(features)
    
    # PCA
    pca = PCA(n_components=n_components, random_state=42)
    pca_feats = pca.fit_transform(scaled_feats)
    
    # Create DataFrame
    pca_df = pd.DataFrame(pca_feats, columns=[f'{prefix}_PC{i+1}' for i in range(n_components)])
    pca_df['BGGId'] = df['BGGId']
    
    # Save explained variance ratio for context
    explained_var = sum(pca.explained_variance_ratio_)
    print(f"  {prefix} PCA explains {explained_var*100:.1f}% variance.")
    return pca_df

# --- 1. Load Main Data ---
print("Loading core games.csv data...")
games = pd.read_csv(os.path.join(base_path, 'games.csv'))
games = games.dropna(subset=['AvgRating'])

core_features = [
    'BGGId', 'YearPublished', 'GameWeight', 'MinPlayers', 'MaxPlayers', 
    'MfgPlaytime', 'MfgAgeRec', 'NumExpansions', 'NumAlternates', 
    'Kickstarted', 'IsReimplementation', 'AvgRating'
]
games_df = games[core_features].copy()

# Fill missing
for col in ['YearPublished', 'GameWeight', 'MinPlayers', 'MaxPlayers', 'MfgPlaytime', 'MfgAgeRec', 'NumExpansions', 'NumAlternates']:
    games_df[col] = games_df[col].fillna(games_df[col].median())

# --- 2. Feature Engineering: Log Transformations ---
print("Applying log1p transformations to skewed numericals...")
# Playtime and Expansions can be highly skewed
games_df['Log_MfgPlaytime'] = np.log1p(games_df['MfgPlaytime'])
games_df['Log_NumExpansions'] = np.log1p(games_df['NumExpansions'])
games_df['Log_NumAlternates'] = np.log1p(games_df['NumAlternates'])
games_df = games_df.drop(columns=['MfgPlaytime', 'NumExpansions', 'NumAlternates'])

# --- 3. Feature Engineering: Interactions ---
print("Creating feature interactions...")
# Weight per Age
games_df['Weight_x_Age'] = games_df['GameWeight'] * games_df['MfgAgeRec']
# Weight per LogPlaytime
games_df['Weight_x_LogPlaytime'] = games_df['GameWeight'] * games_df['Log_MfgPlaytime']
# Player Range
games_df['PlayerRange'] = games_df['MaxPlayers'] - games_df['MinPlayers']

# --- 4. PCA on Sparse Matrices ---
# Game features
mech_pca = load_and_pca('mechanics.csv', 'Mech', 15)
theme_pca = load_and_pca('themes.csv', 'Theme', 15)

# Creator features
des_pca = load_and_pca('designers_reduced.csv', 'Designer', 15)
pub_pca = load_and_pca('publishers_reduced.csv', 'Publisher', 15)
art_pca = load_and_pca('artists_reduced.csv', 'Artist', 15)

# --- 5. Merge Everything ---
print("\nMerging dataset...")
final_df = pd.merge(games_df, mech_pca, on='BGGId', how='left')
final_df = pd.merge(final_df, theme_pca, on='BGGId', how='left')
final_df = pd.merge(final_df, des_pca, on='BGGId', how='left')
final_df = pd.merge(final_df, pub_pca, on='BGGId', how='left')
final_df = pd.merge(final_df, art_pca, on='BGGId', how='left')

# Drop NA rows introduced by merge
final_df = final_df.dropna()

print(f"Final shape: {final_df.shape}")

# --- 6. Output ---
out_path = os.path.join(base_path, 'prepared_data_v2.csv')
print(f"Saving to {out_path}...")
final_df.to_csv(out_path, index=False)
print("Done!")
