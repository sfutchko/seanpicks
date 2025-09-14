#!/usr/bin/env python3
"""
SIMPLIFIED NFL Analyzer - Focus on PROVEN EDGES only
Inspired by MLB's success: Focus on 2-3 KEY factors, not 20 weak ones

Research shows only 3 factors consistently predict NFL games:
1. Sharp money movement (steam, RLM)
2. Key numbers (3, 7, 10)  
3. Extreme weather (wind > 20mph, temp < 20°F)

Everything else is NOISE.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SimplifiedNFLAnalyzer:
    """
    NFL analyzer that actually WORKS
    Like MLB focuses on pitchers, we focus on sharp money
    """
    
    def __init__(self):
        # Start conservative - prove we can win
        self.base_confidence = 0.48
        
        # ONLY the factors that matter
        self.weights = {
            # Sharp Money (60% of decision)
            'steam_move': 0.08,          # Synchronized line movement
            'reverse_line_movement': 0.06,  # Line moves against public
            'sharp_vs_square': 0.06,     # Sharp book divergence
            
            # Key Numbers (30% of decision)  
            'key_number_3': 0.04,        # Most important
            'key_number_7': 0.03,        # Second most
            'key_number_10': 0.02,       # Third
            'line_value': 0.03,          # Getting extra 0.5-1 point
            
            # Extreme Situations (10% of decision)
            'extreme_weather': 0.03,     # Only EXTREME weather
            'primetime_dog': 0.02        # Proven primetime dog pattern
        }
        
        logger.info("🎯 Simplified NFL Analyzer initialized - SHARP MONEY FOCUS")
    
    def analyze_game(self, game: Dict) -> Dict:
        """
        Analyze NFL game with ONLY proven factors
        """
        confidence = self.base_confidence
        factors = []
        pick = None
        
        # 1. SHARP MONEY DETECTION (Most Important!)
        sharp_edge = self._detect_sharp_money(game)
        if sharp_edge['has_edge']:
            confidence += sharp_edge['boost']
            factors.append(sharp_edge['factor'])
            pick = sharp_edge.get('pick')
        
        # 2. KEY NUMBER ANALYSIS
        key_edge = self._analyze_key_numbers(game)
        if key_edge['has_edge']:
            confidence += key_edge['boost']
            factors.append(key_edge['factor'])
            if not pick:
                pick = key_edge.get('pick')
        
        # 3. EXTREME WEATHER (Only if truly extreme)
        weather_edge = self._check_extreme_weather(game)
        if weather_edge['has_edge']:
            confidence += weather_edge['boost']
            factors.append(weather_edge['factor'])
        
        # 4. PROVEN PATTERNS (Very selective)
        pattern_edge = self._check_proven_patterns(game)
        if pattern_edge['has_edge']:
            confidence += pattern_edge['boost']
            factors.append(pattern_edge['factor'])
        
        # Cap confidence realistically
        final_confidence = min(confidence, 0.62)  # Be conservative
        
        # Determine pick if not set by sharp money
        if not pick:
            pick = self._determine_pick(game, factors)
        
        # Only bet if we have REAL edge
        if final_confidence < 0.52:
            return {
                'confidence': 0.48,
                'pick': None,
                'factors': ['No edge detected - PASS'],
                'recommendation': 'NO BET'
            }
        
        return {
            'confidence': final_confidence,
            'pick': pick,
            'factors': factors,
            'recommendation': self._get_recommendation(final_confidence)
        }
    
    def _detect_sharp_money(self, game: Dict) -> Dict:
        """
        Detect REAL sharp money movement
        This is our bread and butter - like pitcher ERA in MLB
        """
        # Check for steam move (most reliable)
        if game.get('steam_move'):
            return {
                'has_edge': True,
                'boost': 0.08,
                'factor': '🔥 STEAM MOVE detected - sharp money synchronized',
                'pick': self._get_steam_side(game)
            }
        
        # Check for reverse line movement
        if game.get('reverse_line_movement'):
            public_pct = game.get('public_percentage', 50)
            if public_pct > 65 or public_pct < 35:
                return {
                    'has_edge': True,
                    'boost': 0.06,
                    'factor': f'💰 RLM: Public {public_pct}% but line moved opposite',
                    'pick': self._get_rlm_side(game)
                }
        
        # Check bookmaker divergence (sharp vs square books)
        book_divergence = self._check_book_divergence(game)
        if book_divergence['has_edge']:
            return book_divergence
        
        return {'has_edge': False}
    
    def _check_book_divergence(self, game: Dict) -> Dict:
        """
        Compare sharp books (Pinnacle, Circa) vs square books (DraftKings, FanDuel)
        """
        if not game.get('bookmakers'):
            return {'has_edge': False}
        
        sharp_books = ['pinnacle', 'circa', 'bookmaker']  # Sharp books
        square_books = ['draftkings', 'fanduel', 'betmgm']  # Square books
        
        sharp_lines = []
        square_lines = []
        
        for book in game['bookmakers']:
            book_key = book.get('key', '').lower()
            
            # Get spread for home team
            for market in book.get('markets', []):
                if market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == game.get('home_team'):
                            spread = outcome.get('point', 0)
                            
                            if book_key in sharp_books:
                                sharp_lines.append(spread)
                            elif book_key in square_books:
                                square_lines.append(spread)
                            break
        
        if sharp_lines and square_lines:
            sharp_avg = sum(sharp_lines) / len(sharp_lines)
            square_avg = sum(square_lines) / len(square_lines)
            diff = abs(sharp_avg - square_avg)
            
            if diff >= 1.0:  # Significant divergence
                sharp_favors = 'home' if sharp_avg > square_avg else 'away'
                team = game.get(f'{sharp_favors}_team')
                
                return {
                    'has_edge': True,
                    'boost': 0.06,
                    'factor': f'📊 Sharp/Square divergence: {diff:.1f} pts',
                    'pick': f'{team} {sharp_avg:+.1f}'
                }
        
        return {'has_edge': False}
    
    def _analyze_key_numbers(self, game: Dict) -> Dict:
        """
        Key numbers are CRUCIAL in NFL
        3 and 7 are gold, 10 is silver
        """
        spread = game.get('spread', 0)
        best_line = game.get('best_available_spread', spread)
        
        # Check if we're getting value crossing key numbers
        if abs(spread) <= 3.5 and abs(spread) >= 2.5:
            if best_line and abs(best_line) > 3:
                # We're getting MORE than 3
                team = self._get_underdog(game)
                return {
                    'has_edge': True,
                    'boost': 0.04,
                    'factor': f'🎯 KEY: Getting {best_line:+.1f} (crosses 3)',
                    'pick': f'{team} {best_line:+.1f}'
                }
        
        elif abs(spread) <= 7.5 and abs(spread) >= 6.5:
            if best_line and abs(best_line) > 7:
                # We're getting MORE than 7
                team = self._get_underdog(game)
                return {
                    'has_edge': True,
                    'boost': 0.03,
                    'factor': f'🎯 KEY: Getting {best_line:+.1f} (crosses 7)',
                    'pick': f'{team} {best_line:+.1f}'
                }
        
        elif abs(spread) <= 10.5 and abs(spread) >= 9.5:
            if best_line and abs(best_line) > 10:
                team = self._get_underdog(game)
                return {
                    'has_edge': True,
                    'boost': 0.02,
                    'factor': f'KEY: Getting {best_line:+.1f} (crosses 10)',
                    'pick': f'{team} {best_line:+.1f}'
                }
        
        return {'has_edge': False}
    
    def _check_extreme_weather(self, game: Dict) -> Dict:
        """
        ONLY extreme weather matters
        Not 10mph wind - we need 20+ mph or freezing temps
        """
        weather = game.get('weather', {})
        
        if not weather or not weather.get('is_outdoor'):
            return {'has_edge': False}
        
        wind = weather.get('wind_speed', 0)
        temp = weather.get('temperature', 60)
        
        # Extreme wind
        if wind >= 20:
            return {
                'has_edge': True,
                'boost': 0.03,
                'factor': f'🌪️ EXTREME: {wind}mph winds - bet UNDER'
            }
        
        # Freezing conditions
        if temp <= 20:
            return {
                'has_edge': True,
                'boost': 0.02,
                'factor': f'🥶 EXTREME: {temp}°F - bet UNDER'
            }
        
        return {'has_edge': False}
    
    def _check_proven_patterns(self, game: Dict) -> Dict:
        """
        Only the MOST proven patterns
        No experimental stuff
        """
        # Primetime dogs of 7+ (56% ATS historically)
        is_primetime = game.get('is_primetime', False)
        spread = game.get('spread', 0)
        
        if is_primetime and abs(spread) >= 7:
            underdog = self._get_underdog(game)
            return {
                'has_edge': True,
                'boost': 0.02,
                'factor': '🌙 Primetime dog +7 or more (56% ATS)',
                'pick': f'{underdog} {abs(spread):+.1f}'
            }
        
        return {'has_edge': False}
    
    def _get_steam_side(self, game: Dict) -> str:
        """Determine which side steam money is on"""
        # Steam typically follows spread movement
        opening = game.get('opening_spread', 0)
        current = game.get('spread', 0)
        
        if current < opening:  # Line moved toward away team
            return f"{game.get('away_team')} {current:+.1f}"
        else:  # Line moved toward home team
            return f"{game.get('home_team')} {current:+.1f}"
    
    def _get_rlm_side(self, game: Dict) -> str:
        """Determine which side has reverse line movement"""
        public_pct = game.get('public_percentage', 50)
        home_team = game.get('home_team')
        away_team = game.get('away_team')
        spread = game.get('spread', 0)
        
        if public_pct > 60:  # Public on favorite
            # But line moved toward dog = take dog
            if spread > 0:
                return f"{home_team} {spread:+.1f}"
            else:
                return f"{away_team} {-spread:+.1f}"
        else:  # Public on dog
            # But line moved toward favorite = take favorite
            if spread < 0:
                return f"{home_team} {spread:.1f}"
            else:
                return f"{away_team} {-spread:.1f}"
    
    def _get_underdog(self, game: Dict) -> str:
        """Get the underdog team"""
        spread = game.get('spread', 0)
        if spread > 0:
            return game.get('home_team')
        else:
            return game.get('away_team')
    
    def _determine_pick(self, game: Dict, factors: List[str]) -> str:
        """Fallback pick determination"""
        # If we have weather factors, bet the under
        if any('EXTREME' in f for f in factors):
            total = game.get('total', 45)
            return f"UNDER {total}"
        
        # Default to underdog with points
        underdog = self._get_underdog(game)
        spread = abs(game.get('spread', 0))
        return f"{underdog} +{spread}"
    
    def _get_recommendation(self, confidence: float) -> str:
        """Get betting recommendation based on confidence"""
        if confidence >= 0.58:
            return "💎 STRONG BET - High confidence"
        elif confidence >= 0.54:
            return "✅ SOLID PLAY - Good value"
        elif confidence >= 0.52:
            return "📊 LEAN - Small edge"
        else:
            return "❌ PASS - No clear edge"