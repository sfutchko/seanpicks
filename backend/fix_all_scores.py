#!/usr/bin/env python3
"""
Fix ALL incorrect game scores based on actual results
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.bet_tracking import TrackedBet

# Connect to database
engine = create_engine('sqlite:///seanpicks.db')
Session = sessionmaker(bind=engine)
session = Session()

# ACTUAL game results - these are the real scores
corrections = [
    {
        'away_team': 'Philadelphia Phillies',
        'home_team': 'Milwaukee Brewers',
        'actual_away_score': 2,  # Phillies scored 2
        'actual_home_score': 0,  # Brewers scored 0
        'winner': 'Phillies'
    },
    # Add more corrections as needed
]

print("Fixing game scores based on actual results...\n")

for game in corrections:
    bet = session.query(TrackedBet).filter(
        TrackedBet.away_team == game['away_team'],
        TrackedBet.home_team == game['home_team']
    ).first()
    
    if bet:
        print(f"Found: {bet.away_team} @ {bet.home_team}")
        print(f"  Current DB score: {bet.away_score}-{bet.home_score}")
        print(f"  Actual score: {game['actual_away_score']}-{game['actual_home_score']}")
        print(f"  Pick: {bet.pick}")
        
        # Update score
        bet.away_score = game['actual_away_score']
        bet.home_score = game['actual_home_score']
        bet.actual_spread = game['actual_home_score'] - game['actual_away_score']
        
        # Fix the result based on the pick
        if 'Brewers' in bet.pick:
            # Picked Brewers, but Phillies won 2-0
            bet.result = 'LOSS'
            print(f"  Result: LOSS (picked Brewers, Phillies won)")
        elif 'Phillies' in bet.pick:
            bet.result = 'WIN'
            print(f"  Result: WIN (picked Phillies, Phillies won)")
        
        print(f"  ✅ FIXED\n")

session.commit()

# Now let's check all MLB games and their results
print("\n=== CURRENT DATABASE STATE ===\n")
mlb_bets = session.query(TrackedBet).filter(
    TrackedBet.sport == 'MLB',
    TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
).all()

for bet in mlb_bets:
    status = "✅" if bet.result == "WIN" else "❌" if bet.result == "LOSS" else "➖"
    print(f"{status} {bet.away_team} @ {bet.home_team}")
    print(f"   Score: {bet.away_score}-{bet.home_score}")
    print(f"   Pick: {bet.pick} | Result: {bet.result}")
    print()