"""
SEAN PICKS - Weather Impact Tracker
Weather is HUGE for totals and scoring
"""

import requests
from datetime import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import WEATHER_API_KEY

class WeatherTracker:
    """Gets weather data and calculates impact on games"""
    
    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        
        # Stadium locations
        self.stadiums = {
            'Buffalo Bills': {'city': 'Orchard Park,NY', 'type': 'outdoor'},
            'Miami Dolphins': {'city': 'Miami Gardens,FL', 'type': 'outdoor'},
            'New England Patriots': {'city': 'Foxborough,MA', 'type': 'outdoor'},
            'New York Jets': {'city': 'East Rutherford,NJ', 'type': 'outdoor'},
            'Baltimore Ravens': {'city': 'Baltimore,MD', 'type': 'outdoor'},
            'Cincinnati Bengals': {'city': 'Cincinnati,OH', 'type': 'outdoor'},
            'Cleveland Browns': {'city': 'Cleveland,OH', 'type': 'outdoor'},
            'Pittsburgh Steelers': {'city': 'Pittsburgh,PA', 'type': 'outdoor'},
            'Houston Texans': {'city': 'Houston,TX', 'type': 'retractable'},
            'Indianapolis Colts': {'city': 'Indianapolis,IN', 'type': 'retractable'},
            'Jacksonville Jaguars': {'city': 'Jacksonville,FL', 'type': 'outdoor'},
            'Tennessee Titans': {'city': 'Nashville,TN', 'type': 'outdoor'},
            'Denver Broncos': {'city': 'Denver,CO', 'type': 'outdoor'},
            'Kansas City Chiefs': {'city': 'Kansas City,MO', 'type': 'outdoor'},
            'Las Vegas Raiders': {'city': 'Las Vegas,NV', 'type': 'dome'},
            'Los Angeles Chargers': {'city': 'Inglewood,CA', 'type': 'dome'},
            'Dallas Cowboys': {'city': 'Arlington,TX', 'type': 'retractable'},
            'New York Giants': {'city': 'East Rutherford,NJ', 'type': 'outdoor'},
            'Philadelphia Eagles': {'city': 'Philadelphia,PA', 'type': 'outdoor'},
            'Washington Commanders': {'city': 'Landover,MD', 'type': 'outdoor'},
            'Chicago Bears': {'city': 'Chicago,IL', 'type': 'outdoor'},
            'Detroit Lions': {'city': 'Detroit,MI', 'type': 'dome'},
            'Green Bay Packers': {'city': 'Green Bay,WI', 'type': 'outdoor'},
            'Minnesota Vikings': {'city': 'Minneapolis,MN', 'type': 'dome'},
            'Atlanta Falcons': {'city': 'Atlanta,GA', 'type': 'retractable'},
            'Carolina Panthers': {'city': 'Charlotte,NC', 'type': 'outdoor'},
            'New Orleans Saints': {'city': 'New Orleans,LA', 'type': 'dome'},
            'Tampa Bay Buccaneers': {'city': 'Tampa,FL', 'type': 'outdoor'},
            'Arizona Cardinals': {'city': 'Glendale,AZ', 'type': 'retractable'},
            'Los Angeles Rams': {'city': 'Inglewood,CA', 'type': 'dome'},
            'San Francisco 49ers': {'city': 'Santa Clara,CA', 'type': 'outdoor'},
            'Seattle Seahawks': {'city': 'Seattle,WA', 'type': 'outdoor'},
        }
        
        # Weather impact on scoring
        self.weather_impacts = {
            'wind': {
                10: -1.0,   # 10+ mph = -1 point total
                15: -3.5,   # 15+ mph = -3.5 points
                20: -7.0,   # 20+ mph = -7 points
                25: -10.0,  # 25+ mph = -10 points
            },
            'temp': {
                32: -3.0,   # Below freezing = -3 points
                20: -5.0,   # Below 20F = -5 points
                10: -7.0,   # Below 10F = -7 points
                95: -2.0,   # Above 95F = -2 points
            },
            'precipitation': {
                'rain': -2.5,      # Rain = -2.5 points
                'snow': -5.0,      # Snow = -5 points
                'heavy_rain': -5.0, # Heavy rain = -5 points
                'freezing': -7.0,   # Freezing rain = -7 points
            }
        }
    
    def get_game_weather(self, home_team, game_time=None):
        """Get weather for a specific game"""
        
        if home_team not in self.stadiums:
            return None
        
        stadium = self.stadiums[home_team]
        
        # Dome/retractable = no weather impact
        if stadium['type'] == 'dome':
            return {
                'temperature': 72,
                'wind_speed': 0,
                'precipitation': None,
                'conditions': 'Dome',
                'impact_total': 0,
                'impact_passing': 0,
                'under_boost': 0
            }
        
        # Get weather data - fix city format (remove state abbreviation with comma)
        city = stadium['city']
        # Convert "Miami Gardens,FL" to "Miami Gardens" (API doesn't like comma+state format)
        if ',' in city:
            city = city.split(',')[0]  # Just use city name without state
        
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'imperial'  # Fahrenheit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                weather = {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'wind_speed': data['wind']['speed'],
                    'wind_gust': data['wind'].get('gust', data['wind']['speed']),
                    'precipitation': self.get_precipitation_type(data),
                    'conditions': data['weather'][0]['main'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity']
                }
                
                # Calculate impacts
                impacts = self.calculate_weather_impact(weather)
                weather.update(impacts)
                
                return weather
            else:
                print(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting weather: {e}")
            return None
    
    def get_precipitation_type(self, data):
        """Determine precipitation type from weather data"""
        
        weather_id = data['weather'][0]['id']
        
        # Weather codes: https://openweathermap.org/weather-conditions
        if 200 <= weather_id <= 232:  # Thunderstorm
            return 'heavy_rain'
        elif 300 <= weather_id <= 321:  # Drizzle
            return 'rain'
        elif 500 <= weather_id <= 531:  # Rain
            if weather_id >= 502:
                return 'heavy_rain'
            return 'rain'
        elif 600 <= weather_id <= 622:  # Snow
            return 'snow'
        elif weather_id == 511:  # Freezing rain
            return 'freezing'
        else:
            return None
    
    def calculate_weather_impact(self, weather):
        """Calculate impact on totals and game play"""
        
        total_impact = 0
        passing_impact = 0
        under_confidence_boost = 0
        factors = []
        
        # Wind impact
        wind = weather['wind_speed']
        for threshold, impact in sorted(self.weather_impacts['wind'].items(), reverse=True):
            if wind >= threshold:
                total_impact += impact
                passing_impact += impact * 1.5  # Wind affects passing more
                under_confidence_boost += 0.03 if threshold >= 15 else 0.01
                factors.append(f"Wind {wind:.0f}mph")
                break
        
        # Temperature impact
        temp = weather['temperature']
        if temp <= 32:
            total_impact += -3.0
            under_confidence_boost += 0.02
            factors.append(f"Freezing {temp:.0f}°F")
        elif temp <= 20:
            total_impact += -5.0
            under_confidence_boost += 0.03
            factors.append(f"Extreme cold {temp:.0f}°F")
        elif temp >= 95:
            total_impact += -2.0
            factors.append(f"Extreme heat {temp:.0f}°F")
        
        # Precipitation impact
        precip = weather.get('precipitation')
        if precip:
            impact = self.weather_impacts['precipitation'].get(precip, 0)
            total_impact += impact
            passing_impact += impact * 0.7
            under_confidence_boost += .02 if impact <= -3 else 0.01
            factors.append(f"{precip.replace('_', ' ').title()}")
        
        return {
            'impact_total': round(total_impact, 1),
            'impact_passing': round(passing_impact, 1),
            'under_boost': min(under_confidence_boost, 0.10),  # Cap at 10%
            'weather_factors': factors,
            'extreme_weather': len(factors) >= 2 or total_impact <= -5
        }
    
    def get_historical_trends(self, conditions):
        """Historical performance in specific weather"""
        
        trends = {
            'wind_15plus': {
                'under_rate': 0.61,
                'home_advantage': 0.02,
                'description': 'Unders hit 61% with 15+ mph wind'
            },
            'snow_game': {
                'under_rate': 0.64,
                'home_advantage': 0.05,
                'description': 'Unders hit 64% in snow'
            },
            'freezing': {
                'under_rate': 0.58,
                'home_advantage': 0.03,
                'description': 'Unders hit 58% below 32°F'
            },
            'dome_team_outdoor': {
                'visitor_disadvantage': -0.03,
                'description': 'Dome teams struggle outdoors'
            },
            'extreme_heat': {
                'under_rate': 0.54,
                'description': 'Slight under tendency in 95°F+'
            }
        }
        
        applicable_trends = []
        
        if conditions.get('wind_speed', 0) >= 15:
            applicable_trends.append(trends['wind_15plus'])
        
        if conditions.get('precipitation') == 'snow':
            applicable_trends.append(trends['snow_game'])
        
        if conditions.get('temperature', 70) <= 32:
            applicable_trends.append(trends['freezing'])
        
        return applicable_trends
    
    def wind_adjusted_props(self, wind_speed):
        """Adjust player props for wind"""
        
        adjustments = {
            'passing_yards': 0,
            'passing_tds': 0,
            'field_goals': 0,
            'punt_distance': 0
        }
        
        if wind_speed >= 20:
            adjustments['passing_yards'] = -40  # -40 yards
            adjustments['passing_tds'] = -0.5   # -0.5 TDs
            adjustments['field_goals'] = -0.25  # 25% less likely
            adjustments['punt_distance'] = -10  # -10 yards
        elif wind_speed >= 15:
            adjustments['passing_yards'] = -25
            adjustments['passing_tds'] = -0.3
            adjustments['field_goals'] = -0.15
            adjustments['punt_distance'] = -7
        elif wind_speed >= 10:
            adjustments['passing_yards'] = -15
            adjustments['passing_tds'] = -0.1
            adjustments['field_goals'] = -0.05
            adjustments['punt_distance'] = -3
        
        return adjustments


class WeatherAlert:
    """Monitor for extreme weather that creates betting value"""
    
    def __init__(self):
        self.alert_thresholds = {
            'wind': 18,         # 18+ mph wind
            'temp_cold': 25,    # Below 25°F
            'temp_hot': 95,     # Above 95°F
            'snow': True,       # Any snow
            'heavy_rain': True  # Heavy rain
        }
    
    def check_for_alerts(self, weather_data):
        """Check if weather creates a strong betting opportunity"""
        
        alerts = []
        
        if weather_data['wind_speed'] >= self.alert_thresholds['wind']:
            alerts.append({
                'type': 'HIGH_WIND',
                'message': f"Wind {weather_data['wind_speed']:.0f}mph - Strong UNDER play",
                'confidence_boost': 0.05,
                'bet_type': 'UNDER'
            })
        
        if weather_data['temperature'] <= self.alert_thresholds['temp_cold']:
            alerts.append({
                'type': 'EXTREME_COLD',
                'message': f"Temperature {weather_data['temperature']:.0f}°F - Favor UNDER",
                'confidence_boost': 0.03,
                'bet_type': 'UNDER'
            })
        
        if weather_data.get('precipitation') == 'snow':
            alerts.append({
                'type': 'SNOW_GAME',
                'message': "Snow game - Heavy UNDER lean",
                'confidence_boost': 0.06,
                'bet_type': 'UNDER'
            })
        
        return alerts


if __name__ == "__main__":
    print("=" * 60)
    print(" WEATHER IMPACT TRACKER")
    print("=" * 60)
    
    tracker = WeatherTracker()
    
    print("\n🏟️ Testing weather for different stadiums:")
    
    # Test outdoor cold weather team
    print("\n❄️ Green Bay Packers (Lambeau Field):")
    weather = tracker.get_game_weather("Green Bay Packers")
    if weather:
        print(f"  Temperature: {weather['temperature']:.0f}°F")
        print(f"  Wind: {weather['wind_speed']:.0f} mph")
        print(f"  Total Impact: {weather['impact_total']} points")
        print(f"  Under Boost: {weather['under_boost']*100:.0f}%")
    
    # Test dome team
    print("\n🏟️ Detroit Lions (Ford Field - Dome):")
    weather = tracker.get_game_weather("Detroit Lions")
    if weather:
        print(f"  Conditions: {weather['conditions']}")
        print(f"  Total Impact: {weather['impact_total']} points")
    
    # Test warm weather team
    print("\n☀️ Miami Dolphins (Hard Rock Stadium):")
    weather = tracker.get_game_weather("Miami Dolphins")
    if weather:
        print(f"  Temperature: {weather['temperature']:.0f}°F")
        print(f"  Wind: {weather['wind_speed']:.0f} mph")
        print(f"  Total Impact: {weather['impact_total']} points")
    
    print("\n💡 How to use:")
    print("1. Call get_game_weather() with home team")
    print("2. Add impact_total to your total prediction")
    print("3. Add under_boost to confidence for unders")
    print("4. Check extreme_weather flag for alerts")