#!/usr/bin/env python3
"""
Debug the Odds API scores to understand the data structure
"""

import requests
import json
from datetime import datetime

API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"

def debug_odds_api():
    """
    Carefully examine the Odds API response
    """
    
    # Test with MLB first
    sport = "baseball_mlb"
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores"
    params = {
        'apiKey': API_KEY,
        'daysFrom': 3
    }
    
    print("Fetching MLB scores from Odds API...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("="*60)
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        scores = response.json()
        
        # Look for specific games we know the results of
        print("\nSearching for known games...")
        
        # Known results:
        # Angels @ Royals: 3-4 (Royals won)
        # Phillies @ Brewers: 2-0 (Phillies won)
        
        for game in scores:
            home = game.get('home_team')
            away = game.get('away_team')
            
            # Look for Angels @ Royals
            if 'Angels' in away and 'Royals' in home:
                print(f"\nFound Angels @ Royals game:")
                print(json.dumps(game, indent=2))
                
                # Check the scores array
                print("\nScores array:")
                for score in game.get('scores', []):
                    print(f"  {score['name']}: {score['score']}")
                
            # Look for Phillies @ Brewers  
            if 'Phillies' in away and 'Brewers' in home:
                print(f"\nFound Phillies @ Brewers game:")
                print(json.dumps(game, indent=2))
                
                print("\nScores array:")
                for score in game.get('scores', []):
                    print(f"  {score['name']}: {score['score']}")
    
    # Now test NFL
    print("\n" + "="*60)
    print("\nTesting NFL scores...")
    
    sport = "americanfootball_nfl"
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores"
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        scores = response.json()
        
        # Look for Cowboys @ Eagles (actual: 6-34)
        for game in scores:
            home = game.get('home_team')
            away = game.get('away_team')
            
            if 'Cowboys' in away and 'Eagles' in home:
                print(f"\nFound Cowboys @ Eagles game:")
                print(json.dumps(game, indent=2))
                
                print("\nScores array:")
                for score in game.get('scores', []):
                    print(f"  {score['name']}: {score['score']}")
                    
                print("\nActual result should be: Cowboys 6, Eagles 34")
                print("API is showing: Cowboys 20, Eagles 24 - WRONG!")

debug_odds_api()