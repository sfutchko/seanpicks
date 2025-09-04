"""
Core confidence calculation algorithm
Migrated from original sean_picks system
"""

from typing import Dict, List, Optional, Tuple
import math

class ConfidenceCalculator:
    """Calculate confidence scores for games"""
    
    def __init__(self):
        self.base_confidence = 0.50
        
    def calculate_confidence(
        self,
        sharp_action: bool = False,
        reverse_line_movement: bool = False,
        steam_move: bool = False,
        key_number_edge: bool = False,
        line_variance: float = 0.0,
        public_fade: bool = False,
        injury_edge: float = 0.0,
        weather_edge: float = 0.0
    ) -> float:
        """
        Calculate confidence score based on multiple factors
        
        Base: 50%
        + Sharp action: +3%
        + Reverse line movement: +3%
        + Steam move: +4%
        + Key number edge: +2%
        + Line variance > 1: +2%
        + Public fade (>65%): +2%
        + Injury edge: +1-3%
        + Weather edge: +1-2%
        """
        confidence = self.base_confidence
        
        # Sharp money indicators
        if sharp_action:
            confidence += 0.03
        
        if reverse_line_movement:
            confidence += 0.03
            
        if steam_move:
            confidence += 0.04  # Strongest indicator
            
        # Line value
        if key_number_edge:
            confidence += 0.02
            
        if line_variance > 1.0:
            confidence += 0.02
            
        # Public betting
        if public_fade:
            confidence += 0.02
            
        # Situational edges
        if injury_edge > 0:
            confidence += min(injury_edge, 0.03)
            
        if weather_edge > 0:
            confidence += min(weather_edge, 0.02)
            
        # Cap at 75% max confidence
        return min(confidence, 0.75)
    
    def detect_reverse_line_movement(
        self,
        opening_spread: float,
        current_spread: float,
        public_percentage: float
    ) -> bool:
        """
        Detect reverse line movement
        Line moves opposite to public betting
        """
        if public_percentage > 60:
            # Public on favorite but line moving toward dog
            if current_spread > opening_spread:
                return True
        elif public_percentage < 40:
            # Public on dog but line moving toward favorite
            if current_spread < opening_spread:
                return True
        return False
    
    def detect_steam_move(
        self,
        line_movements: List[Dict],
        time_window: int = 300  # 5 minutes
    ) -> bool:
        """
        Detect steam move (rapid synchronized line movement)
        """
        if len(line_movements) < 3:
            return False
            
        # Check if multiple books moved in same direction within time window
        recent_moves = [m for m in line_movements if m['time_diff'] <= time_window]
        
        if len(recent_moves) >= 3:
            # Check if all moved in same direction
            directions = [m['direction'] for m in recent_moves]
            if len(set(directions)) == 1:
                return True
                
        return False
    
    def check_key_number(self, spread: float) -> Tuple[bool, str]:
        """
        Check if spread is near key number
        Key numbers in NFL: 3, 7, 10
        """
        key_numbers = [3, 7, 10]
        
        for key in key_numbers:
            if abs(abs(spread) - key) <= 0.5:
                if spread > 0:  # Getting points
                    return True, f"Getting {spread:+.1f} (crosses {key})"
                else:  # Giving points
                    if abs(spread) < key:
                        return True, f"Giving {spread:.1f} (under {key})"
                        
        return False, ""
    
    def calculate_sharp_square_variance(
        self,
        sharp_books: Dict[str, float],
        square_books: Dict[str, float]
    ) -> float:
        """
        Calculate variance between sharp and square books
        Higher variance indicates potential value
        """
        if not sharp_books or not square_books:
            return 0.0
            
        sharp_avg = sum(sharp_books.values()) / len(sharp_books)
        square_avg = sum(square_books.values()) / len(square_books)
        
        return abs(sharp_avg - square_avg)
    
    def calculate_injury_impact(
        self,
        home_injuries: List[Dict],
        away_injuries: List[Dict]
    ) -> float:
        """
        Calculate injury impact on confidence
        """
        impact_scores = {
            'QB': 0.03,
            'RB': 0.01,
            'WR': 0.01,
            'OL': 0.005,
            'EDGE': 0.01,
            'CB': 0.01
        }
        
        home_impact = sum(impact_scores.get(inj.get('position', ''), 0) 
                         for inj in home_injuries if inj.get('status') == 'OUT')
        away_impact = sum(impact_scores.get(inj.get('position', ''), 0) 
                         for inj in away_injuries if inj.get('status') == 'OUT')
        
        # Return differential (positive favors away team)
        return away_impact - home_impact
    
    def calculate_weather_impact(
        self,
        weather_data: Dict,
        total: float
    ) -> float:
        """
        Calculate weather impact on totals
        """
        if not weather_data:
            return 0.0
            
        impact = 0.0
        
        # Wind impact
        wind_speed = weather_data.get('wind_speed', 0)
        if wind_speed > 15:
            impact += 0.01  # Favors under
            
        # Temperature impact
        temp = weather_data.get('temperature', 60)
        if temp < 32:
            impact += 0.01  # Cold favors under
        elif temp > 85:
            impact += 0.005  # Heat can favor over (tired defenses)
            
        # Precipitation
        if weather_data.get('precipitation', False):
            impact += 0.015  # Rain/snow favors under
            
        return impact