#!/usr/bin/env python3
"""
Test script to verify REAL data scraping is working
"""

from app.services.real_data_scraper import RealDataScraper
from app.services.complete_analyzer import CompleteAnalyzer

# Test injury scraping
print("\n=== TESTING REAL INJURY DATA ===")
scraper = RealDataScraper()

teams_to_test = ["Kansas City Chiefs", "Buffalo Bills", "Dallas Cowboys", "Philadelphia Eagles"]

for team in teams_to_test:
    print(f"\n{team}:")
    injuries = scraper.get_nfl_injuries(team)
    print(f"  Out: {injuries.get('out', [])[:3]}")  # Show first 3
    print(f"  Questionable: {injuries.get('questionable', [])[:3]}")
    print(f"  Impact Score: {injuries.get('impact_score', 0)}")

# Test public betting
print("\n\n=== TESTING REAL PUBLIC BETTING DATA ===")
games_to_test = [
    ("Buffalo Bills", "Miami Dolphins"),
    ("Kansas City Chiefs", "Cincinnati Bengals"),
    ("Dallas Cowboys", "Philadelphia Eagles")
]

for away, home in games_to_test:
    print(f"\n{away} @ {home}:")
    public_data = scraper.get_all_public_betting(away, home)
    print(f"  Home %: {public_data.get('home_percentage')}%")
    print(f"  Away %: {public_data.get('away_percentage')}%")
    print(f"  Sources: {public_data.get('sources', [])}")
    print(f"  Confidence: {public_data.get('confidence')}")

# Test complete analyzer with a sample game
print("\n\n=== TESTING COMPLETE ANALYZER WITH REAL DATA ===")
analyzer = CompleteAnalyzer()

sample_game = {
    'home_team': 'Kansas City Chiefs',
    'away_team': 'Buffalo Bills',
    'spread': -3.5,
    'total': 48.5,
    'bookmakers': [
        {
            'key': 'draftkings',
            'markets': [
                {
                    'key': 'spreads',
                    'outcomes': [
                        {'name': 'Kansas City Chiefs', 'point': -3.5},
                        {'name': 'Buffalo Bills', 'point': 3.5}
                    ]
                }
            ]
        },
        {
            'key': 'fanduel',
            'markets': [
                {
                    'key': 'spreads',
                    'outcomes': [
                        {'name': 'Kansas City Chiefs', 'point': -3.0},
                        {'name': 'Buffalo Bills', 'point': 3.0}
                    ]
                }
            ]
        }
    ]
}

analysis = analyzer.analyze_game_complete(sample_game)
print(f"\nGame: {analysis['game']}")
print(f"Final Confidence: {analysis['final_confidence']:.1%}")
print(f"Factors: {analysis.get('factors', [])}")
print(f"Insights: {analysis.get('insights', [])[:3]}")  # First 3 insights

# Check if injuries are being factored in
if 'injuries' in analysis:
    print(f"\nInjury Impact: {analysis['injuries'].get('net_impact', 0)}")
    print(f"Injury Boost: {analysis['injuries'].get('boost', 0):.1%}")

print("\n✅ Test complete!")