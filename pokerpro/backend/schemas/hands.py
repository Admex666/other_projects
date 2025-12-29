from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HandImport(BaseModel):
    """Schema for hand history import"""
    raw_hand_text: str
    site: Optional[str] = None  # Auto-detect if not provided


class LeakDetection(BaseModel):
    """Schema for detected leak"""
    street: str  # "preflop", "flop", "turn", "river"
    action: str
    leak_type: str  # "overfolding", "overcalling", "sizing_error", etc.
    ev_loss: float  # in BB
    explanation: str


class HandAnalysisResponse(BaseModel):
    """Schema for hand analysis result"""
    hand_id: str
    overall_score: float = Field(..., ge=0, le=100)
    ev_loss: float
    leaks: List[LeakDetection]
    gto_comparison: Dict[str, Any]
    recommendations: str
    analyzed_at: datetime
    
    class Config:
        from_attributes = True
