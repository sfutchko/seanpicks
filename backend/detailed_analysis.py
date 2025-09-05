#!/usr/bin/env python3
"""
Detailed analysis of the Kansas City Royals game mentioned as an example
"""

import sqlite3

def analyze_royals_game():
    """
    Analyze the specific Kansas City Royals game mentioned
    """
    conn = sqlite3.connect('/Users/sean/Downloads/sean-picks-app/backend/seanpicks.db')
    cursor = conn.cursor()
    
    # Get the specific game
    cursor.execute("""
        SELECT 
            id, home_team, away_team, game_time, pick, 
            home_score, away_score, result, sport,
            confidence, spread, actual_spread
        FROM tracked_bets 
        WHERE home_team LIKE '%Royals%' 
        AND away_team LIKE '%Angels%'
    """)
    
    bet = cursor.fetchone()
    
    if bet:
        bet_id, home_team, away_team, game_time, pick, home_score, away_score, result, sport, confidence, spread, actual_spread = bet
        
        print("DETAILED ANALYSIS: Los Angeles Angels @ Kansas City Royals")
        print("=" * 60)
        print(f"Game ID: {bet_id}")
        print(f"Teams: {away_team} @ {home_team}")
        print(f"Game Time: {game_time}")
        print(f"Pick: {pick}")
        print(f"Stored Score: Away={away_score}, Home={home_score}")
        print(f"Score Display: {away_score}-{home_score}")
        print(f"Result: {result}")
        print(f"Actual Spread: {actual_spread}")
        print()
        
        print("ANALYSIS:")
        print(f"- Format is 'Away @ Home': {away_team} @ {home_team}")
        print(f"- Score format should be 'Away-Home': {away_score}-{home_score}")
        print(f"- Away team (Angels) scored: {away_score}")
        print(f"- Home team (Royals) scored: {home_score}")
        print(f"- Winner: {'Angels' if away_score > home_score else 'Royals' if home_score > away_score else 'Tie'}")
        print(f"- Pick was: {pick}")
        print(f"- Result was: {result}")
        print()
        
        # Check if result is correct
        if 'ML' in pick:
            pick_team = pick.replace(' ML', '').strip()
            
            if away_score > home_score:
                winner = away_team
                should_win = pick_team == away_team or any(word in away_team for word in pick_team.split())
            elif home_score > away_score:
                winner = home_team
                should_win = pick_team == home_team or any(word in home_team for word in pick_team.split())
            else:
                winner = "Tie"
                should_win = False
            
            expected_result = 'WIN' if should_win else 'LOSS'
            
            print(f"VERIFICATION:")
            print(f"- Game winner: {winner}")
            print(f"- Pick team: {pick_team}")
            print(f"- Expected result: {expected_result}")
            print(f"- Actual result: {result}")
            
            if expected_result == result:
                print("✅ Result is CORRECT - no score reversal detected")
            else:
                print("⚠️  Result is INCORRECT - possible score reversal!")
                print(f"    If scores were reversed ({home_score}-{away_score}):")
                print(f"    Winner would be: {'Royals' if home_score > away_score else 'Angels'}")
                print(f"    Result would be: {'WIN' if (home_score > away_score and 'Royals' in pick_team) or (away_score > home_score and 'Angels' in pick_team) else 'LOSS'}")
    
    conn.close()

def check_all_suspicious_patterns():
    """
    Check for patterns that might indicate score reversal across all games
    """
    conn = sqlite3.connect('/Users/sean/Downloads/sean-picks-app/backend/seanpicks.db')
    cursor = conn.cursor()
    
    print("\n\nCOMPREHENSIVE PATTERN ANALYSIS")
    print("=" * 60)
    
    # Get all completed bets
    cursor.execute("""
        SELECT 
            home_team, away_team, game_time, pick, 
            home_score, away_score, result, sport
        FROM tracked_bets 
        WHERE result IN ('WIN', 'LOSS', 'PUSH')
        ORDER BY game_time DESC
    """)
    
    bets = cursor.fetchall()
    issues = []
    
    for bet in bets:
        home_team, away_team, game_time, pick, home_score, away_score, result, sport = bet
        
        if home_score is None or away_score is None or not pick:
            continue
        
        # Analyze moneyline bets
        if ' ML' in pick:
            pick_team = pick.replace(' ML', '').strip()
            
            # Determine actual winner
            if away_score > home_score:
                actual_winner = away_team
            elif home_score > away_score:
                actual_winner = home_team
            else:
                continue  # Skip ties
            
            # Check if pick team matches
            pick_is_home = (pick_team == home_team or 
                           any(word in home_team for word in pick_team.split()) or
                           any(word in pick_team for word in home_team.split()))
            pick_is_away = (pick_team == away_team or 
                           any(word in away_team for word in pick_team.split()) or
                           any(word in pick_team for word in away_team.split()))
            
            if pick_is_home:
                expected = 'WIN' if home_score > away_score else 'LOSS'
            elif pick_is_away:
                expected = 'WIN' if away_score > home_score else 'LOSS'
            else:
                continue  # Can't match team
            
            if expected != result:
                issues.append({
                    'game': f"{away_team} @ {home_team}",
                    'score': f"{away_score}-{home_score}",
                    'pick': pick,
                    'result': result,
                    'expected': expected,
                    'issue': 'Result mismatch'
                })
    
    print(f"Found {len(issues)} games with result mismatches:")
    for issue in issues:
        print(f"  {issue['game']}")
        print(f"    Score: {issue['score']}")
        print(f"    Pick: {issue['pick']}")
        print(f"    Result: {issue['result']} (Expected: {issue['expected']})")
        print(f"    Issue: {issue['issue']}")
        print()
    
    conn.close()

if __name__ == "__main__":
    analyze_royals_game()
    check_all_suspicious_patterns()