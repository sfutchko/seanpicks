"""
User model for authentication and preferences
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database.connection import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Betting information
    bankroll = Column(Float, default=1000.0)
    unit_size = Column(Float, default=20.0)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Preferences (stored as JSON)
    preferences = Column(JSON, default={
        "notifications": {
            "sharp_moves": True,
            "line_changes": True,
            "live_opportunities": True
        },
        "default_sport": "nfl",
        "kelly_multiplier": 0.25,
        "max_parlay_size": 3
    })
    
    def __repr__(self):
        return f"<User {self.username}>"