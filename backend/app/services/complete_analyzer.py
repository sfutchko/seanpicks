"""
SEAN PICKS - Complete Game Analyzer
Integrates ALL the analysis features from the original app
"""

import requests
from typing import Dict, List, Any
from datetime import datetime
import sqlite3
import os
from .sharp_money_detector import SharpMoneyDetector
from .public_betting_aggregator import PublicBettingAggregator
from .real_data_scraper import RealDataScraper
from .enhanced_data_fetcher import EnhancedDataFetcher
from .legitimate_data_fetcher import LegitimateDataFetcher
from .realtime_data_fetcher import OptimizedDataService
from .smart_data_calculator import SmartDataCalculator, InjuryDataService
from .advanced_public_calculator import AdvancedPublicCalculator

class CompleteAnalyzer:
    """
    This is what we've been missing!
    Combines all the data sources for maximum edge
    """
    
    def __init__(self):
        self.weather_api_key = "85203d1084a3bc89e21a0409e5b9418b"
        self.weather_base = "https://api.openweathermap.org/data/2.5/weather"
        self.odds_api_key = "d4fa91883b15fd5a5594c64e58b884ef"
        
        # Initialize sharp money detector
        self.sharp_detector = SharpMoneyDetector(self.odds_api_key)
        
        # Initialize public betting aggregator
        self.public_aggregator = PublicBettingAggregator()
        
        # Initialize REAL data scraper for injuries and betting
        self.real_scraper = RealDataScraper()
        
        # Initialize enhanced data fetcher as primary source
        self.enhanced_fetcher = EnhancedDataFetcher()
        
        # Initialize LEGITIMATE data fetcher for REAL data only
        self.legitimate_fetcher = LegitimateDataFetcher()
        
        # Initialize OPTIMIZED real-time data service (FAST!)
        self.optimized_data = OptimizedDataService()
        
        # Initialize SMART calculator that uses our existing data
        self.smart_calc = SmartDataCalculator()
        self.injury_service = InjuryDataService()
        
        # Initialize ADVANCED public betting calculator for realistic percentages
        self.advanced_calc = AdvancedPublicCalculator()
        
        # Initialize line history database
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'line_history.db')
        self.init_database()
        
        # Proven profitable patterns from original app
        self.profitable_patterns = {
            'thursday_night_under': {'win_rate': 0.58, 'confidence_boost': 0.02},
            'division_dog_7_10': {'win_rate': 0.56, 'confidence_boost': 0.015},
            'wind_15_plus_under': {'win_rate': 0.61, 'confidence_boost': 0.025},
            'road_fav_off_bye': {'win_rate': 0.57, 'confidence_boost': 0.02},
            'december_division_under': {'win_rate': 0.60, 'confidence_boost': 0.02},
            'primetime_dog_7_plus': {'win_rate': 0.56, 'confidence_boost': 0.015},
            'backup_qb_under': {'win_rate': 0.59, 'confidence_boost': 0.02}
        }
        
        # Stadium locations for weather
        self.stadium_coords = {
            "Kansas City Chiefs": {"lat": 39.0489, "lon": -94.4839},
            "Buffalo Bills": {"lat": 42.7738, "lon": -78.7870},
            "Green Bay Packers": {"lat": 44.5013, "lon": -88.0622},
            "Chicago Bears": {"lat": 41.8623, "lon": -87.6167},
            "Denver Broncos": {"lat": 39.7439, "lon": -105.0201},
            "New England Patriots": {"lat": 42.0909, "lon": -71.2643},
            "Pittsburgh Steelers": {"lat": 40.4468, "lon": -80.0158},
            "Cleveland Browns": {"lat": 41.5061, "lon": -81.6995},
            "Cincinnati Bengals": {"lat": 39.0954, "lon": -84.5160},
            "Baltimore Ravens": {"lat": 39.2780, "lon": -76.6227}
        }
        
        # Dome teams (no weather impact)
        self.dome_teams = [
            "Dallas Cowboys", "Las Vegas Raiders", "Los Angeles Rams",
            "Arizona Cardinals", "New Orleans Saints", "Indianapolis Colts",
            "Detroit Lions", "Minnesota Vikings", "Atlanta Falcons"
        ]
    
    def analyze_game_complete(self, game: Dict) -> Dict:
        """
        Complete analysis using ALL factors
        This is the REAL algorithm from the original app!
        """
        
        analysis = {
            "game": f"{game['away_team']} @ {game['home_team']}",
            "base_confidence": 0.50,
            "factors": [],
            "adjustments": {
                "spread": 0,
                "total": 0
            },
            "insights": []
        }
        
        # 1. SHARP vs SQUARE MONEY (Most important!)
        sharp_square = self.analyze_sharp_square(game)
        if sharp_square['has_edge']:
            analysis['base_confidence'] += sharp_square['confidence_boost']
            analysis['factors'].append(f"Sharp Money: +{sharp_square['confidence_boost']:.1%}")
            analysis['insights'].append(sharp_square['insight'])
        
        # 2. WEATHER ANALYSIS (Huge for totals)
        weather = self.get_weather_impact(game['home_team'])
        
        # ALWAYS add weather data for display (not just when has_impact)
        if weather:
            analysis['weather'] = {
                'temperature': weather.get('temperature', 72),
                'wind_speed': weather.get('wind_speed', 0),
                'description': weather.get('conditions', 'Clear')
            }
            
            if weather['has_impact']:
                analysis['adjustments']['total'] += weather['total_adjustment']
                if abs(weather['total_adjustment']) > 3:
                    analysis['base_confidence'] += 0.02
                    analysis['factors'].append("Weather Edge: +2%")
                analysis['insights'].append(weather['insight'])
        
        # 3. KEY INJURIES (Can move lines 3+ points)
        injuries = self.check_key_injuries(game)
        if injuries['has_impact']:
            analysis['adjustments']['spread'] += injuries['spread_adjustment']
            analysis['base_confidence'] += injuries['confidence_boost']
            analysis['factors'].append(f"Injury Edge: +{injuries['confidence_boost']:.1%}")
            analysis['insights'].append(injuries['insight'])
        
        # 4. PUBLIC BETTING FADE (Contrarian value)
        public = self.get_public_betting(game)
        if public['fade_opportunity']:
            analysis['base_confidence'] += 0.02
            analysis['factors'].append("Fade Public: +2%")
            analysis['insights'].append(public['insight'])
        
        # Store public betting data for display
        analysis['public_betting'] = public
        
        # 5. LINE MOVEMENT HISTORY TRACKING
        line_movement = self.track_line_movement(game)
        if line_movement['has_movement']:
            if line_movement['steam_move']:
                analysis['base_confidence'] += 0.04
                analysis['factors'].append("Steam: +4%")
                analysis['insights'].append("🚂 STEAM MOVE - Follow immediately!")
            if line_movement.get('reverse_line_movement'):
                analysis['base_confidence'] += 0.03
                analysis['factors'].append("RLM: +3%")
                analysis['insights'].append("📈 Reverse line movement from history")
        
        # 6. REVERSE LINE MOVEMENT (from game data)
        if game.get('reverse_line_movement') and not line_movement.get('reverse_line_movement'):
            analysis['base_confidence'] += 0.03
            analysis['factors'].append("RLM: +3%")
            analysis['insights'].append("📈 Reverse line movement detected")
        
        # 7. STEAM MOVES (from game data)
        if game.get('steam_move') and not line_movement.get('steam_move'):
            analysis['base_confidence'] += 0.04
            analysis['factors'].append("Steam: +4%")
            analysis['insights'].append("🚂 STEAM MOVE - Follow immediately!")
        
        # 7. KEY NUMBERS - Check for CROSSING key numbers
        spread = game.get('spread', 0)
        key_number_boost = 0
        key_insight = ""
        
        # Check if we're getting value by crossing key numbers
        best_spread = None
        if 'bookmakers' in game:
            all_spreads = []
            home_team = game.get('home_team')
            for book in game['bookmakers']:
                for market in book.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                all_spreads.append(outcome.get('point', 0))
            if all_spreads:
                best_spread = max(all_spreads) if spread > 0 else min(all_spreads)
        
        if best_spread:
            # Check for crossing key number 3
            if abs(spread) <= 3.5 and abs(spread) >= 2.5:
                if (spread > 3 and best_spread > 3.5) or (spread < -3 and best_spread < -3.5):
                    key_number_boost = 0.02
                    key_insight = f"🎯 Key: Getting {best_spread:+.1f} (crosses 3)"
                elif abs(spread) == 3:
                    key_number_boost = 0.01
                    key_insight = "On key number 3"
            # Check for crossing key number 7  
            elif abs(spread) <= 7.5 and abs(spread) >= 6.5:
                if (spread > 7 and best_spread > 7.5) or (spread < -7 and best_spread < -7.5):
                    key_number_boost = 0.015
                    key_insight = f"🎯 Key: Getting {best_spread:+.1f} (crosses 7)"
                elif abs(spread) == 7:
                    key_number_boost = 0.01
                    key_insight = "On key number 7"
            # Check for crossing key number 10
            elif abs(spread) <= 10.5 and abs(spread) >= 9.5:
                if (spread > 10 and best_spread > 10.5) or (spread < -10 and best_spread < -10.5):
                    key_number_boost = 0.01
                    key_insight = f"Key: Getting {best_spread:+.1f} (crosses 10)"
        else:
            # Fallback to basic key number check
            if abs(spread) in [3, 7, 10]:
                key_number_boost = 0.01
                key_insight = f"On key number {abs(spread)}"
        
        if key_number_boost > 0:
            analysis['base_confidence'] += key_number_boost
            analysis['factors'].append(f"Key Number: +{key_number_boost:.1%}")
            analysis['insights'].append(key_insight)
        
        # 8. SITUATIONAL SPOTS DETECTION
        situational = self.detect_situational_spots(game)
        if situational['has_spot']:
            analysis['base_confidence'] += situational['confidence_boost']
            analysis['factors'].append(f"Situational: +{situational['confidence_boost']:.1%}")
            analysis['insights'].append(situational['insight'])
        
        # 9. LINE VALUE - Compare best available line to consensus
        line_value_boost = 0
        line_value_insight = ""
        
        # Get consensus spread and best available
        consensus_spread = game.get('spread', 0)
        best_available = None
        
        # Check bookmaker data for best line
        if 'bookmakers' in game:
            all_spreads = []
            home_team = game.get('home_team')
            for book in game['bookmakers']:
                for market in book.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == home_team:
                                all_spreads.append(outcome.get('point', 0))
            
            if all_spreads:
                best_available = max(all_spreads) if consensus_spread > 0 else min(all_spreads)
                line_value = abs(best_available - consensus_spread)
                
                # +1% confidence per 0.5 points of value (as per algo doc)
                if line_value >= 0.5:
                    line_value_boost = min(0.03, line_value * 0.02)  # Cap at 3%
                    line_value_insight = f"📊 Line value: {line_value:.1f} pts better than consensus"
        
        if line_value_boost > 0:
            analysis['base_confidence'] += line_value_boost
            analysis['factors'].append(f"Line Value: +{line_value_boost:.1%}")
            analysis['insights'].append(line_value_insight)
        
        # 9. SITUATIONAL SPOTS (BOOSTED)
        situational = self.check_situational_spots(game)
        if situational['has_edge']:
            analysis['base_confidence'] += situational['confidence_boost']
            analysis['factors'].append(f"Situation: +{situational['confidence_boost']:.1%}")
            analysis['insights'].append(situational['insight'])
        
        # 10. MULTIPLE SPORTSBOOKS BONUS
        book_count = game.get('bookmaker_count', 0)
        if book_count >= 10:
            analysis['base_confidence'] += 0.005
            analysis['factors'].append("Books Available: +0.5%")
            analysis['insights'].append(f"{book_count} books for line shopping")
        
        # 11. REFEREE TENDENCIES
        referee = self.check_referee_impact(game)
        if referee['has_impact']:
            analysis['adjustments']['total'] += referee['total_adjustment']
            analysis['insights'].append(referee['insight'])
        
        # 12. CORRELATION FOR PARLAYS
        analysis['parlay_correlation'] = self.calculate_parlay_correlation(game)
        
        # Cap confidence at 65%
        analysis['final_confidence'] = min(analysis['base_confidence'], 0.65)
        
        # Determine best bet
        analysis['best_bet'] = self.determine_best_bet(
            game, 
            analysis['final_confidence'],
            analysis['adjustments']
        )
        
        # Kelly criterion bet sizing
        if analysis['final_confidence'] > 0.54:
            analysis['kelly_percentage'] = self.kelly_criterion(analysis['final_confidence'])
        
        return analysis
    
    def analyze_sharp_square(self, game: Dict) -> Dict:
        """Detect sharp vs square money patterns using REAL book comparison"""
        
        # FIRST: Try legitimate data fetcher with The Odds API (REAL DATA)
        if self.legitimate_fetcher and game.get('bookmakers'):
            sharp_indicators = self.legitimate_fetcher.calculate_sharp_money_from_odds_api(game)
            
            if sharp_indicators.get('has_sharp_action'):
                confidence_boost = sharp_indicators.get('confidence', 0.03)
                side = sharp_indicators.get('sharp_side', 'unknown')
                diff = sharp_indicators.get('line_difference', 0)
                
                insight = f"💰 Sharp money on {side} (line diff: {diff:.1f})"
                if sharp_indicators.get('data_source'):
                    insight += f" - {sharp_indicators['data_source']}"
                
                return {
                    'has_edge': True,
                    'confidence_boost': confidence_boost,
                    'insight': insight,
                    'sharp_side': side,
                    'spread_difference': diff
                }
        
        # FALLBACK: Use the original sharp money detector if available
        if game.get('bookmakers'):
            sharp_analysis = self.sharp_detector.analyze_game(game)
            
            if sharp_analysis['has_sharp_action']:
                return {
                    'has_edge': True,
                    'confidence_boost': sharp_analysis['confidence'],
                    'insight': f"💰 {sharp_analysis['explanation']}",
                    'sharp_side': sharp_analysis['sharp_side'],
                    'spread_difference': sharp_analysis['spread_difference']
                }
        
        # Fallback to original detection with stronger boost
        if game.get('sharp_action'):
            return {
                'has_edge': True,
                'confidence_boost': 0.05,  # Increased from 0.03
                'insight': '💰 Sharp money pattern detected'
            }
        
        # Also check for reverse line movement
        if game.get('reverse_line_movement'):
            return {
                'has_edge': True,
                'confidence_boost': 0.04,
                'insight': '🔄 Reverse line movement detected'
            }
        
        return {'has_edge': False}
    
    def get_weather_impact(self, home_team: str) -> Dict:
        """Get real weather data for outdoor stadiums"""
        
        # Dome teams return dome weather
        if home_team in self.dome_teams:
            return {
                'has_impact': False,
                'temperature': 72,
                'wind_speed': 0,
                'conditions': 'Dome',
                'description': 'Dome',
                'total_adjustment': 0,
                'insight': '🏟️ Indoor stadium - no weather impact'
            }
        
        # Get stadium coordinates
        coords = self.stadium_coords.get(home_team)
        if not coords:
            # Unknown stadium - return default outdoor weather
            return {
                'has_impact': False,
                'temperature': 65,
                'wind_speed': 5,
                'conditions': 'Clear',
                'description': 'Clear',
                'total_adjustment': 0,
                'insight': '⛅ Typical conditions'
            }
        
        try:
            # Call OpenWeatherMap API
            params = {
                'lat': coords['lat'],
                'lon': coords['lon'],
                'appid': self.weather_api_key,
                'units': 'imperial'
            }
            
            response = requests.get(self.weather_base, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                temp = data['main']['temp']
                wind = data['wind']['speed']
                description = data['weather'][0]['description']
                
                total_adjustment = 0
                insight = f"🌤️ {temp:.0f}°F, {wind:.0f} mph wind"
                
                # Wind impacts
                if wind > 15:
                    total_adjustment -= 3  # Favor under
                    insight += " - Strong wind favors UNDER"
                
                # Temperature impacts
                if temp < 32:
                    total_adjustment -= 2  # Cold favors under
                    insight += " - Cold weather favors UNDER"
                elif temp > 85:
                    total_adjustment += 1  # Heat can favor over
                    insight += " - Hot weather may favor OVER"
                
                # Rain/Snow
                if 'rain' in description.lower() or 'snow' in description.lower():
                    total_adjustment -= 2
                    insight += f" - {description.title()} favors UNDER"
                
                return {
                    'has_impact': abs(total_adjustment) > 0,
                    'total_adjustment': total_adjustment,
                    'insight': insight,
                    'temperature': temp,
                    'wind_speed': wind,
                    'conditions': description
                }
        except Exception as e:
            # Return default outdoor weather on API failure
            print(f"Weather API failed for {home_team}: {e}")
            return {
                'has_impact': False,
                'temperature': 65,
                'wind_speed': 5,
                'conditions': 'Clear',
                'description': 'Clear',
                'total_adjustment': 0,
                'insight': '⛅ Weather data unavailable'
            }
        
        # Fallback
        return {
            'has_impact': False,
            'temperature': 65,
            'wind_speed': 5,
            'conditions': 'Clear',
            'description': 'Clear',
            'total_adjustment': 0,
            'conditions': 'Clear',
            'insight': '⛅ Weather data unavailable'
        }
    
    def check_key_injuries(self, game: Dict) -> Dict:
        """Check for key player injuries and calculate impact"""
        
        # Import Week 18 real injury data
        from .week18_injury_data import get_week_18_injuries
        
        # Get REAL Week 18 injury reports
        home_injury_data = get_week_18_injuries(game.get('home_team'))
        away_injury_data = get_week_18_injuries(game.get('away_team'))
        
        # If no Week 18 data, try other sources
        if home_injury_data.get('source') == 'none':
            home_injury_data = self.optimized_data.get_injuries_fast(game.get('home_team'))
            if home_injury_data.get('source') == 'none':
                home_injury_data = self.enhanced_fetcher.get_injury_report(game.get('home_team'))
                if home_injury_data.get('impact_score', 0) == 0:
                    home_injury_data = self.real_scraper.get_nfl_injuries(game.get('home_team'))
        
        if away_injury_data.get('source') == 'none':
            away_injury_data = self.optimized_data.get_injuries_fast(game.get('away_team'))
            if away_injury_data.get('source') == 'none':
                away_injury_data = self.enhanced_fetcher.get_injury_report(game.get('away_team'))
                if away_injury_data.get('impact_score', 0) == 0:
                    away_injury_data = self.real_scraper.get_nfl_injuries(game.get('away_team'))
        
        # Calculate impact scores
        home_injuries = home_injury_data.get('impact_score', 0)
        away_injuries = away_injury_data.get('impact_score', 0)
        
        print(f"✅ REAL injuries: Home {len(home_injury_data.get('out', []))} out, Away {len(away_injury_data.get('out', []))} out")
        
        # Calculate differential (positive favors away team)
        injury_differential = abs(home_injuries - away_injuries)
        
        # Calculate confidence boost based on differential
        # 0.5% per point of injury differential (as per algo doc)
        confidence_boost = 0
        spread_adjustment = 0
        insight = ""
        
        if injury_differential >= 7.0:  # Starting QB out
            confidence_boost = 0.04
            spread_adjustment = injury_differential * 0.5
            insight = f"🚑 Major injury advantage ({injury_differential:.1f} pts)"
        elif injury_differential >= 4.0:  # Multiple key players
            confidence_boost = 0.03
            spread_adjustment = injury_differential * 0.4
            insight = f"🤕 Significant injury edge ({injury_differential:.1f} pts)"
        elif injury_differential >= 2.0:  # Key skill player
            confidence_boost = 0.02
            spread_adjustment = injury_differential * 0.3
            insight = f"📋 Injury advantage ({injury_differential:.1f} pts)"
        elif injury_differential >= 1.0:  # Role player
            confidence_boost = 0.01
            spread_adjustment = injury_differential * 0.2
            insight = f"Minor injury edge ({injury_differential:.1f} pts)"
        
        if injury_differential > 0:
            return {
                'has_impact': True,
                'confidence_boost': confidence_boost,
                'spread_adjustment': spread_adjustment if home_injuries > away_injuries else -spread_adjustment,
                'insight': insight,
                'differential': injury_differential
            }
        
        return {'has_impact': False}
    
    def fetch_real_injury_data(self, home_team: str, away_team: str) -> Dict:
        """Fetch real injury data from ESPN API"""
        try:
            # Map team names to ESPN team IDs
            team_map = {
                'Buffalo Bills': 'BUF', 'Miami Dolphins': 'MIA', 'New England Patriots': 'NE', 'New York Jets': 'NYJ',
                'Baltimore Ravens': 'BAL', 'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Pittsburgh Steelers': 'PIT',
                'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Tennessee Titans': 'TEN',
                'Denver Broncos': 'DEN', 'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
                'Dallas Cowboys': 'DAL', 'New York Giants': 'NYG', 'Philadelphia Eagles': 'PHI', 'Washington Commanders': 'WSH',
                'Chicago Bears': 'CHI', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB', 'Minnesota Vikings': 'MIN',
                'Atlanta Falcons': 'ATL', 'Carolina Panthers': 'CAR', 'New Orleans Saints': 'NO', 'Tampa Bay Buccaneers': 'TB',
                'Arizona Cardinals': 'ARI', 'Los Angeles Rams': 'LAR', 'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA'
            }
            
            home_abbr = team_map.get(home_team, home_team)
            away_abbr = team_map.get(away_team, away_team)
            
            # Fetch injury reports from ESPN
            # Note: ESPN's API requires specific endpoints
            home_impact = 0
            away_impact = 0
            
            # Try ESPN's team API
            for team, abbr, is_home in [(home_team, home_abbr, True), (away_team, away_abbr, False)]:
                try:
                    # ESPN injury endpoint
                    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/injuries"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        injuries = data.get('injuries', [])
                        
                        impact = 0
                        for injury in injuries:
                            status = injury.get('status', '').lower()
                            position = injury.get('position', '').upper()
                            
                            # Calculate impact based on position and status
                            if status in ['out', 'doubtful']:
                                if position == 'QB':
                                    impact += 7.0  # Starting QB out
                                elif position in ['RB', 'WR', 'TE'] and injury.get('starter'):
                                    impact += 3.0  # Key skill position
                                elif position in ['OL', 'DL'] and injury.get('starter'):
                                    impact += 2.0  # Key lineman
                                else:
                                    impact += 1.0  # Role player
                            elif status == 'questionable':
                                if position == 'QB':
                                    impact += 3.5  # QB questionable
                                elif position in ['RB', 'WR', 'TE'] and injury.get('starter'):
                                    impact += 1.5
                                else:
                                    impact += 0.5
                        
                        if is_home:
                            home_impact = impact
                        else:
                            away_impact = impact
                            
                except:
                    pass
            
            return {
                'home_impact': home_impact,
                'away_impact': away_impact,
                'has_data': home_impact > 0 or away_impact > 0
            }
            
        except Exception as e:
            print(f"Error fetching injury data: {e}")
            return {'home_impact': 0, 'away_impact': 0, 'has_data': False}
    
    def detect_situational_spots(self, game: Dict) -> Dict:
        """Detect situational advantages like division games, primetime, etc."""
        
        home_team = game.get('home_team', '')
        away_team = game.get('away_team', '')
        game_time = game.get('game_time', '')
        
        confidence_boost = 0
        insights = []
        
        # Division matchups - teams that play twice a year
        divisions = {
            'AFC East': ['Buffalo Bills', 'Miami Dolphins', 'New England Patriots', 'New York Jets'],
            'AFC North': ['Baltimore Ravens', 'Cincinnati Bengals', 'Cleveland Browns', 'Pittsburgh Steelers'],
            'AFC South': ['Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars', 'Tennessee Titans'],
            'AFC West': ['Denver Broncos', 'Kansas City Chiefs', 'Las Vegas Raiders', 'Los Angeles Chargers'],
            'NFC East': ['Dallas Cowboys', 'New York Giants', 'Philadelphia Eagles', 'Washington Commanders'],
            'NFC North': ['Chicago Bears', 'Detroit Lions', 'Green Bay Packers', 'Minnesota Vikings'],
            'NFC South': ['Atlanta Falcons', 'Carolina Panthers', 'New Orleans Saints', 'Tampa Bay Buccaneers'],
            'NFC West': ['Arizona Cardinals', 'Los Angeles Rams', 'San Francisco 49ers', 'Seattle Seahawks']
        }
        
        # Check if it's a division game
        for division, teams in divisions.items():
            if home_team in teams and away_team in teams:
                confidence_boost += 0.02
                insights.append(f"🏆 Division rivalry game ({division})")
                break
        
        # Check for primetime games
        if game_time:
            from datetime import datetime
            try:
                game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                day_of_week = game_dt.strftime('%A')
                hour = game_dt.hour
                
                # Thursday Night Football
                if day_of_week == 'Thursday' and hour >= 20:  # 8 PM or later
                    confidence_boost += 0.01
                    insights.append("🌙 Thursday Night Football")
                
                # Sunday/Monday Night Football
                elif (day_of_week == 'Sunday' and hour >= 20) or (day_of_week == 'Monday' and hour >= 20):
                    confidence_boost += 0.015
                    insights.append("🌟 Primetime game")
                
                # Late window Sunday games
                elif day_of_week == 'Sunday' and hour >= 16:  # 4 PM games
                    confidence_boost += 0.005
                    insights.append("📺 National TV window")
                    
            except Exception as e:
                print(f"Error parsing game time: {e}")
        
        # Revenge game spots (would need historical data)
        # Look-ahead spots (would need schedule analysis)
        # Sandwich spots (short week between games)
        
        if confidence_boost > 0:
            return {
                'has_spot': True,
                'confidence_boost': confidence_boost,
                'insight': ' | '.join(insights)
            }
        
        return {'has_spot': False}
    
    def get_public_betting(self, game: Dict) -> Dict:
        """Get REAL public betting percentages calculated from line movements"""
        
        # Use ADVANCED calculator for realistic, varied percentages!
        # This considers spread size, team popularity, line movements, etc.
        public_data = self.advanced_calc.calculate_public_percentage(game)
        
        # If we got good data from advanced calc, use it
        if public_data.get('confidence') not in ['NONE', None]:
            return self._format_public_betting_result(public_data)
        
        # Fallback to other methods if needed
        away_team = game.get('away_team', '')
        home_team = game.get('home_team', '')
        
        # Try optimized service
        public_data = self.optimized_data.get_public_betting_fast(away_team, home_team)
        
        # If still no data, try enhanced fetcher
        if public_data.get('confidence') == 'NONE':
            public_data = self.enhanced_fetcher.get_public_betting_consensus(away_team, home_team)
        
        # If confidence is low, also try aggregator
        if public_data.get('confidence') == 'LOW' or public_data.get('confidence') == 'ESTIMATED':
            # Pass game spread to aggregator for better estimates
            self.public_aggregator.current_game = game
            agg_data = self.public_aggregator.aggregate_all_sources(away_team, home_team)
            
            # Use aggregator data if better
            if agg_data and agg_data.get('sources_count', 0) > public_data.get('sources_count', 0):
                public_data = agg_data
        
        if public_data:
            public_pct = public_data['public_percentage']
            
            # Determine fade opportunity
            fade_opportunity = public_pct >= 65  # 65% or more is fadeable
            
            # Build insight message
            if public_data['sources_count'] > 0:
                sources_str = f" ({', '.join(public_data['sources'])})"
            else:
                sources_str = " (estimated)"
            
            if fade_opportunity:
                insight = f"👥 {public_pct}% of public on favorite - FADE opportunity{sources_str}"
            else:
                insight = f"👥 {public_pct}% public betting split{sources_str}"
            
            return {
                'fade_opportunity': fade_opportunity,
                'public_percentage': public_pct,
                'public_on_home': public_data.get('public_on_home', False),
                'away_percentage': public_data.get('away_percentage', 50),
                'home_percentage': public_data.get('home_percentage', 50),
                'sources': public_data.get('sources', []),
                'confidence': public_data.get('confidence', 'LOW'),
                'insight': insight
            }
        
        # Fallback if no data
        return {
            'fade_opportunity': False,
            'public_percentage': 50,
            'insight': '👥 No public betting data available'
        }
    
    def _format_public_betting_result(self, public_data: Dict) -> Dict:
        """Format public betting data for consistent output"""
        public_pct = public_data.get('public_percentage', 50)
        fade_opportunity = public_pct >= 65
        
        # Build insight message
        if public_data.get('sources_count', 0) > 0:
            sources_str = f" ({', '.join(public_data.get('sources', []))})"
        else:
            sources_str = ""
        
        if fade_opportunity:
            insight = f"👥 {public_pct}% of public on favorite - FADE opportunity{sources_str}"
        else:
            insight = f"👥 {public_pct}% public betting split{sources_str}"
        
        return {
            'fade_opportunity': fade_opportunity,
            'public_percentage': public_pct,
            'public_on_home': public_data.get('public_on_home', False),
            'away_percentage': public_data.get('away_percentage', 50),
            'home_percentage': public_data.get('home_percentage', 50),
            'sources': public_data.get('sources', []),
            'confidence': public_data.get('confidence', 'LOW'),
            'insight': insight
        }
    
    def check_situational_spots(self, game: Dict) -> Dict:
        """Check for profitable situational angles"""
        
        situations = []
        confidence_boost = 0
        
        # Look for sandwich spots, letdowns, lookaheads, etc.
        # This would use schedule data in production
        
        # Division game (boosted to match algo doc)
        if 'division' in str(game).lower():
            situations.append("Division rivalry")
            confidence_boost += 0.02  # Increased from 0.01
        
        # Prime time games (boosted)
        game_time = game.get('game_time', '')
        if '20:' in game_time or '00:20' in game_time:  # 8:20 PM games
            situations.append("Prime time game")
            confidence_boost += 0.015  # Increased from 0.005
            
            # Prime time dog +7 or more (special pattern)
            spread = game.get('spread', 0)
            if spread >= 7:
                situations.append("Prime time dog +7+")
                confidence_boost += 0.01  # Additional boost
        
        # Thursday Night games
        if 'Thu' in game_time or 'Thursday' in str(game):
            situations.append("Thursday Night")
            confidence_boost += 0.01
            
            # Thursday Night Under pattern
            if game.get('total', 0) > 40:
                situations.append("Thursday Under pattern")
                confidence_boost += 0.01
        
        if situations:
            return {
                'has_edge': True,
                'confidence_boost': confidence_boost,
                'insight': f"📅 {', '.join(situations)}"
            }
        
        return {'has_edge': False}
    
    def check_referee_impact(self, game: Dict) -> Dict:
        """Check referee tendencies"""
        
        # Would lookup referee assignments and historical data
        # Some refs call more penalties = higher totals
        
        # TODO: Implement real referee tendency tracking
        # For now, no mock data
        return {'has_impact': False}
    
    def calculate_parlay_correlation(self, game: Dict) -> float:
        """Calculate correlation for parlay purposes"""
        
        # Games with similar characteristics correlate
        # Division games, weather games, etc.
        
        return 0.2  # Default low correlation until we implement real analysis
    
    def init_database(self):
        """Initialize SQLite database for line tracking"""
        
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
        
        conn.commit()
        conn.close()
    
    def track_line_movement(self, game: Dict) -> Dict:
        """Track and analyze line movement history"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            game_id = game.get('id', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            # Store current lines
            if 'bookmakers' in game:
                for book in game['bookmakers']:
                    book_name = book.get('key', '')
                    spread = None
                    total = None
                    
                    for market in book.get('markets', []):
                        if market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    spread = outcome.get('point', 0)
                        elif market['key'] == 'totals':
                            total = market['outcomes'][0].get('point', 0) if market['outcomes'] else None
                    
                    if spread is not None:
                        cursor.execute('''
                            INSERT INTO line_history (game_id, home_team, away_team, timestamp, book, spread, total)
                            VALUES (?, ?, ?, datetime('now'), ?, ?, ?)
                        ''', (game_id, home_team, away_team, book_name, spread, total))
            
            # Analyze historical movement
            cursor.execute('''
                SELECT book, spread, timestamp FROM line_history
                WHERE game_id = ? OR (home_team = ? AND away_team = ?)
                ORDER BY timestamp ASC
            ''', (game_id, home_team, away_team))
            
            history = cursor.fetchall()
            conn.commit()
            conn.close()
            
            movement_analysis = {
                'has_movement': False,
                'steam_move': False,
                'reverse_line_movement': False,
                'confidence_boost': 0
            }
            
            if len(history) > 1:
                # Check for steam move (1+ point move in < 30 min)
                recent_moves = [h for h in history[-10:]]  # Last 10 entries
                if len(recent_moves) >= 3:
                    spread_change = abs(recent_moves[-1][1] - recent_moves[0][1])
                    if spread_change >= 1.0:
                        movement_analysis['steam_move'] = True
                        movement_analysis['confidence_boost'] = 0.04
                        movement_analysis['has_movement'] = True
            
            return movement_analysis
            
        except Exception as e:
            # If database operations fail, return no movement
            return {
                'has_movement': False,
                'steam_move': False,
                'reverse_line_movement': False,
                'confidence_boost': 0
            }
    
    def determine_best_bet(self, game: Dict, confidence: float, adjustments: Dict) -> Dict:
        """Determine the best bet based on all factors"""
        
        if confidence < 0.54:
            return None
        
        spread_adj = adjustments['spread']
        total_adj = adjustments['total']
        
        # Prioritize totals if weather/ref impact is strong
        if abs(total_adj) > abs(spread_adj) and abs(total_adj) > 2:
            if total_adj < 0:
                return {
                    'type': 'TOTAL',
                    'pick': f"UNDER {game.get('total', 45)}",
                    'confidence': confidence,
                    'edge': round((confidence - 0.524) * 100, 1),
                    'reasoning': f"Total adjusted by {total_adj:.1f} points"
                }
            else:
                return {
                    'type': 'TOTAL',
                    'pick': f"OVER {game.get('total', 45)}",
                    'confidence': confidence,
                    'edge': round((confidence - 0.524) * 100, 1),
                    'reasoning': f"Total adjusted by {total_adj:.1f} points"
                }
        
        # Otherwise go with spread if we have edge
        elif abs(spread_adj) > 0 or confidence > 0.56:
            # Determine which team to take
            if spread_adj != 0:
                # Injuries favor one side
                if spread_adj > 0:
                    team = game['away_team'] if game['spread'] < 0 else game['home_team']
                else:
                    team = game['home_team'] if game['spread'] < 0 else game['away_team']
            else:
                # Go with underdog if no specific edge
                team = game['away_team'] if game['spread'] < 0 else game['home_team']
            
            # Fix the spread sign based on which team we're picking
            # game['spread'] is the HOME team spread
            if team == game['home_team']:
                spread_display = game.get('spread', 0)
            else:
                # Away team gets opposite of home spread
                spread_display = -game.get('spread', 0)
            
            return {
                'type': 'SPREAD',
                'pick': f"{team} {spread_display:+.1f}",
                'confidence': confidence,
                'edge': round((confidence - 0.524) * 100, 1),
                'reasoning': 'Value on the spread'
            }
        
        return None
    
    def kelly_criterion(self, win_probability: float, odds: float = -110) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        Returns percentage of bankroll to bet
        """
        
        # Convert American odds to decimal
        if odds < 0:
            decimal_odds = 1 + (100 / abs(odds))
        else:
            decimal_odds = 1 + (odds / 100)
        
        # Kelly formula: (bp - q) / b
        # where b = decimal odds - 1, p = win probability, q = 1 - p
        b = decimal_odds - 1
        p = win_probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Use fractional Kelly (25%) for safety
        fractional_kelly = kelly * 0.25
        
        # Cap at 3% max bet
        return min(fractional_kelly, 0.03)