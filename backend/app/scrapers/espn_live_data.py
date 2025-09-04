#!/usr/bin/env python3
"""
ESPN Live Data Integration - FREE real-time NFL data
No API key required!
"""

import requests
import json
from datetime import datetime
import pytz

class ESPNLiveData:
    """Get free live NFL data from ESPN's hidden API"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_current_scores(self):
        """Get all current NFL games with live scores"""
        url = f"{self.base_url}/scoreboard"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return self.parse_games(data)
            else:
                print(f"ESPN API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching ESPN data: {e}")
            return []
    
    def parse_games(self, data):
        """Parse ESPN data into our format"""
        games = []
        
        for event in data.get('events', []):
            game = self.parse_single_game(event)
            if game:
                games.append(game)
        
        return games
    
    def parse_single_game(self, event):
        """Parse a single game from ESPN format"""
        try:
            competition = event['competitions'][0]
            
            # Teams (ESPN lists home team first in competitors)
            home_team_data = competition['competitors'][0]
            away_team_data = competition['competitors'][1]
            
            # Make sure we have the right home/away
            if home_team_data['homeAway'] != 'home':
                home_team_data, away_team_data = away_team_data, home_team_data
            
            # Game status
            status = event['status']
            
            game_data = {
                'game_id': event['id'],
                'home_team': home_team_data['team']['displayName'],
                'away_team': away_team_data['team']['displayName'],
                'home_team_abbr': home_team_data['team']['abbreviation'],
                'away_team_abbr': away_team_data['team']['abbreviation'],
                'status': status['type']['name'],
                'status_detail': status['type']['description'],
                'is_live': status['type']['state'] == 'in',
                'is_final': status['type']['completed'],
                'start_time': event.get('date', ''),
                'venue': competition.get('venue', {}).get('fullName', ''),
                
                # Scores
                'home_score': int(home_team_data.get('score', 0)),
                'away_score': int(away_team_data.get('score', 0)),
                
                # Game situation (for live games)
                'quarter': status.get('period', 0),
                'time_remaining': status.get('displayClock', ''),
                'possession': None,
                'red_zone': False,
                'down_distance': None,
                
                # Betting relevant info
                'home_timeouts': home_team_data.get('timeouts', 3),
                'away_timeouts': away_team_data.get('timeouts', 3),
                
                # Records
                'home_record': home_team_data.get('records', [{}])[0].get('summary', ''),
                'away_record': away_team_data.get('records', [{}])[0].get('summary', ''),
            }
            
            # Get possession for live games
            if game_data['is_live']:
                situation = competition.get('situation', {})
                if situation:
                    game_data['possession'] = situation.get('possession')
                    game_data['red_zone'] = situation.get('isRedZone', False)
                    
                    # Down and distance
                    if situation.get('downDistanceText'):
                        game_data['down_distance'] = situation['downDistanceText']
                    
                    # Field position
                    game_data['field_position'] = situation.get('possessionText', '')
            
            # Get live betting opportunities
            if game_data['is_live']:
                game_data['live_betting_angles'] = self.analyze_live_angles(game_data)
            
            return game_data
            
        except Exception as e:
            print(f"Error parsing game: {e}")
            return None
    
    def analyze_live_angles(self, game):
        """Identify live betting opportunities"""
        angles = []
        
        # Halftime under opportunity
        if game['quarter'] == 2 and game['time_remaining'] == '0:00':
            total_score = game['home_score'] + game['away_score']
            if total_score < 20:  # Low scoring first half
                angles.append({
                    'type': 'halftime_under',
                    'description': 'Low scoring first half - consider 2H under',
                    'confidence': 0.57
                })
        
        # Fourth quarter dog
        if game['quarter'] == 4:
            score_diff = abs(game['home_score'] - game['away_score'])
            if score_diff >= 10:
                trailing_team = game['away_team'] if game['home_score'] > game['away_score'] else game['home_team']
                angles.append({
                    'type': 'fourth_quarter_dog',
                    'description': f'{trailing_team} +{score_diff} (backdoor cover)',
                    'confidence': 0.56
                })
        
        # Red zone failure pattern
        if game.get('red_zone'):
            angles.append({
                'type': 'red_zone',
                'description': 'Team in red zone - watch for FG vs TD',
                'confidence': 0.54
            })
        
        # Two minute drill
        if game['quarter'] in [2, 4]:
            time_parts = game['time_remaining'].split(':')
            if len(time_parts) == 2:
                minutes = int(time_parts[0])
                if minutes <= 2:
                    angles.append({
                        'type': 'two_minute_drill',
                        'description': 'Two minute situation - pace picks up',
                        'confidence': 0.55
                    })
        
        return angles
    
    def get_game_details(self, game_id):
        """Get detailed stats for a specific game"""
        url = f"{self.base_url}/summary"
        params = {'event': game_id}
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_team_injuries(self, team_abbr):
        """Get injury report for a team"""
        # ESPN has injury data in their team pages
        # This would need more complex scraping
        # For now, return placeholder
        return []

# Test function
if __name__ == "__main__":
    espn = ESPNLiveData()
    games = espn.get_current_scores()
    
    print(f"\n🏈 Found {len(games)} NFL games from ESPN\n")
    
    for game in games[:3]:
        print(f"{game['away_team']} @ {game['home_team']}")
        print(f"  Status: {game['status_detail']}")
        if game['is_live']:
            print(f"  Score: {game['away_score']} - {game['home_score']}")
            print(f"  Quarter {game['quarter']}, {game['time_remaining']}")
            if game.get('live_betting_angles'):
                print(f"  Live Angles: {len(game['live_betting_angles'])} opportunities")
        print()