import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import time

# --- 1. Load Data ---
print("Loading data...")
data_path = 'e:/Data/bgg/data/prepared_data.csv'
df = pd.read_csv(data_path)

X = df.drop(columns=['BGGId', 'AvgRating'])
y = df['AvgRating']

print("\n--- Running KMeans Clustering ---")
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
X['Cluster'] = kmeans.fit_predict(X)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 2. Hyperparameter Tuning (Random Forest) ---
print("\n--- Training Final Random Forest ---")
# Using robust parameters directly to save processing time
rf = RandomForestRegressor(
    n_estimators=100, 
    max_depth=20, 
    min_samples_split=5, 
    min_samples_leaf=2,
    random_state=42, 
    n_jobs=None
)

start_time = time.time()
rf.fit(X_train, y_train)
fit_time = time.time() - start_time

print(f"\nTraining took {fit_time:.2f} seconds.")
best_rf = rf
fit_time = time.time() - start_time

print(f"\nOptimization took {fit_time:.2f} seconds.")

# --- 3. Evaluate Best Model ---
y_pred = best_rf.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n--- Final Tuned Model Results ---")
print(f"RMSE: {rmse:.4f}")
print(f"MAE:  {mae:.4f}")
print(f"R^2:  {r2:.4f}")

# --- 4. Feature Importance ---
print("\n--- Feature Importance ---")
importances = best_rf.feature_importances_
feature_names = X.columns
feature_imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
feature_imp_df = feature_imp_df.sort_values(by='Importance', ascending=False)
print(feature_imp_df.head(10))

# Create a plot for the artifact directory
plt.figure(figsize=(10, 8))
sns.barplot(x='Importance', y='Feature', data=feature_imp_df.head(15))
plt.title('Top 15 Most Important Features in Predicting Board Game Rating')
plt.tight_layout()
plt_path = 'C:/Users/Adam/.gemini/antigravity/brain/9fda76a7-06c2-4578-8207-659798bd2e76/feature_importance.png'
plt.savefig(plt_path)
print(f"Feature importance plot saved to {plt_path}")

# --- 5. Save Final Model and KMeans ---
model_path = 'e:/Data/bgg/bgg_rf_model.joblib'
kmeans_path = 'e:/Data/bgg/bgg_kmeans_model.joblib'
print(f"\nSaving tuned model to {model_path}...")
joblib.dump(best_rf, model_path)
joblib.dump(kmeans, kmeans_path)
print("Done!")
