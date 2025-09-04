#!/usr/bin/env python3
"""
ADVANCED PUBLIC BETTING CALCULATOR
Calculates realistic public betting percentages using multiple factors
"""

import hashlib
from typing import Dict, List
from datetime import datetime

class AdvancedPublicCalculator:
    """
    Calculates public betting percentages based on:
    1. Line movements between books
    2. Team popularity/market size
    3. Recent performance (winning streaks)
    4. Primetime/national TV games
    5. Spread size (public loves favorites)
    """
    
    def __init__(self):
        # Team market sizes/popularity (1-10 scale)
        self.team_popularity = {
            'Cowboys': 10, 'Patriots': 9, 'Packers': 9, 'Steelers': 9,
            'Chiefs': 9, '49ers': 8, 'Eagles': 8, 'Giants': 8,
            'Bears': 7, 'Broncos': 7, 'Raiders': 7, 'Seahawks': 7,
            'Bills': 7, 'Dolphins': 6, 'Rams': 6, 'Vikings': 6,
            'Ravens': 6, 'Saints': 6, 'Falcons': 5, 'Cardinals': 5,
            'Colts': 5, 'Chargers': 5, 'Titans': 4, 'Browns': 4,
            'Lions': 5, 'Bengals': 5, 'Buccaneers': 6, 'Jets': 6,
            'Panthers': 4, 'Commanders': 4, 'Texans': 4, 'Jaguars': 3,
            'Washington': 4
        }
    
    def calculate_public_percentage(self, game: Dict) -> Dict:
        """
        Calculate realistic public betting percentages
        """
        home_team = game.get('home_team', '')
        away_team = game.get('away_team', '')
        spread = game.get('spread', 0)  # Home team spread
        
        # Start with base 50/50
        home_public = 50.0
        
        # Factor 1: Spread size (public loves big favorites)
        if abs(spread) > 7:
            # Big favorite gets more public action
            if spread < 0:  # Home favored
                home_public += min(15, abs(spread) * 1.5)
            else:  # Away favored
                home_public -= min(15, abs(spread) * 1.5)
        elif abs(spread) > 3:
            # Moderate favorite
            if spread < 0:
                home_public += min(10, abs(spread) * 2)
            else:
                home_public -= min(10, abs(spread) * 2)
        
        # Factor 2: Team popularity
        home_pop = self.team_popularity.get(home_team.split()[-1], 5)
        away_pop = self.team_popularity.get(away_team.split()[-1], 5)
        popularity_diff = home_pop - away_pop
        home_public += popularity_diff * 2  # 2% per popularity point
        
        # Factor 3: Line movement (from bookmaker data)
        if game.get('bookmakers'):
            line_movement_adjustment = self._analyze_line_movement(game)
            home_public += line_movement_adjustment
        
        # Factor 4: Primetime games get more public action on favorites
        game_time = game.get('game_time', '')
        if any(time in str(game_time) for time in ['20:', '00:20', 'Sunday Night', 'Monday Night']):
            # Primetime - public hammers the favorite
            if spread < -3:
                home_public += 5
            elif spread > 3:
                home_public -= 5
        
        # Factor 5: Home team bias (public slightly favors home teams)
        home_public += 2
        
        # Factor 6: Create some randomness based on matchup
        # Use team names to generate consistent but varied results
        hash_input = f"{away_team}_{home_team}_{spread}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        variance = (hash_value % 11) - 5  # -5 to +5 variance
        home_public += variance
        
        # Keep within realistic bounds
        home_public = max(15, min(85, home_public))
        away_public = 100 - home_public
        
        # Determine confidence based on factors
        confidence = self._determine_confidence(game, abs(home_public - 50))
        
        return {
            'home_percentage': round(home_public),
            'away_percentage': round(away_public),
            'public_on_home': home_public > 50,
            'public_percentage': round(max(home_public, away_public)),
            'sources_count': len(game.get('bookmakers', [])),
            'sources': ['Calculated from odds movement & team factors'],
            'confidence': confidence,
            'factors': {
                'spread_influence': abs(spread) > 3,
                'popularity_diff': popularity_diff,
                'primetime': 'Night' in str(game_time)
            }
        }
    
    def _analyze_line_movement(self, game: Dict) -> float:
        """
        Analyze line movement between sharp and square books
        Returns adjustment to home public percentage
        """
        sharp_books = ['pinnacle', 'bookmaker', 'circa', 'betonlineag']
        square_books = ['draftkings', 'fanduel', 'betmgm', 'caesars']
        
        sharp_lines = []
        square_lines = []
        home_team = game.get('home_team', '')
        
        for book in game.get('bookmakers', []):
            book_key = book.get('key', '').lower()
            
            for market in book.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team:
                            spread = outcome.get('point', 0)
                            
                            if any(sb in book_key for sb in sharp_books):
                                sharp_lines.append(spread)
                            elif any(sb in book_key for sb in square_books):
                                square_lines.append(spread)
        
        if sharp_lines and square_lines:
            sharp_avg = sum(sharp_lines) / len(sharp_lines)
            square_avg = sum(square_lines) / len(square_lines)
            diff = square_avg - sharp_avg
            
            # Square books shading means public on other side
            if abs(diff) >= 1.0:
                return -diff * 8  # Strong movement
            elif abs(diff) >= 0.5:
                return -diff * 5  # Moderate movement
            else:
                return -diff * 2  # Slight movement
        
        return 0
    
    def _determine_confidence(self, game: Dict, public_lean: float) -> str:
        """
        Determine confidence level of public betting calculation
        """
        books_count = len(game.get('bookmakers', []))
        
        if books_count >= 5 and public_lean > 15:
            return 'HIGH'
        elif books_count >= 3 and public_lean > 10:
            return 'MEDIUM'
        elif books_count >= 2:
            return 'LOW'
        else:
            return 'ESTIMATED'


class RealisticBettingPatterns:
    """
    Generate realistic betting patterns based on game scenarios
    """
    
    @staticmethod
    def get_typical_patterns() -> Dict:
        """
        Typical public betting patterns we see in real games
        """
        return {
            'big_favorite': {
                'description': 'Public hammers big favorites (-7 or more)',
                'typical_range': '65-75% on favorite'
            },
            'popular_team': {
                'description': 'Cowboys, Chiefs, Patriots get extra public action',
                'typical_range': '60-70% on popular team'
            },
            'primetime_favorite': {
                'description': 'Sunday/Monday night favorites get heavy public action',
                'typical_range': '65-75% on favorite'
            },
            'home_underdog': {
                'description': 'Home dogs often get contrarian sharp money',
                'typical_range': '35-45% public (sharp on dog)'
            },
            'division_rival': {
                'description': 'Division games more balanced',
                'typical_range': '45-55% fairly even'
            },
            'neutral_game': {
                'description': 'Pick em games are usually balanced',
                'typical_range': '48-52% very balanced'
            }
        }