#!/usr/bin/env python3
"""
Check what prop bet markets are available from the Odds API
"""

import requests
import json

API_KEY = "d4fa91883b15fd5a5594c64e58b884ef"

def check_event_props():
    """Check prop markets for specific events/games"""
    
    print("Checking prop markets for specific NFL games...")
    print("=" * 60)
    
    # First get upcoming games
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events"
    params = {'apiKey': API_KEY}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        events = response.json()
        print(f"\nFound {len(events)} upcoming NFL games\n")
        
        # Check first game for available prop markets
        if events:
            event = events[0]
            event_id = event['id']
            print(f"Checking props for: {event['away_team']} @ {event['home_team']}")
            print(f"Event ID: {event_id}\n")
            
            # Try to get odds with player props for this specific event
            odds_url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event_id}/odds"
            
            # List of all possible player prop markets from API docs
            prop_markets = [
                "player_pass_tds",
                "player_pass_yds",
                "player_pass_completions", 
                "player_pass_attempts",
                "player_pass_interceptions",
                "player_rush_yds",
                "player_rush_attempts",
                "player_reception_yds",
                "player_receptions",
                "player_anytime_td"
            ]
            
            for market in prop_markets:
                params = {
                    'apiKey': API_KEY,
                    'regions': 'us',
                    'markets': market,
                    'oddsFormat': 'american'
                }
                
                try:
                    resp = requests.get(odds_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        # Check if any bookmaker has this market
                        has_market = False
                        for bookmaker in data.get('bookmakers', []):
                            for mkt in bookmaker.get('markets', []):
                                if mkt.get('key') == market:
                                    has_market = True
                                    outcomes = mkt.get('outcomes', [])
                                    print(f"  ✅ {market}: AVAILABLE")
                                    print(f"     Bookmaker: {bookmaker['title']}")
                                    if outcomes:
                                        print(f"     Sample props ({len(outcomes)} total):")
                                        for outcome in outcomes[:3]:
                                            print(f"       • {outcome.get('description', outcome.get('name'))}: {outcome.get('point', 'N/A')} at {outcome.get('price', 'N/A')}")
                                    break
                            if has_market:
                                break
                        
                        if not has_market:
                            print(f"  ❌ {market}: Not available")
                            
                except Exception as e:
                    print(f"  ⚠️ {market}: Error checking - {str(e)}")
                    
    else:
        print(f"Error fetching events: {response.status_code}")
        print(response.text)

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

print("\n" + "="*60)
print("CHECKING SPECIFIC EVENT PROPS (Using event endpoint)")
print("="*60 + "\n")
check_event_props()

print("\n" + "="*60)
print("CHECKING GENERAL MARKET AVAILABILITY")
print("="*60 + "\n")
check_available_markets()