import pandas as pd
import numpy as np
import joblib
import itertools

model_path = 'e:/Data/bgg/bgg_rf_model.joblib'
kmeans_path = 'e:/Data/bgg/bgg_kmeans_model.joblib'

print("Loading models...")
rf_model = joblib.load(model_path)
kmeans_model = joblib.load(kmeans_path)

# Let's grid search the core numerical/categorical features
weights = [1.5, 2.5, 3.5, 4.5, 5.0]
min_players = [1, 2, 3]
max_players = [4, 6, 8]
playtimes = [30, 60, 120, 180, 240, 360]
ages = [10, 12, 14, 16]
expansions = [0, 1, 3, 5]
kickstarted = [0, 1]
reimp = [0, 1]

combinations = list(itertools.product(weights, min_players, max_players, playtimes, ages, expansions, kickstarted, reimp))
print(f"Testing {len(combinations)} hypothetical games for the year 2025...")

# We will just hold the PCA components at 0.0 (the average mechanic/theme profile)
mechanics_themes = {f'Mech_PC{i}': 0.0 for i in range(1, 11)}
mechanics_themes.update({f'Theme_PC{i}': 0.0 for i in range(1, 11)})

data = []
for c in combinations:
    w, mip, map, pt, a, exp, k, r = c
    
    # We enforce logic: MaxPlayers >= MinPlayers
    if map < mip:
        continue
        
    row = {
        'YearPublished': 2025,
        'GameWeight': w,
        'MinPlayers': mip,
        'MaxPlayers': map,
        'MfgPlaytime': pt,
        'MfgAgeRec': a,
        'NumExpansions': exp,
        'Kickstarted': k,
        'IsReimplementation': r
    }
    row.update(mechanics_themes)
    data.append(row)

df = pd.DataFrame(data)

# Predict cluster
kmeans_features = [col for col in rf_model.feature_names_in_ if col != 'Cluster']
df_k = df[kmeans_features]
df['Cluster'] = kmeans_model.predict(df_k)

# Predict rating
df_eval = df[rf_model.feature_names_in_]
df['PredictedRating'] = rf_model.predict(df_eval)

top_games = df.sort_values(by='PredictedRating', ascending=False)
print("\n=== TOP 5 BEST COMBINATIONS FOR 2025 ===")
pd.set_option('display.max_columns', None)
print(top_games[['PredictedRating', 'GameWeight', 'MfgPlaytime', 'Kickstarted', 'NumExpansions', 'MinPlayers', 'MaxPlayers', 'MfgAgeRec', 'IsReimplementation']].head(5))

print("\n=== TOP 5 WORST COMBINATIONS FOR 2025 ===")
print(top_games[['PredictedRating', 'GameWeight', 'MfgPlaytime', 'Kickstarted', 'NumExpansions', 'MinPlayers', 'MaxPlayers', 'MfgAgeRec', 'IsReimplementation']].tail(5))
