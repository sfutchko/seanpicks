#!/usr/bin/env python3
"""
Fix sport labels for tracked bets
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.bet_tracking import TrackedBet

# Connect to database
engine = create_engine('sqlite:///seanpicks.db')
Session = sessionmaker(bind=engine)
session = Session()

# MLB teams
MLB_TEAMS = [
    'San Francisco Giants', 'Colorado Rockies',
    'Los Angeles Angels', 'Kansas City Royals',
    'Atlanta Braves', 'Chicago Cubs',
    'Philadelphia Phillies', 'Milwaukee Brewers',
    'Toronto Blue Jays', 'Cincinnati Reds',
    'Arizona Diamondbacks', 'San Diego Padres',
    'Miami Marlins', 'Washington Nationals',
    'New York Yankees', 'New York Mets',
    'Boston Red Sox', 'Baltimore Orioles',
    'Tampa Bay Rays', 'Detroit Tigers',
    'Cleveland Guardians', 'Chicago White Sox',
    'Minnesota Twins', 'Houston Astros',
    'Texas Rangers', 'Oakland Athletics',
    'Seattle Mariners', 'Los Angeles Dodgers',
    'St. Louis Cardinals', 'Pittsburgh Pirates'
]

# Get all tracked bets
bets = session.query(TrackedBet).all()

updated = 0
for bet in bets:
    # Check if either team is an MLB team
    if any(team in bet.home_team for team in MLB_TEAMS) or any(team in bet.away_team for team in MLB_TEAMS):
        if bet.sport != 'MLB':
            print(f"Updating {bet.away_team} @ {bet.home_team} from {bet.sport} to MLB")
            bet.sport = 'MLB'
            updated += 1

session.commit()
print(f"\nUpdated {updated} bets to correct sport")

# Show summary by sport
for sport in ['NFL', 'MLB', 'NCAAF']:
    count = session.query(TrackedBet).filter_by(sport=sport).count()
    wins = session.query(TrackedBet).filter_by(sport=sport, result='WIN').count()
    losses = session.query(TrackedBet).filter_by(sport=sport, result='LOSS').count()
    pending = session.query(TrackedBet).filter_by(sport=sport, result='PENDING').count()
    print(f"{sport}: {count} total ({wins}W-{losses}L, {pending} pending)")