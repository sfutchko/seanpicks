#!/usr/bin/env python3
"""
Script to investigate incorrect game scores in the database.
Specifically looking for reversed home/away scores.
"""

import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Add the app path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def investigate_database(db_path):
    """
    Investigate all database files for score inconsistencies
    """
    print(f"Investigating database: {db_path}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, let's see what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {[table[0] for table in tables]}")
    print()
    
    # Look for tracked_bets table
    if 'tracked_bets' in [table[0] for table in tables]:
        print("TRACKED BETS TABLE ANALYSIS")
        print("-" * 40)
        
        # Get table schema
        cursor.execute("PRAGMA table_info(tracked_bets);")
        columns = cursor.fetchall()
        print("Table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        print()
        
        # Get all bets with results (focusing on completed games)
        cursor.execute("""
            SELECT 
                id, home_team, away_team, game_time, pick, 
                home_score, away_score, result, sport,
                confidence, spread
            FROM tracked_bets 
            WHERE result IN ('WIN', 'LOSS', 'PUSH')
            AND sport = 'MLB'
            ORDER BY game_time DESC
        """)
        
        bets = cursor.fetchall()
        print(f"Found {len(bets)} completed MLB bets")
        print()
        
        # Focus on September 3-4, 2025 games
        target_dates = ['2025-09-03', '2025-09-04']
        suspicious_games = []
        
        for bet in bets:
            bet_id, home_team, away_team, game_time, pick, home_score, away_score, result, sport, confidence, spread = bet
            
            # Parse game time
            if game_time:
                try:
                    game_date = datetime.fromisoformat(game_time.replace('Z', '+00:00')).date()
                    if game_date.strftime('%Y-%m-%d') not in target_dates:
                        continue
                except:
                    continue
            
            print(f"Game: {away_team} @ {home_team}")
            print(f"  Date: {game_time}")
            print(f"  Pick: {pick}")
            print(f"  Score: {away_score}-{home_score} (Away-Home)")
            print(f"  Result: {result}")
            print(f"  Sport: {sport}")
            
            # Analyze for potential score reversal
            if home_score is not None and away_score is not None and pick:
                # Check if result makes sense
                actual_spread = home_score - away_score  # Home perspective
                
                # Extract pick details
                if ' ML' in pick:
                    # Moneyline bet
                    pick_team = pick.replace(' ML', '').strip()
                    print(f"  Pick Team: {pick_team}")
                    
                    # Check if result makes sense
                    home_won = home_score > away_score
                    away_won = away_score > home_score
                    
                    if pick_team == home_team:
                        expected_result = 'WIN' if home_won else 'LOSS'
                    elif pick_team == away_team:
                        expected_result = 'WIN' if away_won else 'LOSS'
                    else:
                        # Try partial matching
                        if any(word in home_team for word in pick_team.split()) or any(word in pick_team for word in home_team.split()):
                            expected_result = 'WIN' if home_won else 'LOSS'
                            pick_team = home_team
                        elif any(word in away_team for word in pick_team.split()) or any(word in pick_team for word in away_team.split()):
                            expected_result = 'WIN' if away_won else 'LOSS'
                            pick_team = away_team
                        else:
                            expected_result = 'UNKNOWN'
                    
                    if expected_result != result and expected_result != 'UNKNOWN':
                        print(f"  ⚠️  SUSPICIOUS: Expected {expected_result}, got {result}")
                        print(f"  ⚠️  This suggests scores might be reversed!")
                        suspicious_games.append({
                            'bet_id': bet_id,
                            'home_team': home_team,
                            'away_team': away_team,
                            'current_home_score': home_score,
                            'current_away_score': away_score,
                            'pick': pick,
                            'result': result,
                            'expected_result': expected_result,
                            'game_time': game_time
                        })
                
                elif ' +' in pick or ' -' in pick:
                    # Spread bet
                    parts = pick.rsplit(' ', 1)
                    if len(parts) == 2:
                        pick_team = parts[0].strip()
                        try:
                            pick_spread = float(parts[1])
                        except:
                            pick_spread = spread if spread else 0
                        
                        print(f"  Pick Team: {pick_team}, Spread: {pick_spread}")
                        
                        # Calculate if bet should have won
                        if pick_team == home_team or any(word in home_team for word in pick_team.split()):
                            # Picked home team
                            covered = actual_spread + pick_spread > 0
                        elif pick_team == away_team or any(word in away_team for word in pick_team.split()):
                            # Picked away team
                            covered = -actual_spread + pick_spread > 0
                        else:
                            covered = None
                        
                        if covered is not None:
                            if abs(actual_spread + pick_spread) < 0.01:
                                expected_result = 'PUSH'
                            elif covered:
                                expected_result = 'WIN'
                            else:
                                expected_result = 'LOSS'
                            
                            if expected_result != result:
                                print(f"  ⚠️  SUSPICIOUS: Expected {expected_result}, got {result}")
                                print(f"  ⚠️  Actual spread: {actual_spread}, Pick spread: {pick_spread}")
                                suspicious_games.append({
                                    'bet_id': bet_id,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'current_home_score': home_score,
                                    'current_away_score': away_score,
                                    'pick': pick,
                                    'result': result,
                                    'expected_result': expected_result,
                                    'actual_spread': actual_spread,
                                    'pick_spread': pick_spread,
                                    'game_time': game_time
                                })
            print()
        
        print("SUSPICIOUS GAMES SUMMARY")
        print("=" * 40)
        if suspicious_games:
            print(f"Found {len(suspicious_games)} games with suspicious scores:")
            for game in suspicious_games:
                print(f"  {game['away_team']} @ {game['home_team']}")
                print(f"    Current Score: {game['current_away_score']}-{game['current_home_score']}")
                print(f"    Pick: {game['pick']}")
                print(f"    Current Result: {game['result']} (Expected: {game['expected_result']})")
                print(f"    Likely Fix: Swap scores to {game['current_home_score']}-{game['current_away_score']}")
                print()
        else:
            print("No suspicious games found in this database.")
    
    conn.close()
    return suspicious_games if 'suspicious_games' in locals() else []

def main():
    """
    Main investigation function
    """
    db_files = [
        '/Users/sean/Downloads/sean-picks-app/backend/sean_picks.db',
        '/Users/sean/Downloads/sean-picks-app/backend/sports_betting.db',
        '/Users/sean/Downloads/sean-picks-app/backend/seanpicks.db'
    ]
    
    all_suspicious = []
    
    for db_file in db_files:
        suspicious = investigate_database(db_file)
        all_suspicious.extend(suspicious)
        print("\n" + "="*80 + "\n")
    
    print("OVERALL SUMMARY")
    print("=" * 40)
    print(f"Total suspicious games found: {len(all_suspicious)}")
    
    if all_suspicious:
        print("\nGames that likely have reversed scores:")
        for game in all_suspicious:
            print(f"  {game['away_team']} @ {game['home_team']} - {game['game_time']}")
            print(f"    Current: {game['current_away_score']}-{game['current_home_score']} -> Fix: {game['current_home_score']}-{game['current_away_score']}")

if __name__ == "__main__":
    main()