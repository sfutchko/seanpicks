#!/usr/bin/env python3
"""
The Odds API Scores Integration
You're already paying for this - let's use it!
"""

import requests
from datetime import datetime, timedelta

class OddsAPIScores:
    """Get live scores from The Odds API"""
    
    def __init__(self, api_key='717b6afb9336e134e3dc2053e31d535f'):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def get_live_and_recent_scores(self, days_from=1):
        """Get scores for recent and live games"""
        
        url = f"{self.base_url}/sports/americanfootball_nfl/scores"
        params = {
            'apiKey': self.api_key,
            'daysFrom': days_from  # Games from last X days
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                games = response.json()
                
                # Check remaining API calls
                remaining = response.headers.get('x-requests-remaining', 'Unknown')
                used = response.headers.get('x-requests-used', 'Unknown')
                print(f"📊 Odds API Usage: {used} used, {remaining} remaining")
                
                return self.parse_scores(games)
            else:
                print(f"Error fetching scores: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def parse_scores(self, games):
        """Parse scores into our format"""
        parsed_games = []
        
        for game in games:
            game_data = {
                'id': game.get('id'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'commence_time': game.get('commence_time'),
                'completed': game.get('completed', False),
                'scores': []
            }
            
            # Parse scores by quarter/period
            if game.get('scores'):
                for score in game['scores']:
                    game_data['scores'].append({
                        'name': score.get('name', ''),
                        'home': score.get('home', 0),
                        'away': score.get('away', 0)
                    })
                
                # Get final or current score
                if game_data['scores']:
                    latest = game_data['scores'][-1]
                    game_data['home_score'] = latest['home']
                    game_data['away_score'] = latest['away']
                    game_data['current_period'] = latest['name']
            
            # Determine if game is live
            if not game_data['completed']:
                # Check if game has started
                start_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                now = datetime.now(start_time.tzinfo)
                
                if now > start_time and len(game_data['scores']) > 0:
                    game_data['is_live'] = True
                else:
                    game_data['is_live'] = False
            else:
                game_data['is_live'] = False
            
            parsed_games.append(game_data)
        
        return parsed_games
    
    def get_game_by_teams(self, home_team, away_team, games=None):
        """Find a specific game by teams"""
        if not games:
            games = self.get_live_and_recent_scores()
        
        for game in games:
            if game['home_team'] == home_team and game['away_team'] == away_team:
                return game
        
        return None

# Test it
if __name__ == "__main__":
    scores_api = OddsAPIScores()
    games = scores_api.get_live_and_recent_scores()
    
    print(f"\n🏈 Found {len(games)} games from The Odds API Scores\n")
    
    for game in games[:5]:
        print(f"{game['away_team']} @ {game['home_team']}")
        if game.get('completed'):
            print(f"  Final: {game.get('away_score', 0)} - {game.get('home_score', 0)}")
        elif game.get('is_live'):
            print(f"  LIVE: {game.get('away_score', 0)} - {game.get('home_score', 0)}")
            print(f"  Period: {game.get('current_period', 'Unknown')}")
        else:
            print(f"  Upcoming: {game['commence_time']}")
        print()