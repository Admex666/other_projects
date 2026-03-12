import pandas as pd
import numpy as np

# Load the dataset
games_path = 'e:/Data/bgg/data/games.csv'
print(f"Loading {games_path}...")
df = pd.read_csv(games_path)

print("--- DATASET INFO ---")
df.info()

print("\n--- MISSING VALUES ---")
missing_vals = df.isnull().sum()
print(missing_vals[missing_vals > 0])

print("\n--- DESCRIPTIVE STATISTICS (Numeric) ---")
print(df.describe().T)

print("\n--- TOP 5 ROWS ---")
print(df.head())

print("\n--- TARGET VARIABLE (AvgRating) Stats ---")
if 'AvgRating' in df.columns:
    print(df['AvgRating'].describe())
else:
    print("AvgRating column not found!")
