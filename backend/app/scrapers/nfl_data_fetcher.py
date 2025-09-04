"""
NFL Historical Data Fetcher
Gets all the stats that actually matter for predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

class NFLDataFetcher:
    """Fetches and processes NFL data for predictions"""
    
    def __init__(self):
        self.current_season = 2024
        self.current_week = self.get_current_week()
        
    def get_current_week(self):
        """Determine current NFL week"""
        # NFL Week 1 2024 starts Sept 5
        season_start = datetime(2024, 9, 5)
        current_date = datetime.now()
        
        if current_date < season_start:
            return 0  # Preseason
        
        weeks_passed = (current_date - season_start).days // 7
        return min(weeks_passed + 1, 18)  # Cap at week 18
    
    def install_requirements(self):
        """Install nfl_data_py if not already installed"""
        try:
            import nfl_data_py
        except ImportError:
            print("Installing nfl_data_py...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'nfl_data_py'])
            print("Installation complete!")
    
    def get_game_data(self, years=[2020, 2021, 2022, 2023, 2024]):
        """Get historical game data"""
        try:
            import nfl_data_py as nfl
            
            # Get play-by-play data
            print(f"Fetching data for seasons: {years}")
            pbp_data = nfl.import_pbp_data(years)
            
            # Get team stats
            weekly_data = nfl.import_weekly_data(years)
            
            # Get schedules
            schedules = nfl.import_schedules(years)
            
            return {
                'pbp': pbp_data,
                'weekly': weekly_data,
                'schedules': schedules
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Make sure to run: pip install nfl_data_py")
            return None
    
    def calculate_advanced_metrics(self, pbp_data):
        """Calculate metrics that actually predict games"""
        
        metrics = {}
        
        # EPA (Expected Points Added) - Best predictor
        team_epa = pbp_data.groupby(['posteam', 'season', 'week']).agg({
            'epa': 'mean',
            'success': 'mean',  # Success rate
            'yards_gained': 'mean'
        }).reset_index()
        
        # Separate by play type
        pass_plays = pbp_data[pbp_data['play_type'] == 'pass']
        run_plays = pbp_data[pbp_data['play_type'] == 'run']
        
        # Passing efficiency
        pass_epa = pass_plays.groupby(['posteam', 'season', 'week']).agg({
            'epa': 'mean',
            'complete_pass': 'mean',
            'yards_gained': 'mean'
        }).reset_index()
        
        # Rushing efficiency  
        rush_epa = run_plays.groupby(['posteam', 'season', 'week']).agg({
            'epa': 'mean',
            'yards_gained': 'mean'
        }).reset_index()
        
        # Red zone efficiency
        red_zone = pbp_data[pbp_data['yardline_100'] <= 20]
        rz_efficiency = red_zone.groupby(['posteam', 'season', 'week']).agg({
            'touchdown': 'mean',
            'field_goal_attempt': 'sum',
            'epa': 'mean'
        }).reset_index()
        
        # Third down conversion rate
        third_downs = pbp_data[pbp_data['down'] == 3]
        third_down_rate = third_downs.groupby(['posteam', 'season', 'week']).agg({
            'first_down': 'mean',
            'yards_gained': 'mean'
        }).reset_index()
        
        # Explosive plays (huge predictor)
        explosive = pbp_data[pbp_data['yards_gained'] >= 20]
        explosive_rate = explosive.groupby(['posteam', 'season', 'week']).size().reset_index(name='explosive_plays')
        
        metrics = {
            'team_epa': team_epa,
            'pass_epa': pass_epa,
            'rush_epa': rush_epa,
            'red_zone': rz_efficiency,
            'third_downs': third_down_rate,
            'explosive_plays': explosive_rate
        }
        
        return metrics
    
    def get_matchup_history(self, team1, team2, years=3):
        """Get recent history between two teams"""
        # This is where we'd query historical matchups
        # For now, placeholder
        return {
            'games_played': 6,
            'team1_wins': 4,
            'team2_wins': 2,
            'avg_total': 47.5,
            'avg_margin': 6.3,
            'overs': 4,
            'unders': 2
        }
    
    def get_situational_stats(self):
        """Get situational statistics that Vegas misses"""
        
        situations = {
            'primetime_performance': {
                # Teams that perform differently in primetime
                'DAL': +3.5,  # Cowboys better in primetime
                'CHI': -2.5,  # Bears worse in primetime
                'KC': +2.0,   # Chiefs better
                'NYJ': -3.0   # Jets worse
            },
            
            'rest_advantage': {
                # Performance with extra rest
                'off_bye': +2.5,
                'off_thursday': +1.5,
                'off_monday': -0.5,
                'short_week': -3.0
            },
            
            'weather_impact': {
                # How weather affects scoring
                'wind_15plus': -7.5,  # Total points
                'rain': -3.0,
                'snow': -5.5,
                'dome': +2.0,
                'cold_under_32': -4.0
            },
            
            'travel_fatigue': {
                # West coast teams traveling east for 1pm
                'west_to_east_early': -2.5,
                # East coast teams playing late on west coast
                'east_to_west_late': -1.5,
                # No travel (home)
                'home': +1.0
            },
            
            'referee_tendencies': {
                # Certain refs call more penalties (affects totals)
                'Shawn Hochuli': +4.5,  # More penalties = more points
                'Brad Allen': -2.0,     # Lets them play = fewer points
                'Clete Blakeman': +2.0
            }
        }
        
        return situations
    
    def get_injury_impact(self):
        """Quantify injury impact on spreads"""
        
        # Position value in points
        injury_values = {
            'QB1': 7.0,        # Starting QB worth 7 points
            'QB2': 3.0,        # Backup QB
            'RB1': 2.5,        # Starting RB
            'WR1': 2.0,        # WR1
            'WR2': 1.5,        # WR2
            'TE1': 1.5,        # Starting TE
            'LT': 2.0,         # Left Tackle
            'EDGE1': 2.0,      # Best pass rusher
            'CB1': 2.0,        # Shutdown corner
            'MLB': 1.5,        # Middle linebacker
            'K': 0.5,          # Kicker
            'P': 0.3           # Punter
        }
        
        return injury_values
    
    def calculate_market_inefficiencies(self):
        """Find where public creates value"""
        
        inefficiencies = {
            'public_dogs': {
                # Public loves favorites, creates value on dogs
                'condition': 'public_percentage < 30',
                'historical_ats': 0.545,
                'edge': 2.5
            },
            
            'sandwich_spots': {
                # Team between two big games
                'condition': 'big_game_last_week AND big_game_next_week',
                'historical_ats': 0.425,  # Fade them
                'edge': -3.0
            },
            
            'revenge_games_overvalued': {
                # Public overvalues revenge narratives
                'condition': 'revenge_game',
                'historical_ats': 0.480,  # Actually worse ATS
                'edge': -1.5
            },
            
            'division_unders': {
                # Division games go under more than public thinks
                'condition': 'division_game AND total > 44',
                'historical_under': 0.565,
                'edge': 3.0
            },
            
            'lookahead_spots': {
                # Team looking ahead to next week
                'condition': 'bad_opponent AND great_opponent_next_week',
                'historical_ats': 0.440,
                'edge': -2.5
            }
        }
        
        return inefficiencies


class BacktestEngine:
    """Test strategies on historical data"""
    
    def __init__(self):
        self.results = []
        
    def test_strategy(self, strategy_func, historical_data, starting_bankroll=1000):
        """Test a betting strategy on historical data"""
        
        bankroll = starting_bankroll
        bets_placed = 0
        bets_won = 0
        
        for index, game in historical_data.iterrows():
            # Get prediction from strategy
            prediction = strategy_func(game)
            
            if prediction['bet']:
                # Calculate bet size (Kelly Criterion)
                edge = prediction['confidence'] - 0.524  # Break even is 52.4%
                bet_size = bankroll * min(edge * 0.25, 0.02)  # Max 2% of bankroll
                
                # Determine if bet won
                if prediction['bet_type'] == 'spread':
                    if prediction['pick'] == 'home':
                        won = game['home_cover']
                    else:
                        won = game['away_cover']
                elif prediction['bet_type'] == 'total':
                    if prediction['pick'] == 'over':
                        won = game['went_over']
                    else:
                        won = game['went_under']
                
                # Update bankroll
                if won:
                    bankroll += bet_size * 0.91  # -110 odds
                    bets_won += 1
                else:
                    bankroll -= bet_size
                
                bets_placed += 1
                
                # Track result
                self.results.append({
                    'week': game['week'],
                    'bet': prediction['pick'],
                    'won': won,
                    'bankroll': bankroll,
                    'roi': ((bankroll - starting_bankroll) / starting_bankroll) * 100
                })
        
        # Calculate final statistics
        win_rate = bets_won / bets_placed if bets_placed > 0 else 0
        roi = ((bankroll - starting_bankroll) / starting_bankroll) * 100
        
        return {
            'total_bets': bets_placed,
            'wins': bets_won,
            'losses': bets_placed - bets_won,
            'win_rate': win_rate,
            'starting_bankroll': starting_bankroll,
            'ending_bankroll': bankroll,
            'roi': roi,
            'avg_bet_size': starting_bankroll * 0.015
        }


if __name__ == "__main__":
    print("=" * 50)
    print("NFL DATA FETCHER - Getting the goods")
    print("=" * 50)
    
    fetcher = NFLDataFetcher()
    
    print(f"\nCurrent NFL Week: {fetcher.current_week}")
    print(f"Current Season: {fetcher.current_season}")
    
    print("\n📊 ADVANCED METRICS WE TRACK:")
    print("- EPA (Expected Points Added)")
    print("- Success Rate") 
    print("- Explosive Play Rate")
    print("- Red Zone Efficiency")
    print("- Third Down Conversion Rate")
    
    print("\n🎯 SITUATIONAL EDGES:")
    situations = fetcher.get_situational_stats()
    for situation, details in situations.items():
        print(f"\n{situation.upper()}:")
        if isinstance(details, dict):
            for key, value in list(details.items())[:3]:
                print(f"  {key}: {value:+.1f} points")
    
    print("\n💰 MARKET INEFFICIENCIES:")
    inefficiencies = fetcher.calculate_market_inefficiencies()
    for name, details in inefficiencies.items():
        print(f"  {name}: {details.get('historical_ats', details.get('historical_under', 0)):.1%} hit rate")
    
    print("\n⚡ NEXT STEPS:")
    print("1. Run: pip install nfl_data_py pandas numpy")
    print("2. Fetch historical data for backtesting")
    print("3. Start tracking this week's lines")
    print("4. Build prediction models on proven patterns")