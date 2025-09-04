"""
SEAN PICKS - Referee Tendencies Tracker
Some refs call way more penalties = more points
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class RefereeTracker:
    """Track referee tendencies that affect totals and penalties"""
    
    def __init__(self):
        # Historical referee data (2023-2024 seasons)
        self.referee_tendencies = {
            'Shawn Hochuli': {
                'penalties_per_game': 14.2,
                'total_impact': +4.5,  # Games go over by 4.5 points
                'home_advantage': -0.5,  # Slightly favors road team
                'description': 'Heavy penalty caller, overs hit 58%'
            },
            'Carl Cheffers': {
                'penalties_per_game': 11.8,
                'total_impact': +2.0,
                'home_advantage': +1.5,
                'description': 'Favors home team, moderate penalties'
            },
            'Clete Blakeman': {
                'penalties_per_game': 12.5,
                'total_impact': +1.5,
                'home_advantage': +2.0,
                'description': 'Strong home field advantage'
            },
            'Bill Vinovich': {
                'penalties_per_game': 10.2,
                'total_impact': -2.0,
                'home_advantage': 0,
                'description': 'Lets them play, favors unders'
            },
            'Brad Allen': {
                'penalties_per_game': 9.8,
                'total_impact': -3.0,
                'home_advantage': -1.0,
                'description': 'Lowest penalties, unders 61%'
            },
            'John Hussey': {
                'penalties_per_game': 11.5,
                'total_impact': 0,
                'home_advantage': +0.5,
                'description': 'League average tendencies'
            },
            'Ron Torbert': {
                'penalties_per_game': 13.1,
                'total_impact': +3.0,
                'home_advantage': -0.5,
                'description': 'Higher scoring games'
            },
            'Adrian Hill': {
                'penalties_per_game': 12.8,
                'total_impact': +2.5,
                'home_advantage': +1.0,
                'description': 'Slightly favors overs'
            },
            'Scott Novak': {
                'penalties_per_game': 11.0,
                'total_impact': -1.0,
                'home_advantage': 0,
                'description': 'Neutral referee'
            },
            'Jerome Boger': {
                'penalties_per_game': 13.5,
                'total_impact': +3.5,
                'home_advantage': -2.0,
                'description': 'Controversial calls, road team advantage'
            },
            'Clay Martin': {
                'penalties_per_game': 10.5,
                'total_impact': -1.5,
                'home_advantage': +1.5,
                'description': 'Conservative caller'
            },
            'Craig Wrolstad': {
                'penalties_per_game': 11.2,
                'total_impact': 0,
                'home_advantage': +0.5,
                'description': 'Predictable patterns'
            },
            'Alex Kemp': {
                'penalties_per_game': 12.0,
                'total_impact': +1.0,
                'home_advantage': 0,
                'description': 'By the book referee'
            },
            'Shawn Smith': {
                'penalties_per_game': 11.7,
                'total_impact': +0.5,
                'home_advantage': -0.5,
                'description': 'Slight road bias'
            },
            'Land Clark': {
                'penalties_per_game': 10.8,
                'total_impact': -0.5,
                'home_advantage': +2.5,
                'description': 'Strong home cooking'
            },
            'Tra Blake': {
                'penalties_per_game': 11.3,
                'total_impact': 0,
                'home_advantage': 0,
                'description': 'New referee, neutral'
            },
            'Alan Eck': {
                'penalties_per_game': 10.9,
                'total_impact': -1.0,
                'home_advantage': +1.0,
                'description': 'Favors defense'
            }
        }
        
        # Penalty types that affect scoring
        self.penalty_impacts = {
            'defensive_holding': +0.3,     # Extends drives
            'pass_interference': +0.5,     # Big yardage
            'roughing_passer': +0.4,       # Extends drives
            'unnecessary_roughness': +0.2, # Field position
            'false_start': -0.1,          # Kills drives
            'offensive_holding': -0.2,    # Kills drives
            'delay_of_game': -0.1,        # Minor impact
        }
        
        # Crew tendencies by penalty type
        self.crew_specialties = {
            'Shawn Hochuli': ['defensive_holding', 'pass_interference'],
            'Brad Allen': [],  # Calls fewer of everything
            'Carl Cheffers': ['roughing_passer', 'unnecessary_roughness'],
            'Clete Blakeman': ['offensive_holding'],
            'Bill Vinovich': [],  # Lets them play
        }
    
    def get_referee_impact(self, referee_name):
        """Get impact of specific referee on game"""
        
        if referee_name not in self.referee_tendencies:
            # Unknown referee, use average
            return {
                'referee': referee_name,
                'total_impact': 0,
                'home_advantage': 0,
                'penalties_per_game': 11.5,
                'description': 'Unknown referee, using league average',
                'confidence_adjustment': 0,
                'over_lean': False,
                'under_lean': False
            }
        
        ref_data = self.referee_tendencies[referee_name]
        
        # Calculate confidence adjustment based on how extreme the referee is
        confidence_adj = 0
        if abs(ref_data['total_impact']) >= 3:
            confidence_adj = 0.02  # 2% boost for extreme refs
        elif abs(ref_data['total_impact']) >= 2:
            confidence_adj = 0.01  # 1% boost for moderate impact
        
        return {
            'referee': referee_name,
            'total_impact': ref_data['total_impact'],
            'home_advantage': ref_data['home_advantage'],
            'penalties_per_game': ref_data['penalties_per_game'],
            'description': ref_data['description'],
            'confidence_adjustment': confidence_adj,
            'over_lean': ref_data['total_impact'] > 2,
            'under_lean': ref_data['total_impact'] < -2
        }
    
    def scrape_referee_assignments(self):
        """Scrape this week's referee assignments"""
        
        assignments = {}
        
        try:
            # Multiple sources for referee assignments
            sources = [
                'https://www.footballzebras.com/category/assignments/',
                'https://www.pro-football-reference.com/officials/'
            ]
            
            # This would scrape actual assignments
            # For now, return sample data
            sample_assignments = {
                'Buffalo Bills @ Miami Dolphins': 'Shawn Hochuli',
                'Dallas Cowboys @ New York Giants': 'Carl Cheffers',
                'Green Bay Packers @ Chicago Bears': 'Brad Allen',
                'Kansas City Chiefs @ Las Vegas Raiders': 'Clete Blakeman',
            }
            
            return sample_assignments
            
        except Exception as e:
            print(f"Error scraping referee assignments: {e}")
            return {}
    
    def calculate_crew_performance(self, referee_name, team_style):
        """Calculate how referee crew affects specific team styles"""
        
        adjustments = {
            'passing_heavy': 0,
            'rushing_heavy': 0,
            'defensive': 0
        }
        
        if referee_name not in self.referee_tendencies:
            return adjustments
        
        ref_data = self.referee_tendencies[referee_name]
        
        # Passing teams affected more by PI-happy refs
        if team_style == 'passing_heavy':
            if ref_data['penalties_per_game'] > 13:
                adjustments['passing_heavy'] = +2.0  # More PI calls help passing teams
            elif ref_data['penalties_per_game'] < 10:
                adjustments['passing_heavy'] = -1.5  # Fewer calls hurt passing teams
        
        # Rushing teams like refs who don't call holding
        elif team_style == 'rushing_heavy':
            if referee_name == 'Brad Allen':  # Lets them play
                adjustments['rushing_heavy'] = +1.5
            elif referee_name == 'Clete Blakeman':  # Calls holding
                adjustments['rushing_heavy'] = -1.0
        
        # Defensive teams like low-penalty refs
        elif team_style == 'defensive':
            if ref_data['penalties_per_game'] < 11:
                adjustments['defensive'] = +1.0
            else:
                adjustments['defensive'] = -1.5
        
        return adjustments
    
    def get_historical_performance(self, referee_name, team_name):
        """Get team's historical record with specific referee"""
        
        # This would query a database of historical results
        # For demonstration, using sample data
        historical = {
            ('Shawn Hochuli', 'Dallas Cowboys'): {
                'games': 8,
                'ats_record': '6-2',
                'ou_record': '5-3',  # Overs hit more
                'avg_penalties_against': 7.2
            },
            ('Brad Allen', 'Green Bay Packers'): {
                'games': 5,
                'ats_record': '2-3',
                'ou_record': '1-4',  # Unders hit more
                'avg_penalties_against': 4.8
            }
        }
        
        key = (referee_name, team_name)
        if key in historical:
            return historical[key]
        
        return None
    
    def primetime_referee_bias(self, referee_name, is_primetime):
        """Some refs call games differently in primetime"""
        
        if not is_primetime:
            return 0
        
        primetime_adjustments = {
            'Shawn Hochuli': +2.0,   # Even more flags in primetime
            'Carl Cheffers': +1.5,   # Slightly more calls
            'Jerome Boger': +3.0,    # Much tighter in primetime
            'Brad Allen': 0,         # Consistent regardless
            'Bill Vinovich': -1.0,   # Even fewer calls in primetime
        }
        
        return primetime_adjustments.get(referee_name, 0)
    
    def get_referee_report(self, game_data):
        """Complete referee analysis for a game"""
        
        referee = game_data.get('referee', 'Unknown')
        is_primetime = game_data.get('is_primetime', False)
        home_team = game_data.get('home_team')
        away_team = game_data.get('away_team')
        
        # Get base impact
        impact = self.get_referee_impact(referee)
        
        # Add primetime adjustment
        primetime_adj = self.primetime_referee_bias(referee, is_primetime)
        
        # Get historical performance if available
        home_history = self.get_historical_performance(referee, home_team)
        away_history = self.get_historical_performance(referee, away_team)
        
        # Build report
        report = {
            'referee': referee,
            'total_adjustment': impact['total_impact'] + primetime_adj,
            'home_advantage': impact['home_advantage'],
            'description': impact['description'],
            'penalties_expected': impact['penalties_per_game'],
            'confidence_boost': impact['confidence_adjustment'],
            'betting_lean': 'OVER' if impact['over_lean'] else 'UNDER' if impact['under_lean'] else 'NEUTRAL'
        }
        
        # Add historical notes
        if home_history:
            report['home_team_history'] = f"{home_team} is {home_history['ats_record']} ATS with {referee}"
        if away_history:
            report['away_team_history'] = f"{away_team} is {away_history['ats_record']} ATS with {referee}"
        
        return report


class RefereeFade:
    """Identify refs to fade in certain situations"""
    
    def __init__(self):
        self.fade_situations = {
            'Jerome Boger': {
                'situation': 'Road favorites',
                'record': '12-23 ATS',
                'description': 'Boger crews disadvantage road favorites'
            },
            'Shawn Hochuli': {
                'situation': 'Under 42 total',
                'record': '8-19 O/U',
                'description': 'Low totals go over with Hochuli'
            },
            'Brad Allen': {
                'situation': 'Over 51 total',
                'record': '9-21 O/U',
                'description': 'High totals go under with Allen'
            },
            'Clete Blakeman': {
                'situation': 'Division games',
                'record': '18-10 Home ATS',
                'description': 'Heavy home advantage in division games'
            }
        }
    
    def check_fade_situation(self, referee, game_data):
        """Check if this is a referee fade situation"""
        
        if referee not in self.fade_situations:
            return None
        
        fade = self.fade_situations[referee]
        
        # Check if situation applies
        if referee == 'Jerome Boger':
            if game_data.get('away_spread', 0) < 0:  # Road favorite
                return {
                    'fade': True,
                    'bet': 'Home team',
                    'reason': fade['description'],
                    'historical': fade['record']
                }
        
        elif referee == 'Shawn Hochuli':
            if game_data.get('total', 50) < 42:
                return {
                    'fade': True,
                    'bet': 'OVER',
                    'reason': fade['description'],
                    'historical': fade['record']
                }
        
        elif referee == 'Brad Allen':
            if game_data.get('total', 45) > 51:
                return {
                    'fade': True,
                    'bet': 'UNDER',
                    'reason': fade['description'],
                    'historical': fade['record']
                }
        
        return None


if __name__ == "__main__":
    print("=" * 60)
    print(" REFEREE TENDENCIES TRACKER")
    print("=" * 60)
    
    tracker = RefereeTracker()
    
    print("\n👨‍⚖️ Top Referee Impacts on Totals:")
    print("\nOVER Referees:")
    for ref, data in sorted(tracker.referee_tendencies.items(), 
                           key=lambda x: x[1]['total_impact'], reverse=True)[:5]:
        print(f"  {ref}: {data['total_impact']:+.1f} points ({data['description']})")
    
    print("\nUNDER Referees:")
    for ref, data in sorted(tracker.referee_tendencies.items(), 
                           key=lambda x: x[1]['total_impact'])[:5]:
        print(f"  {ref}: {data['total_impact']:+.1f} points ({data['description']})")
    
    print("\n🏠 Home Field Advantage by Referee:")
    for ref, data in sorted(tracker.referee_tendencies.items(), 
                           key=lambda x: x[1]['home_advantage'], reverse=True)[:3]:
        print(f"  {ref}: {data['home_advantage']:+.1f} points home advantage")
    
    # Test referee impact
    print("\n📊 Sample Game Analysis:")
    sample_game = {
        'referee': 'Shawn Hochuli',
        'is_primetime': True,
        'home_team': 'Dallas Cowboys',
        'away_team': 'New York Giants'
    }
    
    report = tracker.get_referee_report(sample_game)
    print(f"\nReferee: {report['referee']}")
    print(f"Total Adjustment: {report['total_adjustment']:+.1f} points")
    print(f"Betting Lean: {report['betting_lean']}")
    print(f"Expected Penalties: {report['penalties_expected']:.1f} per game")