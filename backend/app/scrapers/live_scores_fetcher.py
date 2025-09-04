"""
SEAN PICKS - Live Scores Fetcher
Fetches real-time game scores and situations for live betting
"""

import requests
from datetime import datetime, timedelta
import json
import time

class LiveScoresFetcher:
    """Fetch live scores from ESPN API (no key required)"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football"
        self.cache = {}
        self.cache_duration = 30  # 30 seconds cache for live data
        
    def fetch_nfl_live_scores(self):
        """Fetch live NFL game scores"""
        url = f"{self.base_url}/nfl/scoreboard"
        
        # Check cache
        cache_key = "nfl_live"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                games = self.parse_espn_games(data, 'NFL')
                
                # Cache the result
                self.cache[cache_key] = (games, time.time())
                return games
            else:
                print(f"ESPN API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching NFL scores: {e}")
            return []
    
    def fetch_ncaaf_live_scores(self):
        """Fetch live NCAAF game scores"""
        url = f"{self.base_url}/college-football/scoreboard"
        
        # Check cache
        cache_key = "ncaaf_live"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                games = self.parse_espn_games(data, 'NCAAF')
                
                # Cache the result
                self.cache[cache_key] = (games, time.time())
                return games
            else:
                print(f"ESPN API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching NCAAF scores: {e}")
            return []
    
    def parse_espn_games(self, data, league):
        """Parse ESPN API response into game data"""
        games = []
        
        if 'events' not in data:
            return games
        
        for event in data['events']:
            competition = event['competitions'][0]
            
            # Get teams
            home_team = None
            away_team = None
            for competitor in competition['competitors']:
                if competitor['homeAway'] == 'home':
                    home_team = competitor
                else:
                    away_team = competitor
            
            if not home_team or not away_team:
                continue
            
            # Get game status
            status = competition['status']
            is_live = status['type']['state'] == 'in'
            is_final = status['type']['completed']
            
            if not is_live:  # Only process live games
                continue
            
            # Get scores
            home_score = int(home_team.get('score', 0))
            away_score = int(away_team.get('score', 0))
            
            # Get game situation
            quarter = status['period']
            clock = status['displayClock']
            
            # Calculate time elapsed percentage
            time_elapsed_pct = self.calculate_time_elapsed(quarter, clock)
            
            # Get betting lines if available
            odds_data = {}
            if 'odds' in competition:
                for odds in competition['odds']:
                    if 'spread' in odds:
                        odds_data['spread'] = odds['spread']
                    if 'overUnder' in odds:
                        odds_data['total'] = odds['overUnder']
            
            # Get recent scoring
            scoring_plays = self.get_recent_scoring(event)
            
            game_data = {
                'league': league,
                'home_team': home_team['team']['displayName'],
                'away_team': away_team['team']['displayName'],
                'home_score': home_score,
                'away_score': away_score,
                'current_total': home_score + away_score,
                'quarter': quarter,
                'clock': clock,
                'time_elapsed_pct': time_elapsed_pct,
                'is_live': is_live,
                'is_final': is_final,
                'pregame_spread': odds_data.get('spread', 0),
                'pregame_total': odds_data.get('total', 48),
                'scoring_plays': scoring_plays,
                'momentum_team': self.detect_momentum(scoring_plays),
                'last_score_time': self.get_last_score_time(scoring_plays),
                'red_zone': self.check_red_zone(event),
                'timeouts': self.get_timeouts(home_team, away_team)
            }
            
            # Calculate derived metrics
            game_data['underdog'] = home_team['team']['displayName'] if odds_data.get('spread', 0) > 0 else away_team['team']['displayName']
            game_data['favorite'] = away_team['team']['displayName'] if odds_data.get('spread', 0) > 0 else home_team['team']['displayName']
            game_data['live_spread'] = abs(home_score - away_score)
            game_data['team_leading'] = home_team['team']['displayName'] if home_score > away_score else away_team['team']['displayName']
            game_data['team_trailing'] = away_team['team']['displayName'] if home_score > away_score else home_team['team']['displayName']
            
            # Quarter-specific flags
            game_data['fourth_quarter'] = (quarter == 4)
            game_data['two_minute_warning'] = (quarter in [2, 4] and self.parse_clock_minutes(clock) <= 2)
            game_data['halftime'] = (quarter == 2 and clock == "0:00")
            
            # Calculate half scores for halftime betting
            if quarter >= 3:
                game_data['first_half_total'] = self.estimate_half_total(game_data)
            
            games.append(game_data)
        
        return games
    
    def calculate_time_elapsed(self, quarter, clock):
        """Calculate percentage of game time elapsed"""
        # NFL/NCAAF: 4 quarters, 15 minutes each = 60 minutes total
        minutes_per_quarter = 15
        total_minutes = 60
        
        # Calculate minutes elapsed
        quarters_complete = max(0, quarter - 1)
        minutes_elapsed = quarters_complete * minutes_per_quarter
        
        # Add minutes from current quarter
        if quarter <= 4:
            clock_minutes = self.parse_clock_minutes(clock)
            minutes_in_current = minutes_per_quarter - clock_minutes
            minutes_elapsed += minutes_in_current
        
        # Calculate percentage
        return min(1.0, minutes_elapsed / total_minutes)
    
    def parse_clock_minutes(self, clock):
        """Parse clock string to minutes"""
        if not clock or clock == "0:00":
            return 0
        
        try:
            parts = clock.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + (seconds / 60)
            return 0
        except:
            return 0
    
    def get_recent_scoring(self, event):
        """Extract recent scoring plays"""
        scoring_plays = []
        
        # This would parse play-by-play if available
        # For now, return empty list
        return scoring_plays
    
    def detect_momentum(self, scoring_plays):
        """Detect which team has momentum based on recent scoring"""
        # Look for consecutive scores by same team
        if len(scoring_plays) >= 2:
            last_two = scoring_plays[-2:]
            if last_two[0]['team'] == last_two[1]['team']:
                return last_two[0]['team']
        return None
    
    def get_last_score_time(self, scoring_plays):
        """Get time since last score"""
        if scoring_plays:
            return scoring_plays[-1].get('time_ago', 0)
        return 999  # Large number if no recent score
    
    def check_red_zone(self, event):
        """Check if team is in red zone"""
        # Would need play-by-play data for accurate red zone detection
        # This is a placeholder
        return False
    
    def get_timeouts(self, home_team, away_team):
        """Get remaining timeouts for each team"""
        return {
            'home': home_team.get('timeouts', 3),
            'away': away_team.get('timeouts', 3)
        }
    
    def estimate_half_total(self, game_data):
        """Estimate first half total based on current score and time"""
        if game_data['quarter'] == 3 and game_data['clock'] == "15:00":
            # Start of second half, use halftime score
            return game_data['current_total']
        elif game_data['quarter'] >= 3:
            # Estimate based on scoring pace
            # This is a rough estimate
            return int(game_data['current_total'] * 0.48)  # First half typically 48% of total
        return 0
    
    def get_all_live_games(self):
        """Get all live games from both NFL and NCAAF"""
        all_games = []
        
        # Fetch NFL games
        nfl_games = self.fetch_nfl_live_scores()
        all_games.extend(nfl_games)
        
        # Fetch NCAAF games
        ncaaf_games = self.fetch_ncaaf_live_scores()
        all_games.extend(ncaaf_games)
        
        return all_games
    
    def format_for_betting_tracker(self, games):
        """Format games for the live betting tracker"""
        formatted = []
        
        for game in games:
            # Add additional fields needed by betting tracker
            game['half_score'] = game['current_total'] if game['quarter'] == 3 else None
            game['expected_half_total'] = game['pregame_total'] * 0.48
            
            # Check for scoring drought
            game['minutes_without_score'] = game.get('last_score_time', 0)
            
            # Add injury flags (would need real injury data)
            game['qb_injury'] = False
            game['injured_team'] = None
            
            # Count red zone failures (placeholder)
            game['red_zone_failures'] = 0
            
            # Track consecutive scores
            game['consecutive_scores'] = 0
            game['unanswered_points'] = 0
            
            formatted.append(game)
        
        return formatted


if __name__ == "__main__":
    fetcher = LiveScoresFetcher()
    
    print("Fetching live games...")
    games = fetcher.get_all_live_games()
    
    if games:
        print(f"\nFound {len(games)} live games:")
        for game in games:
            print(f"\n{game['away_team']} @ {game['home_team']}")
            print(f"  Score: {game['away_score']} - {game['home_score']}")
            print(f"  Quarter: {game['quarter']} - {game['clock']}")
            print(f"  Total: {game['current_total']} (O/U {game['pregame_total']})")
    else:
        print("\nNo live games currently")