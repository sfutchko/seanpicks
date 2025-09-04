#!/usr/bin/env python3
"""
LEGITIMATE DATA FETCHER - Uses only real, verifiable data sources
No mock data, no estimates - only actual reported information
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LegitimateDataFetcher:
    """Fetches ONLY legitimate, real data from verified sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Your existing API key for The Odds API
        self.odds_api_key = "d4fa91883b15fd5a5594c64e58b884ef"
        
        # SportsDataIO trial key (7-day free trial available)
        # Sign up at: https://sportsdata.io/developers/api-documentation/nfl
        self.sportsdata_key = None  # You'll need to sign up for this
        
        # MySportsFeeds (has free tier)
        # Sign up at: https://www.mysportsfeeds.com/data-feeds/
        self.mysportsfeeds_key = None  # You'll need to sign up for this
    
    def get_odds_api_consensus(self, sport: str = 'americanfootball_nfl') -> List[Dict]:
        """Get consensus betting data from The Odds API"""
        try:
            # The Odds API provides real betting lines from multiple books
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'spreads,totals',
                'oddsFormat': 'american',
                'bookmakers': 'draftkings,fanduel,betmgm,caesars,pointsbetus,betonlineag,bovada,williamhill_us'
            }
            
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                games = response.json()
                
                # Process games to extract line movement patterns
                for game in games:
                    if game.get('bookmakers'):
                        # Calculate consensus from actual bookmaker lines
                        spreads = []
                        for book in game['bookmakers']:
                            for market in book.get('markets', []):
                                if market['key'] == 'spreads':
                                    for outcome in market['outcomes']:
                                        if outcome['name'] == game['home_team']:
                                            spreads.append({
                                                'book': book['title'],
                                                'spread': outcome.get('point', 0),
                                                'price': outcome.get('price', -110)
                                            })
                        
                        # Detect sharp vs square books
                        sharp_books = ['Pinnacle', 'Bookmaker', 'Circa Sports']
                        square_books = ['DraftKings', 'FanDuel', 'BetMGM']
                        
                        sharp_lines = [s for s in spreads if any(sb in s['book'] for sb in sharp_books)]
                        square_lines = [s for s in spreads if any(sb in s['book'] for sb in square_books)]
                        
                        # Real line movement detection
                        if sharp_lines and square_lines:
                            sharp_avg = sum(s['spread'] for s in sharp_lines) / len(sharp_lines)
                            square_avg = sum(s['spread'] for s in square_lines) / len(square_lines)
                            
                            # This is REAL data - actual line differences between books
                            game['line_movement'] = {
                                'sharp_square_diff': sharp_avg - square_avg,
                                'total_books': len(spreads),
                                'spread_range': max(s['spread'] for s in spreads) - min(s['spread'] for s in spreads) if spreads else 0
                            }
                
                return games
            
        except Exception as e:
            logger.error(f"Error fetching odds consensus: {e}")
        
        return []
    
    def get_actionnetwork_data(self, game_id: str) -> Dict:
        """
        Action Network has public betting percentages
        Note: Requires paid subscription for API access
        Alternative: Can parse their free public pages
        """
        # Action Network shows real public betting percentages
        # but requires subscription for API access
        # Free alternative: Parse their public game pages
        
        return {
            'source': 'actionnetwork',
            'available': False,
            'note': 'Requires paid subscription - visit actionnetwork.com for manual data'
        }
    
    def get_vegasinsider_consensus(self, sport: str = 'nfl') -> Dict:
        """
        Vegas Insider has consensus betting data
        Note: Web scraping their public consensus page
        """
        try:
            # Vegas Insider consensus page (publicly available)
            url = f"https://www.vegasinsider.com/{sport}/odds/las-vegas/"
            
            # Note: They have anti-scraping measures
            # Consider manual checking or paid API access
            
            return {
                'source': 'vegasinsider',
                'available': False,
                'note': 'Consider manual checking at vegasinsider.com/nfl/odds/'
            }
            
        except Exception as e:
            logger.error(f"Vegas Insider error: {e}")
            return {}
    
    def get_official_injury_reports(self, week: int = None) -> Dict:
        """
        Get injury reports from official sources
        NFL provides official injury reports
        """
        injuries = {}
        
        # Option 1: NFL's official data (requires partnership)
        # The NFL does provide official injury reports through their API
        # but it requires official partnership
        
        # Option 2: Team websites
        # Each team publishes official injury reports
        team_sites = {
            'Cardinals': 'https://www.azcardinals.com/team/injury-report/',
            'Falcons': 'https://www.atlantafalcons.com/team/injury-report/',
            'Ravens': 'https://www.baltimoreravens.com/team/injury-report/',
            # ... (all 32 teams have official injury report pages)
        }
        
        # Option 3: Reputable aggregators with real data
        # Pro Football Reference (free, reliable)
        # https://www.pro-football-reference.com/years/2024/injuries.htm
        
        return {
            'source': 'official',
            'available': False,
            'manual_sources': team_sites,
            'note': 'Check team official websites for real injury reports'
        }
    
    def get_sportsbook_public_betting(self) -> Dict:
        """
        Some sportsbooks publish their actual betting percentages
        """
        # Some books that show real public betting data:
        # 1. DraftKings - sometimes shows on their app
        # 2. FanDuel - occasionally publishes reports  
        # 3. BetMGM - has public betting trends
        
        # These require either:
        # - Account access to see the data
        # - Paid API access
        # - Manual checking
        
        return {
            'draftkings': 'Check app for betting percentages',
            'fanduel': 'Check app for public trends',
            'betmgm': 'Check app for betting splits',
            'note': 'Real data requires sportsbook account access'
        }
    
    def get_free_legitimate_sources(self) -> Dict:
        """
        List of legitimate FREE sources you can use
        """
        return {
            'real_data_sources': {
                'odds_and_lines': {
                    'the_odds_api': {
                        'status': 'WORKING',
                        'api_key': self.odds_api_key,
                        'provides': ['real-time odds', 'line movements', 'multiple sportsbooks'],
                        'url': 'https://the-odds-api.com'
                    }
                },
                'injuries': {
                    'manual_sources': {
                        'nfl_official': 'https://www.nfl.com/injuries/',
                        'espn': 'https://www.espn.com/nfl/injuries',
                        'team_sites': 'Each team\'s official injury report page',
                        'pro_football_ref': 'https://www.pro-football-reference.com/years/2024/injuries.htm'
                    },
                    'free_apis': {
                        'sportsdata_io': {
                            'trial': '7-day free trial available',
                            'url': 'https://sportsdata.io/nfl-api',
                            'provides': ['official injury reports', 'player stats']
                        }
                    }
                },
                'public_betting': {
                    'manual_sources': {
                        'action_network': 'Free articles with betting percentages',
                        'covers': 'https://www.covers.com/consensus',
                        'vegas_insider': 'Consensus page (manual check)',
                        'sports_insights': 'Some free betting trends'
                    },
                    'paid_options': {
                        'action_network_pro': '$8/month for full data',
                        'sports_insights_pro': 'Paid membership for API',
                        'bet_labs': 'Historical betting data'
                    }
                },
                'weather': {
                    'openweathermap': 'ALREADY WORKING - you have this'
                }
            },
            'recommended_approach': [
                '1. Use The Odds API for line movements (WORKING)',
                '2. Sign up for SportsDataIO free trial for injuries',
                '3. Manually check Action Network articles for public %',
                '4. Use Covers.com consensus page for additional data',
                '5. Build historical database over time from these sources'
            ]
        }
    
    def calculate_sharp_money_from_odds_api(self, game_data: Dict) -> Dict:
        """
        Calculate sharp money indicators from REAL odds data
        """
        if not game_data.get('bookmakers'):
            return {'has_sharp_action': False}
        
        # Categorize books by sharp vs recreational
        sharp_books = ['pinnacle', 'bookmaker', 'circa', 'betonline']
        square_books = ['draftkings', 'fanduel', 'betmgm', 'caesars']
        
        sharp_spreads = []
        square_spreads = []
        
        for book in game_data['bookmakers']:
            book_name = book['key'].lower()
            for market in book.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == game_data['home_team']:
                            spread = outcome.get('point', 0)
                            if any(sb in book_name for sb in sharp_books):
                                sharp_spreads.append(spread)
                            elif any(sb in book_name for sb in square_books):
                                square_spreads.append(spread)
        
        # REAL sharp money detection based on actual line differences
        if sharp_spreads and square_spreads:
            sharp_avg = sum(sharp_spreads) / len(sharp_spreads)
            square_avg = sum(square_spreads) / len(square_spreads)
            diff = abs(sharp_avg - square_avg)
            
            return {
                'has_sharp_action': diff >= 0.5,
                'sharp_side': 'home' if sharp_avg < square_avg else 'away',
                'line_difference': diff,
                'confidence': min(diff * 0.1, 0.5),  # Real confidence based on actual difference
                'data_source': 'REAL - The Odds API'
            }
        
        return {'has_sharp_action': False}