#!/usr/bin/env python3
"""
Models for tracking best bets and their performance
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TrackedBet(Base):
    """
    Store each bet that appears in best bets
    """
    __tablename__ = "tracked_bets"
    
    id = Column(String, primary_key=True)  # game_id + timestamp
    game_id = Column(String, nullable=False)
    
    # Game info
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    game_time = Column(DateTime, nullable=False)
    
    # Bet details
    pick = Column(String, nullable=False)  # "Cowboys -7.5"
    spread = Column(Float, nullable=False)
    odds = Column(Integer, default=-110)
    confidence = Column(Float, nullable=False)
    kelly_bet = Column(Float)
    edge = Column(Float)
    
    # Tracking info
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    times_appeared = Column(Integer, default=1)
    
    # Best line info at time of tracking
    best_book = Column(String)
    best_spread = Column(Float)
    best_odds = Column(Integer)
    
    # Result
    result = Column(String)  # WIN, LOSS, PUSH, PENDING
    home_score = Column(Integer)
    away_score = Column(Integer)
    actual_spread = Column(Float)
    
    # Metadata
    patterns = Column(JSON)  # Store detected patterns
    public_percentage = Column(Float)
    sharp_action = Column(Boolean)
    weather = Column(JSON)


class BetSnapshot(Base):
    """
    Daily snapshots of best bets for historical tracking
    """
    __tablename__ = "bet_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    sport = Column(String, default="NFL")
    
    # Store the full best bets list at this moment
    best_bets = Column(JSON)  # List of bet details
    total_bets = Column(Integer)
    avg_confidence = Column(Float)
    
    # Performance at time of snapshot
    pending_count = Column(Integer)
    win_count = Column(Integer)
    loss_count = Column(Integer)
    push_count = Column(Integer)
    

class BetPerformance(Base):
    """
    Track overall performance metrics
    """
    __tablename__ = "bet_performance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow)
    sport = Column(String, default="NFL")
    
    # Daily performance
    daily_wins = Column(Integer, default=0)
    daily_losses = Column(Integer, default=0)
    daily_pushes = Column(Integer, default=0)
    daily_units = Column(Float, default=0.0)
    daily_roi = Column(Float, default=0.0)
    
    # Running totals
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_pushes = Column(Integer, default=0)
    total_units = Column(Float, default=0.0)
    total_roi = Column(Float, default=0.0)
    
    # By confidence level
    high_conf_record = Column(JSON)  # {"W": 10, "L": 2, "P": 1}
    medium_conf_record = Column(JSON)
    low_conf_record = Column(JSON)