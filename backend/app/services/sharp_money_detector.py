"""
Sharp vs Square Book Detection
Imported from original Sean Picks - PROVEN WORKING
"""

import requests
from typing import Dict, List, Any

class SharpMoneyDetector:
    """Detect sharp action by comparing sharp vs square books"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Books categorized by sharpness (from original app)
        self.sharp_books = [
            'pinnacle',      # Sharpest book in the world
            'bookmaker',     # Sharp offshore book
            'betonlineag',   # Takes big sharp action
            'lowvig',        # Low juice sharp book
            'bovada',        # Offshore, takes sharp action
        ]
        
        self.square_books = [
            'draftkings',    # Public/square heavy
            'fanduel',       # Public/square heavy  
            'betmgm',        # Public/square heavy
            'caesars',       # Public/square heavy
            'espnbet',       # Public/square heavy (ESPN/PENN)
            'betrivers',     # Public/square heavy
            'wynnbet',       # Public/square heavy (if available)
        ]
        
        self.middle_books = [
            'mybookieag',    # Mix of sharp/square
            'betus',         # Mix of sharp/square
        ]
    
    def analyze_game(self, game: Dict) -> Dict:
        """Analyze a single game for sharp action"""
        
        home = game['home_team']
        away = game['away_team']
        
        # Collect odds from different book types
        sharp_odds = []
        square_odds = []
        
        for bookmaker in game.get('bookmakers', []):
            book_name = bookmaker['key']
            
            # Get spread for this book
            for market in bookmaker.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == home:
                            if book_name in self.sharp_books:
                                sharp_odds.append({
                                    'book': book_name,
                                    'spread': outcome['point'],
                                    'price': outcome.get('price', -110)
                                })
                            elif book_name in self.square_books:
                                square_odds.append({
                                    'book': book_name,
                                    'spread': outcome['point'],
                                    'price': outcome.get('price', -110)
                                })
        
        # Analyze the difference
        result = {
            'game': f"{away} @ {home}",
            'has_sharp_action': False,
            'sharp_side': None,
            'confidence': 0,
            'spread_difference': 0,
            'explanation': ''
        }
        
        if sharp_odds and square_odds:
            # Average spreads
            avg_sharp = sum(o['spread'] for o in sharp_odds) / len(sharp_odds)
            avg_square = sum(o['spread'] for o in square_odds) / len(square_odds)
            
            spread_diff = abs(avg_sharp - avg_square)
            result['spread_difference'] = spread_diff
            
            # Significant difference = sharp action
            if spread_diff >= 0.5:
                result['has_sharp_action'] = True
                
                if avg_sharp > avg_square:
                    # Sharp books favor home more (higher spread)
                    result['sharp_side'] = away
                    result['explanation'] = f"Sharp books: {avg_sharp:.1f}, Square books: {avg_square:.1f}. Sharp money on {away}"
                else:
                    # Sharp books favor away more (lower spread)
                    result['sharp_side'] = home
                    result['explanation'] = f"Sharp books: {avg_sharp:.1f}, Square books: {avg_square:.1f}. Sharp money on {home}"
                
                # Confidence based on spread difference
                if spread_diff >= 1.5:
                    result['confidence'] = 0.04  # +4% confidence
                elif spread_diff >= 1.0:
                    result['confidence'] = 0.03  # +3% confidence
                elif spread_diff >= 0.5:
                    result['confidence'] = 0.02  # +2% confidence
        
        return result
    
    def find_steam_moves(self, current_game: Dict, historical_lines: List[Dict]) -> Dict:
        """Detect steam moves (rapid synchronized line movement)"""
        
        # Steam move = all books move same direction within short time
        # Need historical data to detect this properly
        
        result = {
            'has_steam': False,
            'direction': None,
            'magnitude': 0,
            'confidence_boost': 0
        }
        
        # Would compare to lines from 1-2 hours ago
        # If 80%+ of books moved 1+ points same direction = steam
        
        return result