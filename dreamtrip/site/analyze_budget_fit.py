import numpy as np
import scipy.stats as stats

# Data
cities = ["New York", "London", "Barcelona", "Tokyo", "Lisbon", "Budapest", "Bangkok", "Bali"]
budgets = [500, 227, 164, 88, 135, 101, 95, 100]
indices = [100.0, 83.2, 59.2, 56.4, 54.5, 50.9, 41.2, 25.4]

# Regression
slope, intercept, r_value, p_value, std_err = stats.linregress(indices, budgets)

print(f"Multiplier (Slope): {slope:.2f}")
print(f"Intercept: {intercept:.2f}")
print(f"Correlation (R): {r_value:.4f}")
print(f"R-squared: {r_value**2:.4f}")

print("\nPredictions vs Actual:")
for city, ind, bud in zip(cities, indices, budgets):
    pred = slope * ind + intercept
    error = pred - bud
    print(f"{city:12}: Index {ind:5.1f} | Real Budget ${bud:3} | Pred ${pred:3.0f} | Error ${error:4.1f}")
