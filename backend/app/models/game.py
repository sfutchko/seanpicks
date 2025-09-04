"""
Game model for storing game information and analysis
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base
from datetime import datetime
import uuid

class Game(Base):
    __tablename__ = "games"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), unique=True, index=True)  # From Odds API
    
    # Game info
    sport = Column(String(10), nullable=False, index=True)  # 'nfl' or 'ncaaf'
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    game_time = Column(DateTime, nullable=False, index=True)
    
    # Current lines
    spread = Column(Float)
    total = Column(Float)
    home_ml = Column(Integer)
    away_ml = Column(Integer)
    
    # Analysis results
    confidence = Column(Float)
    edge = Column(Float)
    best_bet = Column(String(200))
    pick = Column(String(200))
    
    # Detailed analysis (JSON)
    analysis = Column(JSON, default={})
    sharp_action = Column(JSON, default={})
    public_betting = Column(JSON, default={})
    weather_data = Column(JSON, default={})
    injury_data = Column(JSON, default={})
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Game {self.away_team} @ {self.home_team}>"