#!/usr/bin/env python3
"""
Check what prop bet markets are available from the Odds API
"""

import requests
import json

API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"

def check_available_markets():
    """Check all available betting markets for each sport"""
    
    sports = [
        "americanfootball_nfl",
        "americanfootball_ncaaf",
        "baseball_mlb"
    ]
    
    print("Checking available prop markets from the Odds API...\n")
    print("=" * 60)
    
    for sport in sports:
        print(f"\n📊 {sport.upper()}")
        print("-" * 40)
        
        # First, let's try to fetch with player props
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        
        # Try common player prop markets
        prop_markets = [
            "player_pass_tds",
            "player_pass_yds", 
            "player_rush_yds",
            "player_reception_yds",
            "player_receptions",
            "player_points",
            "player_rebounds",
            "player_assists",
            "batter_home_runs",
            "batter_hits",
            "batter_total_bases",
            "pitcher_strikeouts"
        ]
        
        for market in prop_markets:
            params = {
                'apiKey': API_KEY,
                'regions': 'us',
                'markets': market,
                'oddsFormat': 'american'
            }
            
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if any games have this market
                    games_with_market = 0
                    for game in data:
                        if game.get('bookmakers'):
                            for bookmaker in game['bookmakers']:
                                if bookmaker.get('markets'):
                                    for mkt in bookmaker['markets']:
                                        if mkt.get('key') == market:
                                            games_with_market += 1
                                            break
                    
                    if games_with_market > 0:
                        print(f"  ✅ {market}: Available ({games_with_market} games)")
                        
                        # Show a sample
                        for game in data[:1]:  # Just first game
                            if game.get('bookmakers'):
                                for bookmaker in game['bookmakers'][:1]:  # Just first book
                                    if bookmaker.get('markets'):
                                        for mkt in bookmaker['markets']:
                                            if mkt.get('key') == market and mkt.get('outcomes'):
                                                print(f"     Sample: {game['away_team']} @ {game['home_team']}")
                                                for outcome in mkt['outcomes'][:3]:  # First 3 props
                                                    print(f"       • {outcome.get('description', outcome.get('name'))}: {outcome.get('point')} at {outcome.get('price')}")
                                                break
                    
            except Exception as e:
                pass  # Skip if market not available
        
        # Also check what markets are in regular odds call
        params = {
            'apiKey': API_KEY,
            'regions': 'us',
            'oddsFormat': 'american'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"\n  Default markets available:")
                markets_found = set()
                for game in data[:5]:  # Check first 5 games
                    if game.get('bookmakers'):
                        for bookmaker in game['bookmakers']:
                            if bookmaker.get('markets'):
                                for market in bookmaker['markets']:
                                    markets_found.add(market.get('key'))
                
                for market in markets_found:
                    print(f"    • {market}")

check_available_markets()