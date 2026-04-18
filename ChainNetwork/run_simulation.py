import os
from simulator.engine import SimulationEngine

def main():
    # Make sure data directory exists
    os.makedirs('data', exist_ok=True)
    
    engine = SimulationEngine(days=90, num_users=1000)
    
    print("Running Baseline Simulation...")
    df_baseline = engine.run(mode='baseline')
    df_baseline.to_csv('data/baseline_visits.csv', index=False)
    print(f"Done. Saved {len(df_baseline)} visits to data/baseline_visits.csv")
    
    print("\nRunning Optimized Simulation...")
    df_optimized = engine.run(mode='optimized')
    df_optimized.to_csv('data/optimized_visits.csv', index=False)
    print(f"Done. Saved {len(df_optimized)} visits to data/optimized_visits.csv")
    
    # Simple stats comparison
    print("\n--- Summary Stats ---")
    print(f"Baseline Total Revenue: {df_baseline['spend'].sum():,.0f} Ft")
    print(f"Optimized Total Revenue: {df_optimized['spend'].sum():,.0f} Ft")
    
    revenue_uplift = (df_optimized['spend'].sum() / df_baseline['spend'].sum() - 1) * 100
    print(f"Revenue Uplift: {revenue_uplift:.2f}%")

if __name__ == "__main__":
    main()
