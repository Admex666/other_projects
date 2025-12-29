from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class HandHistory(Base):
    __tablename__ = "hand_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Hand metadata
    hand_id = Column(String, unique=True, nullable=False)  # External hand ID
    site = Column(String, nullable=True)  # e.g., "PokerStars", "GGPoker"
    game_type = Column(String, nullable=False)  # e.g., "NLH", "PLO"
    stakes = Column(String, nullable=False)  # e.g., "NL10", "NL50"
    
    # Hand data
    raw_hand_text = Column(Text, nullable=False)  # Original hand history
    parsed_data = Column(JSON, nullable=True)  # Parsed hand structure
    
    # Results
    hero_position = Column(String, nullable=True)
    hero_cards = Column(String, nullable=True)
    board = Column(String, nullable=True)
    pot_size = Column(Float, nullable=True)
    hero_won = Column(Float, nullable=True)  # Amount won/lost
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="hand_histories")
    analysis = relationship("HandAnalysis", back_populates="hand", uselist=False)


class HandAnalysis(Base):
    __tablename__ = "hand_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hand_histories.id"), unique=True, nullable=False)
    
    # Analysis results
    overall_score = Column(Float, nullable=True)  # 0-100
    ev_loss = Column(Float, nullable=True)  # Estimated EV loss in BB
    
    # Detected leaks (JSON array of leak objects)
    leaks = Column(JSON, nullable=True)
    # Example: [{"street": "flop", "action": "call", "leak_type": "overcalling", "ev_loss": 0.5}]
    
    # GTO comparison
    gto_comparison = Column(JSON, nullable=True)
    # Example: {"preflop": {"action": "raise", "gto_action": "fold", "ev_diff": -0.3}}
    
    # Recommendations
    recommendations = Column(Text, nullable=True)
    
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hand = relationship("HandHistory", back_populates="analysis")
