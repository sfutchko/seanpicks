#!/usr/bin/env python3
"""
Update ALL game scores with the correct verified results
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.bet_tracking import TrackedBet

# Connect to database
engine = create_engine('sqlite:///seanpicks.db')
Session = sessionmaker(bind=engine)
session = Session()

# VERIFIED CORRECT game results from user
corrections = [
    {
        'away_team': 'Dallas Cowboys',
        'home_team': 'Philadelphia Eagles',
        'actual_away_score': 6,
        'actual_home_score': 34,
        'pick_team': 'Eagles',
        'expected_result': 'LOSS'  # Eagles covered -8.4
    },
    {
        'away_team': 'San Francisco Giants',
        'home_team': 'Colorado Rockies',
        'actual_away_score': 7,
        'actual_home_score': 4,
        'pick_team': 'Giants',
        'expected_result': 'WIN'
    },
    {
        'away_team': 'Los Angeles Angels',
        'home_team': 'Kansas City Royals',
        'actual_away_score': 3,  # Angels scored 3
        'actual_home_score': 4,  # Royals scored 4 (Royals won 4-3)
        'pick_team': 'Royals',
        'expected_result': 'WIN'
    },
    {
        'away_team': 'Atlanta Braves',
        'home_team': 'Chicago Cubs',
        'actual_away_score': 5,  # Braves scored 5
        'actual_home_score': 1,  # Cubs scored 1 (Braves won 5-1)
        'pick_team': 'Cubs',
        'expected_result': 'LOSS'
    },
    {
        'away_team': 'Philadelphia Phillies',
        'home_team': 'Milwaukee Brewers',
        'actual_away_score': 2,  # Phillies scored 2
        'actual_home_score': 0,  # Brewers scored 0 (Phillies won 2-0)
        'pick_team': 'Brewers',
        'expected_result': 'LOSS'
    },
    {
        'away_team': 'Toronto Blue Jays',
        'home_team': 'Cincinnati Reds',
        'actual_away_score': 12,
        'actual_home_score': 9,
        'pick_team': 'Blue Jays',
        'expected_result': 'WIN'
    }
]

print("Updating all game scores with verified correct results...\n")
print("=" * 60)

for game in corrections:
    bet = session.query(TrackedBet).filter(
        TrackedBet.away_team == game['away_team'],
        TrackedBet.home_team == game['home_team']
    ).first()
    
    if bet:
        print(f"\n{game['away_team']} @ {game['home_team']}")
        print(f"  Old score: {bet.away_score}-{bet.home_score} ({bet.result})")
        print(f"  New score: {game['actual_away_score']}-{game['actual_home_score']}")
        
        # Update score
        bet.away_score = game['actual_away_score']
        bet.home_score = game['actual_home_score']
        bet.actual_spread = game['actual_home_score'] - game['actual_away_score']
        
        # Update result
        bet.result = game['expected_result']
        
        print(f"  Pick: {bet.pick}")
        print(f"  Result: {bet.result}")
        print(f"  ✅ UPDATED")

session.commit()

print("\n" + "=" * 60)
print("\n=== FINAL DATABASE STATE ===\n")

# Show NFL games
print("🏈 NFL Games:")
nfl_bets = session.query(TrackedBet).filter(
    TrackedBet.sport == 'NFL',
    TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
).all()

for bet in nfl_bets:
    status = "✅" if bet.result == "WIN" else "❌"
    print(f"{status} {bet.away_team} @ {bet.home_team}: {bet.away_score}-{bet.home_score} | {bet.pick} | {bet.result}")

# Show MLB games
print("\n⚾ MLB Games:")
mlb_bets = session.query(TrackedBet).filter(
    TrackedBet.sport == 'MLB',
    TrackedBet.result.in_(['WIN', 'LOSS', 'PUSH'])
).all()

for bet in mlb_bets:
    status = "✅" if bet.result == "WIN" else "❌"
    print(f"{status} {bet.away_team} @ {bet.home_team}: {bet.away_score}-{bet.home_score} | {bet.pick} | {bet.result}")

# Show updated performance
print("\n" + "=" * 60)
print("\n=== UPDATED PERFORMANCE ===\n")

for sport in ['ALL', 'NFL', 'MLB']:
    if sport == 'ALL':
        bets = session.query(TrackedBet).filter(
            TrackedBet.result.in_(['WIN', 'LOSS'])
        ).all()
    else:
        bets = session.query(TrackedBet).filter(
            TrackedBet.sport == sport,
            TrackedBet.result.in_(['WIN', 'LOSS'])
        ).all()
    
    wins = sum(1 for b in bets if b.result == 'WIN')
    losses = sum(1 for b in bets if b.result == 'LOSS')
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    print(f"{sport}: {wins}-{losses} ({win_rate:.1f}% win rate)")