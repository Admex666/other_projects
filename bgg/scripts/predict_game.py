import pandas as pd
import numpy as np
import joblib

model_path = 'e:/Data/bgg/bgg_rf_model.joblib'
kmeans_path = 'e:/Data/bgg/bgg_kmeans_model.joblib'

print("Loading models...")
try:
    rf_model = joblib.load(model_path)
    kmeans_model = joblib.load(kmeans_path)
except FileNotFoundError:
    print("Error: Models not found. Make sure optimize_rf.py has finished running.")
    exit(1)

# Define a hypothetical game
# Core features (using median/average values as a base, tweaked for a specific genre)
# Let's imagine a heavy, modern, long-playing Kickstarter game
hypothetical_game = {
    'YearPublished': [2024],
    'GameWeight': [4.5],       # Very heavy/complex
    'MinPlayers': [1],
    'MaxPlayers': [4],
    'MfgPlaytime': [180],      # 3 hours
    'MfgAgeRec': [14],         # For teenagers/adults
    'NumExpansions': [2],      # Comes with expansions
    'Kickstarted': [1],        # Yes
    'IsReimplementation': [0]  # Original IP
}

# The PCA features for mechanics and themes are harder to guess manually
# so we will just feed in zeros (average value since they are standard scaled)
for i in range(1, 11):
    hypothetical_game[f'Mech_PC{i}'] = [0.0]
    hypothetical_game[f'Theme_PC{i}'] = [0.0]

# Convert to DataFrame
test_df = pd.DataFrame(hypothetical_game)

# Apply KMeans clustering to get the 'Cluster' feature
print("Calculating cluster...")
kmeans_features = [col for col in rf_model.feature_names_in_ if col != 'Cluster']
test_df = test_df[kmeans_features]
test_df['Cluster'] = kmeans_model.predict(test_df)

# Predict Rating
print("Predicting average rating...")
predicted_rating = rf_model.predict(test_df[rf_model.feature_names_in_])

print("\n==============================================")
print(" Hypothetical Game Profile:")
for k, v in hypothetical_game.items():
    if not k.startswith("Mech") and not k.startswith("Theme"):
        print(f"  - {k}: {v[0]}")
print("----------------------------------------------")
print(f" Predicted BGG Average Rating: {predicted_rating[0]:.2f}")
print("==============================================")
