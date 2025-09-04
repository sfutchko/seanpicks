#!/usr/bin/env python3
"""Test that weather is included in API response"""

import requests
import json

# First register/login
login_data = {
    "username": "weather_test@example.com",
    "password": "test123"
}

# Try to register first
reg_data = {
    "email": "weather_test@example.com",
    "username": "weather_test",
    "password": "test123",
    "full_name": "Weather Test"
}

print("Attempting registration...")
reg_resp = requests.post("http://localhost:8001/api/auth/register", json=reg_data)
if reg_resp.status_code == 200:
    print("✅ User registered")
else:
    print("User may already exist, trying login...")

# Login
print("\nLogging in...")
login_resp = requests.post(
    "http://localhost:8001/api/auth/login",
    data={"username": "weather_test@example.com", "password": "test123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if login_resp.status_code != 200:
    print(f"❌ Login failed: {login_resp.json()}")
    exit(1)

token = login_resp.json()["access_token"]
print(f"✅ Got token: {token[:20]}...")

# Get games
print("\nFetching NFL games...")
games_resp = requests.get(
    "http://localhost:8001/api/nfl/games",
    headers={"Authorization": f"Bearer {token}"}
)

if games_resp.status_code != 200:
    print(f"❌ Failed to get games: {games_resp.json()}")
    exit(1)

data = games_resp.json()
print(f"✅ Got {len(data.get('games', []))} games")

# Check weather in games
print("\n=== WEATHER DATA IN GAMES ===")
for i, game in enumerate(data.get('games', [])[:5]):  # First 5 games
    weather = game.get('weather', {})
    print(f"\nGame {i+1}: {game.get('away_team')} @ {game.get('home_team')}")
    if weather:
        print(f"  Temperature: {weather.get('temperature')}°F")
        print(f"  Wind: {weather.get('wind_speed')} mph")
        print(f"  Description: {weather.get('description')}")
    else:
        print("  ⚠️ NO WEATHER DATA!")

# Check if best bets have weather
print("\n=== WEATHER IN BEST BETS ===")
for i, bet in enumerate(data.get('best_bets', [])[:3]):
    weather = bet.get('weather', {})
    print(f"\nBest Bet {i+1}: {bet.get('pick')}")
    if weather:
        print(f"  Weather: {weather.get('temperature')}°F, {weather.get('description')}")
    else:
        print("  ⚠️ NO WEATHER!")

print("\n✅ Test complete!")