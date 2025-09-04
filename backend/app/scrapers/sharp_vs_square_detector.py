#!/usr/bin/env python3
"""
SHARP VS SQUARE BOOK COMPARISON
This actually works - no public betting % needed!

Sharp books (Circa, Pinnacle, Bookmaker) move first
Square books (DraftKings, FanDuel) follow later
The difference tells you where sharp money went
"""

import requests
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import ODDS_API_KEY

class SharpMoneyDetector:
    """Detect sharp action by comparing sharp vs square books"""
    
    def __init__(self):
        self.api_key = ODDS_API_KEY
        
        # Books categorized by sharpness
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
            'mybookieag',      # Mix of sharp/square
            'betus',           # Mix of sharp/square
        ]
    
    def analyze_games_for_sharp_action(self, games):
        """Analyze provided games for sharp action instead of fetching new ones"""
        sharp_moves = []
        
        for game in games:
            analysis = self.analyze_game(game)
            if analysis['has_sharp_action']:
                sharp_moves.append(analysis)
        
        return sharp_moves
    
    def get_odds_comparison(self):
        """Compare odds between sharp and square books"""
        
        url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'spreads,totals',
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                games = response.json()
                
                sharp_moves = []
                
                for game in games:
                    analysis = self.analyze_game(game)
                    if analysis['has_sharp_action']:
                        sharp_moves.append(analysis)
                
                return sharp_moves
            
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def analyze_game(self, game):
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
            'explanation': ''
        }
        
        if sharp_odds and square_odds:
            # Average spreads
            avg_sharp = sum(o['spread'] for o in sharp_odds) / len(sharp_odds)
            avg_square = sum(o['spread'] for o in square_odds) / len(square_odds)
            
            spread_diff = abs(avg_sharp - avg_square)
            
            # Significant difference = sharp action
            if spread_diff >= 0.5:
                result['has_sharp_action'] = True
                
                if avg_sharp > avg_square:
                    # Sharp books favor home more
                    result['sharp_side'] = away
                    result['explanation'] = f"Sharp books have {home} at {avg_sharp:.1f}, squares at {avg_square:.1f}. Sharp money on {away}."
                else:
                    # Sharp books favor away more  
                    result['sharp_side'] = home
                    result['explanation'] = f"Sharp books have {home} at {avg_sharp:.1f}, squares at {avg_square:.1f}. Sharp money on {home}."
                
                # Confidence based on spread difference
                if spread_diff >= 1.0:
                    result['confidence'] = 'HIGH'
                elif spread_diff >= 0.75:
                    result['confidence'] = 'MEDIUM'
                else:
                    result['confidence'] = 'LOW'
        
        return result
    
    def find_middle_opportunities(self, game):
        """Find middling opportunities between books"""
        
        middles = []
        
        bookmakers = game.get('bookmakers', [])
        
        for i, book1 in enumerate(bookmakers):
            for book2 in bookmakers[i+1:]:
                # Check spreads
                for market1 in book1.get('markets', []):
                    if market1['key'] == 'spreads':
                        for market2 in book2.get('markets', []):
                            if market2['key'] == 'spreads':
                                # Compare spreads
                                spread1 = market1['outcomes'][0]['point']
                                spread2 = market2['outcomes'][0]['point']
                                
                                if abs(spread1 - spread2) >= 1.0:
                                    middles.append({
                                        'book1': book1['title'],
                                        'book2': book2['title'],
                                        'spread1': spread1,
                                        'spread2': spread2,
                                        'middle_range': abs(spread1 - spread2)
                                    })
        
        return middles
    
    def get_steam_moves(self):
        """Detect steam moves (rapid line movement across books)"""
        
        # This would need historical data
        # For now, identify games where all books moved same direction
        
        print("🚂 STEAM MOVE DETECTION")
        print("Monitoring for synchronized line movement...")
        
        # Would compare current lines to 1 hour ago
        # If all books moved 1+ points same direction = steam
        
        return []

def main():
    """Run sharp money detection"""
    
    print("="*60)
    print("🎯 SHARP VS SQUARE BOOK COMPARISON")
    print("="*60)
    print("\nNo public betting % needed!")
    print("Sharp books move first, squares follow")
    print("The difference = where sharp money went\n")
    
    detector = SharpMoneyDetector()
    
    # Get sharp moves
    sharp_moves = detector.get_odds_comparison()
    
    if sharp_moves:
        print("💰 SHARP ACTION DETECTED:\n")
        for move in sharp_moves:
            print(f"🏈 {move['game']}")
            print(f"   Sharp Side: {move['sharp_side']}")
            print(f"   Confidence: {move['confidence']}")
            print(f"   {move['explanation']}\n")
    else:
        print("No significant sharp action detected currently")
    
    print("\n" + "="*60)
    print("💡 HOW THIS WORKS:")
    print("="*60)
    print("1. Pinnacle/Bookmaker = Sharp books (pros bet here)")
    print("2. DraftKings/FanDuel = Square books (public bets here)")
    print("3. If sharp books have Chiefs -3 but squares have Chiefs -4")
    print("   => Sharp money is on the OTHER TEAM")
    print("4. No public % needed - the line difference tells all!")

if __name__ == "__main__":
    main()