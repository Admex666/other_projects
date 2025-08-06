import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from analysis import Analyzer # Assuming Analyzer is available

class Visualizer:
    """
    Handles visualization of simulation data.
    """
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
        self.df = self.analyzer.get_dataframe()

    def plot_win_rates(self):
        """Plots the win rates of the two strategies."""
        if self.df.empty:
            print("No data to plot win rates.")
            return

        win_counts = self.df['phase_winner'].value_counts()
        
        plt.figure(figsize=(8, 6))
        sns.barplot(x=win_counts.index, y=win_counts.values, palette='viridis')
        plt.title('Strategy Win Rates')
        plt.xlabel('Strategy')
        plt.ylabel('Number of Wins')
        plt.show()

    def plot_damage_distribution(self):
        """Plots the distribution of damage dealt."""
        if self.df.empty:
            print("No data to plot damage distribution.")
            return

        plt.figure(figsize=(10, 6))
        sns.histplot(self.df['defender_final_damage'], bins=10, kde=True, color='skyblue')
        plt.title('Distribution of Damage Dealt by Attacker')
        plt.xlabel('Total Damage Dealt')
        plt.ylabel('Frequency')
        plt.show()

    def plot_injury_distribution(self):
        """Plots the distribution of serious injuries received."""
        if self.df.empty:
            print("No data to plot injury distribution.")
            return

        plt.figure(figsize=(8, 6))
        sns.countplot(x=self.df['attacker_final_injuries'], palette='magma')
        plt.title('Distribution of Serious Injuries Received by Attacker')
        plt.xlabel('Number of Serious Injuries')
        plt.ylabel('Frequency')
        plt.show()

if __name__ == '__main__':
    # Example usage:
    # 1. Run main.py to generate simulation_log.json
    # 2. Run analysis.py to see basic stats
    # 3. Run this file to generate plots

    # Ensure you have matplotlib and seaborn installed:
    # pip install matplotlib seaborn pandas

    analyzer = Analyzer("simulation_log.json")
    visualizer = Visualizer(analyzer)

    visualizer.plot_win_rates()
    visualizer.plot_damage_distribution()
    visualizer.plot_injury_distribution()
