#!/usr/bin/env python3
"""
Test the COMPLETE system with enhanced data fetching
"""

from app.services.enhanced_data_fetcher import EnhancedDataFetcher
from app.services.complete_analyzer import CompleteAnalyzer

print("=== TESTING ENHANCED DATA SYSTEM ===\n")

# Test enhanced fetcher
fetcher = EnhancedDataFetcher()

# Test injury data
print("1. INJURY REPORTS:")
print("-" * 40)
teams = ["Kansas City Chiefs", "Buffalo Bills", "Dallas Cowboys"]
for team in teams:
    injuries = fetcher.get_injury_report(team)
    print(f"{team}:")
    print(f"  Out: {injuries['out']}")
    print(f"  Questionable: {injuries['questionable']}")
    print(f"  Impact: {injuries['impact_score']}")
    print(f"  Source: {injuries['source']}")
    print()

# Test public betting
print("\n2. PUBLIC BETTING CONSENSUS:")
print("-" * 40)
games = [
    ("Buffalo Bills", "Kansas City Chiefs"),
    ("Dallas Cowboys", "Philadelphia Eagles"),
    ("Green Bay Packers", "Chicago Bears")
]

for away, home in games:
    public = fetcher.get_public_betting_consensus(away, home)
    print(f"{away} @ {home}:")
    print(f"  Home: {public['home_percentage']}%")
    print(f"  Away: {public['away_percentage']}%")
    print(f"  Confidence: {public['confidence']}")
    print(f"  Total Bets: {public.get('total_bets', 'N/A')}")
    print()

# Test complete analyzer
print("\n3. COMPLETE GAME ANALYSIS:")
print("-" * 40)

analyzer = CompleteAnalyzer()

# Sample game with bookmaker data
game = {
    'home_team': 'Kansas City Chiefs',
    'away_team': 'Buffalo Bills',
    'spread': -3.5,
    'total': 48.5,
    'sharp_action': True,
    'reverse_line_movement': True,
    'bookmakers': [
        {
            'key': 'draftkings',
            'markets': [
                {'key': 'spreads', 'outcomes': [
                    {'name': 'Kansas City Chiefs', 'point': -3.5},
                    {'name': 'Buffalo Bills', 'point': 3.5}
                ]},
                {'key': 'totals', 'outcomes': [
                    {'name': 'Over', 'point': 48.5},
                    {'name': 'Under', 'point': 48.5}
                ]}
            ]
        },
        {
            'key': 'fanduel',
            'markets': [
                {'key': 'spreads', 'outcomes': [
                    {'name': 'Kansas City Chiefs', 'point': -3.0},
                    {'name': 'Buffalo Bills', 'point': 3.0}
                ]},
                {'key': 'totals', 'outcomes': [
                    {'name': 'Over', 'point': 49.0},
                    {'name': 'Under', 'point': 49.0}
                ]}
            ]
        },
        {
            'key': 'betmgm',
            'markets': [
                {'key': 'spreads', 'outcomes': [
                    {'name': 'Kansas City Chiefs', 'point': -4.0},
                    {'name': 'Buffalo Bills', 'point': 4.0}
                ]}
            ]
        }
    ]
}

analysis = analyzer.analyze_game_complete(game)

print(f"Game: {analysis['game']}")
print(f"Confidence: {analysis['final_confidence']:.1%}")
print(f"\nFactors:")
for factor in analysis['factors']:
    print(f"  • {factor}")

print(f"\nInsights:")
for insight in analysis['insights'][:5]:
    print(f"  • {insight}")

# Check public betting
if 'public_betting' in analysis:
    pb = analysis['public_betting']
    print(f"\nPublic Betting:")
    print(f"  Home: {pb.get('home_percentage')}%")
    print(f"  Away: {pb.get('away_percentage')}%")
    print(f"  Sources: {pb.get('sources_count')}")

# Check injuries
injury_factors = [f for f in analysis['factors'] if 'Injur' in f]
if injury_factors:
    print(f"\nInjury Impact: {injury_factors[0]}")

print("\n✅ Complete system test finished!")
print("=" * 50)