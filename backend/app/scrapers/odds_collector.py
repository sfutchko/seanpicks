"""
SEAN PICKS - Odds Collection System
This gets us real-time odds from multiple sources
"""

import requests
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List
import time

class OddsCollector:
    """Collects odds from multiple sources"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Free sources (scraping needed)
        self.free_sources = {
            'covers': 'https://www.covers.com/sports/nfl/matchups',
            'espn': 'https://www.espn.com/nfl/lines',
            'vegas_insider': 'https://www.vegasinsider.com/nfl/odds/'
        }
        
        # Sportsbooks to track
        self.books = [
            'draftkings',
            'fanduel', 
            'betmgm',
            'pointsbet',
            'caesars'
        ]
        
    def get_current_week_games(self):
        """Get this week's NFL games with odds"""
        
        if self.api_key:
            # Use The Odds API (most reliable)
            endpoint = f"{self.base_url}/sports/americanfootball_nfl/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'spreads,totals,h2h',
                'oddsFormat': 'american',
                'bookmakers': ','.join(self.books)
            }
            
            response = requests.get(endpoint, params=params)
            
            if response.status_code == 200:
                return self.parse_odds_api_response(response.json())
            else:
                print(f"API Error: {response.status_code}")
                return None
        else:
            # Fallback to scraping
            return self.scrape_free_odds()
    
    def parse_odds_api_response(self, data):
        """Parse API response into usable format"""
        
        games = []
        
        for game in data:
            game_info = {
                'game_id': game['id'],
                'commence_time': game['commence_time'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'odds': {}
            }
            
            # Parse each bookmaker's odds
            for bookmaker in game.get('bookmakers', []):
                book_name = bookmaker['key']
                
                for market in bookmaker['markets']:
                    market_type = market['key']
                    
                    if market_type == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                game_info['odds'][f'{book_name}_home_spread'] = outcome['point']
                                game_info['odds'][f'{book_name}_home_spread_odds'] = outcome['price']
                            else:
                                game_info['odds'][f'{book_name}_away_spread'] = outcome['point']
                                game_info['odds'][f'{book_name}_away_spread_odds'] = outcome['price']
                    
                    elif market_type == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over':
                                game_info['odds'][f'{book_name}_total'] = outcome['point']
                                game_info['odds'][f'{book_name}_over_odds'] = outcome['price']
                            else:
                                game_info['odds'][f'{book_name}_under_odds'] = outcome['price']
                    
                    elif market_type == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                game_info['odds'][f'{book_name}_home_ml'] = outcome['price']
                            else:
                                game_info['odds'][f'{book_name}_away_ml'] = outcome['price']
            
            games.append(game_info)
        
        return games
    
    def find_arbitrage_opportunities(self, games):
        """Find arbitrage betting opportunities across books"""
        
        arb_opportunities = []
        
        for game in games:
            odds = game['odds']
            
            # Check for middle opportunities on spreads
            spreads = {}
            for book in self.books:
                home_spread_key = f'{book}_home_spread'
                if home_spread_key in odds:
                    spreads[book] = odds[home_spread_key]
            
            if spreads:
                max_spread = max(spreads.values())
                min_spread = min(spreads.values())
                
                if max_spread - min_spread >= 1.5:  # 1.5 point middle
                    arb_opportunities.append({
                        'type': 'spread_middle',
                        'game': f"{game['away_team']} @ {game['home_team']}",
                        'opportunity': f"Buy {max_spread} and {min_spread}",
                        'books': [k for k, v in spreads.items() if v in [max_spread, min_spread]]
                    })
            
            # Check for total middles
            totals = {}
            for book in self.books:
                total_key = f'{book}_total'
                if total_key in odds:
                    totals[book] = odds[total_key]
            
            if totals:
                max_total = max(totals.values())
                min_total = min(totals.values())
                
                if max_total - min_total >= 1.5:  # 1.5 point middle
                    arb_opportunities.append({
                        'type': 'total_middle',
                        'game': f"{game['away_team']} @ {game['home_team']}",
                        'opportunity': f"Over {min_total} / Under {max_total}",
                        'books': [k for k, v in totals.items() if v in [max_total, min_total]]
                    })
        
        return arb_opportunities
    
    def get_line_movement(self, game_id):
        """Track how lines have moved since open"""
        # This would query our database of historical odds
        # For now, returning placeholder
        return {
            'opening_spread': -3.5,
            'current_spread': -2.5,
            'movement': 1.0,
            'direction': 'away_team',
            'sharp_side': 'away'  # Side sharp money is on
        }
    
    def calculate_expected_value(self, predicted_prob, odds):
        """Calculate EV of a bet"""
        # Convert American odds to decimal
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
        
        # EV = (Probability of Winning * Amount Won) - (Probability of Losing * Amount Lost)
        ev = (predicted_prob * (decimal_odds - 1)) - ((1 - predicted_prob) * 1)
        
        return ev
    
    def scrape_free_odds(self):
        """Fallback scraping method"""
        print("Note: API key not provided. Would scrape from free sources.")
        # Implement BeautifulSoup scraping here
        return []


class PatternMatcher:
    """Identifies profitable betting patterns"""
    
    def __init__(self):
        self.patterns = {
            'thursday_under': {
                'description': 'Thursday night game unders',
                'hit_rate': 0.58,
                'conditions': lambda g: g['day'] == 'Thursday'
            },
            'division_dog': {
                'description': 'Division underdog +7 to +10',
                'hit_rate': 0.56,
                'conditions': lambda g: g['is_division'] and 7 <= g['spread'] <= 10
            },
            'windy_under': {
                'description': 'Wind > 15mph = under',
                'hit_rate': 0.61,
                'conditions': lambda g: g.get('wind_speed', 0) > 15
            },
            'backup_qb_under': {
                'description': 'Backup QB starting = under team total',
                'hit_rate': 0.59,
                'conditions': lambda g: g.get('backup_qb', False)
            },
            'public_fade': {
                'description': 'Fade when 80%+ public on one side',
                'hit_rate': 0.55,
                'conditions': lambda g: g.get('public_percentage', 50) >= 80
            }
        }
    
    def find_matching_patterns(self, game_data):
        """Find which patterns match this game"""
        matches = []
        
        for pattern_name, pattern in self.patterns.items():
            if pattern['conditions'](game_data):
                matches.append({
                    'pattern': pattern_name,
                    'description': pattern['description'],
                    'historical_hit_rate': pattern['hit_rate']
                })
        
        return matches
    
    def calculate_confidence(self, matches):
        """Calculate overall confidence based on pattern matches"""
        if not matches:
            return 0.5  # No edge
        
        # Average hit rates of matching patterns
        avg_hit_rate = sum(m['historical_hit_rate'] for m in matches) / len(matches)
        
        # Boost confidence if multiple patterns align
        if len(matches) >= 3:
            avg_hit_rate += 0.03
        elif len(matches) >= 2:
            avg_hit_rate += 0.01
        
        return min(avg_hit_rate, 0.65)  # Cap at 65% confidence


if __name__ == "__main__":
    print("=" * 50)
    print("SEAN PICKS - NFL Odds Collector")
    print("=" * 50)
    
    # Initialize without API key for now
    collector = OddsCollector()
    
    print("\n1. Sign up for The Odds API (free):")
    print("   https://the-odds-api.com")
    print("\n2. Add your API key to this script")
    print("\n3. Current sportsbooks tracked:")
    for book in collector.books:
        print(f"   - {book}")
    
    print("\n4. Available pattern matching:")
    matcher = PatternMatcher()
    for name, pattern in matcher.patterns.items():
        print(f"   - {pattern['description']}: {pattern['hit_rate']*100:.0f}% historical")
    
    print("\n5. Next step: Create config file with your API keys")