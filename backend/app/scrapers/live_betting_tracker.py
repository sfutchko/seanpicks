"""
SEAN PICKS - Live Betting Opportunities Tracker
Identifies profitable in-game betting opportunities
"""

import requests
from datetime import datetime, timedelta
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import ODDS_API_KEY

class LiveBettingTracker:
    """Track live games for betting opportunities"""
    
    def __init__(self):
        self.api_key = ODDS_API_KEY
        
        # Live betting patterns that work
        self.live_patterns = {
            'halftime_under': {
                'description': 'Take under at halftime if total pace < expected',
                'confidence': 0.57,
                'conditions': lambda game: game['half_score'] < game['expected_half_total'] * 0.85
            },
            'fourth_quarter_dog': {
                'description': 'Take dog +10+ in 4th quarter',
                'confidence': 0.56,
                'conditions': lambda game: game['quarter'] == 4 and game['live_spread'] >= 10
            },
            'momentum_shift': {
                'description': 'Bet team that just scored 10+ unanswered',
                'confidence': 0.55,
                'conditions': lambda game: game.get('unanswered_points', 0) >= 10
            },
            'injury_adjustment': {
                'description': 'Bet against team that just lost QB',
                'confidence': 0.60,
                'conditions': lambda game: game.get('qb_injury', False)
            },
            'blowout_prevention': {
                'description': 'Take points on team down 21+ (backdoor cover)',
                'confidence': 0.54,
                'conditions': lambda game: game['live_spread'] >= 21
            },
            'scoring_drought': {
                'description': 'Bet over after 10+ min scoring drought',
                'confidence': 0.55,
                'conditions': lambda game: game.get('minutes_without_score', 0) >= 10
            },
            'red_zone_failure': {
                'description': 'Fade team after 3+ red zone failures',
                'confidence': 0.56,
                'conditions': lambda game: game.get('red_zone_failures', 0) >= 3
            }
        }
        
        # Quarter-specific strategies
        self.quarter_strategies = {
            1: {
                'slow_start_over': 'If Q1 total < 7, bet over (teams wake up)',
                'fast_start_under': 'If Q1 total > 21, bet under (regression)',
            },
            2: {
                'two_minute_drill': 'Bet over in last 2 min of half',
                'defensive_struggle': 'If half total < 17, bet under',
            },
            3: {
                'adjustment_period': 'Wait 5 min for coaching adjustments',
                'momentum_bet': 'Bet team that gets ball first if tied',
            },
            4: {
                'garbage_time': 'Take dog if down 14+ (backdoor)',
                'clock_management': 'Under if winning team up 7-10',
            }
        }
        
        # Live prop opportunities
        self.prop_patterns = {
            'quarterback': {
                'passing_yards': {
                    'trailing_team': +25,  # QB throws more when behind
                    'bad_weather': -40,    # Weather impact on passing
                    'injured_wr': -30,      # Missing top target
                },
                'passing_tds': {
                    'red_zone_trips': +0.3,  # Per RZ trip
                    'goal_line': +0.5,       # Inside 5 yard line
                }
            },
            'running_back': {
                'rushing_yards': {
                    'leading_team': +20,    # Teams run when ahead
                    'fourth_quarter': +15,   # Clock killing
                    'bad_weather': +10,      # More rushing in weather
                }
            },
            'anytime_td': {
                'red_zone_back': 0.35,    # RB in red zone
                'slot_receiver': 0.25,    # Slot WR in red zone
                'tight_end': 0.20,        # TE red zone target
            }
        }

    def fetch_live_games(self):
        """Fetch currently live games"""
        
        url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds-live"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'spreads,totals',
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching live games: {e}")
            return []
    
    def analyze_game_flow(self, game_data):
        """Analyze how the game is flowing vs expectations"""
        
        analysis = {
            'pace': 'normal',
            'scoring_trend': 'expected',
            'momentum': 'neutral',
            'key_factors': []
        }
        
        # This would connect to live score feed
        # For demo, using sample analysis
        current_total = game_data.get('current_total', 0)
        expected_total = game_data.get('pregame_total', 48)
        time_elapsed = game_data.get('time_elapsed_pct', 0.5)
        
        expected_current = expected_total * time_elapsed
        
        # Pace analysis
        if current_total < expected_current * 0.85:
            analysis['pace'] = 'slow'
            analysis['scoring_trend'] = 'under'
            analysis['key_factors'].append('Game trending under')
        elif current_total > expected_current * 1.15:
            analysis['pace'] = 'fast'
            analysis['scoring_trend'] = 'over'
            analysis['key_factors'].append('Game trending over')
        
        # Check for momentum shifts
        last_score = game_data.get('last_scoring_team')
        consecutive_scores = game_data.get('consecutive_scores', 0)
        
        if consecutive_scores >= 2:
            analysis['momentum'] = last_score
            analysis['key_factors'].append(f'{last_score} has momentum')
        
        return analysis
    
    def find_live_edges(self, game_data):
        """Find edges in live games"""
        
        edges = []
        
        # Check each pattern
        for pattern_name, pattern in self.live_patterns.items():
            if pattern['conditions'](game_data):
                edges.append({
                    'type': pattern_name,
                    'description': pattern['description'],
                    'confidence': pattern['confidence'],
                    'bet': self.determine_live_bet(pattern_name, game_data)
                })
        
        # Quarter-specific opportunities
        current_quarter = game_data.get('quarter', 1)
        if current_quarter in self.quarter_strategies:
            quarter_strats = self.quarter_strategies[current_quarter]
            
            # Check quarter-specific conditions
            if current_quarter == 1 and game_data.get('q1_total', 0) < 7:
                edges.append({
                    'type': 'slow_start',
                    'description': quarter_strats['slow_start_over'],
                    'confidence': 0.55,
                    'bet': f"OVER {game_data.get('live_total', 45)}"
                })
        
        return edges
    
    def determine_live_bet(self, pattern_type, game_data):
        """Determine specific bet based on pattern"""
        
        bets = {
            'halftime_under': f"UNDER {game_data.get('live_total', 45)}",
            'fourth_quarter_dog': f"{game_data.get('underdog')} +{game_data.get('live_spread', 10)}",
            'momentum_shift': f"{game_data.get('momentum_team')} ML",
            'injury_adjustment': f"Fade {game_data.get('injured_team')}",
            'blowout_prevention': f"{game_data.get('underdog')} +{game_data.get('live_spread', 21)}",
            'scoring_drought': f"OVER {game_data.get('live_total', 45)}",
            'red_zone_failure': f"Fade {game_data.get('failing_team')}"
        }
        
        return bets.get(pattern_type, "Check live lines")
    
    def calculate_live_props(self, player_data, game_situation):
        """Calculate adjusted player props based on game flow"""
        
        adjustments = {}
        position = player_data.get('position')
        
        if position == 'QB':
            base_yards = player_data.get('projected_yards', 250)
            
            # Adjust for game situation
            if game_situation.get('team_trailing'):
                base_yards += self.prop_patterns['quarterback']['passing_yards']['trailing_team']
            
            if game_situation.get('bad_weather'):
                base_yards += self.prop_patterns['quarterback']['passing_yards']['bad_weather']
            
            adjustments['passing_yards'] = {
                'original': player_data.get('line_yards', 250),
                'adjusted': base_yards,
                'edge': base_yards - player_data.get('line_yards', 250),
                'confidence': 0.54 if abs(base_yards - player_data.get('line_yards', 250)) > 20 else 0.50
            }
        
        elif position == 'RB':
            base_yards = player_data.get('projected_yards', 60)
            
            if game_situation.get('team_leading'):
                base_yards += self.prop_patterns['running_back']['rushing_yards']['leading_team']
            
            if game_situation.get('fourth_quarter'):
                base_yards += self.prop_patterns['running_back']['rushing_yards']['fourth_quarter']
            
            adjustments['rushing_yards'] = {
                'original': player_data.get('line_yards', 60),
                'adjusted': base_yards,
                'edge': base_yards - player_data.get('line_yards', 60),
                'confidence': 0.55 if base_yards - player_data.get('line_yards', 60) > 15 else 0.50
            }
        
        # Anytime TD scorer
        if game_situation.get('red_zone'):
            td_prob = self.prop_patterns['anytime_td'].get(player_data.get('role', 'other'), 0.15)
            adjustments['anytime_td'] = {
                'probability': td_prob,
                'odds_needed': int(100 / td_prob) - 100,  # Convert to American odds
                'confidence': 0.56 if td_prob > 0.25 else 0.52
            }
        
        return adjustments
    
    def second_half_strategies(self, first_half_data):
        """Strategies specific to second half betting"""
        
        strategies = []
        
        # Total points adjustments
        first_half_total = first_half_data.get('total_points', 0)
        pregame_total = first_half_data.get('pregame_total', 48)
        
        # Second half typically scores more
        expected_2h = pregame_total * 0.52  # 52% of scoring in 2nd half historically
        
        if first_half_total < pregame_total * 0.40:
            strategies.append({
                'bet': 'Second Half OVER',
                'reasoning': 'Low scoring 1st half, expect regression',
                'confidence': 0.56,
                'line': expected_2h
            })
        elif first_half_total > pregame_total * 0.60:
            strategies.append({
                'bet': 'Second Half UNDER',
                'reasoning': 'High scoring 1st half, expect regression',
                'confidence': 0.55,
                'line': expected_2h
            })
        
        # Team totals
        if first_half_data.get('home_points', 0) == 0:
            strategies.append({
                'bet': 'Home Team 2H Over',
                'reasoning': 'Home team shut out in 1st half rarely happens twice',
                'confidence': 0.58,
                'line': first_half_data.get('home_2h_total', 14)
            })
        
        # Coaching adjustments
        if abs(first_half_data.get('home_points', 0) - first_half_data.get('away_points', 0)) <= 3:
            strategies.append({
                'bet': 'Take the points',
                'reasoning': 'Close game, take dog in 2nd half',
                'confidence': 0.54,
                'line': first_half_data.get('2h_spread', 3)
            })
        
        return strategies
    
    def monitor_live_opportunities(self):
        """Main function to monitor live betting opportunities"""
        
        print("=" * 60)
        print(" LIVE BETTING MONITOR")
        print("=" * 60)
        
        # Get live games
        live_games = self.fetch_live_games()
        
        if not live_games:
            print("\n📺 No live games currently")
            return []
        
        opportunities = []
        
        for game in live_games:
            print(f"\n🏈 {game.get('away_team')} @ {game.get('home_team')}")
            
            # Create game data (would come from live feed)
            game_data = {
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'quarter': 2,  # Sample data
                'current_total': 24,
                'pregame_total': 48,
                'time_elapsed_pct': 0.5,
                'live_spread': 7,
                'live_total': 45,
                'half_score': 24,
                'expected_half_total': 24,
                'underdog': game.get('away_team'),
                'momentum_team': game.get('home_team')
            }
            
            # Analyze game flow
            flow = self.analyze_game_flow(game_data)
            print(f"  Pace: {flow['pace']}")
            print(f"  Trend: {flow['scoring_trend']}")
            
            # Find edges
            edges = self.find_live_edges(game_data)
            
            if edges:
                print("  💰 OPPORTUNITIES FOUND:")
                for edge in edges:
                    print(f"    • {edge['description']}")
                    print(f"      Bet: {edge['bet']}")
                    print(f"      Confidence: {edge['confidence']:.1%}")
                    
                    opportunities.append({
                        'game': f"{game_data['away_team']} @ {game_data['home_team']}",
                        'type': edge['type'],
                        'bet': edge['bet'],
                        'confidence': edge['confidence'],
                        'quarter': game_data['quarter']
                    })
        
        return opportunities


class LiveAlerts:
    """Send alerts for time-sensitive opportunities"""
    
    def __init__(self):
        self.alert_thresholds = {
            'confidence': 0.56,  # Min confidence for alert
            'edge': 5,           # Min edge in points/percentage
            'time_sensitive': ['two_minute_drill', 'red_zone', 'injury']
        }
    
    def should_alert(self, opportunity):
        """Determine if opportunity warrants an alert"""
        
        # High confidence
        if opportunity.get('confidence', 0) >= self.alert_thresholds['confidence']:
            return True
        
        # Time sensitive
        if opportunity.get('type') in self.alert_thresholds['time_sensitive']:
            return True
        
        # Large edge
        if opportunity.get('edge', 0) >= self.alert_thresholds['edge']:
            return True
        
        return False
    
    def format_alert(self, opportunity):
        """Format alert message"""
        
        alert = {
            'priority': 'HIGH' if opportunity['confidence'] >= 0.58 else 'MEDIUM',
            'message': f"🚨 LIVE BET ALERT: {opportunity['game']}",
            'bet': opportunity['bet'],
            'confidence': f"{opportunity['confidence']:.1%}",
            'action': 'BET NOW - Time sensitive',
            'timestamp': datetime.now().isoformat()
        }
        
        return alert


if __name__ == "__main__":
    tracker = LiveBettingTracker()
    alerts = LiveAlerts()
    
    print("\n🔴 LIVE BETTING OPPORTUNITIES\n")
    
    # Monitor for opportunities
    opportunities = tracker.monitor_live_opportunities()
    
    if opportunities:
        print("\n" + "=" * 60)
        print(" 💰 SUMMARY OF LIVE OPPORTUNITIES")
        print("=" * 60)
        
        for opp in opportunities:
            if alerts.should_alert(opp):
                alert = alerts.format_alert(opp)
                print(f"\n{alert['priority']} PRIORITY:")
                print(f"{alert['message']}")
                print(f"BET: {alert['bet']}")
                print(f"Confidence: {alert['confidence']}")
    else:
        print("\n✅ No live betting opportunities at this time")
    
    print("\n💡 Live Betting Tips:")
    print("1. Watch for momentum shifts after turnovers")
    print("2. Halftime lines often have value")
    print("3. Weather changes affect live totals")
    print("4. Injury news moves lines slowly")
    print("5. Take dogs late in blowouts (backdoor covers)")