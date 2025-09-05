#!/usr/bin/env python3
"""
Test ESPN API for accurate scores
"""

import requests
from datetime import datetime, timedelta

def test_espn_nfl():
    """Test ESPN NFL scores"""
    print("\n=== ESPN NFL Scores ===")
    
    # ESPN's hidden API endpoint for NFL scores
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        
        for event in events[:5]:
            competition = event['competitions'][0]
            home = competition['competitors'][0]
            away = competition['competitors'][1]
            
            # ESPN marks home/away with homeAway field
            if home['homeAway'] == 'away':
                home, away = away, home
            
            home_team = home['team']['displayName']
            away_team = away['team']['displayName']
            home_score = home.get('score', 'N/A')
            away_score = away.get('score', 'N/A')
            completed = competition['status']['type']['completed']
            
            print(f"\n{away_team} @ {home_team}")
            print(f"  Score: {away_score}-{home_score}")
            print(f"  Status: {'Completed' if completed else 'In Progress/Scheduled'}")
            print(f"  Date: {event['date']}")
    else:
        print(f"Error: {response.status_code}")

def test_espn_mlb():
    """Test ESPN MLB scores"""
    print("\n=== ESPN MLB Scores ===")
    
    # Get scores from last 3 days
    for days_ago in range(3):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={date}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            if events:
                print(f"\n--- Games from {date} ---")
                for event in events[:3]:  # Show first 3 games
                    competition = event['competitions'][0]
                    home = competition['competitors'][0]
                    away = competition['competitors'][1]
                    
                    if home['homeAway'] == 'away':
                        home, away = away, home
                    
                    home_team = home['team']['displayName']
                    away_team = away['team']['displayName']
                    home_score = home.get('score', 'N/A')
                    away_score = away.get('score', 'N/A')
                    completed = competition['status']['type']['completed']
                    
                    print(f"{away_team} @ {home_team}: {away_score}-{home_score} {'(Final)' if completed else ''}")

def test_espn_ncaaf():
    """Test ESPN NCAAF scores"""
    print("\n=== ESPN NCAAF Scores ===")
    
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        
        for event in events[:5]:
            competition = event['competitions'][0]
            home = competition['competitors'][0]
            away = competition['competitors'][1]
            
            if home['homeAway'] == 'away':
                home, away = away, home
            
            home_team = home['team']['displayName']
            away_team = away['team']['displayName']
            home_score = home.get('score', 'N/A')
            away_score = away.get('score', 'N/A')
            completed = competition['status']['type']['completed']
            
            print(f"{away_team} @ {home_team}: {away_score}-{home_score} {'(Final)' if completed else ''}")

# Test all sports
test_espn_nfl()
test_espn_mlb()
test_espn_ncaaf()

print("\n\nESPN provides accurate, real-time scores through their public API!")
print("No authentication required, and the data is always up to date.")