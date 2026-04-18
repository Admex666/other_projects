import random
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple
from .models import User, Visit, GroupSession

class DataGenerator:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self.users: List[User] = []

    def generate_users(self, count: int = 100) -> List[User]:
        segments = ['casual', 'regular', 'loyal']
        weights = [0.6, 0.3, 0.1]
        
        for i in range(count):
            segment = random.choices(segments, weights=weights)[0]
            if segment == 'casual':
                retention = random.uniform(0.05, 0.15)
                spend = random.uniform(2000, 4000)
            elif segment == 'regular':
                retention = random.uniform(0.2, 0.4)
                spend = random.uniform(3500, 7000)
            else: # loyal
                retention = random.uniform(0.5, 0.8)
                spend = random.uniform(6000, 12000)
                
            user = User(
                user_id=f"U_{i:04d}",
                segment=segment,
                base_retention_prob=retention,
                avg_spend=spend,
                is_registered=random.random() < 0.2, # 20% registration rate baseline
                friend_ids=[]
            )
            # Sociability: 0 means solo-only, 1 means group-heavy
            user.sociability = random.uniform(0, 1) if segment != 'casual' else random.uniform(0, 0.4)
            self.users.append(user)
            
        # Assign social circles (friends) - smaller circles: 3-7 people
        for user in self.users:
            if user.sociability < 0.3: # Loners have very few or no dining friends
                num_friends = random.randint(0, 2)
            else:
                num_friends = random.randint(3, 7)
                
            same_segment_pool = [u.user_id for u in self.users if u.segment == user.segment and u.user_id != user.user_id]
            if num_friends > 0:
                user.friend_ids = random.sample(same_segment_pool, min(num_friends, len(same_segment_pool)))
            
        return self.users

    def create_group_visit(self, timestamp: datetime, host: User, potential_members: List[User]) -> Tuple[GroupSession, List[Visit]]:
        group_id = f"G_{uuid.uuid4().hex[:6]}"
        size = random.randint(2, 5)
        
        # Select members ONLY from the host's social circle
        members_pool = [uid for uid in host.friend_ids]
        selected_uids = random.sample(members_pool, min(size - 1, len(members_pool)))
        all_ids = [host.user_id] + selected_uids
        
        session = GroupSession(
            session_id=group_id,
            host_id=host.user_id,
            member_ids=selected_uids,
            timestamp=timestamp,
            table_id=f"T_{random.randint(1, 20)}"
        )
        
        visits = []
        for uid in all_ids:
            # Find the user object if they exist in our pool
            user_obj = next((u for u in self.users if u.user_id == uid), None)
            base_spend = user_obj.avg_spend if user_obj else 3000
            
            visit = Visit(
                visit_id=f"V_{uuid.uuid4().hex[:8]}",
                user_id=uid,
                timestamp=timestamp,
                spend=base_spend * random.uniform(0.8, 1.2),
                is_group_visit=True,
                group_id=group_id,
                is_host=(uid == host.user_id)
            )
            visits.append(visit)
            
        return session, visits
