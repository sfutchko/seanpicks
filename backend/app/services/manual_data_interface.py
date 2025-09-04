#!/usr/bin/env python3
"""
Manual Data Interface - Allows you to input REAL injury and public betting data
Since automated scraping is blocked, this lets you manually enter real data
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ManualDataInterface:
    """
    Interface for manually entering REAL data from legitimate sources
    This ensures we NEVER use fake or estimated data
    """
    
    def __init__(self):
        # Store manual data in JSON files
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'manual')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.injuries_file = os.path.join(self.data_dir, 'injuries.json')
        self.public_betting_file = os.path.join(self.data_dir, 'public_betting.json')
    
    def save_injury_data(self, team: str, injuries: Dict) -> bool:
        """
        Save REAL injury data that you manually checked from:
        - NFL.com official injury reports
        - Team official websites
        - ESPN injury reports
        
        Example:
        injuries = {
            'out': ['Patrick Mahomes', 'Travis Kelce'],
            'doubtful': ['Chris Jones'],
            'questionable': ['Tyreek Hill'],
            'source': 'NFL.com',
            'updated': '2024-01-15 14:30:00'
        }
        """
        try:
            # Load existing data
            if os.path.exists(self.injuries_file):
                with open(self.injuries_file, 'r') as f:
                    all_injuries = json.load(f)
            else:
                all_injuries = {}
            
            # Update with new data
            all_injuries[team] = {
                **injuries,
                'updated': datetime.now().isoformat()
            }
            
            # Save back
            with open(self.injuries_file, 'w') as f:
                json.dump(all_injuries, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving injury data: {e}")
            return False
    
    def save_public_betting(self, away_team: str, home_team: str, data: Dict) -> bool:
        """
        Save REAL public betting data that you manually checked from:
        - Action Network
        - Covers.com consensus
        - Vegas Insider
        - DraftKings/FanDuel app
        
        Example:
        data = {
            'home_percentage': 65,
            'away_percentage': 35,
            'total_bets': 15000,
            'source': 'Action Network',
            'updated': '2024-01-15 14:30:00'
        }
        """
        try:
            # Load existing data
            if os.path.exists(self.public_betting_file):
                with open(self.public_betting_file, 'r') as f:
                    all_betting = json.load(f)
            else:
                all_betting = {}
            
            # Create game key
            game_key = f"{away_team}_at_{home_team}"
            
            # Update with new data
            all_betting[game_key] = {
                **data,
                'updated': datetime.now().isoformat()
            }
            
            # Save back
            with open(self.public_betting_file, 'w') as f:
                json.dump(all_betting, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving public betting data: {e}")
            return False
    
    def get_injury_data(self, team: str) -> Dict:
        """Get manually entered injury data for a team"""
        try:
            if os.path.exists(self.injuries_file):
                with open(self.injuries_file, 'r') as f:
                    all_injuries = json.load(f)
                    
                if team in all_injuries:
                    # Check if data is recent (within 7 days)
                    updated = datetime.fromisoformat(all_injuries[team]['updated'])
                    if (datetime.now() - updated).days <= 7:
                        return all_injuries[team]
        except:
            pass
        
        # No data available
        return {
            'out': [],
            'doubtful': [],
            'questionable': [],
            'source': 'none',
            'impact_score': 0
        }
    
    def get_public_betting(self, away_team: str, home_team: str) -> Dict:
        """Get manually entered public betting data"""
        try:
            if os.path.exists(self.public_betting_file):
                with open(self.public_betting_file, 'r') as f:
                    all_betting = json.load(f)
                    
                game_key = f"{away_team}_at_{home_team}"
                if game_key in all_betting:
                    # Check if data is recent (within 3 days)
                    updated = datetime.fromisoformat(all_betting[game_key]['updated'])
                    if (datetime.now() - updated).days <= 3:
                        return all_betting[game_key]
        except:
            pass
        
        # No data available - return neutral
        return {
            'home_percentage': 50,
            'away_percentage': 50,
            'public_on_home': False,
            'public_percentage': 50,
            'sources_count': 0,
            'sources': ['No manual data entered'],
            'confidence': 'NONE'
        }
    
    def create_data_entry_script(self):
        """
        Create a simple script to help you enter data
        """
        script = '''#!/usr/bin/env python3
"""
Data Entry Script - Enter REAL injury and public betting data
Check these sources and enter the data:

INJURIES:
- https://www.nfl.com/injuries/
- https://www.espn.com/nfl/injuries
- Team official websites

PUBLIC BETTING:
- https://www.actionnetwork.com/nfl
- https://www.covers.com/sports/nfl/matchups
- https://www.vegasinsider.com/nfl/matchups/

Run this script and follow the prompts to enter real data.
"""

from manual_data_interface import ManualDataInterface

def main():
    mdi = ManualDataInterface()
    
    while True:
        print("\\n=== SEAN PICKS Data Entry ===")
        print("1. Enter injury data")
        print("2. Enter public betting data")
        print("3. Exit")
        
        choice = input("\\nChoice: ")
        
        if choice == '1':
            team = input("Team name: ")
            print("Enter injured players (comma separated)")
            out = input("OUT: ").split(',') if input else []
            doubtful = input("DOUBTFUL: ").split(',') if input else []
            questionable = input("QUESTIONABLE: ").split(',') if input else []
            source = input("Source (e.g., NFL.com): ")
            
            injuries = {
                'out': [p.strip() for p in out if p.strip()],
                'doubtful': [p.strip() for p in doubtful if p.strip()],
                'questionable': [p.strip() for p in questionable if p.strip()],
                'source': source
            }
            
            if mdi.save_injury_data(team, injuries):
                print("✓ Injury data saved")
        
        elif choice == '2':
            away = input("Away team: ")
            home = input("Home team: ")
            home_pct = float(input("Home betting %: "))
            away_pct = 100 - home_pct
            source = input("Source (e.g., Action Network): ")
            
            data = {
                'home_percentage': home_pct,
                'away_percentage': away_pct,
                'source': source
            }
            
            if mdi.save_public_betting(away, home, data):
                print("✓ Betting data saved")
        
        elif choice == '3':
            break

if __name__ == "__main__":
    main()
'''
        
        script_path = os.path.join(os.path.dirname(__file__), 'enter_data.py')
        with open(script_path, 'w') as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        
        print(f"Data entry script created: {script_path}")
        print("Run it with: python enter_data.py")
        
        return script_path