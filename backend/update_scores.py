#!/usr/bin/env python3
"""
Script to check and update game scores in the database
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.bet_tracking import TrackedBet, Base
from datetime import datetime

# Connect to database
engine = create_engine('sqlite:///seanpicks.db')
Session = sessionmaker(bind=engine)
session = Session()

# Get all tracked bets with scores
bets = session.query(TrackedBet).filter(
    TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
).all()

print(f"Found {len(bets)} bets with results\n")

# Actual game scores (you can add more as needed)
actual_scores = {
    # NFL games
    ("Dallas Cowboys", "Philadelphia Eagles"): (6, 34),  # Cowboys 6, Eagles 34
    # Add more games as needed
}

for bet in bets:
    print(f"Game: {bet.away_team} @ {bet.home_team}")
    print(f"  Current score: {bet.away_score}-{bet.home_score}")
    print(f"  Sport: {bet.sport}")
    print(f"  Result: {bet.result}")
    print(f"  Game time: {bet.game_time}")
    
    # Check if we have the actual score
    key = (bet.away_team, bet.home_team)
    if key in actual_scores:
        actual_away, actual_home = actual_scores[key]
        if bet.away_score != actual_away or bet.home_score != actual_home:
            print(f"  ⚠️  INCORRECT! Actual score: {actual_away}-{actual_home}")
            # Update the score
            bet.away_score = actual_away
            bet.home_score = actual_home
            bet.actual_spread = actual_home - actual_away
            
            # Recalculate result
            if bet.pick:
                if ' +' in bet.pick or ' -' in bet.pick:
                    parts = bet.pick.rsplit(' ', 1)
                    if len(parts) == 2:
                        pick_team = parts[0]
                        try:
                            pick_spread = float(parts[1])
                        except:
                            pick_spread = bet.spread
                    else:
                        pick_team = bet.pick.split()[0]
                        pick_spread = bet.spread
                    
                    # Determine if bet won
                    actual_spread = actual_home - actual_away
                    if pick_team == bet.home_team or bet.home_team.startswith(pick_team):
                        covered = actual_spread + pick_spread > 0
                    elif pick_team == bet.away_team or bet.away_team.startswith(pick_team):
                        covered = -actual_spread + pick_spread > 0
                    else:
                        covered = False
                    
                    # Update result
                    if abs(actual_spread + pick_spread) < 0.01:
                        bet.result = 'PUSH'
                    elif covered:
                        bet.result = 'WIN'
                    else:
                        bet.result = 'LOSS'
                    
                    print(f"  ✅ Updated to: {actual_away}-{actual_home}, Result: {bet.result}")
    print()

# Commit changes
session.commit()
print("Database updated successfully!")

# Show summary
wins = session.query(TrackedBet).filter_by(result='WIN').count()
losses = session.query(TrackedBet).filter_by(result='LOSS').count()
pushes = session.query(TrackedBet).filter_by(result='PUSH').count()
pending = session.query(TrackedBet).filter_by(result='PENDING').count()

print(f"\nSummary:")
print(f"  Wins: {wins}")
print(f"  Losses: {losses}")
print(f"  Pushes: {pushes}")
print(f"  Pending: {pending}")
print(f"  Total: {wins + losses + pushes + pending}")