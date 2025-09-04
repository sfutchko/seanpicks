"""
SEAN PICKS - Injury Report Scraper
Gets real-time injury data that moves lines
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

class InjuryScraper:
    """Scrapes injury reports from multiple sources"""
    
    def __init__(self):
        self.injury_impact = {
            # Position: Point value impact on spread
            'QB': 7.0,      # Starting QB worth 7 points
            'RB': 2.5,      # RB1 worth 2.5 points
            'WR': 1.5,      # WR1 worth 1.5 points
            'OL': 2.0,      # Starting OLineman worth 2 points
            'EDGE': 2.0,    # Best pass rusher worth 2 points
            'CB': 1.5,      # CB1 worth 1.5 points
            'S': 1.0,       # Safety worth 1 point
            'LB': 1.0,      # Linebacker worth 1 point
            'K': 0.5,       # Kicker worth 0.5 points
        }
        
        self.status_multiplier = {
            'OUT': 1.0,          # Full impact
            'DOUBTFUL': 0.75,    # 75% likely out
            'QUESTIONABLE': 0.25, # 25% impact
            'PROBABLE': 0.0,      # No impact
        }
    
    def scrape_espn_injuries(self):
        """Scrape ESPN injury report"""
        injuries = {}
        
        # ESPN injury report URL
        url = "https://www.espn.com/nfl/injuries"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse injury tables by team
            teams = soup.find_all('div', class_='Table__Title')
            
            for team_section in teams:
                team_name = team_section.text.strip()
                injuries[team_name] = []
                
                # Get injury table for this team
                table = team_section.find_next('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            player_name = cols[0].text.strip()
                            position = cols[1].text.strip()
                            status = cols[2].text.strip().upper()
                            
                            # Calculate impact
                            pos_value = self.injury_impact.get(position, 0.5)
                            status_mult = self.status_multiplier.get(status, 0)
                            impact = pos_value * status_mult
                            
                            injuries[team_name].append({
                                'player': player_name,
                                'position': position,
                                'status': status,
                                'impact_points': impact
                            })
            
            return injuries
            
        except Exception as e:
            print(f"Error scraping ESPN: {e}")
            return {}
    
    def scrape_draftkings_news(self):
        """Scrape DraftKings for late-breaking injury news"""
        # DraftKings often has the fastest injury updates
        news = []
        
        try:
            url = "https://sportsbook.draftkings.com/leagues/football/nfl"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            # Look for injury badges or news items
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find player props that are suspended (usually means injury)
            suspended = soup.find_all('span', text='SUSPENDED')
            
            for item in suspended:
                parent = item.find_parent('div', class_='sportsbook-outcome-cell')
                if parent:
                    player = parent.find('span', class_='sportsbook-outcome-cell__label')
                    if player:
                        news.append({
                            'player': player.text,
                            'status': 'LIKELY OUT',
                            'source': 'DraftKings',
                            'timestamp': datetime.now().isoformat()
                        })
            
            return news
            
        except Exception as e:
            print(f"Error scraping DraftKings: {e}")
            return []
    
    def calculate_total_impact(self, team_injuries):
        """Calculate total point impact for a team's injuries"""
        total_impact = 0
        key_injuries = []
        
        for injury in team_injuries:
            if injury['impact_points'] > 0:
                total_impact += injury['impact_points']
                if injury['impact_points'] >= 2.0:  # Key player
                    key_injuries.append(f"{injury['player']} ({injury['position']})")
        
        return {
            'total_impact': round(total_impact, 1),
            'key_injuries': key_injuries,
            'injury_count': len([i for i in team_injuries if i['impact_points'] > 0])
        }
    
    def get_injury_adjustments(self, home_team, away_team):
        """Get spread adjustments based on injuries"""
        
        injuries = self.scrape_espn_injuries()
        
        home_impact = 0
        away_impact = 0
        
        if home_team in injuries:
            home_data = self.calculate_total_impact(injuries[home_team])
            home_impact = home_data['total_impact']
        
        if away_team in injuries:
            away_data = self.calculate_total_impact(injuries[away_team])
            away_impact = away_data['total_impact']
        
        # Spread adjustment (negative means move toward away team)
        spread_adjustment = away_impact - home_impact
        
        # Total adjustment (injuries generally lower totals)
        total_adjustment = -(home_impact + away_impact) * 0.5
        
        return {
            'spread_adjustment': spread_adjustment,
            'total_adjustment': total_adjustment,
            'home_injuries': home_data if home_team in injuries else None,
            'away_injuries': away_data if away_team in injuries else None,
            'confidence_boost': 0.02 if abs(spread_adjustment) > 3 else 0
        }
    
    def monitor_breaking_news(self):
        """Check for late-breaking injury news"""
        
        sources = []
        
        # Check multiple sources
        sources.append(self.scrape_draftkings_news())
        
        # Check Twitter for Schefter/Rapoport bombs
        twitter_keywords = [
            "ruled out",
            "won't play",
            "inactive",
            "game-time decision",
            "emergency QB"
        ]
        
        breaking_news = []
        for source in sources:
            if source:
                breaking_news.extend(source)
        
        return breaking_news


class QuickInjuryCheck:
    """Simplified injury checker for key players"""
    
    def __init__(self):
        # Manually track key players for quick checks
        self.key_players = {
            'Josh Allen': {'team': 'BUF', 'position': 'QB', 'value': 7.0},
            'Tua Tagovailoa': {'team': 'MIA', 'position': 'QB', 'value': 6.5},
            'Patrick Mahomes': {'team': 'KC', 'position': 'QB', 'value': 6.0},
            'Lamar Jackson': {'team': 'BAL', 'position': 'QB', 'value': 7.5},
            'Dak Prescott': {'team': 'DAL', 'position': 'QB', 'value': 5.5},
            'Jalen Hurts': {'team': 'PHI', 'position': 'QB', 'value': 7.0},
            'Justin Jefferson': {'team': 'MIN', 'position': 'WR', 'value': 2.5},
            'Tyreek Hill': {'team': 'MIA', 'position': 'WR', 'value': 3.0},
            'Christian McCaffrey': {'team': 'SF', 'position': 'RB', 'value': 4.0},
            'Nick Bosa': {'team': 'SF', 'position': 'EDGE', 'value': 2.5},
            'Micah Parsons': {'team': 'DAL', 'position': 'EDGE', 'value': 3.0},
        }
    
    def quick_check(self, team_abbr):
        """Quick check for key injuries on a team"""
        team_injuries = []
        
        for player, info in self.key_players.items():
            if info['team'] == team_abbr:
                # This would check a quick source
                # For now, return as healthy
                team_injuries.append({
                    'player': player,
                    'status': 'ACTIVE',
                    'impact': 0
                })
        
        return team_injuries


if __name__ == "__main__":
    print("=" * 60)
    print(" INJURY REPORT SCRAPER")
    print("=" * 60)
    
    scraper = InjuryScraper()
    
    print("\n📋 Injury Impact Values:")
    for position, value in scraper.injury_impact.items():
        print(f"  {position}: {value} points")
    
    print("\n🏥 Testing injury adjustment calculation:")
    
    # Example calculation
    sample_adjustment = scraper.get_injury_adjustments("Buffalo Bills", "Miami Dolphins")
    
    print(f"\nSpread Adjustment: {sample_adjustment['spread_adjustment']:+.1f} points")
    print(f"Total Adjustment: {sample_adjustment['total_adjustment']:+.1f} points")
    
    print("\n💡 How to use:")
    print("1. Call get_injury_adjustments() with team names")
    print("2. Add spread_adjustment to your line")
    print("3. Add confidence_boost if significant injuries")
    print("4. Check monitor_breaking_news() before kickoff")