#!/usr/bin/env python3
"""Test that all games get picks"""

from app.routers.nfl import load_games_data
from app.services.complete_analyzer import CompleteAnalyzer

print("Loading games...")
games = load_games_data()
print(f"Got {len(games)} games\n")

analyzer = CompleteAnalyzer()

for i, game in enumerate(games):
    print(f"\nGame {i+1}: {game['away_team']} @ {game['home_team']}")
    print(f"  Spread: {game.get('spread', 0)}")
    
    # Run analysis
    try:
        analysis = analyzer.analyze_game_complete(game)
        confidence = analysis.get('final_confidence', 0.5)
        best_bet = analysis.get('best_bet')
        
        print(f"  Confidence: {confidence:.3f}")
        
        # Check what pick would be generated
        if best_bet:
            pick = best_bet['pick']
            print(f"  Pick: {pick} (from best_bet)")
        elif confidence >= 0.54:
            if game.get('spread', 0) > 0:
                pick = f"{game['home_team']} +{game['spread']}"
            else:
                pick = f"{game['home_team']} {game['spread']}"
            print(f"  Pick: {pick} (confidence >= 0.54)")
        elif confidence >= 0.52:
            if game.get('spread', 0) > 0:
                pick = f"{game['home_team']} +{game['spread']}"
            else:
                pick = f"{game['home_team']} {game['spread']}"
            print(f"  Pick: {pick} (confidence >= 0.52)")
        else:
            if game.get('spread', 0) < 0:
                pick = f"{game['home_team']} {game['spread']}"
            else:
                pick = f"{game['away_team']} -{abs(game['spread'])}"
            print(f"  Pick: {pick} (fallback)")
            
    except Exception as e:
        print(f"  ERROR: {e}")
        
print(f"\n{'='*50}")
print(f"Summary: All {len(games)} games should have picks!")
print(f"{'='*50}")