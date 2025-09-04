#!/usr/bin/env python3
"""Direct test of weather in the complete flow"""

from app.services.complete_analyzer import CompleteAnalyzer
from app.routers.nfl import load_games_data
import json

print("=== TESTING WEATHER IN COMPLETE FLOW ===\n")

# Get some real games
games = load_games_data()[:3]  # First 3 games
analyzer = CompleteAnalyzer()

for i, game in enumerate(games):
    print(f"\nGame {i+1}: {game.get('away_team')} @ {game.get('home_team')}")
    print(f"  Home team: {game.get('home_team')}")
    
    # Run complete analysis
    analysis = analyzer.analyze_game_complete(game)
    
    # Check weather
    if 'weather' in analysis:
        weather = analysis['weather']
        print(f"  ✅ Weather data present:")
        print(f"     Temperature: {weather.get('temperature')}°F")
        print(f"     Wind: {weather.get('wind_speed')} mph")
        print(f"     Description: {weather.get('description')}")
    else:
        print(f"  ❌ NO WEATHER DATA IN ANALYSIS!")
    
    # Build the game object like the router does
    analyzed_game = {
        "home_team": game.get("home_team"),
        "away_team": game.get("away_team"),
        "spread": game.get("spread", 0),
        "confidence": analysis['final_confidence']
    }
    
    # Add weather if present (like router does)
    weather_obj = analysis.get('weather')
    if weather_obj:
        analyzed_game["weather"] = weather_obj
        print(f"  ✅ Weather would be sent to frontend")
    else:
        print(f"  ❌ No weather would be sent to frontend")

print("\n" + "="*50)
print("SUMMARY: Weather should be included in all games!")
print("="*50)