from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Transaction:
    transaction_id: str
    timestamp: datetime
    amount: float
    user_id: Optional[str] = None # Can be None for anonymous guests
    session_id: Optional[str] = None # Links multiple transactions in a group visit

@dataclass
class UserProfile:
    user_id: str
    segment: str # Derived from behavior
    avg_spend: float
    frequency: float # Visits per month
    is_loyalty_member: bool = False
    friends: List[str] = field(default_factory=list)
