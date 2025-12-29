from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GTOQuery(BaseModel):
    """Schema for GTO solver query"""
    position: str  # "BTN", "CO", "MP", "EP", "SB", "BB"
    action: str  # "rfi", "3bet", "4bet", "call_3bet", etc.
    stack_depth: Optional[int] = Field(100, ge=10, le=500)  # in BB
    
    # Postflop (optional)
    board: Optional[str] = None  # e.g., "Ah Kd 7s"
    pot_size: Optional[float] = None
    hero_range: Optional[List[str]] = None  # e.g., ["AA", "KK", "AKs"]


class RangeData(BaseModel):
    """Schema for range visualization data"""
    ranges: Dict[str, float]  # hand -> frequency (0-1)
    # Example: {"AA": 1.0, "KK": 1.0, "AKs": 0.75, "AKo": 0.5}
    total_combos: int
    vpip: float  # Percentage


class GTOResponse(BaseModel):
    """Schema for GTO solver response"""
    query: GTOQuery
    range_data: RangeData
    recommendations: Dict[str, Any]
    # Example: {"suggested_action": "raise", "sizing": [2.5, 3.0], "ev": 0.5}
