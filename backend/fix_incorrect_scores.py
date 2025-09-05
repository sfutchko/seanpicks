#!/usr/bin/env python3
"""
Fix incorrect game scores in the database based on actual MLB results
"""

import sqlite3
from datetime import datetime

def fix_incorrect_scores():
    """
    Fix the incorrect scores found in the database
    """
    print("FIXING INCORRECT GAME SCORES")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('/Users/sean/Downloads/sean-picks-app/backend/seanpicks.db')
    cursor = conn.cursor()
    
    # Corrections based on actual game results from September 3, 2025
    corrections = [
        {
            'description': 'Los Angeles Angels @ Kansas City Royals',
            'home_team': 'Kansas City Royals',
            'away_team': 'Los Angeles Angels',
            'actual_away_score': 4,  # Angels scored 4
            'actual_home_score': 3,  # Royals scored 3
            'current_away_score': 5,
            'current_home_score': 1,
            'reason': 'Database shows 5-1, actual was 4-3'
        },
        {
            'description': 'Atlanta Braves @ Chicago Cubs',
            'home_team': 'Chicago Cubs',
            'away_team': 'Atlanta Braves', 
            'actual_away_score': 5,  # Braves scored 5
            'actual_home_score': 1,  # Cubs scored 1
            'current_away_score': 3,
            'current_home_score': 4,
            'reason': 'Database shows 3-4, actual was 5-1'
        }
        # Note: Philadelphia Phillies @ Milwaukee Brewers (3-6) appears correct
        # Note: Other games need verification but weren't clearly wrong in initial analysis
    ]
    
    total_fixed = 0
    
    for correction in corrections:
        print(f"\nProcessing: {correction['description']}")
        print(f"Current in DB: {correction['current_away_score']}-{correction['current_home_score']}")
        print(f"Actual result: {correction['actual_away_score']}-{correction['actual_home_score']}")
        print(f"Reason: {correction['reason']}")
        
        # Find the bet in the database
        cursor.execute("""
            SELECT id, home_team, away_team, home_score, away_score, pick, result
            FROM tracked_bets 
            WHERE home_team = ? AND away_team = ?
            AND home_score = ? AND away_score = ?
        """, (correction['home_team'], correction['away_team'], 
              correction['current_home_score'], correction['current_away_score']))
        
        bet = cursor.fetchone()
        
        if bet:
            bet_id, home_team, away_team, old_home_score, old_away_score, pick, old_result = bet
            
            # Update the scores
            new_home_score = correction['actual_home_score']
            new_away_score = correction['actual_away_score']
            new_actual_spread = new_home_score - new_away_score
            
            # Recalculate the result
            new_result = calculate_bet_result(pick, home_team, away_team, new_home_score, new_away_score)
            
            print(f"  Updating bet ID: {bet_id}")
            print(f"  Old scores: Away={old_away_score}, Home={old_home_score}")
            print(f"  New scores: Away={new_away_score}, Home={new_home_score}")
            print(f"  Old result: {old_result}")
            print(f"  New result: {new_result}")
            
            # Update the database
            cursor.execute("""
                UPDATE tracked_bets 
                SET home_score = ?, away_score = ?, actual_spread = ?, result = ?
                WHERE id = ?
            """, (new_home_score, new_away_score, new_actual_spread, new_result, bet_id))
            
            total_fixed += 1
            print(f"  ✅ Fixed!")
            
        else:
            print(f"  ⚠️  Could not find bet in database")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\n" + "="*50)
    print(f"SUMMARY: Fixed {total_fixed} incorrect scores")
    print("All corrections have been applied to the database.")

def calculate_bet_result(pick, home_team, away_team, home_score, away_score):
    """
    Calculate the correct bet result based on pick and final score
    """
    if not pick:
        return 'PENDING'
    
    if ' ML' in pick:
        # Moneyline bet
        pick_team = pick.replace(' ML', '').strip()
        
        if away_score > home_score:
            winner = away_team
        elif home_score > away_score:
            winner = home_team
        else:
            return 'PUSH'
        
        # Check if pick team matches winner
        if (pick_team == winner or 
            any(word in winner for word in pick_team.split()) or
            any(word in pick_team for word in winner.split())):
            return 'WIN'
        else:
            return 'LOSS'
    
    elif ' +' in pick or ' -' in pick:
        # Spread bet
        parts = pick.rsplit(' ', 1)
        if len(parts) == 2:
            pick_team = parts[0].strip()
            try:
                pick_spread = float(parts[1])
            except:
                return 'PENDING'
        else:
            return 'PENDING'
        
        actual_spread = home_score - away_score
        
        # Determine if bet covered
        if (pick_team == home_team or 
            any(word in home_team for word in pick_team.split()) or
            any(word in pick_team for word in home_team.split())):
            # Picked home team
            covered = actual_spread + pick_spread > 0
        elif (pick_team == away_team or 
              any(word in away_team for word in pick_team.split()) or
              any(word in pick_team for word in away_team.split())):
            # Picked away team
            covered = -actual_spread + pick_spread > 0
        else:
            return 'PENDING'
        
        # Check for push
        if abs(actual_spread + pick_spread) < 0.01:
            return 'PUSH'
        elif covered:
            return 'WIN'
        else:
            return 'LOSS'
    
    return 'PENDING'

def verify_corrections():
    """
    Verify that corrections were applied correctly
    """
    print("\n" + "="*50)
    print("VERIFYING CORRECTIONS")
    print("="*50)
    
    conn = sqlite3.connect('/Users/sean/Downloads/sean-picks-app/backend/seanpicks.db')
    cursor = conn.cursor()
    
    # Check the specific games we corrected
    games_to_check = [
        ('Kansas City Royals', 'Los Angeles Angels'),
        ('Chicago Cubs', 'Atlanta Braves'),
    ]
    
    for home_team, away_team in games_to_check:
        cursor.execute("""
            SELECT home_team, away_team, home_score, away_score, pick, result, actual_spread
            FROM tracked_bets 
            WHERE home_team = ? AND away_team = ?
        """, (home_team, away_team))
        
        bet = cursor.fetchone()
        if bet:
            home_team, away_team, home_score, away_score, pick, result, actual_spread = bet
            print(f"\n{away_team} @ {home_team}")
            print(f"Score: {away_score}-{home_score} (Away-Home)")
            print(f"Pick: {pick}")
            print(f"Result: {result}")
            print(f"Actual Spread: {actual_spread}")
            
            # Verify the result is correct
            expected_result = calculate_bet_result(pick, home_team, away_team, home_score, away_score)
            if expected_result == result:
                print("✅ Verified correct")
            else:
                print(f"⚠️  Still incorrect! Expected: {expected_result}, Got: {result}")
    
    conn.close()

if __name__ == "__main__":
    fix_incorrect_scores()
    verify_corrections()