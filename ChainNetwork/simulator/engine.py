import pandas as pd
import random
from datetime import datetime, timedelta
from .history import HistoryGenerator
from .analyzer import DataAnalyzer

class SimulationEngine:
    def __init__(self, num_users: int = 1000):
        self.gen = HistoryGenerator(num_users=num_users)
        self.df_history = None
        self.analyzer = None
        self.user_stats = None
        
    def generate_past(self, months: int = 6):
        self.df_history = self.gen.generate_history(months=months)
        self.analyzer = DataAnalyzer(self.df_history)
        self.user_stats, self.graph = self.analyzer.analyze()
        return self.df_history, self.user_stats
        
    def run_projection(self, days: int = 90, 
                       identification_boost: float = 2.0, 
                       influencer_retention_boost: float = 1.3,
                       reward_cost_pct: float = 0.05):
        """
        Simulates the FUTURE.
        Baseline: Future as regular (following historical trends).
        Optimized: Future with ChainNetwork logic.
        """
        # We start from 'today'
        start_date = datetime.now()
        
        # Calculate Future Baseline vs Optimized
        results = []
        
        for mode in ['baseline', 'optimized']:
            total_rev = 0
            total_costs = 0
            future_visits = []
            
            # The "Optimized" mode makes influencers come back 30% more often
            # and identifies more people.
            
            for day in range(days):
                curr_date = start_date + timedelta(days=day)
                for u in self.gen.users:
                    
                    # Determine current retention prob
                    prob = u['base_prob']
                    
                    # If we identified this user through analyzer and they are an influencer
                    if mode == 'optimized':
                        user_id = u['user_id']
                        # Check if high influence in history
                        cent = self.user_stats[self.user_stats['user_id'] == user_id]['influence_score'].values
                        if len(cent) > 0 and cent[0] > 0.02:
                             prob *= influencer_retention_boost
                    
                    if random.random() < prob / 7.0:
                        spend = u['avg_spend'] * random.uniform(0.9, 1.1)
                        cost = spend * reward_cost_pct if mode == 'optimized' else 0
                        
                        future_visits.append({
                            'date': curr_date,
                            'spend': spend,
                            'cost': cost,
                            'mode': mode
                        })
            
            results.append(pd.DataFrame(future_visits))
            
        return results[0], results[1] # baseline_df, optimized_df
