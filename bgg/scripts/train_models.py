import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import time

# --- 1. Load Prepared Data ---
print("Loading prepared data...")
data_path = 'e:/Data/bgg/data/prepared_data.csv'
df = pd.read_csv(data_path)

# Separate features (X) and target (y)
# We drop BGGId as it's just an identifier
X = df.drop(columns=['BGGId', 'AvgRating'])
y = df['AvgRating']

# --- 2. KMeans Clustering (Feature Engineering) ---
# The user requested KMeans. KMeans is for unsupervised learning, 
# so we will use it to cluster the games and add the cluster label as a new feature
print("\n--- Running KMeans Clustering ---")
# Use 5 clusters as a starting point
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)
X['Cluster'] = cluster_labels
print("Added KMeans cluster labels as a new feature.")

# --- 3. Train-Test Split ---
print("\nSplitting data into train/test sets (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training set size: {X_train.shape[0]}")
print(f"Testing set size: {X_test.shape[0]}")

# --- 4. Model Training & Evaluation Function ---
def evaluate_model(model_name, y_true, y_pred, fit_time):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n--- {model_name} Results ---")
    print(f"Training Time: {fit_time:.2f} seconds")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE:  {mae:.4f}")
    print(f"R^2:  {r2:.4f}")
    return {"Model": model_name, "RMSE": rmse, "MAE": mae, "R2": r2, "Time": fit_time}

results = []

# --- 5. Linear Regression ---
print("\nTraining Linear Regression...")
lr = LinearRegression()
start_time = time.time()
lr.fit(X_train, y_train)
fit_time_lr = time.time() - start_time
y_pred_lr = lr.predict(X_test)
results.append(evaluate_model("Linear Regression", y_test, y_pred_lr, fit_time_lr))

# --- 6. Decision Tree Regressor ---
print("\nTraining Decision Tree Regressor...")
dt = DecisionTreeRegressor(random_state=42, max_depth=10) # limit depth to prevent massive overfitting
start_time = time.time()
dt.fit(X_train, y_train)
fit_time_dt = time.time() - start_time
y_pred_dt = dt.predict(X_test)
results.append(evaluate_model("Decision Tree", y_test, y_pred_dt, fit_time_dt))

# --- 7. Random Forest Regressor ---
print("\nTraining Random Forest Regressor (this may take a minute)...")
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
start_time = time.time()
rf.fit(X_train, y_train)
fit_time_rf = time.time() - start_time
y_pred_rf = rf.predict(X_test)
results.append(evaluate_model("Random Forest", y_test, y_pred_rf, fit_time_rf))

# --- 8. Summary ---
print("\n\n=== FINAL MODEL COMPARISON ===")
results_df = pd.DataFrame(results)
print(results_df.sort_values(by='RMSE'))
