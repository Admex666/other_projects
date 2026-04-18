import random
import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple
from .models import Transaction, UserProfile

class HistoryGenerator:
    def __init__(self, num_users: int = 1000, seed: int = 42):
        random.seed(seed)
        self.num_users = num_users
        self.users = self._generate_base_population()
        
    def _generate_base_population(self):
        users = []
        segments = ['casual', 'regular', 'loyal']
        weights = [0.6, 0.3, 0.1]
        
        for i in range(self.num_users):
            seg = random.choices(segments, weights)[0]
            # Hidden traits that will govern behavior
            users.append({
                'user_id': f"U_{i:04d}",
                'segment': seg,
                'base_prob': random.uniform(0.01, 0.05) if seg == 'casual' else random.uniform(0.1, 0.3) if seg == 'regular' else random.uniform(0.4, 0.7),
                'avg_spend': random.uniform(2000, 4000) if seg == 'casual' else random.uniform(4000, 8000) if seg == 'regular' else random.uniform(7000, 15000),
                'sociability': random.uniform(0, 1),
                'friends': []
            })
            
        # Create a social graph (hidden circles)
        for u in users:
            circle_size = random.randint(2, 6)
            same_seg = [other['user_id'] for other in users if other['segment'] == u['segment'] and other['user_id'] != u['user_id']]
            u['friends'] = random.sample(same_seg, min(circle_size, len(same_seg)))
            
        return users

    def generate_history(self, months: int = 6) -> pd.DataFrame:
        start_date = datetime.now() - timedelta(days=months * 30)
        transactions = []
        
        for day in range(months * 30):
            current_date = start_date + timedelta(days=day)
            
            for u in self.users:
                # Does the user visit today?
                if random.random() < u['base_prob'] / 7.0:
                    
                    # Is it a group session?
                    if u['friends'] and random.random() < u['sociability']:
                        session_id = f"S_{uuid.uuid4().hex[:6]}"
                        num_friends = random.randint(1, 4)
                        attendees = [u['user_id']] + random.sample(u['friends'], min(num_friends, len(u['friends'])))
                        
                        for attendee_id in attendees:
                            # 70% chance to be "identified" in history (e.g. paying via app or card linked to account)
                            # Actually, in raw history, most are anonymous. Let's make it 30% identified.
                            is_identified = random.random() < 0.3
                            
                            transactions.append({
                                'transaction_id': f"T_{uuid.uuid4().hex[:8]}",
                                'timestamp': current_date + timedelta(minutes=random.randint(0, 120)),
                                'amount': next(usr['avg_spend'] for usr in self.users if usr['user_id'] == attendee_id) * random.uniform(0.9, 1.1),
                                'user_id': attendee_id if is_identified else None,
                                'session_id': session_id
                            })
                    else:
                        # Individual visit
                        transactions.append({
                            'transaction_id': f"T_{uuid.uuid4().hex[:8]}",
                            'timestamp': current_date,
                            'amount': u['avg_spend'] * random.uniform(0.9, 1.1),
                            'user_id': u['user_id'] if random.random() < 0.3 else None,
                            'session_id': None
                        })
                        
        return pd.DataFrame(transactions)
