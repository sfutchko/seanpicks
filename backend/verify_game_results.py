#!/usr/bin/env python3
"""
Verify game results by analyzing the actual API data
"""

import json

# API data from the tracking results
api_data = [
    {
        "game": "San Francisco Giants @ Colorado Rockies",
        "pick": "San Francisco Giants ML",
        "spread": -2.5,
        "confidence": 58.4,
        "result": "WIN",
        "score": "7-4",
        "actual_spread": -3.0,
        "game_time": "2025-09-04T00:40:00",
        "sport": "mlb"
    },
    {
        "game": "Los Angeles Angels @ Kansas City Royals",
        "pick": "Kansas City Royals ML",
        "spread": -1.5,
        "confidence": 57.0,
        "result": "LOSS",
        "score": "5-1",
        "actual_spread": -4.0,
        "game_time": "2025-09-03T23:40:00",
        "sport": "mlb"
    },
    {
        "game": "Atlanta Braves @ Chicago Cubs",
        "pick": "Chicago Cubs ML",
        "spread": -1.5,
        "confidence": 56.9,
        "result": "WIN",
        "score": "3-4",
        "actual_spread": 1.0,
        "game_time": "2025-09-03T23:40:00",
        "sport": "mlb"
    },
    {
        "game": "Philadelphia Phillies @ Milwaukee Brewers",
        "pick": "Milwaukee Brewers ML",
        "spread": -1.5,
        "confidence": 56.6,
        "result": "WIN",
        "score": "3-6",
        "actual_spread": 3.0,
        "game_time": "2025-09-03T23:40:00",
        "sport": "mlb"
    },
    {
        "game": "Toronto Blue Jays @ Cincinnati Reds",
        "pick": "Toronto Blue Jays +1.5",
        "spread": -1.5,
        "confidence": 55.0,
        "result": "WIN",
        "score": "12-9",
        "actual_spread": -3.0,
        "game_time": "2025-09-03T22:40:00",
        "sport": "mlb"
    }
]

def verify_game_results():
    """
    Verify each game result for accuracy
    """
    print("GAME RESULTS VERIFICATION")
    print("=" * 60)
    
    issues_found = []
    
    for game in api_data:
        print(f"\nGame: {game['game']}")
        print(f"Score: {game['score']} (Away-Home format)")
        print(f"Pick: {game['pick']}")
        print(f"Result: {game['result']}")
        print(f"Actual Spread: {game['actual_spread']} (Home - Away)")
        
        # Parse game and score
        teams = game['game'].split(' @ ')
        away_team = teams[0]
        home_team = teams[1]
        
        score_parts = game['score'].split('-')
        away_score = int(score_parts[0])
        home_score = int(score_parts[1])
        
        print(f"Away Team: {away_team} (scored {away_score})")
        print(f"Home Team: {home_team} (scored {home_score})")
        
        # Verify actual spread calculation
        calculated_spread = home_score - away_score
        print(f"Calculated Spread: {calculated_spread} (Home - Away)")
        
        if abs(calculated_spread - game['actual_spread']) > 0.01:
            print(f"⚠️  SPREAD MISMATCH: Calculated {calculated_spread}, API shows {game['actual_spread']}")
            issues_found.append({
                'game': game['game'],
                'issue': 'Spread calculation mismatch',
                'calculated': calculated_spread,
                'api': game['actual_spread']
            })
        
        # Verify result for ML bets
        if ' ML' in game['pick']:
            pick_team = game['pick'].replace(' ML', '').strip()
            
            # Determine actual winner
            if away_score > home_score:
                actual_winner = away_team
            elif home_score > away_score:
                actual_winner = home_team
            else:
                actual_winner = "TIE"
            
            print(f"Actual Winner: {actual_winner}")
            print(f"Pick Team: {pick_team}")
            
            # Check if result is correct
            if actual_winner == pick_team:
                expected_result = "WIN"
            elif actual_winner == "TIE":
                expected_result = "PUSH"
            else:
                expected_result = "LOSS"
            
            print(f"Expected Result: {expected_result}")
            
            if expected_result != game['result']:
                print(f"⚠️  RESULT MISMATCH: Expected {expected_result}, API shows {game['result']}")
                issues_found.append({
                    'game': game['game'],
                    'issue': 'Result mismatch',
                    'expected': expected_result,
                    'api': game['result'],
                    'pick': game['pick'],
                    'actual_winner': actual_winner
                })
            else:
                print("✅ Result is correct")
        
        # Verify result for spread bets
        elif '+' in game['pick'] or '-' in game['pick']:
            # Extract spread from pick
            pick_parts = game['pick'].rsplit(' ', 1)
            pick_team = pick_parts[0]
            pick_spread = float(pick_parts[1])
            
            print(f"Pick Team: {pick_team}")
            print(f"Pick Spread: {pick_spread}")
            
            # Determine if bet covered
            if pick_team == home_team:
                # Picked home team
                covered = calculated_spread + pick_spread > 0
            elif pick_team == away_team:
                # Picked away team
                covered = -calculated_spread + pick_spread > 0
            else:
                print(f"⚠️  Could not match pick team '{pick_team}'")
                continue
            
            # Check for push
            if abs(calculated_spread + pick_spread) < 0.01:
                expected_result = "PUSH"
            elif covered:
                expected_result = "WIN"
            else:
                expected_result = "LOSS"
            
            print(f"Expected Result: {expected_result}")
            
            if expected_result != game['result']:
                print(f"⚠️  RESULT MISMATCH: Expected {expected_result}, API shows {game['result']}")
                issues_found.append({
                    'game': game['game'],
                    'issue': 'Spread result mismatch',
                    'expected': expected_result,
                    'api': game['result'],
                    'pick': game['pick'],
                    'covered': covered
                })
            else:
                print("✅ Result is correct")
        
        print("-" * 40)
    
    print(f"\nSUMMARY:")
    print(f"Games analyzed: {len(api_data)}")
    print(f"Issues found: {len(issues_found)}")
    
    if issues_found:
        print("\nISSUES DETECTED:")
        for issue in issues_found:
            print(f"  {issue['game']}: {issue['issue']}")
            for key, value in issue.items():
                if key not in ['game', 'issue']:
                    print(f"    {key}: {value}")
    else:
        print("\n✅ All game results appear to be correct!")
        print("No score reversals or result mismatches detected.")

if __name__ == "__main__":
    verify_game_results()