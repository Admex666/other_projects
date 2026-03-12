import pandas as pd
import joblib
import os

base_path = 'e:/Data/bgg/'
data_path = os.path.join(base_path, 'data/')

print("1. Loading V2 Model...")
model = joblib.load(os.path.join(base_path, 'models/bgg_xgboost_v2_model.joblib'))
feature_names = model.feature_names_in_

print("2. Loading game datasets...")
# Base game info for humans
games_df = pd.read_csv(os.path.join(data_path, 'games.csv'))
games_df = games_df.dropna(subset=['AvgRating'])

# V2 Prepared data for the ML model
v2_df = pd.read_csv(os.path.join(data_path, 'prepared_data_v2.csv'))

# Keep only the rows that exist in the V2 dataset (some might have been dropped during PCA merges)
games_df = games_df[games_df['BGGId'].isin(v2_df['BGGId'])]

print(f"Loaded {len(v2_df)} matching games.")

print("3. Predicting ratings and calculating residuals...")
# Ensure column order
X = v2_df[feature_names]

# Predict
predicted_ratings = model.predict(X)
v2_df['ExpectedRating'] = predicted_ratings

# Calculate residual (Actual - Expected)
v2_df['Residual'] = v2_df['AvgRating'] - v2_df['ExpectedRating']

print("4. Merging with human-readable game data...")
# We only want to pull the human readable names and image paths from games_df, 
# while keeping the core stats from V2 and the Residuals.
display_cols = ['BGGId', 'Name', 'Description', 'ImagePath', 'YearPublished']
human_data = games_df[display_cols]

final_df = pd.merge(human_data, v2_df, on=['BGGId', 'YearPublished'])

print("5. Saving backend cache...")
# Sort by highest residual to make the Streamlit default view interesting
final_df = final_df.sort_values(by='Residual', ascending=False)
out_path = os.path.join(data_path, 'hidden_gems_cache.csv')
final_df.to_csv(out_path, index=False)

print(f"Success! Cached data saved to {out_path}")
