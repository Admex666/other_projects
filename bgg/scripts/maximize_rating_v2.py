import pandas as pd
import numpy as np
import joblib
import itertools

model_path = 'e:/Data/bgg/bgg_xgboost_v2_model.joblib'

print("Loading XGBoost V2 model...")
xgb_model = joblib.load(model_path)
feature_names = xgb_model.feature_names_in_

# Grid search parameters for 2025
weights = [1.5, 2.5, 3.5, 4.5, 5.0]
min_players = [1, 2, 3]
max_players = [4, 6, 8]
playtimes = [30, 60, 120, 240, 360, 720] # up to 12 hours
ages = [10, 12, 14, 16, 18]
expansions = [0, 1, 3, 5, 10] # lots of expansions
kickstarted = [0, 1]
reimp = [0, 1]

combinations = list(itertools.product(weights, min_players, max_players, playtimes, ages, expansions, kickstarted, reimp))
print(f"Testing {len(combinations)} hypothetical games for the year 2025...")

# Base values for all 90 features (0.0 implies average for standard scaled PCA features)
base_row = {col: 0.0 for col in feature_names}

data = []
for c in combinations:
    w, mip, map, pt, a, exp, k, r = c
    
    if map < mip:
        continue
        
    row = base_row.copy()
    
    row['YearPublished'] = 2025
    row['GameWeight'] = w
    row['MinPlayers'] = mip
    row['MaxPlayers'] = map
    
    # Logs
    row['Log_MfgPlaytime'] = np.log1p(pt)
    row['Log_NumExpansions'] = np.log1p(exp)
    row['Log_NumAlternates'] = np.log1p(0)
    
    row['MfgAgeRec'] = a
    row['Kickstarted'] = k
    row['IsReimplementation'] = r
    
    # Interactions
    row['Weight_x_Age'] = w * a
    row['Weight_x_LogPlaytime'] = w * np.log1p(pt)
    row['PlayerRange'] = map - mip
    
    data.append(row)

df = pd.DataFrame(data)
df_eval = df[feature_names] # Ensure correct column order

print("Predicting ratings...")
df['PredictedRating'] = xgb_model.predict(df_eval)

top_games = df.sort_values(by='PredictedRating', ascending=False)
print("\n=== TOP 5 BEST COMBINATIONS FOR 2025 (XGBoost V2) ===")
pd.set_option('display.max_columns', None)

cols_to_print = ['PredictedRating', 'GameWeight', 'Log_MfgPlaytime', 'Log_NumExpansions', 'Kickstarted', 'MinPlayers', 'MaxPlayers', 'MfgAgeRec', 'IsReimplementation']
top_print = top_games[cols_to_print].head(5).copy()
top_print['Playtime_mins'] = np.expm1(top_print['Log_MfgPlaytime']).round()
top_print['Expansions'] = np.expm1(top_print['Log_NumExpansions']).round()

print(top_print[['PredictedRating', 'GameWeight', 'Playtime_mins', 'Expansions', 'Kickstarted', 'MinPlayers', 'MaxPlayers', 'MfgAgeRec', 'IsReimplementation']])
