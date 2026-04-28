import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import os

def analyze_results():
    if not os.path.exists('results.json'):
        print("No results found. Please run tester.py first.")
        return

    try:
        with open('results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading results.json: {e}")
        return

    if not data:
        print("results.json is empty. Please complete at least one scenario in tester.py.")
        return

    df = pd.DataFrame(data)
    
    ev_losses = df['ev_loss'].values
    n = len(ev_losses)
    mean_loss = np.mean(ev_losses)
    std_dev = np.std(ev_losses, ddof=1) if n > 1 else 0
    
    # 95% Confidence Interval for the mean EV loss
    if n > 1:
        se = stats.sem(ev_losses)
        if se == 0:
            ci = (mean_loss, mean_loss)
        else:
            ci = stats.t.interval(0.95, n-1, loc=mean_loss, scale=se)
    else:
        ci = (mean_loss, mean_loss)

    print("\n" + "="*60)
    print("  STATISTICAL PERFORMANCE ANALYSIS".center(60))
    print("="*60)
    print(f"Total Decisions Analyzed: {n}")
    print(f"Accuracy Rate:           {(df['correct'].mean()*100):.1f}%")
    print(f"Average EV Loss/Decision: {mean_loss:.4f} bb")
    print(f"Standard Deviation:      {std_dev:.4f} bb")
    print(f"95% Confidence Interval:  [{ci[0]:.4f}, {ci[1]:.4f}] bb")
    print("-" * 60)

    # Simulation Logic
    # Assuming 2 decisions per hand on average
    decisions_per_hand = 2.0
    estimated_winrate_loss = mean_loss * decisions_per_hand * 100 # bb/100
    
    print(f"Estimated Winrate Impact: -{estimated_winrate_loss:.2f} bb/100")
    print("\nInterpretation:")
    if mean_loss < 0.05:
        print(">>> ELITE: Your theory is near-optimal. Focus on exploitation.")
    elif mean_loss < 0.15:
        print(">>> ADVANCED: Solid fundamentals. Minor leaks found.")
    else:
        print(">>> DEVELOPING: Significant theory gaps. Study recommended.")
    
    # Visualization
    try:
        plt.figure(figsize=(12, 5))
        plt.style.use('dark_background')
        
        # Histogram of EV losses
        plt.subplot(1, 2, 1)
        plt.hist(ev_losses, bins=max(5, n), color='#00f2ff', alpha=0.7, edgecolor='white')
        plt.title('Distribution of EV Losses')
        plt.xlabel('EV Loss (bb)')
        plt.ylabel('Frequency')

        # Simulation plot (Monte Carlo)
        plt.subplot(1, 2, 2)
        # Simulate winrate distribution
        # Standard deviation for winrate in bb/100 is typically around 70-100 bb/100
        # Here we use the measured variance of decisions to show potential spread
        winrates = - estimated_winrate_loss + np.random.normal(0, max(5, std_dev * 50), 1000)
        plt.hist(winrates, bins=30, color='#ff00ff', alpha=0.7, edgecolor='white')
        plt.axvline(0, color='white', linestyle='--', label='Breakeven')
        plt.axvline(-estimated_winrate_loss, color='yellow', linestyle='-', label='Mean')
        plt.title('Projected 100k Hand Winrate Spread')
        plt.xlabel('bb/100')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('performance_report.png')
        print(f"\n[V] Performance visualization saved to performance_report.png")
        # plt.show() # Disabled for headless or background execution consistency
    except Exception as e:
        print(f"Visualization error: {e}")

if __name__ == "__main__":
    analyze_results()
