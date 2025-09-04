#!/usr/bin/env python3
"""
MANUAL PUBLIC BETTING DATA ENTRY
When scrapers fail, manually get the data from these sites
"""

import json
from datetime import datetime

class ManualPublicBetting:
    """Manually input public betting data from free sources"""
    
    def __init__(self):
        self.sources = {
            'covers': {
                'url': 'https://contests.covers.com/consensus/topconsensus/nfl/overall',
                'instructions': [
                    '1. Go to the URL above',
                    '2. Look for "Top Consensus" section',
                    '3. Find the percentages next to each team',
                    '4. Enter below'
                ]
            },
            'sportsbettingdime': {
                'url': 'https://www.sportsbettingdime.com/nfl/public-betting-trends/',
                'instructions': [
                    '1. Go to the URL above',
                    '2. Look for "Public Betting" percentages',
                    '3. Note both bet % and money %',
                    '4. Enter below'
                ]
            },
            'action_network': {
                'url': 'https://www.actionnetwork.com/nfl/public-betting',
                'instructions': [
                    '1. Go to the URL above (no login needed)',
                    '2. Look for betting percentages on each game',
                    '3. Some data visible without PRO',
                    '4. Enter what you can see'
                ]
            }
        }
        
        self.manual_data = {}
    
    def show_instructions(self):
        """Display instructions for manual data entry"""
        
        print("\n" + "="*60)
        print("📋 MANUAL PUBLIC BETTING DATA ENTRY")
        print("="*60 + "\n")
        
        for source, info in self.sources.items():
            print(f"\n🌐 {source.upper()}")
            print(f"URL: {info['url']}")
            print("Instructions:")
            for step in info['instructions']:
                print(f"  {step}")
        
        print("\n" + "="*60)
    
    def input_game_data(self):
        """Manually input data for a game"""
        
        print("\n📝 Enter Public Betting Data:")
        
        # Get game info
        away_team = input("Away Team: ").strip()
        home_team = input("Home Team: ").strip()
        
        # Get betting percentages
        print("\nBetting Percentages (enter 0 if unknown):")
        away_bet_pct = input(f"% of bets on {away_team}: ").strip()
        home_bet_pct = input(f"% of bets on {home_team}: ").strip()
        
        # Get money percentages if available
        print("\nMoney Percentages (optional, press Enter to skip):")
        away_money_pct = input(f"% of money on {away_team}: ").strip() or "0"
        home_money_pct = input(f"% of money on {home_team}: ").strip() or "0"
        
        # Store the data
        game_key = f"{away_team} @ {home_team}"
        self.manual_data[game_key] = {
            'away_team': away_team,
            'home_team': home_team,
            'away_bet_pct': float(away_bet_pct),
            'home_bet_pct': float(home_bet_pct),
            'away_money_pct': float(away_money_pct),
            'home_money_pct': float(home_money_pct),
            'timestamp': datetime.now().isoformat(),
            'source': 'manual_entry'
        }
        
        # Analyze for sharp action
        self.analyze_sharp_action(game_key)
        
        return self.manual_data[game_key]
    
    def analyze_sharp_action(self, game_key):
        """Detect sharp money from bet % vs money % discrepancy"""
        
        data = self.manual_data[game_key]
        
        # Skip if no money % data
        if data['away_money_pct'] == 0 or data['home_money_pct'] == 0:
            return
        
        # Sharp money indicators
        away_bet = data['away_bet_pct']
        away_money = data['away_money_pct']
        home_bet = data['home_bet_pct']
        home_money = data['home_money_pct']
        
        sharp_indicators = []
        
        # Check for bet/money discrepancy (sharp indicator)
        if away_bet < 40 and away_money > 50:
            sharp_indicators.append(f"🎯 Sharp money on {data['away_team']} (Low bets, high money)")
        
        if home_bet < 40 and home_money > 50:
            sharp_indicators.append(f"🎯 Sharp money on {data['home_team']} (Low bets, high money)")
        
        # Reverse line movement indicator
        if away_bet > 60 and away_money < 40:
            sharp_indicators.append(f"⚠️ Public heavy on {data['away_team']}, fade candidate")
        
        if home_bet > 60 and home_money < 40:
            sharp_indicators.append(f"⚠️ Public heavy on {data['home_team']}, fade candidate")
        
        if sharp_indicators:
            print("\n💰 SHARP MONEY DETECTED:")
            for indicator in sharp_indicators:
                print(f"  {indicator}")
        
        data['sharp_indicators'] = sharp_indicators
    
    def save_data(self, filename='manual_public_data.json'):
        """Save manually entered data"""
        
        with open(filename, 'w') as f:
            json.dump(self.manual_data, f, indent=2)
        
        print(f"\n✅ Data saved to {filename}")
    
    def load_data(self, filename='manual_public_data.json'):
        """Load previously entered data"""
        
        try:
            with open(filename, 'r') as f:
                self.manual_data = json.load(f)
            print(f"✅ Loaded {len(self.manual_data)} games from {filename}")
            return self.manual_data
        except FileNotFoundError:
            print("No saved data found")
            return {}
    
    def quick_entry_mode(self):
        """Quick entry for multiple games"""
        
        print("\n⚡ QUICK ENTRY MODE")
        print("Format: AwayTeam,HomeTeam,AwayBet%,HomeBet%,AwayMoney%,HomeMoney%")
        print("Example: Bills,Chiefs,35,65,25,75")
        print("(Money % optional, type 'done' when finished)")
        
        while True:
            entry = input("\nEnter data: ").strip()
            
            if entry.lower() == 'done':
                break
            
            try:
                parts = entry.split(',')
                if len(parts) >= 4:
                    away_team = parts[0].strip()
                    home_team = parts[1].strip()
                    away_bet = float(parts[2])
                    home_bet = float(parts[3])
                    away_money = float(parts[4]) if len(parts) > 4 else 0
                    home_money = float(parts[5]) if len(parts) > 5 else 0
                    
                    game_key = f"{away_team} @ {home_team}"
                    self.manual_data[game_key] = {
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_bet_pct': away_bet,
                        'home_bet_pct': home_bet,
                        'away_money_pct': away_money,
                        'home_money_pct': home_money,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'quick_entry'
                    }
                    
                    self.analyze_sharp_action(game_key)
                    print(f"✅ Added {game_key}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Check format and try again")
    
    def display_all_data(self):
        """Show all manually entered data"""
        
        if not self.manual_data:
            print("No data entered yet")
            return
        
        print("\n" + "="*60)
        print("📊 ALL PUBLIC BETTING DATA")
        print("="*60)
        
        for game, data in self.manual_data.items():
            print(f"\n🏈 {game}")
            print(f"  Bets: {data['away_team']} {data['away_bet_pct']}% vs {data['home_team']} {data['home_bet_pct']}%")
            
            if data['away_money_pct'] > 0:
                print(f"  Money: {data['away_team']} {data['away_money_pct']}% vs {data['home_team']} {data['home_money_pct']}%")
            
            if 'sharp_indicators' in data and data['sharp_indicators']:
                for indicator in data['sharp_indicators']:
                    print(f"  {indicator}")


def main():
    """Interactive manual data entry"""
    
    manual = ManualPublicBetting()
    
    while True:
        print("\n" + "="*60)
        print("🎰 MANUAL PUBLIC BETTING DATA SYSTEM")
        print("="*60)
        print("\n1. Show instructions for getting data")
        print("2. Enter single game data")
        print("3. Quick entry mode (multiple games)")
        print("4. Display all data")
        print("5. Save data")
        print("6. Load previous data")
        print("7. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            manual.show_instructions()
        elif choice == '2':
            manual.input_game_data()
        elif choice == '3':
            manual.quick_entry_mode()
        elif choice == '4':
            manual.display_all_data()
        elif choice == '5':
            manual.save_data()
        elif choice == '6':
            manual.load_data()
        elif choice == '7':
            break
        else:
            print("Invalid choice")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()