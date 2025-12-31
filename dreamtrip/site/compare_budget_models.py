import numpy as np
import scipy.stats as stats
import math

# Data
cities = ["New York", "London", "Barcelona", "Tokyo", "Lisbon", "Budapest", "Bangkok", "Bali"]
y = np.array([500, 227, 164, 88, 135, 101, 95, 100])
x = np.array([100.0, 83.2, 59.2, 56.4, 54.5, 50.9, 41.2, 25.4])

def check_fit(x_data, y_data, model_name):
    # Linear: y = a*x + b
    res_lin = stats.linregress(x_data, y_data)
    
    # Log: y = a*ln(x) + b
    ln_x = np.log(x_data)
    res_log = stats.linregress(ln_x, y_data)
    
    # Exponential: ln(y) = a*x + b  => y = e^b * e^(ax)
    ln_y = np.log(y_data)
    res_exp = stats.linregress(x_data, ln_y)
    
    # Power: ln(y) = a*ln(x) + b => y = e^b * x^a
    res_pow = stats.linregress(ln_x, ln_y)
    
    return {
        "Linear": res_lin.rvalue**2,
        "Logarithmic": res_log.rvalue**2,
        "Exponential": res_exp.rvalue**2,
        "Power": res_pow.rvalue**2
    }

print("R-squared comparison for various models:")
fits = check_fit(x, y, "All")
for name, r2 in fits.items():
    print(f"{name:12}: R2 = {r2:.4f}")

# Let's see the Logarithmic prediction
ln_x = np.log(x)
slope, intercept, r, p, std = stats.linregress(ln_x, y)
print(f"\nLogarithmic Formula: Cost = {slope:.2f} * ln(Index) + {intercept:.2f}")

print("\nLogarithmic Predictions:")
for c, xi, yi in zip(cities, x, y):
    pred = slope * math.log(xi) + intercept
    print(f"{c:12}: Actual ${yi:3} | Pred ${pred:3.0f} | Diff ${yi - pred:4.1f}")
