#!/usr/bin/env python3
"""
Test what scores the Odds API is actually returning
"""

import requests
from datetime import datetime

API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"

def test_scores(sport):
    """
    Test scores for a specific sport
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores"
    params = {
        'apiKey': API_KEY,
        'daysFrom': 3  # Get scores from last 3 days
    }
    
    print(f"\n{'='*60}")
    print(f"Testing {sport} scores")
    print('='*60)
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        scores = response.json()
        print(f"Found {len(scores)} games")
        
        # Show completed games
        completed = [g for g in scores if g.get('completed')]
        print(f"Completed games: {len(completed)}")
        
        for game in completed[:10]:  # Show first 10
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Extract scores
            home_score = None
            away_score = None
            
            for score_data in game.get('scores', []):
                if score_data['name'] == home_team:
                    home_score = score_data['score']
                elif score_data['name'] == away_team:
                    away_score = score_data['score']
            
            print(f"\n{away_team} @ {home_team}")
            print(f"  Score: {away_score}-{home_score}")
            print(f"  Game ID: {game['id']}")
            print(f"  Commence time: {game.get('commence_time')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Test NFL
test_scores("americanfootball_nfl")

# Test MLB  
test_scores("baseball_mlb")

print("\n\nNOTE: These are the scores coming from the Odds API.")
print("If these don't match real game results, the API data is wrong/outdated.")
print("We may need to use a different data source for accurate scores.")