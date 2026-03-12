import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import time

# --- 1. Load Data ---
print("Loading V2 prepared data...")
data_path = 'e:/Data/bgg/data/prepared_data_v2.csv'
df = pd.read_csv(data_path)

X = df.drop(columns=['BGGId', 'AvgRating'])
y = df['AvgRating']

print(f"Dataset shape: {X.shape}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 2. Train XGBoost Model ---
print("\n--- Training XGBoost Regressor ---")
# Using robust parameters for a wide dataset
xgb_model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

start_time = time.time()
xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)
fit_time = time.time() - start_time

print(f"\nTraining took {fit_time:.2f} seconds.")

# --- 3. Evaluate Best Model ---
y_pred = xgb_model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n=== FINAL V2 MODEL RESULTS (XGBoost) ===")
print("Previous Baseline: RMSE: 0.6533 | R^2: 0.5373")
print("----------------------------------------")
print(f"XGBoost RMSE: {rmse:.4f}")
print(f"XGBoost MAE:  {mae:.4f}")
print(f"XGBoost R^2:  {r2:.4f}")

# --- 4. Feature Importance ---
print("\n--- Feature Importance ---")
importances = xgb_model.feature_importances_
feature_names = X.columns
feature_imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
feature_imp_df = feature_imp_df.sort_values(by='Importance', ascending=False)
print(feature_imp_df.head(15))

# Create a plot for the artifact directory
plt.figure(figsize=(10, 8))
sns.barplot(x='Importance', y='Feature', data=feature_imp_df.head(20))
plt.title('Top 20 Most Important Features (XGBoost V2)')
plt.tight_layout()
plt_path = 'C:/Users/Adam/.gemini/antigravity/brain/9fda76a7-06c2-4578-8207-659798bd2e76/feature_importance_v2.png'
plt.savefig(plt_path)
print(f"V2 Feature importance plot saved to {plt_path}")

# --- 5. Save Final Model ---
model_path = 'e:/Data/bgg/bgg_xgboost_v2_model.joblib'
print(f"\nSaving XGBoost model to {model_path}...")
joblib.dump(xgb_model, model_path)
print("Done!")
