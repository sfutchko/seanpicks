#!/usr/bin/env python3
"""Test weather functionality"""

from app.services.complete_analyzer import CompleteAnalyzer

analyzer = CompleteAnalyzer()

# Test different teams
teams = [
    "Kansas City Chiefs",  # Outdoor - cold
    "Buffalo Bills",       # Outdoor - cold
    "Dallas Cowboys",      # Dome
    "Las Vegas Raiders",   # Dome
    "Miami Dolphins",      # Outdoor - warm
    "Green Bay Packers",   # Outdoor - cold
    "New Orleans Saints",  # Dome
    "Seattle Seahawks"     # Outdoor - rainy
]

print("=== WEATHER TEST ===\n")

for team in teams:
    weather = analyzer.get_weather_impact(team)
    print(f"{team}:")
    print(f"  Temperature: {weather['temperature']}°F")
    print(f"  Wind: {weather['wind_speed']} mph")
    print(f"  Conditions: {weather.get('conditions', 'N/A')}")
    print(f"  Description: {weather.get('description', 'N/A')}")
    print(f"  Insight: {weather['insight']}")
    print()

print("\n=== COMPLETE GAME TEST ===\n")

# Test a full game
game = {
    'home_team': 'Kansas City Chiefs',
    'away_team': 'Buffalo Bills',
    'spread': -3.5,
    'total': 48.5
}

analysis = analyzer.analyze_game_complete(game)

if 'weather' in analysis:
    print(f"Weather data in analysis:")
    print(f"  Temperature: {analysis['weather'].get('temperature')}°F")
    print(f"  Wind: {analysis['weather'].get('wind_speed')} mph")
    print(f"  Description: {analysis['weather'].get('description')}")
else:
    print("⚠️ NO WEATHER DATA IN ANALYSIS!")

print("\nDone!")