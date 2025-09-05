#!/usr/bin/env python3
"""
Verify live scores are being fetched and parsed correctly
"""

import requests
from datetime import datetime

API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"

def test_live_scores():
    """Test all sports for live scores"""
    
    sports = [
        ("americanfootball_nfl", "NFL"),
        ("americanfootball_ncaaf", "NCAAF"),
        ("baseball_mlb", "MLB")
    ]
    
    for sport_key, sport_name in sports:
        print(f"\n{'='*60}")
        print(f"Testing {sport_name} Live Scores")
        print('='*60)
        
        # Fetch odds (which includes upcoming games)
        odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        odds_params = {
            'apiKey': API_KEY,
            'regions': 'us',
            'markets': 'spreads'
        }
        
        odds_response = requests.get(odds_url, params=odds_params)
        
        if odds_response.status_code == 200:
            games = odds_response.json()
            print(f"Found {len(games)} upcoming/live games")
            
            # Now fetch scores
            scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores"
            scores_params = {
                'apiKey': API_KEY,
                'daysFrom': 1
            }
            
            scores_response = requests.get(scores_url, params=scores_params)
            
            if scores_response.status_code == 200:
                scores_data = scores_response.json()
                
                # Find live games (not completed)
                live_count = 0
                for game in scores_data:
                    if not game.get('completed'):
                        live_count += 1
                        home_team = game.get('home_team')
                        away_team = game.get('away_team')
                        
                        # Parse scores correctly
                        home_score = '0'
                        away_score = '0'
                        scores = game.get('scores', [])
                        
                        if scores:
                            for score in scores:
                                if score.get('name') == home_team:
                                    home_score = score.get('score', '0')
                                elif score.get('name') == away_team:
                                    away_score = score.get('score', '0')
                        
                        print(f"\nLIVE: {away_team} @ {home_team}")
                        print(f"  Score: {away_score}-{home_score}")
                        print(f"  Started: {game.get('commence_time')}")
                
                if live_count == 0:
                    print("  No live games at the moment")
                    
                # Show some completed games to verify score parsing
                completed = [g for g in scores_data if g.get('completed')][:3]
                if completed:
                    print(f"\nRecent completed games (verifying score parsing):")
                    for game in completed:
                        home_team = game.get('home_team')
                        away_team = game.get('away_team')
                        
                        # Parse scores
                        home_score = '0'
                        away_score = '0'
                        scores = game.get('scores', [])
                        
                        if scores:
                            for score in scores:
                                if score.get('name') == home_team:
                                    home_score = score.get('score', '0')
                                elif score.get('name') == away_team:
                                    away_score = score.get('score', '0')
                        
                        print(f"  {away_team} @ {home_team}: {away_score}-{home_score} (Final)")
            else:
                print(f"  Error fetching scores: {scores_response.status_code}")
        else:
            print(f"  Error fetching odds: {odds_response.status_code}")

test_live_scores()