"""
SEAN PICKS - Line Movement Tracker
Tracks how lines move to identify sharp money
"""

import requests
import json
from datetime import datetime, timedelta
import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import ODDS_API_KEY

class LineMovementTracker:
    """Tracks line movements to identify sharp action"""
    
    def __init__(self):
        self.api_key = ODDS_API_KEY
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'line_history.db')
        self.init_database()
        
        # Sharp sportsbooks (professional money)
        self.sharp_books = ['pinnacle', 'circa', 'bookmaker']
        
        # Public sportsbooks (recreational money)
        self.public_books = ['draftkings', 'fanduel', 'betmgm', 'caesars']
        
        # Movement thresholds
        self.significant_move = {
            'spread': 1.0,      # 1 point spread move
            'total': 2.0,       # 2 point total move
            'moneyline': 20     # 20 cent line move
        }
    
    def init_database(self):
        """Initialize SQLite database for tracking"""
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create line history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS line_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                home_team TEXT,
                away_team TEXT,
                timestamp DATETIME,
                book TEXT,
                spread REAL,
                total REAL,
                home_ml INTEGER,
                away_ml INTEGER
            )
        ''')
        
        # Create line moves table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS line_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                timestamp DATETIME,
                market TEXT,
                direction TEXT,
                magnitude REAL,
                sharp_indicator BOOLEAN,
                description TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_current_lines(self):
        """Fetch current lines from API"""
        
        url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'spreads,totals,h2h',
            'oddsFormat': 'american',
            'bookmakers': ','.join(self.sharp_books + self.public_books)
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching lines: {e}")
            return []
    
    def store_lines(self, games):
        """Store current lines in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now()
        
        for game in games:
            game_id = game['id']
            home_team = game['home_team']
            away_team = game['away_team']
            
            for bookmaker in game.get('bookmakers', []):
                book = bookmaker['key']
                spread = None
                total = None
                home_ml = None
                away_ml = None
                
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                spread = outcome.get('point', 0)
                    
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over':
                                total = outcome.get('point', 0)
                    
                    elif market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                home_ml = outcome.get('price', 0)
                            else:
                                away_ml = outcome.get('price', 0)
                
                # Store in database
                cursor.execute('''
                    INSERT INTO line_history 
                    (game_id, home_team, away_team, timestamp, book, spread, total, home_ml, away_ml)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (game_id, home_team, away_team, timestamp, book, spread, total, home_ml, away_ml))
        
        conn.commit()
        conn.close()
    
    def analyze_movement(self, game_id):
        """Analyze line movement for a specific game"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get line history
        cursor.execute('''
            SELECT timestamp, book, spread, total, home_ml, away_ml
            FROM line_history
            WHERE game_id = ?
            ORDER BY timestamp
        ''', (game_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        if len(history) < 2:
            return None
        
        movements = {
            'spread': [],
            'total': [],
            'sharp_action': None,
            'reverse_line_movement': False,
            'steam_move': False
        }
        
        # Track opening lines
        opening = {}
        current = {}
        
        for row in history:
            timestamp, book, spread, total, home_ml, away_ml = row
            
            if book not in opening:
                opening[book] = {'spread': spread, 'total': total}
            
            current[book] = {'spread': spread, 'total': total}
        
        # Calculate movements
        for book in current:
            if book in opening:
                # Handle None values
                if opening[book]['spread'] is not None and current[book]['spread'] is not None:
                    spread_move = current[book]['spread'] - opening[book]['spread']
                else:
                    spread_move = 0
                
                if opening[book]['total'] is not None and current[book]['total'] is not None:
                    total_move = current[book]['total'] - opening[book]['total']
                else:
                    total_move = 0
                
                if abs(spread_move) >= 0.5:
                    movements['spread'].append({
                        'book': book,
                        'move': spread_move,
                        'is_sharp': book in self.sharp_books
                    })
                
                if abs(total_move) >= 1.0:
                    movements['total'].append({
                        'book': book,
                        'move': total_move,
                        'is_sharp': book in self.sharp_books
                    })
        
        # Identify sharp action
        sharp_spread_moves = [m for m in movements['spread'] if m['is_sharp']]
        public_spread_moves = [m for m in movements['spread'] if not m['is_sharp']]
        
        if sharp_spread_moves and public_spread_moves:
            sharp_direction = sum(m['move'] for m in sharp_spread_moves)
            public_direction = sum(m['move'] for m in public_spread_moves)
            
            # Reverse line movement (sharp vs public)
            if (sharp_direction > 0 and public_direction < 0) or (sharp_direction < 0 and public_direction > 0):
                movements['reverse_line_movement'] = True
                movements['sharp_action'] = 'home' if sharp_direction > 0 else 'away'
        
        # Check for steam move (rapid movement across books)
        if len(movements['spread']) >= 3:
            avg_move = sum(m['move'] for m in movements['spread']) / len(movements['spread'])
            if abs(avg_move) >= 1.5:
                movements['steam_move'] = True
        
        return movements
    
    def get_sharp_report(self, game_data):
        """Generate sharp money report for a game"""
        
        game_id = game_data.get('game_id')
        if not game_id:
            return None
        
        movements = self.analyze_movement(game_id)
        if not movements:
            return None
        
        report = {
            'game': f"{game_data['away_team']} @ {game_data['home_team']}",
            'sharp_indicators': [],
            'confidence_boost': 0,
            'recommended_bet': None
        }
        
        # Reverse line movement is strongest indicator
        if movements['reverse_line_movement']:
            report['sharp_indicators'].append('REVERSE LINE MOVEMENT DETECTED')
            report['confidence_boost'] = 0.04
            report['recommended_bet'] = f"Follow sharp money on {movements['sharp_action']}"
        
        # Steam move is also strong
        if movements['steam_move']:
            report['sharp_indicators'].append('STEAM MOVE DETECTED')
            report['confidence_boost'] = max(report['confidence_boost'], 0.03)
        
        # Analyze spread movements
        if movements['spread']:
            total_move = sum(m['move'] for m in movements['spread'])
            if abs(total_move) >= 2.0:
                direction = 'home' if total_move > 0 else 'away'
                report['sharp_indicators'].append(f'Significant line move toward {direction}')
        
        # Analyze total movements
        if movements['total']:
            total_move = sum(m['move'] for m in movements['total'])
            if total_move >= 2.0:
                report['sharp_indicators'].append('Sharp money on OVER')
            elif total_move <= -2.0:
                report['sharp_indicators'].append('Sharp money on UNDER')
        
        return report
    
    def track_live_movements(self):
        """Track lines throughout the day"""
        
        print("📊 Fetching current lines...")
        games = self.fetch_current_lines()
        
        if games:
            self.store_lines(games)
            print(f"✅ Stored lines for {len(games)} games")
            
            # Analyze each game
            for game in games[:5]:  # Top 5 games
                movements = self.analyze_movement(game['id'])
                if movements and movements.get('sharp_action'):
                    print(f"\n💰 SHARP ACTION: {game['away_team']} @ {game['home_team']}")
                    print(f"   Direction: {movements['sharp_action']}")
                    if movements['reverse_line_movement']:
                        print("   ⚠️ REVERSE LINE MOVEMENT!")
                    if movements['steam_move']:
                        print("   🔥 STEAM MOVE!")
        else:
            print("❌ No games found")


class PublicMoneyTracker:
    """Track public betting percentages"""
    
    def __init__(self):
        self.public_sources = [
            'actionnetwork',  # Best source but paid
            'vegasinsider',   # Free but delayed
            'espn',           # Limited data
        ]
    
    def scrape_public_percentages(self):
        """Scrape public betting percentages"""
        
        # This would scrape actual sites
        # For demo, returning sample data
        return {
            'Buffalo Bills @ Miami Dolphins': {
                'spread_tickets': {'home': 35, 'away': 65},
                'spread_money': {'home': 42, 'away': 58},
                'total_tickets': {'over': 71, 'under': 29},
                'total_money': {'over': 68, 'under': 32}
            },
            'Dallas Cowboys @ New York Giants': {
                'spread_tickets': {'home': 22, 'away': 78},
                'spread_money': {'home': 31, 'away': 69},
                'total_tickets': {'over': 55, 'under': 45},
                'total_money': {'over': 52, 'under': 48}
            }
        }
    
    def identify_contrarian_plays(self, public_data):
        """Find contrarian betting opportunities"""
        
        contrarian = []
        
        for game, data in public_data.items():
            # Ticket vs money discrepancy
            spread_ticket_diff = abs(data['spread_tickets']['home'] - data['spread_money']['home'])
            total_ticket_diff = abs(data['total_tickets']['over'] - data['total_money']['over'])
            
            # Large discrepancy means sharp money opposing public
            if spread_ticket_diff >= 15:
                if data['spread_tickets']['home'] > data['spread_money']['home']:
                    # Public on home, sharp on away
                    contrarian.append({
                        'game': game,
                        'bet': 'Away team',
                        'reason': f"Public {data['spread_tickets']['home']}% tickets but only {data['spread_money']['home']}% money",
                        'confidence_boost': 0.02
                    })
                else:
                    contrarian.append({
                        'game': game,
                        'bet': 'Home team',
                        'reason': f"Public {data['spread_tickets']['away']}% tickets on away but money on home",
                        'confidence_boost': 0.02
                    })
            
            # Extreme public betting (fade)
            for side in ['home', 'away']:
                if data['spread_tickets'][side] >= 80:
                    fade_side = 'away' if side == 'home' else 'home'
                    contrarian.append({
                        'game': game,
                        'bet': f'{fade_side.title()} team',
                        'reason': f"Fade {data['spread_tickets'][side]}% public",
                        'confidence_boost': 0.03
                    })
            
            # Total extremes
            if data['total_tickets']['over'] >= 75:
                contrarian.append({
                    'game': game,
                    'bet': 'UNDER',
                    'reason': f"Fade {data['total_tickets']['over']}% public on over",
                    'confidence_boost': 0.02
                })
            elif data['total_tickets']['under'] >= 75:
                contrarian.append({
                    'game': game,
                    'bet': 'OVER',
                    'reason': f"Fade {data['total_tickets']['under']}% public on under",
                    'confidence_boost': 0.02
                })
        
        return contrarian


class SteamChaser:
    """Identify and chase steam moves"""
    
    def __init__(self):
        self.steam_threshold = {
            'spread': 1.5,  # 1.5 point move
            'total': 2.5,   # 2.5 point move
            'time': 30      # Within 30 minutes
        }
    
    def detect_steam(self, line_history):
        """Detect steam moves in real-time"""
        
        steam_moves = []
        
        # Group by time windows
        current_time = datetime.now()
        recent_window = current_time - timedelta(minutes=30)
        
        recent_moves = [h for h in line_history if h['timestamp'] > recent_window]
        
        if len(recent_moves) >= 3:
            # Calculate movement velocity
            spread_moves = [h['spread'] for h in recent_moves if h['spread']]
            total_moves = [h['total'] for h in recent_moves if h['total']]
            
            if spread_moves:
                spread_change = spread_moves[-1] - spread_moves[0]
                if abs(spread_change) >= self.steam_threshold['spread']:
                    steam_moves.append({
                        'type': 'spread',
                        'direction': 'home' if spread_change > 0 else 'away',
                        'magnitude': abs(spread_change),
                        'confidence': 0.04,
                        'action': 'FOLLOW THE STEAM'
                    })
            
            if total_moves:
                total_change = total_moves[-1] - total_moves[0]
                if abs(total_change) >= self.steam_threshold['total']:
                    steam_moves.append({
                        'type': 'total',
                        'direction': 'over' if total_change > 0 else 'under',
                        'magnitude': abs(total_change),
                        'confidence': 0.03,
                        'action': 'FOLLOW THE STEAM'
                    })
        
        return steam_moves


if __name__ == "__main__":
    print("=" * 60)
    print(" LINE MOVEMENT TRACKER")
    print("=" * 60)
    
    # Initialize tracker
    tracker = LineMovementTracker()
    public_tracker = PublicMoneyTracker()
    steam = SteamChaser()
    
    print("\n📈 Sharp vs Public Books:")
    print(f"Sharp: {', '.join(tracker.sharp_books)}")
    print(f"Public: {', '.join(tracker.public_books)}")
    
    print("\n🔄 Tracking current lines...")
    tracker.track_live_movements()
    
    print("\n👥 Public Betting Percentages:")
    public_data = public_tracker.scrape_public_percentages()
    for game, data in public_data.items():
        print(f"\n{game}:")
        print(f"  Spread: {data['spread_tickets']['away']}% tickets on away")
        print(f"  Money: {data['spread_money']['away']}% money on away")
        discrepancy = abs(data['spread_tickets']['away'] - data['spread_money']['away'])
        if discrepancy >= 10:
            print(f"  ⚠️ SHARP/PUBLIC DISCREPANCY: {discrepancy}%")
    
    print("\n💡 Contrarian Plays:")
    contrarian = public_tracker.identify_contrarian_plays(public_data)
    for play in contrarian:
        print(f"  {play['game']}: {play['bet']}")
        print(f"    Reason: {play['reason']}")
    
    print("\n📊 To use line movement:")
    print("1. Run this script every hour to track")
    print("2. Look for reverse line movement")
    print("3. Follow steam moves quickly")
    print("4. Fade extreme public betting")