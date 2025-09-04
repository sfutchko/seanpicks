#!/usr/bin/env python3
"""
MLB Confidence Calculator - BASEBALL SPECIFIC!
Completely separate from NFL algorithm
Uses REAL pitcher data, bullpen stats, and matchups
"""

from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MLBConfidenceCalculator:
    """
    Calculate betting confidence for MLB games
    COMPLETELY DIFFERENT from NFL - focused on pitching matchups
    """
    
    def __init__(self):
        # MLB-specific base confidence (lower than NFL due to more variance)
        self.base_confidence = 0.48
        
        # MLB confidence weights - PITCHING IS KING!
        self.weights = {
            # Starting Pitcher Analysis (40% total)
            'starter_era': 0.15,           # Lower ERA = better
            'starter_recent_form': 0.10,   # Last 3 starts
            'starter_vs_opponent': 0.08,   # Historical vs this team
            'starter_k_rate': 0.07,        # Strikeout ability
            
            # Bullpen Analysis (15% total)
            'bullpen_era': 0.08,           # Bullpen strength
            'bullpen_recent': 0.07,        # Last 7 days
            
            # Batting Matchups (15% total)
            'team_ops': 0.05,              # Overall hitting ability
            'lefty_righty_splits': 0.05,   # L/R advantages
            'recent_hitting': 0.05,        # Hot/cold streaks
            
            # Situational Factors (15% total)
            'park_factor': 0.05,           # Venue advantages
            'day_night': 0.03,             # Day/night splits
            'weather': 0.04,               # Wind, temp effects
            'rest_advantage': 0.03,        # Rest days
            
            # Betting Patterns (15% total)
            'line_movement': 0.08,         # Sharp money indicators
            'total_movement': 0.07         # Over/under sharp action
        }
        
        logger.info("⚾ MLB Confidence Calculator initialized - REAL DATA ONLY!")
    
    def calculate_confidence(
        self,
        home_pitcher: Dict,
        away_pitcher: Dict,
        home_batting: Dict,
        away_batting: Dict,
        home_bullpen: Dict,
        away_bullpen: Dict,
        park_factors: Dict,
        weather: Optional[Dict] = None,
        line_movement: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        Calculate comprehensive MLB betting confidence
        """
        confidence = self.base_confidence
        factors = []
        
        # 1. STARTING PITCHER ANALYSIS (Most Important!)
        pitcher_edge = self._analyze_pitchers(home_pitcher, away_pitcher)
        if pitcher_edge:
            confidence += pitcher_edge['boost']
            factors.append(pitcher_edge['factor'])
        
        # 2. RECENT FORM (Last 3 starts)
        form_edge = self._analyze_recent_form(home_pitcher, away_pitcher)
        if form_edge:
            confidence += form_edge['boost']
            factors.append(form_edge['factor'])
        
        # 3. BULLPEN COMPARISON
        bullpen_edge = self._analyze_bullpens(home_bullpen, away_bullpen)
        if bullpen_edge:
            confidence += bullpen_edge['boost']
            factors.append(bullpen_edge['factor'])
        
        # 4. BATTING MATCHUPS
        hitting_edge = self._analyze_hitting(home_batting, away_batting, 
                                            home_pitcher, away_pitcher)
        if hitting_edge:
            confidence += hitting_edge['boost']
            factors.append(hitting_edge['factor'])
        
        # 5. PARK FACTORS
        park_edge = self._analyze_park_factors(park_factors, home_pitcher, away_pitcher)
        if park_edge:
            confidence += park_edge['boost']
            factors.append(park_edge['factor'])
        
        # 6. WEATHER IMPACT (if outdoor stadium)
        if weather:
            weather_edge = self._analyze_weather(weather, park_factors)
            if weather_edge:
                confidence += weather_edge['boost']
                factors.append(weather_edge['factor'])
        
        # 7. LINE MOVEMENT (Sharp money)
        if line_movement:
            sharp_edge = self._analyze_line_movement(line_movement)
            if sharp_edge:
                confidence += sharp_edge['boost']
                factors.append(sharp_edge['factor'])
        
        # Determine pick based on edges
        pick = self._determine_pick(
            home_pitcher, away_pitcher,
            home_batting, away_batting,
            confidence, factors,
            home_team=kwargs.get('home_team'),
            away_team=kwargs.get('away_team')
        )
        
        return {
            'confidence': min(max(confidence, 0.40), 0.65),  # Cap between 40-65%
            'pick': pick,
            'factors': factors,
            'pitcher_advantage': pitcher_edge,
            'bullpen_advantage': bullpen_edge,
            'hitting_advantage': hitting_edge,
            'park_advantage': park_edge
        }
    
    def _analyze_pitchers(self, home: Dict, away: Dict) -> Optional[Dict]:
        """
        Compare starting pitchers - MOST IMPORTANT FACTOR!
        """
        if not home or not away:
            return None
        
        home_era = home.get('era', 4.50)
        away_era = away.get('era', 4.50)
        
        # ERA difference analysis
        era_diff = away_era - home_era
        
        if abs(era_diff) > 1.0:  # Significant ERA advantage
            if era_diff > 0:
                # Home pitcher better
                boost = min(era_diff * 0.02, 0.06)
                return {
                    'boost': boost,
                    'factor': f"🔥 Home pitcher ERA advantage: {home_era:.2f} vs {away_era:.2f}",
                    'favors': 'home'
                }
            else:
                # Away pitcher better
                boost = min(abs(era_diff) * 0.02, 0.06)
                return {
                    'boost': boost,
                    'factor': f"🔥 Away pitcher ERA advantage: {away_era:.2f} vs {home_era:.2f}",
                    'favors': 'away'
                }
        
        # Also check strikeout rates
        home_k9 = home.get('k_per_9', 8.0)
        away_k9 = away.get('k_per_9', 8.0)
        
        if abs(home_k9 - away_k9) > 2.0:
            if home_k9 > away_k9:
                return {
                    'boost': 0.02,
                    'factor': f"⚡ Home pitcher K-rate: {home_k9:.1f} K/9",
                    'favors': 'home'
                }
            else:
                return {
                    'boost': 0.02,
                    'factor': f"⚡ Away pitcher K-rate: {away_k9:.1f} K/9",
                    'favors': 'away'
                }
        
        return None
    
    def _analyze_recent_form(self, home: Dict, away: Dict) -> Optional[Dict]:
        """
        Analyze last 3 starts performance
        """
        home_recent = home.get('last_3_starts', [])
        away_recent = away.get('last_3_starts', [])
        
        # Calculate avg ERA from last 3 starts (they're lists of game logs)
        home_recent_era = 4.50  # default
        away_recent_era = 4.50  # default
        
        if home_recent and isinstance(home_recent, list):
            total_innings = sum(s.get('innings', 0) for s in home_recent if isinstance(s, dict))
            total_earned_runs = sum(s.get('earned_runs', 0) for s in home_recent if isinstance(s, dict))
            if total_innings > 0:
                home_recent_era = (total_earned_runs * 9) / total_innings
        
        if away_recent and isinstance(away_recent, list):
            total_innings = sum(s.get('innings', 0) for s in away_recent if isinstance(s, dict))
            total_earned_runs = sum(s.get('earned_runs', 0) for s in away_recent if isinstance(s, dict))
            if total_innings > 0:
                away_recent_era = (total_earned_runs * 9) / total_innings
        
        if home_recent_era != 4.50 or away_recent_era != 4.50:
            diff = away_recent_era - home_recent_era
            
            if abs(diff) > 1.5:
                if diff > 0:
                    return {
                        'boost': 0.03,
                        'factor': f"📈 Home pitcher hot: {home_recent_era:.2f} ERA last 3",
                        'favors': 'home'
                    }
                else:
                    return {
                        'boost': 0.03,
                        'factor': f"📈 Away pitcher hot: {away_recent_era:.2f} ERA last 3",
                        'favors': 'away'
                    }
        
        return None
    
    def _analyze_bullpens(self, home: Dict, away: Dict) -> Optional[Dict]:
        """
        Compare bullpen strength
        """
        if not home or not away:
            return None
        
        home_era = home.get('era', 4.00)
        away_era = away.get('era', 4.00)
        
        diff = away_era - home_era
        
        if abs(diff) > 0.75:
            if diff > 0:
                return {
                    'boost': 0.025,
                    'factor': f"💪 Home bullpen advantage: {home_era:.2f} ERA",
                    'favors': 'home'
                }
            else:
                return {
                    'boost': 0.025,
                    'factor': f"💪 Away bullpen advantage: {away_era:.2f} ERA",
                    'favors': 'away'
                }
        
        return None
    
    def _analyze_hitting(self, home_batting: Dict, away_batting: Dict,
                        home_pitcher: Dict, away_pitcher: Dict) -> Optional[Dict]:
        """
        Analyze batting matchups and recent hitting form
        """
        if not home_batting or not away_batting:
            return None
        
        home_ops = home_batting.get('ops', 0.700)
        away_ops = away_batting.get('ops', 0.700)
        
        # Check for significant OPS advantage
        if abs(home_ops - away_ops) > 0.050:
            if home_ops > away_ops:
                return {
                    'boost': 0.02,
                    'factor': f"🏏 Home batting advantage: {home_ops:.3f} OPS",
                    'favors': 'home'
                }
            else:
                return {
                    'boost': 0.02,
                    'factor': f"🏏 Away batting advantage: {away_ops:.3f} OPS",
                    'favors': 'away'
                }
        
        return None
    
    def _analyze_park_factors(self, park: Dict, home_pitcher: Dict, 
                             away_pitcher: Dict) -> Optional[Dict]:
        """
        Analyze how park factors affect the matchup
        """
        if not park:
            return None
        
        runs_factor = park.get('runs_factor', 1.0)
        hr_factor = park.get('hr_factor', 1.0)
        
        # Extreme parks provide edges
        if runs_factor > 1.1:  # Hitter's park
            # Check if we have a ground ball pitcher
            return {
                'boost': 0.015,
                'factor': f"🏟️ Hitter-friendly park (factor: {runs_factor:.2f})",
                'favors': 'over'
            }
        elif runs_factor < 0.9:  # Pitcher's park
            return {
                'boost': 0.015,
                'factor': f"🏟️ Pitcher-friendly park (factor: {runs_factor:.2f})",
                'favors': 'under'
            }
        
        return None
    
    def _analyze_weather(self, weather: Dict, park: Dict) -> Optional[Dict]:
        """
        Weather impact on baseball games
        """
        if not weather:
            return None
        
        wind_speed = weather.get('wind_speed', 0)
        wind_direction = weather.get('wind_direction', 'calm')
        temp = weather.get('temperature', 72)
        
        # Wind effects
        if wind_speed > 15:
            if 'out' in wind_direction.lower():
                return {
                    'boost': 0.02,
                    'factor': f"💨 Wind {wind_speed}mph blowing out",
                    'favors': 'over'
                }
            elif 'in' in wind_direction.lower():
                return {
                    'boost': 0.02,
                    'factor': f"💨 Wind {wind_speed}mph blowing in",
                    'favors': 'under'
                }
        
        # Temperature effects
        if temp > 90:
            return {
                'boost': 0.01,
                'factor': f"🌡️ Hot weather ({temp}°F) - ball carries",
                'favors': 'over'
            }
        elif temp < 50:
            return {
                'boost': 0.01,
                'factor': f"🌡️ Cold weather ({temp}°F) - pitcher advantage",
                'favors': 'under'
            }
        
        return None
    
    def _analyze_line_movement(self, movement: Dict) -> Optional[Dict]:
        """
        Detect sharp money movement in MLB
        """
        if not movement:
            return None
        
        ml_move = movement.get('moneyline_movement', 0)
        total_move = movement.get('total_movement', 0)
        rl_move = movement.get('runline_movement', 0)
        
        # Significant line movement
        if abs(ml_move) > 20:  # 20+ cent move
            if ml_move > 0:
                return {
                    'boost': 0.03,
                    'factor': f"💰 Sharp money on home team (+{ml_move} cents)",
                    'favors': 'home'
                }
            else:
                return {
                    'boost': 0.03,
                    'factor': f"💰 Sharp money on away team ({ml_move} cents)",
                    'favors': 'away'
                }
        
        # Total movement
        if abs(total_move) > 0.5:
            if total_move > 0:
                return {
                    'boost': 0.02,
                    'factor': f"📊 Total moved up {total_move} runs - sharp over",
                    'favors': 'over'
                }
            else:
                return {
                    'boost': 0.02,
                    'factor': f"📊 Total moved down {abs(total_move)} runs - sharp under",
                    'favors': 'under'
                }
        
        return None
    
    def _determine_pick(self, home_pitcher: Dict, away_pitcher: Dict,
                       home_batting: Dict, away_batting: Dict,
                       confidence: float, factors: List[str],
                       home_team: str = None, away_team: str = None) -> str:
        """
        Determine the best bet based on all factors
        """
        # Count which team factors favor
        home_factors = sum(1 for f in factors if 'Home' in f or 'home' in f)
        away_factors = sum(1 for f in factors if 'Away' in f or 'away' in f)
        over_factors = sum(1 for f in factors if 'over' in f.lower())
        under_factors = sum(1 for f in factors if 'under' in f.lower())
        
        # Use actual team names
        home_name = home_team or "Home Team"
        away_name = away_team or "Away Team"
        
        # Moneyline/Runline pick
        if home_factors > away_factors:
            pick = home_name
            if confidence > 0.55:
                pick += " ML"  # Moneyline for high confidence
            else:
                pick += " +1.5"  # Runline for lower confidence
        elif away_factors > home_factors:
            pick = away_name
            if confidence > 0.55:
                pick += " ML"
            else:
                pick += " +1.5"
        # Total pick if that's stronger
        elif over_factors > under_factors:
            pick = "Over Total"
        elif under_factors > over_factors:
            pick = "Under Total"
        else:
            # Default to better pitcher
            home_era = home_pitcher.get('era', 4.50)
            away_era = away_pitcher.get('era', 4.50)
            
            if home_era < away_era:
                pick = f"{home_name} +1.5"
            else:
                pick = f"{away_name} +1.5"
        
        return pick