import pandas as pd
import networkx as nx
from typing import Dict, List

class DataAnalyzer:
    def __init__(self, df_history: pd.DataFrame):
        self.df = df_history
        self.graph = nx.Graph()
        
    def analyze(self):
        # 1. Build Network from Sessions
        sessions = self.df[self.df['session_id'].notnull()]
        for sid, group in sessions.groupby('session_id'):
            users_in_session = group['user_id'].dropna().unique().tolist()
            for i in range(len(users_in_session)):
                for j in range(i + 1, len(users_in_session)):
                    u1, u2 = users_in_session[i], users_in_session[j]
                    if self.graph.has_edge(u1, u2):
                        self.graph[u1][u2]['weight'] += 1
                    else:
                        self.graph.add_edge(u1, u2, weight=1)
        
        # 2. Key Metrics per Identified User
        user_stats = self.df[self.df['user_id'].notnull()].groupby('user_id').agg({
            'amount': ['sum', 'count', 'mean'],
            'timestamp': 'max'
        }).reset_index()
        
        user_stats.columns = ['user_id', 'total_spend', 'visit_count', 'avg_ticket', 'last_visit']
        
        # 3. Add Network Metrics
        centrality = nx.degree_centrality(self.graph)
        degrees = dict(self.graph.degree())
        
        user_stats['influence_score'] = user_stats['user_id'].map(centrality).fillna(0)
        user_stats['connections'] = user_stats['user_id'].map(degrees).fillna(0)
        
        # 4. Churn Risk (Simplified)
        # Risk = Days since last visit / Avg interval
        today = self.df['timestamp'].max()
        user_stats['days_since_last'] = (today - user_stats['last_visit']).dt.days
        user_stats['churn_risk'] = (user_stats['days_since_last'] > 30).astype(int) # Simple threshold
        
        # 5. Viral Attribution (Who brings new people?)
        # Find first visit for every ID
        first_visits = self.df.groupby('user_id')['timestamp'].min().reset_index()
        # Non-essential simplification: we track hosts of sessions containing these first visits
        user_stats['viral_acquisitions'] = 0 # Placeholder for complex logic in next iteration
        
        # 6. Lookalike Influencer Detection (Anonymous with large sessions)
        self.lookalikes = self.df[self.df['user_id'].isnull()].groupby('session_id').filter(lambda x: len(x) > 2)
        
        return user_stats, self.graph

    def get_summary_stats(self):
        total_rev = self.df['amount'].sum()
        total_trans = len(self.df)
        identified_pct = self.df['user_id'].notnull().mean() * 100
        
        return {
            'total_revenue': total_rev,
            'total_transactions': total_trans,
            'identified_percentage': identified_pct,
            'avg_group_size': self.df.groupby('session_id').size().mean() if not self.df['session_id'].isnull().all() else 1
        }
